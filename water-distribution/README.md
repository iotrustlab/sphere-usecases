# Water Distribution UC0

Water distribution use case for the SPHERE CPS Enclave. Models a municipal water distribution system with three process groups:

- **Supply Line** — intake tank, variable-speed pump, chemical dosing (NaOCl, NH4Cl), mixer
- **Distribution Grid** — elevated storage tank, consumer storage tank, gravity-fed distribution
- **Return Water System (RWS)** — return tank, recirculation pump, return valve

## Assets

| File | Description |
|------|-------------|
| `tag_contract.yaml` | 21 tags across 5 groups (supply, grid, rws, system, alarms) |
| `slices/wd-uc0-slice.yaml` | Minimal visualization slice for UC0 |
| `assets/water-distribution.svg` | P&ID diagram |
| `assets/water-distribution.overlay.yaml` | Tag overlay positions for diagram |
| `runs/` | Golden run bundles (synthetic data) |

## Running

```bash
# From cps-enclave-model repo:
./scripts/smoke.sh
```

The viewer loads both Water Treatment and Water Distribution slices. Use the slice selector dropdown to switch between them.

## References

- Control assumptions: `docs/assumptions.md`
- Architecture: `../../sphere-docs/ARCH.md`
