# Water Distribution UC0 — OpenPLC Implementation

This directory contains the controller + simulator ST programs and the
Modbus bridge used to run WD UC0 in a closed loop.

## Files

- `st/wd_controller.st` — controller PLC logic
- `st/wd_simulator.st` — physical process simulator
- `configs/openplc_map.yaml` — Modbus mapping reference
- `scripts/modbus_bridge.py` — controller ↔ simulator bridge

## Quick Start (local OpenPLC)

1. Load the controller ST into an OpenPLC instance (port 502).
2. Load the simulator ST into a second OpenPLC instance (port 503).
3. Start the Modbus bridge:

```bash
python scripts/modbus_bridge.py --controller localhost:502 --simulator localhost:503
```

If your OpenPLC build rejects writes to discrete inputs, use the fallback:

```bash
python scripts/modbus_bridge.py --controller localhost:502 --simulator localhost:503 --status-holding
```

## Scenarios

Scenario YAMLs live in `scenarios/` and can be used by custom harnesses
to drive HMI start/stop actions.
