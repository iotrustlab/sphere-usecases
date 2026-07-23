# Water Treatment Process Models

This directory contains detailed dynamic models for each process in the Water Treatment use case.

## Process Map

```
                    ┌─────────────────────────────────────────────────┐
                    │              Water Treatment Plant              │
                    └─────────────────────────────────────────────────┘
                                          │
      ┌───────────────────────────────────┼───────────────────────────────────┐
      │                                   │                                   │
      ▼                                   ▼                                   ▼
┌───────────┐                      ┌───────────┐                      ┌───────────┐
│    P1     │                      │    P2     │                      │    P3     │
│ Raw Water │ ─────────────────►   │ Chemical  │ ─────────────────►   │   Ultra-  │
│  Intake   │                      │ Treatment │                      │ filtration│
└───────────┘                      └───────────┘                      └───────────┘
     │                                   │                                   │
     │ RW Tank                           │ NaCl, NaOCl, HCl                  │ UFFT Tank
     │ RW Pump                           │ Dosing Valves                     │ Drain/ROFT
     │ PR/P6B/P Valves                   │                                   │ BWP Valves
     │                                   │                                   │
     ▼                                   ▼                                   ▼
   ════════════════════════════════════════════════════════════════════════════
                              Implemented in UC1 (wt-uc1)
   ════════════════════════════════════════════════════════════════════════════

   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                              Planned for Future Slices
   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│    P4     │   │    P5     │   │    P6     │   │    P7     │   │    P8     │
│Dechlori-  │   │ Reverse   │   │ Backwash  │   │ Permeate  │   │  Supply   │
│  nation   │   │  Osmosis  │   │           │   │           │   │           │
└───────────┘   └───────────┘   └───────────┘   └───────────┘   └───────────┘
   (planned)      (planned)      (planned)      (planned)      (planned)
```

## Process Documentation

| Process | ID | Document | Status |
|---------|-----|----------|--------|
| Raw Water Intake | WT-P1 | [wt-p1-raw-water.md](wt-p1-raw-water.md) | Documented |
| Chemical Treatment | WT-P2 | [wt-p2-chemical-treatment.md](wt-p2-chemical-treatment.md) | Documented |
| Ultrafiltration | WT-P3 | [wt-p3-ultrafiltration.md](wt-p3-ultrafiltration.md) | Documented |
| Dechlorination | WT-P4 | - | Planned |
| Reverse Osmosis | WT-P5 | - | Planned |
| Backwash | WT-P6 | - | Planned |
| Permeate | WT-P7 | - | Planned |
| Supply | WT-P8 | - | Planned |

## Slices

| Slice | Processes | Description |
|-------|-----------|-------------|
| `wt-uc1` | P1 + P2 + P3 | Basic treatment train (current) |
| `wt-uc2` | P1 + P2 + P3 + P5 | Add RO for higher purity (planned) |
| `wt-uc3` | P1-P7 | Complete treatment plant (planned) |

## System-Level Documentation

- [System State Machine](wt-system-state.md) (planned) - IDLE/START/RUNNING/SHUTDOWN states and transitions
- [Alarm Model](wt-alarms.md) (planned) - Level alarms and their thresholds

## References

- **Functional Design Specification**: USC24A-FDS-001 Rev B (RoviSys, Dec 2024)
- **I/O List**: USC24A-IOL-001 (USC Finalized IO List)
- **Tag Contract**: [`../../tag_contract.yaml`](../../tag_contract.yaml)
- **Invariant Rules**: [`tools/defense/rules/water-treatment.yaml`](https://github.com/SPHERE/cps-enclave-model/blob/main/tools/defense/rules/water-treatment.yaml)
- **Simulation Architecture**: [`sphere-docs/docs/sim/ARCH_SIM_TICK.md`](https://github.com/SPHERE/sphere-docs/blob/main/docs/sim/ARCH_SIM_TICK.md)

## Validation

Each process model must satisfy:

1. **Tag consistency**: All tags in the model match `tag_contract.yaml`
2. **Invariant coverage**: Range, correlation, and rate-of-change rules defined
3. **Scenario coverage**: At least one validation scenario per process
4. **Parameter sourcing**: All parameters cite their source (FDS, literature, or estimated)
