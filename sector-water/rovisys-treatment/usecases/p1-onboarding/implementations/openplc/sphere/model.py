"""
SPHERE Network Model for OpenPLC Water Treatment Scenario

This model defines a 3-node experiment:
- controller: Runs OpenPLC controller program
- simulator: Runs OpenPLC simulator program
- viewer: Runs CPS Enclave Viewer web UI (replay + optional live)

Controller and simulator communicate via Modbus TCP.
The viewer is exposed externally via MergeTB HTTP ingress.
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

# Viewer node — serves the web UI for run bundle replay
# Lighter requirements: no PLC workload, just HTTP server
viewer = net.node(
    'viewer',
    image == '2204',
    proc.cores >= 1,
    memory.capacity >= gb(2),
    disk.capacity == gb(5),    # Extra disk for run bundles + Docker
)

# Expose the viewer via MergeTB HTTP ingress (reverse proxy)
# Accessible from the portal at: http://<gateway>/<rid.eid.pid>/viewer/8080
viewer.ingress(http, 8080)

# Create a link connecting all three nodes
# Controller <-> Simulator: Modbus TCP
# Viewer: reads run bundles (no live Modbus needed for replay mode)
link = net.connect([controller, simulator, viewer])

# Assign IP addresses on the experiment network
# These match our Ansible configuration
link[controller].socket.addrs = ip4('10.100.0.10/24')
link[simulator].socket.addrs = ip4('10.100.0.20/24')
link[viewer].socket.addrs = ip4('10.100.0.30/24')

# Export the experiment
experiment(net)
