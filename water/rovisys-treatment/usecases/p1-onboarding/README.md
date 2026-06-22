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
2. Import `implementations/rockwell/controller/Controller_PLC_V1.1.L5X`
3. Import `implementations/rockwell/simulator/Simulator_PLC_V1.1.L5X`
4. Open HMI from `implementations/rockwell/hmi/HMI_V1.1.xml`
5. Download to PLCs and run

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

## Differences from Full P1-to-P6

This demo is intentionally simplified:
- Single process only (P1)
- Minimal HMI (ultrafiltration tank fill)
- Basic physics model

The full P1-to-P6 implementation will include all six processes with interconnections.

## Known Limitations

- [ ] Physics model needs refinement for realistic waterflow
- [ ] HMI version-control format TBD
- [ ] Golden runs not yet generated
- [ ] OpenPLC implementation needs validation against Rockwell

## Related Issues

- [sphere-usecases#27](https://github.com/iotrustlab/sphere-usecases/issues/27) - Package this demo
- [sphere-usecases#5](https://github.com/iotrustlab/sphere-usecases/issues/5) - Beta user smoke tests
- [sphere-usecases#6](https://github.com/iotrustlab/sphere-usecases/issues/6) - Beta user onboarding
