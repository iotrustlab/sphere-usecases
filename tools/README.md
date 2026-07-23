# SPHERE Use Cases - Tools

Repository-level tools for use case validation and testing.

## Available Tools

### hwtest/

Backend-agnostic hardware signal testing framework for validating PLC I/O configurations.

- [hwtest README](hwtest/README.md)

### fuxa-demo/

FUXA-based HMI demo stack for demonstrating SPHERE use cases with a web interface. Includes Docker Compose setup, Modbus bridge, and demo automation scripts.

- [fuxa-demo README](fuxa-demo/README.md)
- Supports multiple use cases: WT (water treatment), WD (water distribution), PS (power hydro)
- Run with `USECASE=wt docker-compose up`

## Reusable Analysis Tools

Use-case-agnostic analysis tools (network capture parsing, timestamp alignment, ground-truth verification) have been consolidated into [`cps-enclave-model/tools/dpi/`](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model/-/tree/main/tools/dpi).

## Use-Case Scripts

Implementation-specific scripts (validation, deployment, local execution) live inside each use case directory:

- `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/openplc/scripts/` - OpenPLC local run scripts
- `sector-water/rovisys-treatment/usecases/p1-onboarding/implementations/rockwell/scripts/` - Rockwell validation and deployment
