from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import logging




def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   waitConnected=False)

    info('*** Adding default controllers\n')
    net.addController(name='default_controller', controller=Controller, ip='127.0.0.1', port=6653)


    info( '*** Adding controllers\n' )
    c1 = net.addController( name='c1', controller=Controller, ip='128.0.0.1', port=555 )

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)

    info('*** Add routers\n')
    r1 = net.addHost('r1', cls=Node)
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2 = net.addHost('r2', cls=Node, ip='10.0.0.2/16')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip = '10.0.0.1/24', mac = '00:11:22:33:44:55')
    h2 = net.addHost('h2', cls=Host, ip = '10.0.0.2/24')
    h3 = net.addHost('h3', cls=Host, ip = '10.0.0.3/24')

    info( '*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(r1, s1)
    net.addLink(r2, s1)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c1])

    info( '*** Post configure switches and hosts\n')
    r1.cmd('ip link add r1-eth2  type dummy')
    r1.cmd('ip addr add 192.168.0.1/24 dev r1-eth2 ')
    r1.cmd('ip link set dev r1-eth2  up')

    logging.log(level=logging.INFO,
                msg="TOPOLOGY LINKS")
    for link in net.links:
        logging.log(level=logging.INFO,
                    msg=f"{link.intf1.name} <-> {link.intf2.name} ({link.intf1.node.name} {link.intf2.node.name})")

    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    logfile = "/home/razvan/Disertatie/disertatie/TopologiesScripts/user_1/created/TOPO_NEW12/logfile.log"
    logging.basicConfig(format='%(message)s', filename=logfile, filemode='a', level=logging.INFO)
    myNetwork()