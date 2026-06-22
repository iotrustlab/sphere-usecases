# Architecture: Water Treatment OpenPLC Scenario

## System Overview

This scenario implements a water treatment control system using two OpenPLC runtimes communicating via Modbus TCP.

```
┌────────────────────────────────────────────────────────────────────┐
│                     Docker Network: water-treatment-net            │
│                         Subnet: 10.100.0.0/24                      │
│                                                                    │
│  ┌──────────────────┐              ┌──────────────────┐           │
│  │   Controller     │              │    Simulator     │           │
│  │   10.100.0.10    │◄────────────►│   10.100.0.20    │           │
│  │                  │  Modbus TCP  │                  │           │
│  │  Port 502 (MB)   │              │  Port 503 (MB)   │           │
│  │  Port 8080 (Web) │              │  Port 8081 (Web) │           │
│  └──────────────────┘              └──────────────────┘           │
│           │                                 │                      │
│           │         ┌──────────────┐        │                      │
│           └────────►│  Historian   │◄───────┘                      │
│                     │  (Polling)   │                               │
│                     └──────────────┘                               │
│                            │                                       │
│                     ┌──────────────┐                               │
│                     │   Capture    │                               │
│                     │  (tcpdump)   │                               │
│                     └──────────────┘                               │
└────────────────────────────────────────────────────────────────────┘
```

## Components

### Controller PLC (10.100.0.10)

**Role**: Executes control logic for the water treatment process

**Program**: `projects/controller_project/plc.xml`

**Functions**:
- State machine management (IDLE, START, RUNNING, SHUTDOWN)
- Tank level monitoring and alarm generation
- Pump and valve sequencing
- Permissive logic enforcement

**I/O**:
- Reads: Tank levels, valve status, pump status (from Simulator)
- Writes: Valve commands, pump commands (to Simulator)

### Simulator PLC (10.100.0.20)

**Role**: Simulates the physical water treatment plant

**Program**: `projects/simulator_project/plc.xml`

**Functions**:
- Tank level dynamics (fill/drain based on valve/pump state)
- Valve position feedback
- Pump status feedback
- Physical constraints (max levels, flow rates)

**I/O**:
- Reads: Valve commands, pump commands (from Controller)
- Writes: Tank levels, status feedback (to Controller)

### Historian

**Role**: Records tag values over time for analysis

**Output**: `logs/tags.csv`

**Poll Rate**: 500ms (configurable)

**Data Collected**:
- All Modbus registers from both PLCs
- Timestamps for each sample

### Packet Capture

**Role**: Records network traffic for protocol analysis

**Output**: `logs/modbus.pcap`

**Filter**: Modbus TCP ports (502, 503)

## Process Description

### Process One (P1): Raw Water System

```
                    ┌───────────────┐
    Inlet ─────────►│   Raw Water   │
    (PR_Valve)      │     Tank      │
                    │  (0-1200mm)   │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │   P_Valve     │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │    Pump       │──────► To UF Tank
                    └───────────────┘
```

**Control Logic**:
1. When UF tank level < 800mm, start pump
2. When UF tank level > 1000mm, stop pump
3. Maintain raw water tank level between 500-800mm via inlet valve
4. Stop pump if raw water tank level drops to 250mm (LL alarm)

## File Structure

```
openplc/
├── scenario.yaml           # SPHERE scenario descriptor
├── configs/
│   └── modbus_map.yaml     # Modbus address definitions
├── docs/
│   ├── architecture.md     # This file
│   └── io_contract.md      # I/O signal definitions
├── projects/
│   ├── controller_project/ # Controller PLCopen XML project
│   │   ├── plc.xml
│   │   └── beremiz.xml
│   └── simulator_project/  # Simulator PLCopen XML project
│       ├── plc.xml
│       └── beremiz.xml
├── scripts/
│   ├── operator.py         # Operator interface
│   └── poll_tags.py        # Tag polling for historian
├── tests/
│   └── test_e2e.py         # End-to-end tests
└── logs/                   # Runtime output (gitignored)
    ├── tags.csv
    └── modbus.pcap
```

## Running the Scenario

### Prerequisites

- Docker and Docker Compose
- cps-enclave CLI (from cps-enclave-model repo)

### Quick Start

```bash
# Generate Docker Compose from scenario
cps-enclave scenario generate scenario.yaml

# Start the scenario
docker-compose up -d

# View logs
docker-compose logs -f

# Access web UIs
# Controller: http://localhost:8080
# Simulator: http://localhost:8081

# Run operator interface
python scripts/operator.py

# Stop the scenario
docker-compose down
```

### Validation

```bash
# Validate scenario configuration
cps-enclave scenario validate scenario.yaml

# Run end-to-end tests
pytest tests/test_e2e.py
```

## OpenPLC Version Compatibility

This scenario is designed for OpenPLC Runtime v3. For reproducibility, pin to a specific commit in the scenario.yaml:

```yaml
backend_config:
  version: "abc123..."  # Replace with tested commit SHA
```

Or use a pre-built image:

```yaml
backend_config:
  image: "ghcr.io/sphere-project/sphere-openplc:v1.0.0"
```

## Extension Points

### Adding Fault Injection

Modify the simulator to accept fault commands via additional Modbus registers:
- Stuck valve simulation
- Sensor spoofing
- Communication delays

### Adding Noise Models

Implement in simulator program:
- Gaussian noise on level sensors
- Quantization effects
- Sensor drift

### Connecting IDS/Anomaly Detection

- Tap the Modbus traffic from capture
- Feed to detection algorithms
- Compare against known-good traces
