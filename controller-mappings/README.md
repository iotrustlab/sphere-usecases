# Controller Mappings

This directory serves as a **global reference** for controller mappings and I/O configurations across all use cases.

## Purpose

- **Reference Documentation**: Global controller mappings and I/O configurations
- **Cross-Use-Case Consistency**: Ensure consistent naming and addressing schemes
- **Development Guidelines**: Standard patterns for controller configuration

## Policy: Reference vs Snapshot

- **This directory**: Contains **reference** documentation that may evolve
- **Per-use-case copies**: Each use case maintains a **frozen snapshot** in `docs/io_map.csv`
- **Versioning**: Use case snapshots are versioned with the use case for reproducibility

## Usage

1. **For Development**: Use this directory as a reference for new use cases
2. **For Use Cases**: Copy relevant mappings to your use case's `docs/io_map.csv`
3. **For Reproducibility**: Use the frozen snapshot in each use case's documentation

## Contributing

- Update global references here when adding new controller types
- Ensure per-use-case snapshots are updated when global references change
- Document any breaking changes or migration requirements