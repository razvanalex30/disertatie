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
    c1 = net.addController( name='c1', controller=Controller, port=6633 )
    c2 = net.addController( name='c2', controller=Controller, port=6634 )

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s4 = net.addSwitch('s4', cls=OVSKernelSwitch)

    info('*** Add routers\n')
    r5 = net.addHost('r5', cls=Node, ip=None)
    r5.cmd('sysctl -w net.ipv4.ip_forward=1')
    r6 = net.addHost('r6', cls=Node, ip=None)
    r6.cmd('sysctl -w net.ipv4.ip_forward=1')

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip = '10.0.0.2/24', mac = 'AA:BB:AA:BB:AA:BB', defaultRoute='via 10.0.0.1')
    h2 = net.addHost('h2', cls=Host, ip = '10.0.0.3/24', mac = '22:22:22:22:22:22', defaultRoute='via 10.0.0.1')
    h3 = net.addHost('h3', cls=Host, ip = '20.0.0.2/24', mac = 'CC:DD:CC:DD:CC:DD', defaultRoute='via 20.0.0.1')
    h4 = net.addHost('h4', cls=Host, ip = '20.0.0.3/24', mac = '44:44:44:44:44:44', defaultRoute='via 20.0.0.1')

    info( '*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s2)
    net.addLink(h4, s2)
    net.addLink(s1, s3)
    net.addLink(r6, s4)
    net.addLink(s3, r5)
    net.addLink(r5, r6)
    net.addLink(s4, s2)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c1])
    net.get('s2').start([c2])

    info( '*** Post configure switches and hosts\n')
    r5.cmd('ip addr add 10.0.0.1/24 broadcast 10.0.0.255 dev r5-eth0 ')
    r5.cmd('ip addr add 30.0.0.1/24 broadcast 30.0.0.255 dev r5-eth1 ')
    r6.cmd('ip addr add 20.0.0.1/24 broadcast 20.0.0.255 dev r6-eth0 ')
    r6.cmd('ip addr add 30.0.0.2/24 broadcast 30.0.0.255 dev r6-eth1 ')

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
    logfile = "/home/razvan/Disertatie/disertatie/TopologiesScripts/user_10/created/TOPO_STATIC_ROUTE/logfile.log"
    logging.basicConfig(format='%(message)s', filename=logfile, filemode='a', level=logging.INFO)
    myNetwork()