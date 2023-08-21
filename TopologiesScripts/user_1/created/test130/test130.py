
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink, Intf
from mininet.node import OVSSwitch, Controller, RemoteController, Node
import logging


class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    # pylint: disable=arguments-differ
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()



class NetworkTopo(Topo):
    # Builds network topology
    def build(self, **_opts):
        s1 = self.addSwitch('s1', failMode='standalone')
        h1 = self.addHost('h1', ip = '192.168.0.1/24', mac = '00:11:22:33:44:55', defaultRoute='via 192.168.0.2')
        h2 = self.addHost('h2', ip = '192.168.1.1/24', defaultRoute='via 192.168.0.3')
        h3 = self.addHost('h3', ip = '10.0.0.4/16')
        h4 = self.addHost('h4', ip = '22.22.22.12/16')

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(topo=topo,
                  waitConnected=True, link=TCLink)  # controller is used by s1-s3
    net.start()
    

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()