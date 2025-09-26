# Controller_PLC Flattened OpenPLC Project

This project contains the flattened OpenPLC translation of the water-treatment Controller_PLC from Rockwell L5X format using unified IR models.

## Files

- `plc.xml` - Main PLC program in PLCopen XML format (flattened)
- `beremiz.xml` - Beremiz/OpenPLC Editor configuration file

## Source

- **Original:** `Controller_PLC.L5X` + `Controller_PLC.L5K` (Rockwell format)
- **Translated:** 2025-09-25 using CrossPLC with unified IR models
- **Target:** OpenPLC Editor (Beremiz-compatible)
- **Mode:** Flattened with unified IR abstractions

## Usage

1. Open OpenPLC Editor
2. Select "Open Project"
3. Choose this entire folder (`controller_flat_project`)
4. The editor should load the project successfully

## Translation Notes

- Generated from Rockwell L5X with L5K overlay for enhanced tag information
- Uses unified IR models for consistent variable declarations and control flow
- Flattened structure for simplified OpenPLC compatibility
- Preserves state machines and control logic
- Compatible with OpenPLC Editor and Beremiz
- High fidelity translation maintaining original functionality

## IR Unification Features

- Unified variable declarations across all parsers
- Consistent control flow statement handling
- Generic IR representations adhering to IEC standards
- Enhanced tag preservation and type mapping
