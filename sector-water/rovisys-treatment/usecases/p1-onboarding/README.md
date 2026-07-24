# P1 Onboarding Demo

Self-contained beta-user demo for the water treatment P1 (Raw Water Intake) process.

## Purpose

This demo provides a minimal, working example for:
- Beta user onboarding and smoke testing
- CTF1 baseline scenario
- First end-to-end validation workflow

## Contents

```
p1-onboarding/
├── implementations/
│   ├── rockwell/
│   │   ├── controller/          # Controller PLC (L5X/L5K)
│   │   ├── simulator/           # Simulator PLC (L5X/L5K)
│   │   ├── hmi/                 # HMI project files
│   │   ├── tests/               # Hardware signal tests
│   │   ├── rockwell_map.yaml    # CIP path mappings
│   │   └── hw_test_config.yaml  # Test configuration
│   └── openplc/
│       ├── controller/          # OpenPLC controller project
│       ├── simulator/           # OpenPLC simulator project
│       └── configs/             # Modbus mappings
├── scenarios/                   # Test scenarios (YAML)
├── screenshots/                 # Operator-facing screenshots
├── validation/                  # Validation checklists
└── golden-runs/                 # Reference run bundles
```

## Quick Start

### Rockwell (Testbed)

1. Open Studio 5000 Logix Designer
2. Import `implementations/rockwell/controller/Controller_PLC.L5X`
3. Import `implementations/rockwell/simulator/Simulator_PLC.L5X`
4. Download both projects to the PLCs
5. In FactoryTalk View SE Studio, import the HMI displays
   `implementations/rockwell/hmi/Graph.xml` and
   `implementations/rockwell/hmi/HMI_Start_Stop.xml`
   (`BatchImport_PLC_V2.xml` is the batch-import manifest for both), then
   connect the display tags to the controller project — see **HMI Operation** below
6. Run the displays and start the demo

### OpenPLC (Virtual)

```bash
cd implementations/openplc
# Load controller project
openplc_editor controller/controller_project/plc.xml
# Load simulator project
openplc_editor simulator/simulator_project/plc.xml
```

## Hardware Signal Testing

Run the hardware signal tests:

```bash
cd implementations/rockwell/tests
pytest test_digital_io.py test_analog_scaling.py -v
```

## Scenarios

Available test scenarios in `scenarios/`:
- `nominal_startup.yaml` - Normal operation
- `alarm_hh.yaml` - High-high alarm condition
- `low_level_block.yaml` - Low level protection
- `emergency_stop.yaml` - Emergency shutdown

## Process Description

The demo runs two PLCs wired together — a **Simulator PLC** that generates tank
levels and sensor values, and a **Controller PLC** that runs the control logic
against those simulated inputs.

```
Fill P1 Raw Water Tank (P1.RW_Tank)
        │  reaches ~800 mm
        ▼
Open transfer valve + start transfer pump
        │
        ▼
Fill P3 Ultrafiltration Tank (P3.Ultrafiltration_Tank)
        │  reaches 1000 mm
        ▼
Wait 5–8 s, then drain P3 tank
        │
        ▼
Repeat
```

## HMI Operation

The HMI is provided as two FactoryTalk View SE display exports (`Graph.xml`,
`HMI_Start_Stop.xml`) under `implementations/rockwell/hmi/`. After importing and
connecting the display tags to the controller project:

| Button | Action |
|--------|--------|
| `Start_Sim` | Start the simulator PLC (begins updating process values) |
| `Start_Cont` | Start the controller PLC (begins executing control logic) |
| `Stop_Cont` | Stop the controller and transition the state machine to shutdown |
| `RST` | Reset the simulator, tank levels, valves, and process values |

The controller follows the state sequence `IDLE → START → RUNNING → SHUTDOWN`.
While running, the HMI shows tank levels, pump/valve status, process state, and
animated tank overlays; a button opens the second display graphing tank levels
over time.

Video walkthrough (HMI + simulator + controller running together): https://youtu.be/Wm_Pji_4yi4

## Differences from Full P1-to-P6

This demo is intentionally scoped to two processes:
- **P1 (Raw Water Intake)** and **P3 (Ultrafiltration)** only
- **P2 (Chemical Mixing)** is omitted — in the full system water is dosed
  before entering P3
- **P4–P6 (downstream treatment)** are omitted — here the P3 tank simply drains
  to restart the loop instead of feeding downstream stages
- Simplified physics: inflow/outflow modeled with constants and a PLC
  scan-time (`dt`) update; no pressure, pump curves, or hydraulic losses

The full P1-to-P6 implementation will include all six processes with interconnections.

## Known Limitations

- Analog values are ideal — no sensor noise, calibration error, or Gaussian measurement noise
- Tank model ignores pressure, pump curves, and hydraulic losses
- P3 drains directly instead of feeding downstream stages (P4–P6)
- [ ] Golden runs not yet generated
- [ ] OpenPLC implementation needs validation against Rockwell

## Related Issues

- [sphere-usecases#27](https://github.com/iotrustlab/sphere-usecases/issues/27) - Package this demo
- [sphere-usecases#5](https://github.com/iotrustlab/sphere-usecases/issues/5) - Beta user smoke tests
- [sphere-usecases#6](https://github.com/iotrustlab/sphere-usecases/issues/6) - Beta user onboarding
