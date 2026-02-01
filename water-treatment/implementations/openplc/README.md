# Water Treatment - OpenPLC Implementation

This implementation runs the water treatment Process One (P1) scenario using OpenPLC runtime containers.

## Overview

The scenario deploys two OpenPLC instances communicating via Modbus TCP:
- **Controller** (10.100.0.10:502): Executes control logic
- **Simulator** (10.100.0.20:503): Simulates the physical plant

## Quick Start

### Prerequisites

- Docker Desktop with API version 1.44+ (check with `docker version`)
- Python 3.8+ with virtual environment
- Ansible 2.10+ with community.docker collection (installed in venv)
- pymodbus (for testing/operator interface)

**macOS Note:** If using Homebrew's Docker CLI, ensure it's up to date or use Docker Desktop's CLI:
```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

### Option 1: Ansible Deployment (Recommended)

```bash
# Activate the virtual environment (contains Ansible and pymodbus)
source .venv/bin/activate

cd ansible

# Install Ansible dependencies (first time only)
ansible-galaxy collection install -r requirements.yml

# Deploy the scenario locally
ansible-playbook -i inventory/local.yml playbooks/deploy-local.yml

# Test Modbus connectivity
ansible-playbook -i inventory/local.yml playbooks/test-modbus.yml

# Teardown when done
ansible-playbook -i inventory/local.yml playbooks/teardown-local.yml
```

### Option 2: Docker Compose (via cps-enclave CLI)

```bash
# Generate Docker Compose from scenario descriptor
cps-enclave scenario generate scenario.yaml

# Start the scenario
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the scenario
docker-compose down
```

### Access Points

After deployment:
- **Controller WebUI**: http://localhost:8080
- **Simulator WebUI**: http://localhost:8081
- **Controller Modbus**: localhost:502
- **Simulator Modbus**: localhost:503

### Testing

```bash
# Run E2E tests
pip install -r scripts/requirements.txt
pytest tests/test_e2e.py -v

# Or use Ansible Modbus test
ansible-playbook ansible/playbooks/test-modbus.yml

# Run operator interface
python scripts/operator.py
```

### Validation

```bash
# Validate scenario configuration
cps-enclave scenario validate scenario.yaml
```

## File Structure

```
openplc/
├── scenario.yaml           # SPHERE scenario descriptor
├── README.md               # This file
├── ansible/                # Ansible deployment
│   ├── ansible.cfg         # Ansible configuration
│   ├── requirements.yml    # Galaxy collection dependencies
│   ├── inventory/
│   │   └── local.yml       # Local deployment inventory
│   ├── playbooks/
│   │   ├── deploy-local.yml    # Deploy containers locally
│   │   ├── teardown-local.yml  # Remove containers
│   │   └── test-modbus.yml     # Test Modbus connectivity
│   └── vars/
│       └── openplc.yml     # Deployment variables
├── configs/
│   └── modbus_map.yaml     # Modbus address definitions
├── docs/
│   ├── architecture.md     # System architecture
│   └── io_contract.md      # I/O signal definitions
├── projects/
│   ├── controller_project/ # Controller PLCopen XML project
│   │   ├── plc.xml         # Main project file
│   │   └── beremiz.xml     # OpenPLC Editor config
│   └── simulator_project/  # Simulator PLCopen XML project
│       ├── plc.xml
│       └── beremiz.xml
├── scripts/
│   ├── operator.py         # CLI operator interface
│   ├── historian_collector.py  # Tag data collection
│   └── requirements.txt    # Python dependencies
├── st/                     # Flat ST files (for reference)
│   ├── controller_flat.st
│   └── simulator_flat.st
├── tests/
│   └── test_e2e.py         # End-to-end pytest tests
└── logs/                   # Runtime output (gitignored)
```

## Process Description

Process One (P1) is the raw water intake system:

1. Raw water enters the tank through the PR (pressure relief) valve
2. When the UF tank needs water, the pump transfers water from raw water tank
3. Tank level is maintained between 500-800mm
4. Alarms trigger at 250mm (LL), 500mm (L), 800mm (H), 1200mm (HH)

## OpenPLC Version

This scenario uses OpenPLC Runtime v3. For reproducibility, pin to a specific
commit in `scenario.yaml`:

```yaml
backend_config:
  version: "abc123..."  # Specific commit SHA
```

## Documentation

- [Architecture](docs/architecture.md) - System design and components
- [I/O Contract](docs/io_contract.md) - Signal definitions and communication protocol
- [Modbus Map](configs/modbus_map.yaml) - Complete address mapping

## Integration with SPHERE

This scenario is designed to work with the SPHERE CPS infrastructure:

- Scenario descriptor follows the `sphere.mergetb.io/v1` schema
- Uses `cps-enclave` CLI for deployment
- Historian collector follows SPHERE collector patterns
- Supports fault injection hooks (planned)

## Troubleshooting

### Docker CLI version error
If you see `client version X.XX is too old. Minimum supported API version is 1.44`:
```bash
# Use Docker Desktop CLI instead of Homebrew's
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

### Ansible command not found
```bash
# Activate the virtual environment first
source .venv/bin/activate
```

### PLCs won't connect
- Ensure Docker containers are running: `docker ps`
- Check container logs: `docker logs openplc-controller`
- Verify network: `docker network ls`

### Modbus communication errors
- Check Modbus addresses match between controller and simulator
- Verify ports 502/503 are exposed correctly
- Ensure PLC is in RUN mode (check logs for "Initializing OpenPLC in RUN mode")
- Test with: `docker exec openplc-controller /workdir/.venv/bin/python3 -c "from pymodbus.client.sync import ModbusTcpClient; c=ModbusTcpClient('10.100.0.20',502); print(c.connect())"`

### OpenPLC compilation fails
- Check container logs for compilation errors
- Open project in OpenPLC Editor to check for ST syntax errors
- Verify the `.st` file path is correct in ansible vars
