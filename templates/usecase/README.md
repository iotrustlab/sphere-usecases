# Use Case Template

This template provides the standard structure for CPS use cases in the SPHERE repository.

## Overview

Use cases are organized by CISA critical infrastructure sector and can contain one or more processes. This template shows the structure for a single use case instance.

## Structure

```
<sector>/<vendor>-<domain>/
├── usecases/
│   └── <instance>/                    # e.g., p1-onboarding, full-system
│       ├── implementations/
│       │   ├── rockwell/
│       │   │   ├── controller/        # Controller PLC (L5X/L5K)
│       │   │   ├── simulator/         # Simulator PLC (L5X/L5K)
│       │   │   ├── hmi/               # HMI project files
│       │   │   ├── scripts/           # Validation and deployment
│       │   │   └── tests/             # Hardware signal tests
│       │   └── openplc/
│       │       ├── controller/        # OpenPLC controller project
│       │       ├── simulator/         # OpenPLC simulator project
│       │       ├── configs/           # Modbus mappings
│       │       ├── ansible/           # Deployment playbooks
│       │       ├── docker/            # Docker configs
│       │       └── scripts/           # Local execution
│       ├── scenarios/                 # Test scenarios (YAML)
│       └── golden-runs/               # Reference run bundles
│
├── shared/                            # Shared assets across use cases
├── processes/                         # Per-process documentation
├── docs/                              # Domain documentation
├── profiles/                          # Simulation parameter profiles
├── slices/                            # Viewer slice definitions
├── assets/                            # Diagrams, images
└── tag_contract.yaml                  # Domain-level tag definitions
```

## Multi-Process Use Cases

Use cases can model multiple processes. For example, water treatment includes P1-P6:
- **P1**: Raw Water Intake
- **P2**: Chemical Treatment
- **P3**: Ultrafiltration
- **P4-P6**: Additional stages

Each process shares the same implementation infrastructure but may have distinct:
- Controller/simulator logic
- Tag groups (prefixed by process, e.g., `RW_`, `ChemTreat_`)
- Scenarios and experiments

## Slices for Experiments

For security experiments that target a subset of processes (e.g., only P1-P3), use the `slices/` directory to define which tags and components are included. This enables:
- Reduced resource requirements for targeted experiments
- Isolation of attack surfaces
- Reproducible experiment configurations

## Getting Started

1. Copy this template to create a new use case:
   ```bash
   cp -r templates/usecase/ <sector>/<vendor>-<domain>/usecases/<instance>/
   ```

2. Update the README with your specific process details

3. Add implementation files to the appropriate directories

4. Create a `tag_contract.yaml` defining your process tags

5. Run validation scripts before committing

## Safety Notes

- Always review safety considerations before deployment
- Test in simulation (OpenPLC) before physical deployment (Rockwell)
- Follow SPHERE enclave protocols for testbed access

## Related Documentation

- [Conventions](../../docs/conventions/) - Tag naming, diagram standards
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines
