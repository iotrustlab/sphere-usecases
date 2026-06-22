# Chemical Sector

**CISA Critical Infrastructure Sector 1**

This sector contains use cases related to chemical manufacturing and processing facilities.

## Vendor Use Cases

| Source | Domain | Description |
|--------|--------|-------------|
| [grfics](./grfics/) | Chemical Process | Tennessee Eastman process (GRFICS testbed) |

## Structure

Each use case follows the standard hierarchy:

```
<source>/
├── usecases/                 # Use case instances
│   └── te-full/              # Full Tennessee Eastman process
├── shared/                   # Shared assets
├── docs/                     # Domain documentation
└── tag_contract.yaml         # Canonical tag definitions
```

## References

- [CISA Chemical Sector Resources](https://www.cisa.gov/topics/critical-infrastructure-security-and-resilience/critical-infrastructure-sectors/chemical-sector)
- [GRFICS Project](https://github.com/Fortiphyd/GRFICSv2) - Graphical Realism Framework for ICS
- [Tennessee Eastman Process](https://depts.washington.edu/control/LARRY/TE/download.html) - Chemical process simulation
