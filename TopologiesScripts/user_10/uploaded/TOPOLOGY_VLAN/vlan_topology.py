from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.node import OVSKernelSwitch, Host, Controller
import logging



def create_vlan_interface(host, intf_name, vlan_id, ip_address):
    host.cmd(f'vconfig add {intf_name} {vlan_id}')
    host.cmd(f'ip addr add {ip_address} dev {intf_name}.{vlan_id}')
    host.cmd(f'ip link set {intf_name}.{vlan_id} up')

def topology():
    net = Mininet()

    net.addController(name='default_controller', controller=Controller, ip='127.0.0.1', port=6653)

    # Add switches
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)

    # Add hosts
    h1 = net.addHost('h1', cls=Host, ip=None, mac = 'AA:BB:AA:BB:AA:BB')
    h2 = net.addHost('h2', cls=Host, ip=None, mac = '22:22:22:22:22:22')
    h3 = net.addHost('h3', cls=Host, ip=None, mac = 'CC:DD:CC:DD:CC:DD')
    h4 = net.addHost('h4', cls=Host, ip=None, mac = '44:44:44:44:44:44')

    # Add links
    net.addLink(h1, s1, cls=TCLink, bw=10, delay="2ms", loss=2)
    net.addLink(h3, s1, cls=TCLink, bw=10, delay="2ms", loss=2)
    net.addLink(s1, s2, cls=TCLink, bw=100, delay="2ms", loss=2)
    net.addLink(s2, s3, cls=TCLink, bw=100, delay="2ms", loss=2)
    net.addLink(h2, s3, cls=TCLink, bw=10, delay="2ms", loss=2)
    net.addLink(h4, s3, cls=TCLink, bw=10, delay="2ms", loss=2)

    net.build()
    info('*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    # Create VLAN interfaces and assign IPs using vconfig
    create_vlan_interface(h1, 'h1-eth0', 10, '192.168.10.1/24')
    create_vlan_interface(h2, 'h2-eth0', 10, '192.168.10.2/24')
    create_vlan_interface(h3, 'h3-eth0', 20, '192.168.10.3/24')
    create_vlan_interface(h4, 'h4-eth0', 20, '192.168.10.4/24')

    # Start network
    net.start()

    # Open Mininet CLI
    CLI(net)

    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    logfile = "/home/razvan/Disertatie/disertatie/TopologiesScripts/user_10/uploaded/TOPOLOGY_VLAN/logfile.log"
    logging.basicConfig(format='%(message)s', filename=logfile, filemode='a', level=logging.INFO)
    topology()