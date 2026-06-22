# Olmsted Hydroelectric Power Station

Hydroelectric power generation use case based on the Olmsted Locks and Dam facility.

## Overview

This use case models a generic hydro station covering the core power generation chain:

**Reservoir → Penstock → Wicket Gate → Turbine → Generator → Breaker → Grid**

The physics model includes:
- Reservoir mass balance with head calculation
- Penstock flow dynamics (1st-order lag)
- Wicket gate actuator with slew limits
- Turbine/generator power conversion
- Grid breaker with fast open/close
- Trip conditions (overspeed, overpressure, low head)

## Structure

```
olmsted-hydro/
├── implementations/
│   └── openplc/
│       ├── projects/        # OpenPLC project files
│       ├── st/              # Structured Text source
│       ├── configs/         # Modbus mappings
│       └── scenarios/       # OpenPLC-specific scenarios
├── scenarios/               # Test scenarios (YAML)
├── docs/
│   ├── process-models/      # Physics documentation
│   ├── power/               # Power system docs
│   └── security/            # Security considerations
├── profiles/                # Site-specific parameters
├── slices/                  # Network topology slices
├── runs/                    # Experiment run artifacts
├── assets/                  # Diagrams, images
└── tag_contract.yaml        # Canonical tag definitions
```

## Quick Start (OpenPLC)

```bash
cd implementations/openplc
# Load the project in OpenPLC Editor
openplc_editor projects/plc.xml
```

## Scenarios

Available test scenarios:
- `harvey_overspeed.yaml` - Overspeed trip condition

## Tag Contract

The `tag_contract.yaml` defines all process tags including:
- HMI operator inputs (start/stop/reset commands)
- Sensor readings (reservoir level, turbine speed, power output)
- Actuator outputs (wicket gate position, breaker status)
- Alarm and trip conditions

## References

- [Olmsted Locks and Dam](https://www.lrl.usace.army.mil/Missions/Civil-Works/Navigation/Olmsted-Locks-and-Dam/)
- DOE Hydropower Handbook
- IEEE C37.013 (AC HV Generator Circuit Breakers)
- PNNL Governor Studies

## Related

- [Energy Sector README](../README.md)
- [SPHERE Use Cases](../../README.md)
