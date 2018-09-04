from properties.tc_config import Tc_config
import unittest

class Test_Tc_config(unittest.TestCase):
    def setUp(self):
        self.tc = Tc_config('test', 'enp0s3')

    def tearDown(self):
        self.tc.stop()

    def test_can_set_inc(self):
        self.tc._in_rate = '1000kbps'
        out, err = self.tc._set_inc()
        self.assertEqual(err, b'')
    
    def test_can_set_out(self):
        self.tc._out_rate = '1000kbps'
        out, err = self.tc._set_out()
        self.assertEqual(err, b'')
    
    def test_can_set_rule(self):
        self.test_can_set_inc()
        self.test_can_set_out()
        self.tc._rules.append({
            'dst_net':'100.100.100.100/24',
            'delay':'10ms',
            'dispersion':'5ms'
        })
        out, err = self.tc._set_rule(0)
        print(err)
        self.assertEqual(err, b'')

    def test_can_start(self):
        status = self.tc.start({
            'in_rate': '10gbps',
            'out_rate': '10gbps',
            'rules': [
                {
                    'dst_net':'100.100.100.100/24',
                    'delay':'10ms',
                    'dispersion':'5ms'
                },{
                    'dst_net':'13.123.24.123/16',
                    'delay':'15ms',
                    'dispersion':'10ms'
                }
            ]
        })
        self.assertTrue(self.tc.status())
    
    def test_can_upd_inc(self):
        self.test_can_start()
        self.tc._in_rate = '1000kbps'
        out, err = self.tc._upd_inc()
        self.assertEqual(err, b'')
    
    def test_can_upd_out(self):
        self.test_can_start()
        self.tc._in_rate = '100mbps'
        out, err = self.tc._upd_out()

    def test_can_upd_rule(self):
        self.test_can_start()
        out, err = self.tc._upd_rule(0)
        self.assertEqual(err, b'')
        out, err = self.tc._upd_rule(1)
        self.assertEqual(err, b'')
    
    def test_can_upd_rule_with_latency_only(self):
        self.test_can_start()
        self.tc._rules[0] = {
            'dst_net':'13.123.24.123/16',
            'delay':'15ms'
        }
        self.test_can_upd_rule()
    
    def test_adds_new_rule_if_update_with_new_dst_net(self):
        self.test_can_start()
        self.tc.update({
            'in_rate':'100kbps',
            'rules': [
                {
                    'dst_net':'2.2.4.5/24',
                    'delay':'24ms',
                    'dispersion':'10ms'
                }
            ]
        })
        self.assertEqual(len(self.tc._rules), 3)

    def test_updates_rule_if_update_with_known_dst_net(self):
        self.test_can_start()
        self.tc.update({
            'in_rate':'100kbps',
            'rules':[
                {
                    'dst_net':'13.123.24.123/16',
                    'delay':'24ms',
                    'dispersion':'10ms'
                }
            ]
        })
        self.assertEqual(len(self.tc._rules), 2)

if __name__ == '__main__':
    unittest.main()
