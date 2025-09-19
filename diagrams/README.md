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

## Usage

1. **For Development**: Use this directory as a reference for new use cases
2. **For Use Cases**: Copy relevant diagrams to your use case's `docs/` directory
3. **For Reproducibility**: Use the frozen snapshots in each use case's documentation

## Contributing

- Update global references here when adding new diagram types or standards
- Ensure per-use-case snapshots are updated when global references change
- Document any breaking changes or migration requirements
- Follow standard naming conventions for diagram files