
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink, Intf, Link
from mininet.term import makeTerm
from mininet.node import OVSSwitch, Controller, RemoteController, Node
import logging
import pexpect


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
        r1 = self.addNode('r1', cls=LinuxRouter)



        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        # self.addLink(s1, c1)
        self.addLink(r1, s1)
        # self.addLink(s1, c2)

def run_links():
    "Run the 'links' command in the CLI"
    info("*** Running 'links' command...\n")
    CLI.do_links(None)


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(topo=topo,
                  waitConnected=True, link=TCLink)  # controller is used by s1-s3
    net.start()
    r1 = net['r1']
    r1.cmd('ip link add r1-eth0  type dummy')
    r1.cmd('ip addr add 192.168.0.1/24 dev r1-eth0 ')
    r1.cmd('ip link set dev r1-eth0  up')

    c1 = net.addController('c1', ip='192.168.0.1', port=1234)
    c2 = net.addController('c2', port=555)

    c1.start()
    c2.start()
    s1 = net['s1']
    s1.start([c1])
    logging.log(level=logging.INFO,
                msg="TOPOLOGY LINKS")
    for link in net.links:
        logging.log(level=logging.INFO, msg=f"{link.intf1.name} <-> {link.intf2.name} ({link.intf1.node.name} {link.intf2.node.name})")
    mininet_interface_names = []
    for link in net.links:
        intf1_name = link.intf1.name
        intf2_name = link.intf2.name
        mininet_interface_names.extend([intf1_name, intf2_name])

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    logging.basicConfig(format='%(message)s', filename='/home/razvan/Disertatie/disertatie/TopologiesScripts/user_1/created/test133/logfile.log', filemode='a', level=logging.INFO)
    run()