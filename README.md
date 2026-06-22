# SPHERE Use Cases

> **SPHERE CPS Enclave (NSF infrastructure based at USC ISI)** provides the real hardware ICS environment; the **Utah-led CPS enclave** is designed, developed, and tested by **PI Garcia**, and this repository hosts the **use-case processes** that run on that enclave. Each use case may offer multiple implementations: **Rockwell** for enclave deployment and **OpenPLC (virtual)** for local exploration.

> Canonical milestone state and backlog live in [`../sphere-docs/ROADMAP.md`](../sphere-docs/ROADMAP.md) and [`../sphere-docs/BACKLOG.md`](../sphere-docs/BACKLOG.md). The table below is a repo-local inventory of available assets, not the source of truth for milestone completion.

## What This Repository Contains

This repository contains **self-contained CPS use cases** for security research and experimentation, organized by **CISA Critical Infrastructure Sectors**. Each use case includes:
- Process documentation (P&IDs, I/O maps, safety notes)
- Multiple implementations (Rockwell for testbed, OpenPLC for virtual)
- Security experiments and perturbation scenarios
- Validation and deployment scripts

## CISA Sector Organization

Use cases are organized by CISA critical infrastructure sector:

| Sector | CISA # | Contents |
|--------|--------|----------|
| [**Water**](water/) | 16 | Water treatment, distribution, and wastewater systems |
| [**Chemical**](chemical/) | 1 | Chemical manufacturing and processing |
| [**Energy**](energy/) | 8 | Power generation, transmission, oil/gas distribution |

## Available Use Cases

### Water and Wastewater (Sector 16)

| Use Case | Status | Rockwell | OpenPLC | Description |
|----------|--------|----------|---------|-------------|
| [rovisys-treatment](water/rovisys-treatment/) | Active | Testbed | Virtual | Multi-stage water purification with chemical dosing (P1-P6) |
| [rovisys-distribution](water/rovisys-distribution/) | Active slice | Planned | Assets | Municipal distribution with controller/simulator |

### Chemical (Sector 1)

| Use Case | Status | Rockwell | OpenPLC | Description |
|----------|--------|----------|---------|-------------|
| [grfics](chemical/grfics/) | Integrated | N/A | SPHERE-native | Tennessee Eastman chemical process |

### Energy (Sector 8)

| Use Case | Status | Rockwell | OpenPLC | Description |
|----------|--------|----------|---------|-------------|
| [olmsted-hydro](energy/olmsted-hydro/) | Active | Planned | Virtual | Hydroelectric power station (Olmsted Dam) |
| [oil-and-gas](energy/oil-and-gas/) | Incubation | Planned | Planned | Pipeline distribution with pressure control |

## Getting Started

1. **Pick a sector** from the table above
2. **Navigate to a use case** and read its README
3. **Choose your implementation**:
   - **Rockwell** = Real SPHERE testbed deployment (requires enclave access)
   - **OpenPLC** = Virtual simulation for local development

### Quick Start: P1 Onboarding Demo

```bash
cd water/rovisys-treatment/usecases/p1-onboarding
cat README.md  # Follow setup instructions
```

## Repository Structure

```
sphere-usecases/
├── water/                             # CISA Sector 16: Water and Wastewater
│   ├── rovisys-treatment/             # Rovisys water treatment (P1-P6)
│   │   ├── usecases/
│   │   │   ├── p1-onboarding/         # P1 demo for beta users
│   │   │   └── full-system-p1-to-p6/  # Complete system
│   │   ├── shared/                    # Shared assets
│   │   └── docs/
│   └── rovisys-distribution/          # Rovisys water distribution
│
├── chemical/                          # CISA Sector 1: Chemical
│   └── grfics/                        # Tennessee Eastman / GRFICS
│
├── energy/                            # CISA Sector 8: Energy
│   ├── olmsted-hydro/                 # Hydroelectric power
│   └── oil-and-gas/                   # Pipeline distribution
│
├── tools/                             # Repo-level tools
│   ├── hwtest/                        # Hardware signal testing
│   └── fuxa-demo/                     # FUXA HMI demo stack
│
├── templates/                         # Golden skeletons
│   └── usecase/                       # Use case template
│
└── docs/                              # Global documentation
    └── conventions/                   # Tag naming, diagram standards
```

## Use Case Structure Pattern

Each vendor use case follows this hierarchy:

```
<sector>/<vendor>-<domain>/
├── usecases/
│   └── <instance>/                    # e.g., p1-onboarding
│       ├── implementations/
│       │   ├── rockwell/
│       │   │   ├── controller/
│       │   │   ├── simulator/
│       │   │   └── hmi/
│       │   └── openplc/
│       │       ├── controller/
│       │       └── simulator/
│       ├── scenarios/
│       └── golden-runs/
├── shared/
├── processes/
├── docs/
└── tag_contract.yaml
```

## For Contributors

### Creating New Use Cases

1. **Identify the CISA sector** for your use case
2. **Copy the template**: `cp -r templates/single-process/ <sector>/<vendor>-<domain>/`
3. **Follow the structure**: Each use case should be self-contained
4. **Add implementations**: Rockwell (testbed) and/or OpenPLC (virtual)
5. **Include experiments**: Security research scenarios
6. **Validate**: Run `validate.sh` scripts before submitting

### Implementation Guidelines

- **Rockwell**: Use Studio 5000, export as L5X files, delegate to SPHERE enclave infra
- **OpenPLC**: Use Structured Text, include Python simulation models
- **Scripts**: All implementations should expose `validate.sh` and appropriate deployment scripts

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidance.

## Related Repositories

- **[cps-enclave-model](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model)**: CPS enclave infrastructure, CPS Enclave Viewer
- **[sphere-docs](https://github.com/iotrustlab/sphere-docs)**: Documentation, roadmap, getting started guides
- **sphere-infra**: Validation tools and enclave infrastructure

## Support

- **Issues**: [GitHub Issues](https://github.com/IOTrust-Lab/sphere-usecases/issues)
- **Project Board**: [SPHERE CPS Enclave](https://github.com/orgs/iotrustlab/projects/8)
- **Documentation**: See individual use case READMEs and [CONTRIBUTING.md](CONTRIBUTING.md)

---

*This repository focuses on **use cases only**. For infrastructure, deployment tools, and detailed documentation, see the related SPHERE repositories.*
