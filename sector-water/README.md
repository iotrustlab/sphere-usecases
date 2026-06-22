# Water and Wastewater Systems

**CISA Critical Infrastructure Sector 16**

This sector contains use cases related to water treatment, distribution, and wastewater systems.

## Vendor Use Cases

| Vendor | Domain | Description |
|--------|--------|-------------|
| [rovisys-treatment](./rovisys-treatment/) | Water Treatment | Rovisys water treatment plant (P1-P6 processes) |
| [rovisys-distribution](./rovisys-distribution/) | Water Distribution | Rovisys water distribution network |

## Structure

Each vendor use case follows the standard hierarchy:

```
<vendor>-<domain>/
├── usecases/                 # Use case instances
│   ├── p1-onboarding/        # Demo/onboarding use case
│   └── full-system-p1-to-p6/ # Full implementation
├── shared/                   # Shared assets across use cases
├── processes/                # Per-process documentation
├── docs/                     # Domain documentation
├── profiles/                 # Simulation profiles
├── slices/                   # Viewer slice definitions
└── tag_contract.yaml         # Canonical tag definitions
```

## References

- [CISA Water Sector Resources](https://www.cisa.gov/topics/critical-infrastructure-security-and-resilience/critical-infrastructure-sectors/water-and-wastewater-systems-sector)
- [SWaT Dataset](https://itrust.sutd.edu.sg/testbeds/secure-water-treatment-swat/) - Singapore Water Treatment testbed
