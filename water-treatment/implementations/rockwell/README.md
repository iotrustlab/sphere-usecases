# Water Treatment - Rockwell Implementation

This directory contains the Rockwell Logix 5000 PLC programs for the water treatment Process One (P1) scenario.

## Authoritative Files

The Rockwell L5X files are the **canonical source** for all PLC logic. OpenPLC implementations are generated from these via CrossPLC translation.

**Main files** (use these):
| File | Format | Purpose |
|------|--------|---------|
| `plc/Controller_PLC.L5X` | Rockwell XML | Controller logic (import to Studio 5000) |
| `plc/Controller_PLC.L5K` | Rockwell ASCII | Controller logic (text format) |
| `plc/Simulator_PLC.L5X` | Rockwell XML | Simulator/plant model (import to Studio 5000) |
| `plc/Simulator_PLC.L5K` | Rockwell ASCII | Simulator/plant model (text format) |

**Supporting files**:
| File | Purpose |
|------|---------|
| `rockwell_map.yaml` | Tag-to-address mapping for DPI and validation |
| `scripts/` | Utility scripts for tag analysis |

**Archived files** (in `old/`):
- `Controller_PLC_Process_*.L5X/L5K` - Earlier naming convention
- `Simulator_Process_*.L5X/L5K` - Earlier naming convention
- `ProcessOne_*_V1.*` - Explicit V1 versions
- `*_Updated_Test.*` - Test versions
- `*.backup` - Backup files

## File Formats

- **L5X (XML)**: Import/export format for Studio 5000 Logix Designer. Use for importing into Rockwell hardware.
- **L5K (ASCII)**: Text-based format, useful for diff/review. Contains same logic as L5X.

## Process Description

Process One (P1) is the raw water intake system:

1. Raw water enters the tank through the PR (pressure relief) valve
2. When the UF tank needs water, the pump transfers water from raw water tank
3. Tank level is maintained between 500-800mm
4. Alarms trigger at 250mm (LL), 500mm (L), 800mm (H), 1200mm (HH)

## CrossPLC Translation

To generate OpenPLC equivalents from these files:

```bash
# Generate PLCopen XML from Rockwell L5X
crossplc translate plc/Controller_PLC.L5X -o ../openplc/projects/controller_project/plc.xml
crossplc translate plc/Simulator_PLC.L5X -o ../openplc/projects/simulator_project/plc.xml
```

## Tag Mapping

The `rockwell_map.yaml` file defines the mapping between Rockwell tags and Modbus addresses used for:
- Deep packet inspection (DPI)
- Run bundle generation
- Invariant validation

## Integration with SPHERE

These files integrate with the SPHERE CPS infrastructure:
- Use `node-test-rockwell` from `cps-enclave-model` for live tag polling
- DPI tools in `cps-enclave-model/tools/dpi/` parse Rockwell protocol traffic
- Tag contracts in `../../../tag_contract.yaml` define expected tag behavior
