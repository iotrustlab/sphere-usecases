# Controller Mappings

Global reference for controller I/O mappings across use cases.

## Current Mappings

- **OpenPLC (Water Treatment UC1):** See [`water-treatment/implementations/openplc/configs/`](../water-treatment/implementations/openplc/configs/) for Modbus address assignments and tag-to-register mappings.
- **Rockwell (Water Treatment):** See [`water-treatment/implementations/rockwell/plc/`](../water-treatment/implementations/rockwell/plc/) for L5X/L5K programs with embedded tag definitions.

## Policy

- **Per-use-case copies**: Each use case maintains a frozen snapshot in `docs/io_map.csv` for reproducibility.
- **This directory**: Contains cross-use-case reference documentation and naming conventions.
