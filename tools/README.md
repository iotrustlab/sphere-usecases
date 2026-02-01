# SPHERE Use Cases — Tools

This directory is reserved for use-case-specific validation and utility scripts.

## Reusable Analysis Tools

Use-case-agnostic analysis tools (network capture parsing, timestamp alignment, ground-truth verification) have been consolidated into [`cps-enclave-model/tools/dpi/`](https://gitlab.com/mergetb/facilities/sphere/cyber-physical-systems/cps-enclave-model/-/tree/main/tools/dpi).

## Use-Case Scripts

Implementation-specific scripts (validation, deployment, local execution) live inside each use case directory:

- `water-treatment/implementations/openplc/scripts/` — OpenPLC local run scripts
- `water-treatment/implementations/rockwell/scripts/` — Rockwell validation and deployment
