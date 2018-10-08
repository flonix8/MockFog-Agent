from properties.property import Property
from subprocess import Popen
import subprocess as sc

class Tc_config(Property):

    def __init__(self, name, iface):
        """
        iface : network interface where to apply tc
        """
        super(Tc_config, self).__init__(name)
        self._iface = iface
        self._rules = []
        self._out_rate = '1gbps'
        self._in_rate = '1gbps'
        self._running = False

    @property
    def parameter(self):
        if self._running:
            return {
                'out_rate':self._out_rate,
                'in_rate':self._in_rate,
                'rules':self._rules
            }
        else:
            return {
                'out_rate':'null',
                'in_rate':'null',
                'rules':[]
            }

    def start(self, parameter):
        p = parameter
        self._rules = p['rules']
        self._in_rate = p['in_rate']
        self._out_rate = p['out_rate']

        self._set_inc()
        self._set_out()
        for id in range(len(self._rules)):
            self._set_rule(id)
        self._running = True
        return True

    def stop(self):
        cmd = (
            f"tc qdisc del dev {self._iface} root\n"
            f"tc qdisc del dev {self._iface} ingress\n"
            f"tc qdisc del dev uplink root\n"
            f"ip link del dev uplink"
        )
        pipe = Popen(cmd, shell=True, stderr=sc.DEVNULL)
        out, err = pipe.communicate()
        self._running = False
        return True

    def update(self, parameter):
        p = parameter
        if 'in_rate' in p:
            self._in_rate = p['in_rate']
        if 'out_rate' in p:
            self._out_rate = p['out_rate']
        rules = p['rules']

        shall_delete = False
        if len(rules)!=len(self._rules):
            shall_delete = True
            self._rules = rules
        else:
            # update self._rules and check if dst_nets match
            for rule in rules:
                id = self._get_rule_by_dst_net(rule['dst_net'])
                if id>=0:
                    self._rules[id] = rule
                else:
                    shall_delete = True
                    self._rules = rules
                    break

        if shall_delete:
            self.stop()
            self._set_inc()
            self._set_out()
            for id in range(len(self._rules)):
                self._set_rule(id)
            self._running = True
        else: #can update every rule
            self._upd_inc()
            self._upd_out()
            for id in range(len(self._rules)):
                self._upd_rule(id)

        return True

    def status(self):
        return self._running

    def _get_rule_by_dst_net(self, dst_net):
        for id,rule in enumerate(self._rules):
            if rule['dst_net']==dst_net:
                return id
        return -1

    def _upd_inc(self):
        cmd = (
            f"tc class change dev uplink parent 1: classid 1:1"
            f"  htb rate {self._in_rate} ceil {self._in_rate}"
        )
        pipe = Popen(cmd, shell=True, stdout=sc.PIPE, stderr=sc.PIPE)
        return pipe.communicate()

    def _upd_out(self):
        cmd = (
            f"tc class change dev {self._iface} parent 1: classid 1:1"
            f"  htb rate {self._out_rate} ceil {self._out_rate}"
        )
        pipe = Popen(cmd, shell=True, stdout=sc.PIPE, stderr=sc.PIPE)
        return pipe.communicate()

    def _upd_rule(self, id):
        rule = self._rules[id]
        cmd = (
            f"tc qdisc replace dev {self._iface} parent 1:1{id}"
        ) + self._netem_qdisc(rule)
        pipe = Popen(cmd, shell=True, stdout=sc.PIPE, stderr=sc.PIPE)
        return pipe.communicate()

    def _set_inc(self):
        cmd = (
            f"ip link add uplink type ifb\n"
            f"ip link set dev uplink up\n"
            f"tc qdisc add dev {self._iface} ingress\n"
            f"tc filter add dev {self._iface} parent ffff: protocol ip u32"
            f"  match u32 0 0"
            f"  flowid 1:"
            f"  action mirred egress redirect dev uplink\n"
            f"tc qdisc add dev uplink root handle 1: htb default 1\n"
            f"tc class add dev uplink parent 1: classid 1:1"
            f"  htb rate {self._in_rate} ceil {self._in_rate}"
        )
        pipe = Popen(cmd, shell=True, stderr=sc.PIPE, stdout=sc.PIPE)
        return pipe.communicate()

    def _set_out(self):
        cmd = (
            f"tc qdisc add dev {self._iface} root handle 1: htb\n"
            f"tc class add dev {self._iface} parent 1: classid 1:1"
            f"  htb rate {self._out_rate} ceil {self._out_rate}"
        )
        pipe = Popen(cmd, shell=True, stdout=sc.PIPE, stderr=sc.PIPE)
        return pipe.communicate()

    def _set_rule(self, id):
        rule = self._rules[id]
        if 'out_rate' in rule:
            out_rate = rule['out_rate']
        else: out_rate = self._out_rate
        cmd = (
            f"tc class add dev {self._iface} parent 1:1 classid 1:1{id}"
            f"  htb rate {out_rate} ceil {out_rate} \n"
            f"tc qdisc add dev {self._iface} parent 1:1{id} handle 2{id}:"
        ) + self._netem_qdisc(rule) + '\n' + (
            f"tc filter add dev {self._iface} protocol ip parent 1:0 prio 1 u32"
            f"  match ip dst {rule['dst_net']}"
            f"  flowid 1:1{id}"
        )
        pipe = Popen(cmd, shell=True, stdout=sc.PIPE, stderr=sc.PIPE)
        return pipe.communicate()

    def _netem_qdisc(self, rule):
        n = []
        n.append(' netem')
        # add "delay Xns Yns"
        if 'delay' in rule:
            n.append('delay')
            n.append(rule['delay'])
            if 'dispersion' in rule:
                n.append(rule['dispersion'])
                n.append("distribution normal")
        if 'loss' in rule:
            n.append('loss')
            n.append(rule['loss'])
        if 'corrupt' in rule:
            n.append('corrupt')
            n.append(rule['corrupt'])
        if 'duplicate' in rule:
            n.append('duplicate')
            n.append(rule['duplicate'])
        if 'reordering' in rule:
            n.append('reordering')
            n.append(rule['reordering'])
        return ' '.join(n)
