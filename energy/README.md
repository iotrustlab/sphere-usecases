# Energy Sector

**CISA Critical Infrastructure Sector 8**

This sector contains use cases related to power generation, transmission, and oil/gas distribution.

## Vendor Use Cases

| Source | Domain | Description |
|--------|--------|-------------|
| [olmsted-hydro](./olmsted-hydro/) | Hydroelectric | Olmsted Dam hydroelectric power station |
| [oil-and-gas](./oil-and-gas/) | Oil & Gas | Pipeline distribution systems |

## Structure

Each use case follows the standard hierarchy:

```
<source>/
├── usecases/                 # Use case instances
│   └── ps-1-generic-hydro/   # Generic hydro station
├── shared/                   # Shared assets
├── docs/                     # Domain documentation
├── profiles/                 # Simulation profiles
└── tag_contract.yaml         # Canonical tag definitions
```

## References

- [CISA Energy Sector Resources](https://www.cisa.gov/topics/critical-infrastructure-security-and-resilience/critical-infrastructure-sectors/energy-sector)
- [Olmsted Locks and Dam](https://www.lrl.usace.army.mil/Missions/Civil-Works/Navigation/Olmsted-Locks-and-Dam/)
