# Water Treatment Repository Migration Plan

This document outlines the plan for reorganizing the water-treatment directory to separate the P1 onboarding demo from the full P1-P6 implementation.

## Background

The current structure mixes demo code with full implementation code, creating confusion for:
- Interns trying to understand the codebase
- Beta users looking for a simple starting point
- Contributors trying to add new processes

## New Structure Overview

```
water-treatment/
  docs/                     # Documentation (existing)
  shared/                   # NEW: Shared assets
    tag-contracts/
    mappings/
    signal-models/
    diagrams/
  processes/                # NEW: Per-process reusable assets
    p1/ through p6/
  demos/                    # NEW: Self-contained demos
    p1-onboarding/          # Beta user demo
  full-system/              # NEW: Full implementation
    p1-to-p6/
  tools/                    # NEW: Generic tooling

  # Existing directories (to be evaluated):
  assets/
  datasets/
  experiments/
  implementations/
  profiles/
  runs/
  slices/
```

## Migration Steps

### Phase 1: Skeleton (This PR)
- [x] Create new directory structure
- [x] Add placeholder READMEs
- [x] Create this migration plan
- [ ] Review with Luis

### Phase 2: Demo Packaging (Issue #27)
Owner: Brandon

Files to move to `demos/p1-onboarding/`:
- [ ] Rockwell L5X from `implementations/rockwell/`
- [ ] HMI project files
- [ ] P1-specific structured text

### Phase 3: Shared Asset Extraction
Owner: TBD

Files to move to `shared/`:
- [ ] `tag_contract.yaml` → `shared/tag-contracts/`
- [ ] Diagrams from `assets/` → `shared/diagrams/`
- [ ] Generic mappings

### Phase 4: Process Organization (Depends on #28)
Owner: Apple

After PLC inventory complete:
- [ ] Create per-process directories with assets
- [ ] Document what exists vs. what's missing
- [ ] Create follow-up issues for missing processes

## Files Requiring Classification

| Current Location | Decision | New Location | Notes |
|------------------|----------|--------------|-------|
| `tag_contract.yaml` | Move | `shared/tag-contracts/` | Generic, shared |
| `validate_contract.go` | Move | `tools/` or keep | Validation tooling |
| `implementations/rockwell/` | Evaluate | Per file | Some demo, some full |
| `implementations/openplc/` | Evaluate | Per file | Some demo, some full |
| `assets/` | Evaluate | `shared/` or `demos/` | Depends on content |
| `runs/` | Keep | - | Run bundles stay |
| `slices/` | Keep | - | Slice definitions stay |

## Do Not Delete

The following should NOT be deleted during migration:
- Any existing run bundles in `runs/`
- Datasets in `datasets/`
- Experiment definitions in `experiments/`

## Rollback Plan

If migration causes issues:
1. Branch remains available for comparison
2. Original structure preserved on main until PR merged
3. Follow-up PRs can revert specific moves

## Related Issues

- #26 (this refactor)
- #27 (P1 demo packaging)
- #28 (PLC inventory)
