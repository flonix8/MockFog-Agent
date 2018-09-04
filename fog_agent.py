#!/usr/bin/env python3

import logging, argparse, netifaces, sys
import re
import subprocess
from threading import Thread

import pingparsing

from properties.tc_config import *
from properties.firewall import *
from properties.test_property import *
from fog_api import create_app
from queue import Queue

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# List of all known Properties
_known_properties=[
            TestProperty("TestProperty")
]

class FogAgent(object):

    ping_running = False

    def __init__(self, hostname, iface, port, properties):
        self.hostname = hostname
        self.api_iface = iface
        self.api_port = port
        self.known_properties = properties
        self.rtt_dict = {}

    def property_running(self, property):
        return property.status()

    def running_properties(self):
        running = []
        for property in self.known_properties:
            if self.property_running(property):
                running.append(property)

        return running

    def start_property(self, property, parameter):
        property.start(parameter)
        if self.property_running(property) == True:
            logging.info("Property %s started " % (property.name))
            return True
        else:
            logging.error("Property %s not started" % (property.name))
            return False

    def stop_property(self, property):
        if not self.property_running(property):
            logging.info("Property %s is not running" % (property.name))
            return True

        property.stop()
        if not self.property_running(property):
            logging.info("Stopped property %s" % (property.name) )
            return True
        else:
            logging.error("Couldn't stop property %s - still running" % (property.name))
            return False

    def update_property(self, property, parameter):
        if not self.property_running(property):
            logging.info("Property %s is not running" % (property.name))
            return False

        if property.update(parameter):
            logging.info("Updated property %s" % (property.name) )
            return True
        else:
            logging.error("Couldn't update property %s - still running" % (property.name))
            return False

    def get_property(self, name):
        for prop in self.known_properties:
            if prop.name == name:
                return prop
        return None


    def ping_hosts(self, num_of_threads, host_list, seconds):
        hosts = Queue()
        results = Queue()
        self.ping_running = True

        for i in range (num_of_threads):
            worker = Thread(target=self.ping_thread, args=(i, hosts, seconds, results))
            worker.setDaemon(True)
            worker.start()

        for host in host_list:
            hosts.put(host)

        hosts.join()
        while not results.empty():
            self.update_rtt_dict(results.get())
        logging.info("Ping ended")
        self.ping_running = False


    def ping_thread(self, thread, hosts, seconds, results):
        while True:
            host = hosts.get()
            logging.info(host)
            hostname = host['hostname']
            ip = host['ip']
            logging.info("Thread %s: Starting Ping to %s at %s for %s seconds" % (thread, hostname, ip, seconds))
            cmd =  ['ping', '-w', seconds, ip]
            output = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            parser = pingparsing.PingParsing()
            stats = parser.parse(output.stdout.read())

            tmp = {
                hostname: stats.as_dict(),
            }
            results.put(tmp)
            hosts.task_done()

    def update_rtt_dict(self, host):
        hostname = list(host)[0]
        logging.info("Adding RTT statistics for host %s" % (hostname))
        self.rtt_dict.update(host)

    def get_rtt_host(self, host):
        return self.rtt_dict.get(host)

    def get_all_rtts(self):
        return self.rtt_dict


def get_ip(iface):
    try:
        if netifaces.ifaddresses(iface):
            ip = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
            logging.info("Using %s as API IP" % (ip))
            return ip
    except ValueError:
        logging.error("Interface %s not known" % (iface))


def fog_agent_main(args):

    parser = argparse.ArgumentParser()

    parser.add_argument("-hostname", dest='hostname', required=True, help="Hostname of the host")
    parser.add_argument("-iface", dest='iface', required=True, help="API Interface")
    parser.add_argument("-port", dest='port', required=True, help="API Port")

    # get arguments
    args = parser.parse_args()

    # check if API interfaces exists and get IP
    api_ip = get_ip(args.iface)

    properties = _known_properties

    if api_ip is not None:
        logging.info("Starting agent on Host %s at %s:%s" % (args.hostname, api_ip, args.port))
        agent = FogAgent(args.hostname, api_ip, args.port, properties)
        logging.info("Started")

        # initialize tc-config and firewall property
        ifaces = netifaces.interfaces()
        iface_candidates = []
        for face in ifaces:
            if (face != args.iface) and (face != 'lo'):
                iface_candidates.append(face)

        if len(iface_candidates)==1:
            tc_iface = iface_candidates[0]
        else:
            tc_iface = args.iface
        logging.info(f"Initializing TC on the {tc_iface} network interface.")
        properties.append(Tc_config('TC', tc_iface))
        properties.append(Firewall('Firewall', tc_iface))
        logging.info("Known properties: %s" % [p.name for p in properties])

        # start api
        api = create_app(agent)
        api.run(host=api_ip, port=args.port, threaded=True)

if __name__ == "__main__":
    fog_agent_main(sys.argv[1:])
