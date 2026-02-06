# Water Treatment Use Case

A comprehensive water treatment facility with multiple processes, demonstrating realistic industrial control scenarios with multiple control loops, safety interlocks, and security considerations.

## 🏭 Process Overview

Multi-stage water purification with chemical dosing:
- **Raw Water Intake** → **Chemical Dosing** → **Mixing** → **Settling** → **Filtration** → **Disinfection** → **Storage**
- **16 I/O points**: 8 digital inputs, 4 digital outputs, 2 analog inputs, 2 analog outputs
- **Complexity**: Advanced (multiple control loops, safety interlocks)

See [docs/process_overview.md](docs/process_overview.md) for detailed process description.

## Quick Start

### OpenPLC Implementation (Virtual)
```bash
# Open OpenPLC Editor and load projects
# Controller: implementations/openplc/projects/controller_project/
# Simulator: implementations/openplc/projects/simulator_project/

# Or use Docker scenario:
cd implementations/openplc
# See scenario.yaml and scripts/ for Docker-based deployment
```

### Rockwell Implementation (SPHERE Testbed)
Requires enclave access and Rockwell hardware (currently offline). L5X/L5K programs are in `implementations/rockwell/plc/`. See `scripts/validate.sh` and `scripts/deploy.sh` for deployment helpers.

## 📁 Structure

```
water-treatment/
├── README.md                          # This file
├── docs/                              # Process documentation
│   ├── process_overview.md            # Detailed process description
│   ├── io_map.csv                     # I/O mapping and tag definitions
│   └── pid.pdf                        # Process & Instrumentation Diagram
├── profiles/                          # Simulation parameter profiles
│   ├── realistic.yaml                 # Research-grounded defaults
│   └── demo.yaml                      # Fast timing for demos
├── slices/                            # Viewer slice definitions
│   └── wt-uc1-slice.yaml             # UC1 slice (overlay + trend tags)
├── implementations/                   # Implementation-specific code
│   ├── rockwell/                      # SPHERE testbed deployment
│   │   ├── plc/                       # L5X files
│   │   │   ├── Controller_PLC.L5X     # Main control program
│   │   │   └── Simulator_PLC.L5X      # Simulation program
│   │   └── scripts/                   # Validation and deployment
│   │       ├── validate.sh            # Validate L5X files
│   │       └── deploy.sh              # Deploy to testbed
│   └── openplc/                       # Virtual simulation
│       ├── projects/                  # OpenPLC Editor projects
│       │   ├── controller_project/    # Main control program
│       │   └── simulator_project/     # Simulation program
│       ├── st/                        # Structured Text source files
│       ├── scenario.yaml              # Scenario descriptor
│       ├── configs/                   # OpenPLC runtime configs
│       ├── ansible/                   # Deployment playbooks
│       ├── sphere/                    # MergeTB model + scripts
│       └── scripts/                   # Local execution scripts
└── experiments/                       # Security research experiments
    ├── sensor_spoofing/               # Sensor manipulation attacks
    └── pump_override/                 # Direct pump control attacks
```

## 🔧 Implementations

### Rockwell (Authoritative)
- **Purpose**: SPHERE testbed deployment
- **Files**: Studio 5000 L5X/L5K programs (Controller_PLC, Simulator_PLC, ProcessOne variants)
- **Status**: Programs exist; hardware validation pending (enclave offline)
- **Deployment**: Delegates to SPHERE enclave infrastructure

### OpenPLC (Virtual)
- **Purpose**: Local development and simulation
- **Files**: OpenPLC Editor projects (PLCopen XML format)
- **Status**: ✅ Active - Ready for OpenPLC Editor
- **Projects**: 
  - `controller_project/` - Main control program
  - `simulator_project/` - Simulation program
- **Usage**: Open in OpenPLC Editor for local development and testing

## Simulation Profiles

The `profiles/` directory contains simulation parameter profiles that define physical timing characteristics for run generation and validation.

### Available profiles

| Profile | Valve tau | Dosing | Alarm HH | Use case |
|---------|-----------|--------|----------|----------|
| `realistic.yaml` | 30s | 0.063 L/min | 95% span | Research validation |
| `demo.yaml` | 0.5s | 5.0 L/min | 80% span | Quick demos |

