# Tag Layouts

This directory serves as a **global reference** for tag naming conventions and layouts across all use cases.

## Purpose

- **Reference Documentation**: Global tag naming conventions and layouts
- **Cross-Use-Case Consistency**: Ensure consistent tag naming across all use cases
- **Development Guidelines**: Standard patterns for tag organization

## Policy: Reference vs Snapshot

- **This directory**: Contains **reference** documentation that may evolve
- **Per-use-case copies**: Each use case maintains a **frozen snapshot** in `docs/io_map.csv`
- **Versioning**: Use case snapshots are versioned with the use case for reproducibility

## Tag Naming Conventions

Tags follow a `Component_Parameter` pattern. The component prefix identifies the process stage; the suffix identifies the role.

### Component prefixes (Water Treatment)

| Prefix | Stage | Description |
|--------|-------|-------------|
| `RW_` | P1 | Raw Water Intake (tank, pump, valves) |
| `ChemTreat_` | P2 | Chemical Treatment (NaCl, NaOCl, HCl tanks) |
| `UF_` | P3 | Ultrafiltration (filter, pump, tank) |
| `SYS_` | sys | System state flags |
| `Alarm_` | alm | Alarm indicators |

### Role suffixes

| Suffix | Role | Data type | Examples |
|--------|------|-----------|---------|
| `_Level` | sensor | analog (mm) | `RW_Tank_Level` |
| `_Flow` | sensor | analog (L/min) | `RW_Pump_Flow` |
| `_Speed` | sensor | analog (%) | `RW_Pump_Speed` |
| `_Sts` | status | boolean | `RW_Pump_Sts` |
| `_Fault` | alarm | boolean | `RW_Pump_Fault` |
| `_Start` / `_Stop` | command | boolean | `RW_Pump_Start` |
| (no suffix) | varies | boolean | `SYS_IDLE`, `SYS_RUNNING` |

### Canonical tag inventory

The authoritative tag inventory for each use case lives in cps-enclave-model:
- `cps-enclave-viewer/assets/water-treatment.tags.normalized.yaml` — tags grouped by component with role and unit metadata
- `cps-enclave-viewer/assets/water-treatment.tags.by_group.yaml` — tags grouped by process stage

## Usage

1. **For Development**: Use this directory as a reference for new use cases
2. **For Use Cases**: Copy relevant tag layouts to your use case's `docs/io_map.csv`
3. **For Reproducibility**: Use the frozen snapshot in each use case's documentation

## Contributing

- Update global references here when adding new tag types or conventions
- Ensure per-use-case snapshots are updated when global references change
- Document any breaking changes or migration requirements
