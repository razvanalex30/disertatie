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
                   waitConnected=True)

    info( '*** Adding controller\n' )
    # Insert Controllers here

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)

    info('*** Add routers\n')
    # Insert Routers here

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip = '192.168.0.1/24', mac = '00:11:22:33:44:55', defaultRoute='via 192.168.0.2')
    h2 = net.addHost('h2', cls=Host, ip = '192.168.1.1/24', defaultRoute='via 192.168.0.3')
    h3 = net.addHost('h3', cls=Host, ip = '10.0.0.4/16')
    h4 = net.addHost('h4', cls=Host, ip = '20.0.0.4/16')
    h5 = net.addHost('h5', cls=Host, ip = '30.0.0.4/16')
    h6 = net.addHost('h6', cls=Host, ip = '40.0.0.4/16')

    info( '*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s2)
    net.addLink(h5, s2)
    net.addLink(h6, s2)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    # Insert switches controllers links here

    info( '*** Post configure switches and hosts\n')
    # Insert router config here

    logging.log(level=logging.INFO,
                msg="TOPOLOGY LINKS")
    for link in net.links:
        logging.log(level=logging.INFO,
                    msg=f"{link.intf1.name} <-> {link.intf2.name} ({link.intf1.node.name} {link.intf2.node.name})")

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    logfile = "/home/razvan/Disertatie/disertatie/TopologiesScripts/user_1/created/TOPO_NEW8/logfile.log"
    logging.basicConfig(format='%(message)s', filename=logfile, filemode='a', level=logging.INFO)
    myNetwork()