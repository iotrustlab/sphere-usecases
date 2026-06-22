# Controller_PLC OpenPLC Project

This project contains the OpenPLC translation of the water-treatment Controller_PLC from Rockwell L5X format.

## Files

- `plc.xml` - Main PLC program in PLCopen XML format
- `beremiz.xml` - Beremiz/OpenPLC Editor configuration file

## Source

- **Original:** `Controller_PLC.L5X` + `Controller_PLC.L5K` (Rockwell format)
- **Translated:** 2025-09-18 using CrossPLC
- **Target:** OpenPLC Editor (Beremiz-compatible)

## Usage

1. Open OpenPLC Editor
2. Select "Open Project"
3. Choose this entire folder (`controller_project`)
4. The editor should load the project successfully

## Translation Notes

- Generated from Rockwell L5X with L5K overlay for enhanced tag information
- Preserves state machines and control logic
- Compatible with OpenPLC Editor and Beremiz
- High fidelity translation maintaining original functionality

