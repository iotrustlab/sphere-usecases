# Water Distribution UC0

Water distribution use case for the SPHERE CPS Enclave. Models a municipal water distribution system with three process groups:

- **Supply Line** — intake tank, variable-speed pump, chemical dosing (NaOCl, NH4Cl), mixer
- **Distribution Grid** — elevated storage tank, consumer storage tank, gravity-fed distribution
- **Return Water System (RWS)** — return tank, recirculation pump, return valve

## Quick Start

```bash
# From cps-enclave-model repo:
./scripts/smoke.sh
```

The viewer loads both Water Treatment and Water Distribution slices. Use the slice selector dropdown to switch between them.

## Process Overview

### Supply Line
Water enters a supply tank, is chemically treated (NaOCl for disinfection, NH4Cl for chloramine formation), mixed, then pumped into the distribution grid via a variable-speed pump. The supply pump speed is the primary flow control actuator.

### Distribution Grid
Water flows from the supply line to an elevated storage tank (gravity feed to consumers) and a consumer storage tank. The elevated tank inlet valve controls grid fill.

### Return Water System (RWS)
Excess or recirculated water collects in a return tank and is pumped back toward the supply line via a variable-speed pump and outlet valve.

## Tag Naming Conventions

| Prefix | Group | Count |
|--------|-------|-------|
| `Supply_` | Supply line | 9 tags (3 real, 6 bool) |
| `Grid_` | Distribution grid | 4 tags (2 real, 2 bool) |
| `RWS_` | Return water system | 5 tags (2 real, 3 bool) |
| `SYS_` | System state | 2 bool |
| `Alarm_` | Alarms | 1 bool |

Total: 21 tags across 5 groups. See `tag_contract.yaml` for full definitions.

## Assets

| File | Description |
|------|-------------|
| `tag_contract.yaml` | 21 tags across 5 groups (supply, grid, rws, system, alarms) |
| `slices/wd-uc0-slice.yaml` | Minimal visualization slice for UC0 |
| `assets/water-distribution.svg` | P&ID diagram |
| `assets/water-distribution.overlay.yaml` | Tag overlay positions for diagram |
| `runs/` | Golden run bundles (synthetic data) |
| `implementations/openplc/configs/openplc_map.yaml` | OpenPLC Modbus mapping (placeholder) |
| `docs/assumptions.md` | Simulation and control assumptions |

## Current Status

- Tag contract, diagram, overlay, slice, golden runs: **complete**
- OpenPLC mapping: **defined** (addresses aligned to controller/simulator ST)
- OpenPLC controller + simulator: **available** (ST source in `implementations/openplc/st/`)
- Live PLC integration: **not started** (golden runs remain synthetic)

## References

- Control assumptions: `docs/assumptions.md`
- OpenPLC mapping status: `implementations/openplc/configs/openplc_map.yaml`
- Architecture: `../../sphere-docs/ARCH.md`
- Roadmap: `../../sphere-docs/ROADMAP.md`
