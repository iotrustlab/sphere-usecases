# Water Distribution Process Models

This directory contains detailed dynamic models for each process in the Water Distribution use case.

## Process Map

```
                    ┌─────────────────────────────────────────────────┐
                    │            Water Distribution System            │
                    └─────────────────────────────────────────────────┘
                                          │
      ┌───────────────────────────────────┼───────────────────────────────────┐
      │                                   │                                   │
      ▼                                   ▼                                   ▼
┌───────────┐                      ┌───────────┐                      ┌───────────┐
│  Supply   │                      │   Grid    │                      │   RWS     │
│   Line    │ ─────────────────►   │Distribution────────────────────► │  Return   │
│           │                      │           │                      │  Water    │
└───────────┘                      └───────────┘                      └───────────┘
     │                                   │                                   │
     │ Supply Tank                       │ Elevated Tank                     │ RWS Tank
     │ Supply Pump                       │ Consumer Tank                     │ RWS Pump
     │ NaOCl/NH4Cl Dosing                │ Elev Valve                        │ RWS Valve
     │ Tank/Mixer                        │                                   │
     │                                   │                                   │
     ▼                                   ▼                                   ▼
   ════════════════════════════════════════════════════════════════════════════
                              Implemented in UC0 (wd-uc0)
   ════════════════════════════════════════════════════════════════════════════
```

## Process Documentation

| Process | ID | Document | Status |
|---------|-----|----------|--------|
| Supply Line | WD-Supply | [wd-supply-line.md](wd-supply-line.md) | Documented |
| Distribution Grid | WD-Grid | [wd-distribution-grid.md](wd-distribution-grid.md) | Documented |
| Return Water System | WD-RWS | [wd-return-water.md](wd-return-water.md) | Documented |

## Slices

| Slice | Processes | Description |
|-------|-----------|-------------|
| `wd-uc0` | Supply + Grid + RWS | Minimal demo slice (current) |
| `wd-uc1` | + Pressure regulation | Add pressure feedback control (planned) |
| `wd-uc2` | + Demand modeling | Add consumer demand profiles (planned) |

## System-Level Documentation

- System State Machine (planned) - IDLE/RUNNING states

## References

- **Tag Contract**: [`../../tag_contract.yaml`](../../tag_contract.yaml)
- **Slice Definition**: [`../../slices/wd-uc0-slice.yaml`](../../slices/wd-uc0-slice.yaml)
- **Simulation Architecture**: [`sphere-docs/docs/sim/ARCH_SIM_TICK.md`](https://github.com/SPHERE/sphere-docs/blob/main/docs/sim/ARCH_SIM_TICK.md)

## Real-World Grounding

- AWWA M32: Computer Modeling of Water Distribution Systems
- EPA EPANET: Hydraulic and water quality modeling
- Municipal water system operational data (when available)

## Current Status

**WD-UC0** is a synthetic/demo slice:
- Tag contract complete (21 tags)
- Golden runs generated via `genruns-wd`
- Diagram and overlay implemented
- **No PLC program** - mapping is structurally valid but pending implementation

## Validation

Each process model must satisfy:

1. **Tag consistency**: All tags in the model match `tag_contract.yaml`
2. **Parameter documentation**: Flow rates, tank capacities, timing documented
3. **Scenario coverage**: At least one golden run scenario defined
4. **Real-world grounding**: Parameters cite source or marked as estimated
