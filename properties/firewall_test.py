from properties.firewall import Firewall
import unittest

class Test_firewall(unittest.TestCase):
    def setUp(self):
        self.fw = Firewall('test', 'eth0')

    def tearDown(self):
        self.fw.stop()

    def test_can_set_rule(self):
        out, err = self.fw._set_rule()
        self.assertEqual(err, b'')

    def test_can_del_rule(self):
        self.test_can_set_rule()
        out, err = self.fw._del_rule()
        self.assertEqual(err, b'')
