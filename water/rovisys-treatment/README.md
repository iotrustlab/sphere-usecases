# Rovisys Water Treatment

Multi-stage water purification facility with chemical dosing (P1-P6 processes).

## Process Overview

Multi-stage water purification with chemical dosing:
- **P1: Raw Water Intake** → **P2: Chemical Dosing** → **P3: Mixing** → **P4: Settling** → **P5: Filtration** → **P6: Disinfection/Storage**

See [docs/process_overview.md](docs/process_overview.md) for detailed process description.

## Use Cases

| Use Case | Description | Status |
|----------|-------------|--------|
| [p1-onboarding](usecases/p1-onboarding/) | P1 demo for beta users and smoke testing | Active |
| [full-system-p1-to-p6](usecases/full-system-p1-to-p6/) | Complete P1-P6 system | In development |

## Quick Start

### P1 Onboarding Demo

```bash
cd usecases/p1-onboarding
cat README.md  # Follow setup instructions
```

#### OpenPLC (Virtual)
```bash
cd usecases/p1-onboarding/implementations/openplc
# Controller: projects/controller_project/
# Simulator: projects/simulator_project/
```

#### Rockwell (SPHERE Testbed)
```bash
cd usecases/p1-onboarding/implementations/rockwell
# Controller: controller/Controller_PLC_V1.1.L5X
# Simulator: simulator/Simulator_PLC_V1.1.L5X
```

## Structure

```
rovisys-treatment/
├── usecases/
│   ├── p1-onboarding/              # P1 demo for beta users
│   │   ├── implementations/
│   │   │   ├── rockwell/
│   │   │   │   ├── controller/     # Controller PLC (L5X/L5K)
│   │   │   │   ├── simulator/      # Simulator PLC (L5X/L5K)
│   │   │   │   ├── hmi/            # HMI project files
│   │   │   │   └── tests/          # Hardware signal tests
│   │   │   └── openplc/
│   │   │       ├── controller/     # OpenPLC controller project
│   │   │       ├── simulator/      # OpenPLC simulator project
│   │   │       ├── ansible/        # Deployment playbooks
│   │   │       ├── docker/         # Docker configs
│   │   │       └── scripts/        # Local execution
│   │   ├── scenarios/              # Test scenarios
│   │   └── golden-runs/            # Reference runs
│   │
│   └── full-system-p1-to-p6/       # Complete system
│       └── implementations/
│
├── shared/                          # Shared diagrams, etc.
├── processes/                       # Per-process documentation
├── docs/                            # Domain documentation
├── profiles/                        # Simulation parameter profiles
├── slices/                          # Viewer slice definitions
├── assets/                          # Images, diagrams
├── tag_contract.yaml                # Domain-level tag definitions
└── _archive/                        # Archived old files
```

## Implementations

Implementations exist at the **use case level** (not domain level):

### Rockwell (Authoritative)
- **Purpose**: SPHERE testbed deployment
- **Files**: Studio 5000 L5X/L5K programs
- **Location**: `usecases/<instance>/implementations/rockwell/`
- **Status**: P1 demo ready; full system in development

### OpenPLC (Virtual)
- **Purpose**: Local development and simulation
- **Files**: OpenPLC Editor projects (PLCopen XML)
- **Location**: `usecases/<instance>/implementations/openplc/`
- **Status**: Active - Ready for OpenPLC Editor

## Simulation Profiles

The `profiles/` directory contains simulation parameter profiles:

| Profile | Valve tau | Dosing | Alarm HH | Use case |
|---------|-----------|--------|----------|----------|
| `realistic.yaml` | 30s | 0.063 L/min | 95% span | Research validation |
| `demo.yaml` | 0.5s | 5.0 L/min | 80% span | Quick demos |

## Tag Naming Conventions

Tags follow a `Component_Parameter` pattern grouped by process stage:

| Prefix | Stage | Examples |
|--------|-------|---------|
| `RW_` | P1 - Raw Water | `RW_Tank_Level`, `RW_Pump_Speed` |
| `ChemTreat_` | P2 - Chemical | `ChemTreat_NaCl_Level` |
| `UF_` | P3 - Ultrafiltration | `UF_UFFT_Tank_Level` |
| `SYS_` | System State | `SYS_IDLE`, `SYS_RUNNING` |
| `Alarm_` | Alarms | `Alarm_RW_Tank_HH` |

## Safety Considerations

- **High/Low Level Alarms**: Prevent tank overflow/underflow
- **Pressure Relief**: Automatic pressure relief valves
- **Chemical Overdose Protection**: Limit chemical injection rates
- **Emergency Shutdown**: Manual and automatic shutdown capabilities

## Related

- [Water Sector README](../README.md)
- [SPHERE Use Cases](../../README.md)
- [CPS Enclave Model](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model)
