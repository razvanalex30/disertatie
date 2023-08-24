
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


class MultiSwitch( OVSSwitch ):
    "Custom Switch() subclass that connects to different controllers"
    def start( self, controllers ):
        return OVSSwitch.start( self, [ cmap[ self.name ] ] )



class NetworkTopo(Topo):
    # Builds network topology
    def build(self, **_opts):
        # Insert your code here

        # Insert links here


def run():
    "Test linux router"
    topo = NetworkTopo()
    net = Mininet(topo=topo, switch=OVSSwitch,
                  waitConnected=True, link=TCLink)  # controller is used by s1-s3
    net.start()
    # Insert router code here

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    logfile = "#LOGFILE"
    logging.basicConfig(format='%(message)s', filename=logfile, filemode='a', level=logging.INFO)
    run()