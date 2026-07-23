# SPHERE Conventions

This directory contains reference documentation for conventions used across all use cases.

## Contents

| Document | Description |
|----------|-------------|
| [diagrams.md](diagrams.md) | P&ID pipeline and diagram generation conventions |
| [tag-naming.md](tag-naming.md) | Tag naming conventions and patterns |
| [controller-mappings.md](controller-mappings.md) | Controller I/O mapping references |

## Policy: Reference vs Snapshot

These documents serve as **evolving references** for conventions. Each use case maintains **frozen snapshots** of relevant artifacts (e.g., `docs/io_map.csv`) for reproducibility.

- **This directory**: Contains reference documentation that may evolve
- **Per-use-case copies**: Use cases freeze snapshots in their own `docs/` directory
- **Versioning**: Use case snapshots are versioned with the use case

## Contributing

When updating conventions:
1. Update the reference documentation here
2. Document any breaking changes or migration requirements
3. Ensure per-use-case snapshots are updated when global references change