### Key parameters
- **Actuator timing**: Motorized valves (30s realistic vs 0.5s demo), solenoids (0.05s), pumps (2s+10s VFD)
- **Per-tag overrides**: Chemical treatment valves classified as solenoids
- **Alarm setpoints**: Industry standard (95% HH) vs demo-friendly (80% HH)
- **Dosing rates**: Realistic metering pump (1 GPH) vs visible demo rate

### Usage
```bash
# Generate synthetic runs with realistic profile
./bin/genruns -profile profiles/realistic.yaml /tmp/runs

# Run validation harness (defaults to realistic)
python scripts/validation_harness.py \
    --scenario scenarios/nominal_startup.yaml \
    --profile profiles/realistic.yaml \
    --output runs/validate-nominal
```

Run bundles include `profile_name` and `params_snapshot` in `meta.json` for traceability.

## Security Experiments (Planned)

Experiment stubs exist in `experiments/` for future security research:

- **Sensor Spoofing** — pH, flow, and level sensor manipulation scenarios
- **Pump Override** — direct control and safety interlock bypass scenarios

These are not yet implemented. See [experiments/README.md](experiments/README.md) for descriptions.

## 🛡️ Safety Considerations

- **High/Low Level Alarms**: Prevent tank overflow/underflow
- **Pressure Relief**: Automatic pressure relief valves
- **Chemical Overdose Protection**: Limit chemical injection rates
- **Emergency Shutdown**: Manual and automatic shutdown capabilities

## 📊 I/O Mapping

| Tag | Address | Type | Units | Range | Safety Notes |
|-----|---------|------|-------|-------|--------------|
| RawWaterPump | DI_01 | Digital Input | Boolean | 0-1 | High priority - controls raw water intake |
| pH_Value | AI_01 | Analog Input | pH | 0-14 | CRITICAL - pH measurement for chemical dosing |
| ChemicalDose1 | AO_01 | Analog Output | % | 0-100 | Chemical dosing pump 1 speed control |

See [docs/io_map.csv](docs/io_map.csv) for complete I/O mapping.

## 📊 Visualization (CPS Enclave Viewer)

The water treatment use case integrates with the [CPS Enclave Viewer](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model/-/tree/main/cps-enclave-viewer) for replay-based visualization of run bundles.

### Slice definition

`slices/wt-uc1-slice.yaml` defines which tags appear in the viewer overlay panel and trend chart. The canonical copy is here; the viewer's `assets/slice.yaml` is derived from it.

### Data-driven P&ID pipeline

The viewer uses a data-driven SVG pipeline (defined in cps-enclave-model):

1. **Tag inventory** (`tags.normalized.yaml`) — canonical tags grouped by component
2. **Diagram spec** (`water-treatment.diagram.yaml`) — components, positions, anchors, pipes
3. **SVG generator** (`cmd/gensvg/`) — produces SVG with stable `anchor:COMP:ANCHOR` IDs
4. **Overlay config** (`water-treatment.overlay.yaml`) — maps tags to component anchors
5. **Validator** (`cmd/validate-diagram/`) — checks consistency across all files

### Tag naming conventions

Tags follow a `Component_Parameter` pattern grouped by process stage:

| Prefix | Stage | Examples |
|--------|-------|---------|
| `RW_` | P1 — Raw Water | `RW_Tank_Level`, `RW_Pump_Speed`, `RW_Pump_Sts` |
| `ChemTreat_` | P2 — Chemical | `ChemTreat_NaCl_Level`, `ChemTreat_HCl_Level` |
| `UF_` | P3 — Ultrafiltration | `UF_UFFT_Tank_Level` |
| `SYS_` | System State | `SYS_IDLE`, `SYS_RUNNING` |
| `Alarm_` | Alarms | `Alarm_RW_Tank_HH` |

Suffixes indicate role: `_Level`/`_Flow`/`_Speed` (sensor), `_Sts` (status), `_Fault` (alarm), `_Start`/`_Stop` (command).

## 🔗 Related

- **[cps-enclave-model](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model)**: Viewer, SVG generator, run bundles, use-case runner
- **Templates**: Based on [templates/single-process/](../templates/single-process/)
- **Validation**: Uses SPHERE infrastructure validation tools
- **Deployment**: Integrates with SPHERE enclave infrastructure