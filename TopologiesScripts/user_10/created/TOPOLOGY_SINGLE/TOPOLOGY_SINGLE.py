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
    # Insert Controllers here

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)

    info('*** Add routers\n')
    # Insert Routers here

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip = '10.0.0.1/24', mac = 'AA:BB:AA:BB:AA:BB')
    h2 = net.addHost('h2', cls=Host, ip = '10.0.0.2/24', mac = '22:22:22:22:22:22')
    h3 = net.addHost('h3', cls=Host, ip = '10.0.0.3/24', mac = 'CC:DD:CC:DD:CC:DD')
    h4 = net.addHost('h4', cls=Host, ip = '10.0.0.4/24', mac = '44:44:44:44:44:44')

    info( '*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    net.addLink(h4, s1)

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

    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    logfile = "/home/razvan/Disertatie/disertatie/TopologiesScripts/user_10/created/TOPOLOGY_SINGLE/logfile.log"
    logging.basicConfig(format='%(message)s', filename=logfile, filemode='a', level=logging.INFO)
    myNetwork()