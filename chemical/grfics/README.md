# GRFICSv3 — Tennessee Eastman Process Integration

SPHERE integration of the Tennessee Eastman chemical reactor process, originally from [GRFICSv3](https://github.com/Fortiphyd/GRFICSv3).

> This README describes local GRFICS assets and execution paths only. Canonical milestone status and backlog live in [`../../sphere-docs/ROADMAP.md`](../../sphere-docs/ROADMAP.md) and [`../../sphere-docs/BACKLOG.md`](../../sphere-docs/BACKLOG.md).

## Overview

This integration adapts the Tennessee Eastman process as a SPHERE use case using a **native dual-PLC architecture** (not the original VirtualBox VMs). The implementation runs via Docker locally or via Ansible on SPHERE testbed nodes.

**Upstream:** [github.com/Fortiphyd/GRFICSv3](https://github.com/Fortiphyd/GRFICSv3)

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Controller    │◄───────►│     Bridge      │◄───────►│   Simulator     │
│   (OpenPLC)     │         │   (Python)      │         │   (OpenPLC)     │
│                 │         │                 │         │                 │
│ grfics_         │  HR 0-3 │ Modbus shuttle  │ HR 200+ │ grfics_         │
│ controller.st   │ ───────►│ every 100ms     │────────►│ simulator.st    │
│                 │         │                 │         │                 │
│                 │ HR 300+ │                 │ HR 300+ │ TE physics      │
│                 │◄─────── │                 │◄────────│ simulation      │
└────────┬────────┘         └─────────────────┘         └─────────────────┘
         │
         ▼
┌─────────────────┐
│    ScadaBR      │
│    (HMI)        │
└─────────────────┘
```

**Key difference from upstream GRFICSv3:** SPHERE uses a dual-PLC pattern where all tags are accessed via the Controller PLC. The bridge shuttles data between Controller and Simulator internally.

## Process Description

The Tennessee Eastman process simulates a chemical reactor with:

- **4 control valves:** Feed 1, Feed 2, Purge, Product
- **Tank measurements:** Pressure (0-3200 kPa), Level (0-100%)
- **Analyzer:** Composition of A, B, C in purge stream (mole fractions)
- **Simplified chemistry:** A + C → D

### Engineering Units

| Measurement | Range | Units |
|-------------|-------|-------|
| Valve position | 0-100 | % |
| Flow rate | 0-500 | kmol/h |
| Tank pressure | 0-3200 | kPa |
| Tank level | 0-100 | % |
| Composition | 0-1 | mole fraction |

## Quick Start

### Local Docker (Recommended for Development)

```bash
cd /path/to/cps-enclave-model

# Start the stack
docker compose -f docker/scadabr/docker-compose.yml up

# Or use the smoke script
./scripts/scadabr-local-smoke.sh --keep-running
```

Access points:
- Controller Web UI: http://localhost:18081 (openplc/openplc)
- Simulator Web UI: http://localhost:18082 (openplc/openplc)
- ScadaBR HMI: http://localhost:18080/ScadaBR/ (admin/admin)
- Controller Modbus: localhost:1502
- Simulator Modbus: localhost:1503

### SPHERE Testbed (Ansible)

```bash
cd /path/to/cps-enclave-model/docker/scadabr/ansible
cp inventory.example.yml inventory.yml
# Edit inventory.yml with actual node IPs
ansible-playbook -i inventory.yml site.yml
```

### Capture Run Bundle

```bash
cd /path/to/cps-enclave-model

./bin/usecase-runner \
  --contract ../sphere-usecases/chemical/grfics/tag_contract.yaml \
  --mapping ../sphere-usecases/chemical/grfics/openplc_backend_map.yaml \
  --controller-endpoint localhost:1502 \
  --simulator-endpoint localhost:1503 \
  --run-dir ../sphere-usecases/chemical/grfics/runs/run-local-01 \
  --duration 120s \
  --poll-ms 500 \
  --emit-tags all_contract

# Validate bundle
./bin/validate-bundle ../sphere-usecases/chemical/grfics/runs/run-local-01
```

### Run Toolbox

```bash
# Attack: perturb tank pressure reading
./scripts/toolbox-run.sh ../sphere-usecases/chemical/grfics/runs/run-local-01 \
  --tag TE_Tank_Pressure --offset 100 \
  --rules tools/defense/rules/grfics-te.yaml

# View in SPHERE viewer
go run ./cps-enclave-viewer/cmd/viewer/ \
  -data ../sphere-usecases/chemical/grfics/runs \
  -assets-dir ../sphere-usecases/chemical/grfics/assets \
  -slice ../sphere-usecases/chemical/grfics/slices/grfics-te-full-slice.yaml \
  -addr :8085
```

## Files

### Use-Case Assets (This Repo)

| File | Purpose |
|------|---------|
| `tag_contract.yaml` | 17 canonical tags for Tennessee Eastman |
| `source_map.yaml` | Rich `SourceMap` reference for bridge/original-VM lineage |
| `openplc_backend_map.yaml` | Flat `BackendMapping` for `usecase-runner` against the SPHERE dual-PLC stack |
| `slices/grfics-te-full-slice.yaml` | Viewer slice definition |
| `profiles/demo.yaml` | Timing/physics profile |
| `implementations/openplc/README.md` | Implementation reference |
| `docs/GRFICS_RUNBOOK.md` | Full deployment guide |
| `runs/` | Captured run bundles |
| `assets/` | Diagrams (placeholder) |

### Platform Files (cps-enclave-model)

| File | Purpose |
|------|---------|
| `docker/scadabr/openplc/grfics_controller.st` | Controller PLC logic |
| `docker/scadabr/openplc/grfics_simulator.st` | Simulator physics |
| `docker/scadabr/bridge/grfics_modbus_bridge.py` | Modbus shuttle |
| `docker/scadabr/docker-compose.yml` | Local Docker deployment |
| `docker/scadabr/ansible/` | SPHERE testbed deployment |
| `tools/defense/rules/grfics-te.yaml` | Invariant rules |

## Register Mapping

| Direction | Source | Destination | Tags |
|-----------|--------|-------------|------|
| Ctrl → Sim | Controller HR 0-3 | Simulator HR 200-203 | 4 valve setpoints |
| Sim → Ctrl | Simulator HR 300-312 | Controller HR 300-312 | 13 sensor values |

`source_map.yaml` keeps the richer multi-endpoint/source-map semantics used by the bridge/reference path. `openplc_backend_map.yaml` is the verified `usecase-runner` mapping for the current SPHERE-native dual-PLC deployment.

## Deprecated

The file `scripts/grfics_bridge.py` was designed for the original GRFICSv3 VirtualBox VMs (6 separate remote I/O servers at 192.168.95.x). It is retained for reference but should not be used. The SPHERE-native bridge is at `cps-enclave-model/docker/scadabr/bridge/grfics_modbus_bridge.py`.

## References

- [GRFICSv3 Documentation](https://github.com/Fortiphyd/GRFICSv3)
- [Tennessee Eastman Process](https://doi.org/10.1016/0098-1354(93)80018-I)
- [GRFICS Runbook](docs/GRFICS_RUNBOOK.md)
- SPHERE ADR-0002: Run Bundle Schema
- SPHERE ADR-0003: Diagram Overlay Schema
