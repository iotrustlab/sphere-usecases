"""
SPHERE Network Model for OpenPLC Water Treatment Scenario

This model defines a 2-node experiment:
- controller: Runs OpenPLC controller program
- simulator: Runs OpenPLC simulator program

Both nodes communicate via Modbus TCP on a shared network.
"""
from mergexp import *

# Create a network topology object
net = Network('openplc-water', addressing==ipv4, routing==static)

# Create nodes with Docker support
# Using moddeter VMs with extra disk for Docker images
# Ubuntu 22.04 image with sufficient resources for OpenPLC containers
controller = net.node(
    'controller',
    image == '2204',           # Ubuntu 22.04
    proc.cores >= 2,           # At least 2 cores
    memory.capacity >= gb(4),  # At least 4GB RAM
    disk.capacity == gb(10),   # Extra 10GB disk at /dev/vdb for Docker
)

simulator = net.node(
    'simulator',
    image == '2204',
    proc.cores >= 2,
    memory.capacity >= gb(4),
    disk.capacity == gb(10),   # Extra 10GB disk at /dev/vdb for Docker
)

# Create a link connecting the two nodes
# This creates the Modbus communication network
link = net.connect([controller, simulator])

# Assign IP addresses on the experiment network
# These match our Ansible configuration
link[controller].socket.addrs = ip4('10.100.0.10/24')
link[simulator].socket.addrs = ip4('10.100.0.20/24')

# Export the experiment
experiment(net)
