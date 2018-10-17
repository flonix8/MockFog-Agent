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

    def status(self):
        return self._running

    def start(self, parameter):
        p = parameter
        if self._running:
            self.stop()

        self._init_firewall()

        self._rules = p['rules']
        if 'in_rate' in p:
            self._in_rate = p['in_rate']
        if 'out_rate' in p:
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

    def _init_firewall(self):
        cmd = "iptables -F"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()
        cmd = "iptables -P OUTPUT DROP"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()
        cmd = "iptables -P FORWARD DROP"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()
        cmd = "iptables -P INPUT DROP"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A OUTPUT -o !{self._iface} -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A INPUT -i !{self._iface} -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A OUTPUT -d 10.0.1.0/24 -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A INPUT -s 10.0.1.0/24 -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A INPUT -i lo -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A OUTPUT -o lo -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A INPUT -p tcp -m tcp --dport 22 -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()

        cmd = f"iptables -A OUTPUT -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT"
        sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE).communicate()


    def update(self, parameter):
        return self.start(parameter)

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
        out1, err1 = pipe.communicate()

        cmd = f"iptables -A OUTPUT -d {rule['dst_net']} -j ACCEPT"
        pipe = sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE)
        out2, err2 = pipe.communicate()

        cmd = f"iptables -A INPUT -s {rule['dst_net']} -j ACCEPT"
        pipe = sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE)
        out3, err3 = pipe.communicate()

        return out1+out2+out3, err1+err2+err3

    def _netem_qdisc(self, rule):
        n = []
        n.append(' netem')
        # add "delay Xns Yns"
        if 'delay' in rule and float(self._get_digits(rule['delay']))>0:
            n.append('delay')
            n.append(rule['delay'])
            if 'dispersion' in rule and float(self._get_digits(rule['dispersion']))>0:
                n.append(rule['dispersion'])
                n.append("distribution normal")

        self._append_prob(n, 'loss', rule['loss'])
        self._append_prob(n, 'corrupt', rule['corrupt'])
        self._append_prob(n, 'duplicate', rule['duplicate'])
        self._append_prob(n, 'reorder', rule['reorder'])

        if len(n)>1:
            return ' '.join(n)
        else:
            return ' '

    def _append_prob(self, n, key, val):
        str_val = str(val).replace('%','',1).strip()
        if str_val.replace('.','',1).isdigit() and float(str_val) > 0:
            n.append(key)
            n.append(str_val)

    def _get_digits(self, value):
        return ''.join([i for i in str(value) if i.isdigit()])
