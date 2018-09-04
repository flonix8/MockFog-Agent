from properties.property import Property
from subprocess import Popen
import subprocess as sc

class Firewall(object):
    def __init__(self, name, iface):
        """
        iface : network interface where to apply the firewall
        """
        self.name = name
        self._iface = iface
        self.running = False

    @property
    def parameter(self):
        return {'active': self.running}

    def start(self, parameter):
        if not ('active' in parameter):
            return False
        if parameter['active']:
            self._set_rule()
            self.running = True
            self._active = True
        return True
        
    def update(self, parameter):
        if not ('active' in parameter):
            return False
        if parameter['active'] and not self.running:
            self._set_rule()
            self._active = True
        if not parameter['active'] and self.running:
            self._del_rule()
            self._active = False
        return True

    def stop(self):
        self._del_rule()
        self.running = False
        self._active = False
        return True

    def status(self):
        return self.running

    def _set_rule(self, ip="0.0.0.0/0"):
        cmd = f"iptables -A OUTPUT -o {self._iface} -s {ip} -j DROP"
        pipe = sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE)
        out, err = pipe.communicate()
        cmd = f"iptables -A INPUT -i {self._iface} -s {ip} -j DROP"
        pipe = sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE)
        out1, err1 = pipe.communicate()
        return out+out1, err+err1

    def _del_rule(self, ip="0.0.0.0/0"):
        cmd = f"iptables -D OUTPUT -o {self._iface} -s {ip} -j DROP"
        pipe = sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE)
        out, err = pipe.communicate()
        cmd = f"iptables -D INPUT -i {self._iface} -s {ip} -j DROP"
        pipe = sc.Popen(cmd.split(), stdout=sc.PIPE, stderr=sc.PIPE)
        out1, err1 = pipe.communicate()
        return out+out1, err+err1

    def __str__(self):
        return self.name

