# SPHERE Use Cases - Tools

Repository-level tools for use case validation and testing.

## Available Tools

### hwtest/

Backend-agnostic hardware signal testing framework for validating PLC I/O configurations.

- [hwtest README](hwtest/README.md)

## Reusable Analysis Tools

Use-case-agnostic analysis tools (network capture parsing, timestamp alignment, ground-truth verification) have been consolidated into [`cps-enclave-model/tools/dpi/`](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model/-/tree/main/tools/dpi).

## Use-Case Scripts

Implementation-specific scripts (validation, deployment, local execution) live inside each use case directory:

- `water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/scripts/` - OpenPLC local run scripts
- `water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/scripts/` - Rockwell validation and deployment
