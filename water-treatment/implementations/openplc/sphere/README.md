# SPHERE Testbed Deployment

This directory contains scripts and playbooks to deploy the OpenPLC water treatment scenario on the SPHERE testbed.

## Prerequisites

1. **SPHERE Account**: Request access at [sphere-testbed.net](https://launch.sphere-testbed.net)

2. **MergeTB CLI (`mrg`)**: Download from [GitLab releases](https://gitlab.com/mergetb/portal/cli/-/releases/permalink/latest)

3. **Configure CLI**:
   ```bash
   mrg config set server grpc.sphere-testbed.net
   mrg login <username>
   ```

4. **SSH Key**: Ensure `~/.ssh/merge_key` exists (or update ssh_config path)

## Quick Start

```bash
cd sphere/

# 1. Create experiment and materialize nodes
./up.sh

# 2. Install Docker and deploy OpenPLC
./ansible.sh

# 3. Test Modbus communication
ansible-playbook -i inventory.ini playbooks/test-modbus.yml

# 4. Cleanup when done
./down.sh
```

## Directory Structure

```
sphere/
├── model.py              # SPHERE network topology (mergexp)
├── up.sh                 # Create & materialize experiment
├── ansible.sh            # Run deployment playbooks
├── down.sh               # Cleanup experiment
├── README.md             # This file
└── playbooks/
    ├── install-docker.yml    # Install Docker on nodes
    ├── build-openplc.yml     # Build OpenPLC image
    ├── deploy-sphere.yml     # Deploy containers
    └── test-modbus.yml       # Test communication
```

## Network Topology

```
                    SPHERE Testbed
    ┌──────────────────────────────────────┐
    │                                      │
    │   ┌─────────────┐   ┌─────────────┐  │
    │   │ controller  │   │  simulator  │  │
    │   │ 10.100.0.10 │◄──►│ 10.100.0.20 │  │
    │   │   :502      │   │    :502     │  │
    │   └─────────────┘   └─────────────┘  │
    │                                      │
    └──────────────────────────────────────┘
             ▲
             │ SSH via XDC
             ▼
    ┌─────────────────┐
    │  Your Machine   │
    └─────────────────┘
```

## Access Points

After deployment:

| Service | Address | Access Method |
|---------|---------|---------------|
| Controller WebUI | 10.100.0.10:8080 | SSH tunnel |
| Simulator WebUI | 10.100.0.20:8080 | SSH tunnel |
| Controller Modbus | 10.100.0.10:502 | Internal |
| Simulator Modbus | 10.100.0.20:502 | Internal |

### SSH Tunnel for WebUI

```bash
# Access controller WebUI
ssh -F ssh_config -L 8080:localhost:8080 controller
# Then open: http://localhost:8080

# Access simulator WebUI (different local port)
ssh -F ssh_config -L 8081:localhost:8080 simulator
# Then open: http://localhost:8081
```

## Troubleshooting

### Can't connect to nodes
```bash
# Check experiment status
mrg show realization test.openplc-water.$USER

# Check XDC attachment
mrg list xdcs
```

### Docker build fails
- SPHERE nodes need internet access for Docker install
- Build can take 10-15 minutes first time

### Modbus connection refused
- Verify containers are running: `ssh -F ssh_config controller docker ps`
- Check container logs: `ssh -F ssh_config controller docker logs openplc-controller`

## Differences from Local Deployment

| Aspect | Local | SPHERE |
|--------|-------|--------|
| Network | Docker bridge (10.100.0.0/24) | SPHERE virtual network |
| Nodes | Both containers on localhost | Separate VMs |
| Docker | Pre-installed | Installed by playbook |
| Image | Built locally once | Built on each node |
| Access | Direct localhost | SSH through XDC |
