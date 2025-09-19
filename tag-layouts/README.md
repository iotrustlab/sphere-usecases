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

- **Process Prefix**: Use case identifier (e.g., `WT_` for water treatment)
- **Component Type**: Equipment type (e.g., `Pump`, `Valve`, `Sensor`)
- **Instance Number**: Sequential numbering (e.g., `01`, `02`)
- **Parameter**: Specific parameter (e.g., `Status`, `Speed`, `Pressure`)

Example: `WT_Pump01_Status`, `WT_Valve02_Position`, `WT_Sensor03_pH`

## Usage

1. **For Development**: Use this directory as a reference for new use cases
2. **For Use Cases**: Copy relevant tag layouts to your use case's `docs/io_map.csv`
3. **For Reproducibility**: Use the frozen snapshot in each use case's documentation

## Contributing

- Update global references here when adding new tag types or conventions
- Ensure per-use-case snapshots are updated when global references change
- Document any breaking changes or migration requirements