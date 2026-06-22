# System Diagrams

This directory serves as a **global reference** for system diagrams and process documentation across all use cases.

## Purpose

- **Reference Documentation**: Global system diagrams and process documentation
- **Cross-Use-Case Consistency**: Ensure consistent diagram standards across all use cases
- **Development Guidelines**: Standard patterns for process documentation

## Policy: Reference vs Snapshot

- **This directory**: Contains **reference** documentation that may evolve
- **Per-use-case copies**: Each use case maintains **frozen snapshots** in `docs/`
- **Versioning**: Use case snapshots are versioned with the use case for reproducibility

## Diagram Types

- **Process & Instrumentation Diagrams (P&IDs)**: Process flow and instrumentation
- **System Architecture Diagrams**: Overall system architecture
- **Network Topology Diagrams**: Communication and network structure
- **Safety System Diagrams**: Safety interlocks and emergency systems

## Data-Driven P&ID Pipeline

P&ID diagrams for the CPS Enclave Viewer are generated from YAML specs using a pipeline in [cps-enclave-model](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model):

1. **Diagram spec** (`water-treatment.diagram.yaml`) — defines components, positions, anchors, and pipe connections
2. **SVG generator** (`cmd/gensvg/`) — reads the spec and produces SVG with stable anchor IDs (`anchor:COMP:ANCHOR`)
3. **Overlay config** (`water-treatment.overlay.yaml`) — maps tag overlays to component anchors
4. **Validator** (`cmd/validate-diagram/`) — checks consistency between diagram, overlays, and tag inventory

### Anchor naming convention

Generated SVGs use colon-delimited IDs:
- Components: `comp:RW_Tank`, `comp:RW_Pump`
- Anchors: `anchor:RW_Tank:badge_pos`, `anchor:RW_Pump:flow_pos`
- Stage groups: `group-p1`, `group-p2`, etc.

### Symbol library

The SVG generator includes built-in symbols: `tank`, `valve`, `pump`, `mixer`, `filter`, `sensor`, `uv`, `ro`. Each symbol is defined as a reusable `<symbol>` in `<defs>` and referenced via `<use>`.

## Usage

1. **For Development**: Use this directory as a reference for new use cases
2. **For Use Cases**: Copy relevant diagrams to your use case's `docs/` directory
3. **For Reproducibility**: Use the frozen snapshots in each use case's documentation
4. **For the Viewer**: Edit the diagram spec YAML and regenerate with `cmd/gensvg/`

## Contributing

- Update global references here when adding new diagram types or standards
- Ensure per-use-case snapshots are updated when global references change
- Document any breaking changes or migration requirements
- Follow standard naming conventions for diagram files
