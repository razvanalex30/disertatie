from __future__ import print_function


from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.cli import CLI
import logging

class NetworkTopo(Topo):
    # Builds network topology
    def build(self, **_opts):
        s1 = self.addSwitch('s1', failMode='standalone')
        s2 = self.addSwitch('s2', failMode='standalone')
        s3 = self.addSwitch('s3', failMode='standalone')
        h1 = self.addHost('h1', ip = '192.168.0.1/24', mac = '00:11:22:33:44:55', defaultRoute='via 192.168.0.2')
        h2 = self.addHost('h2', ip = '192.168.1.1/24', defaultRoute='via 192.168.0.3')
        h3 = self.addHost('h3', ip = '10.0.0.4/16')