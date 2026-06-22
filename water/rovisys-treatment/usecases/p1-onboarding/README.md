# P1 Onboarding Demo

Self-contained beta-user demo for the water treatment P1 (Raw Water Intake) process.

## Purpose

This demo provides a minimal, working example for:
- Beta user onboarding and smoke testing
- CTF1 baseline scenario
- First end-to-end validation workflow

## Contents

- `rockwell/` - Rockwell L5X project files and HMI assets
- `openplc/` - OpenPLC structured text and project files
- `screenshots/` - Operator-facing screenshots and walkthroughs
- `validation/` - Validation checklists and results
- `golden-runs/` - Reference run bundles for comparison

## How to Use

1. Choose your implementation (Rockwell or OpenPLC)
2. Load the PLC project files
3. Start the HMI
4. Run the demo scenario

See `runbook.md` for detailed steps.

## Differences from Full P1-to-P6

This demo is intentionally simplified:
- Single process only (P1)
- Minimal HMI (ultrafiltration tank fill)
- Basic physics model

The full P1-to-P6 implementation will include all six processes with interconnections.

## Known Limitations

- [ ] Physics model needs refinement for realistic waterflow
- [ ] HMI version-control format TBD
- [ ] Golden runs not yet generated

## Related Issues

- sphere-usecases#27 (packaging this demo)
- sphere-usecases#5 (beta user smoke tests)
- sphere-usecases#6 (beta user onboarding)
