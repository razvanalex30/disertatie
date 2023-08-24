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
    # Insert Switches here

    info('*** Add routers\n')
    # Insert Routers here

    info( '*** Add hosts\n')
    # Insert Hosts here

    info( '*** Add links\n')
    # Insert links here

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
    logfile = "#LOGFILE"
    logging.basicConfig(format='%(message)s', filename=logfile, filemode='a', level=logging.INFO)
    myNetwork()