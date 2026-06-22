# GRFICS OpenPLC Implementation (SPHERE-Native)

This implementation uses SPHERE's dual-PLC architecture to replicate the Tennessee Eastman process from GRFICSv3.

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
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

## File Locations

The SPHERE-native GRFICS implementation files are in the platform repo, not here:

| File | Location | Purpose |
|------|----------|---------|
| Controller ST | `cps-enclave-model/docker/scadabr/openplc/grfics_controller.st` | Control logic |
| Simulator ST | `cps-enclave-model/docker/scadabr/openplc/grfics_simulator.st` | TE physics |
| Bridge | `cps-enclave-model/docker/scadabr/bridge/grfics_modbus_bridge.py` | Modbus shuttle |
| Docker Compose | `cps-enclave-model/docker/scadabr/docker-compose.yml` | Local deployment |
| Ansible | `cps-enclave-model/docker/scadabr/ansible/` | SPHERE testbed deployment |

## Why Not Here?

The OpenPLC logic and bridge are deployed via Docker/Ansible from `cps-enclave-model`. This directory exists for consistency with the SPHERE use-case pattern, but the actual implementation artifacts are in the platform repo because:

1. **Docker build context** — ST files must be adjacent to Dockerfiles
2. **Ansible roles** — Deployment playbooks live with the Docker stack
3. **Shared infrastructure** — The ScadaBR stack supports multiple use cases

## Use-Case Assets

Use-case-specific assets remain in this repo:

| Asset | Location |
|-------|----------|
| Tag contract | `../../tag_contract.yaml` |
| Source map | `../../source_map.yaml` |
| Slice definitions | `../../slices/` |
| Invariant rules | `cps-enclave-model/tools/defense/rules/grfics-te.yaml` |

## Deployment

See the [GRFICS Runbook](../../docs/GRFICS_RUNBOOK.md) for deployment instructions.

### Quick Start (Local Docker)

```bash
cd /path/to/cps-enclave-model
docker compose -f docker/scadabr/docker-compose.yml up
```

### SPHERE Testbed

```bash
cd /path/to/cps-enclave-model/docker/scadabr/ansible
ansible-playbook -i inventory.yml site.yml
```

## Register Mapping

| Direction | Source | Destination | Tags |
|-----------|--------|-------------|------|
| Ctrl → Sim | Controller HR 0-3 | Simulator HR 200-203 | 4 valve setpoints |
| Sim → Ctrl | Simulator HR 300-312 | Controller HR 300-312 | 13 sensor values |

## Differences from Original GRFICSv3

| Aspect | GRFICSv3 VMs | SPHERE-Native |
|--------|--------------|---------------|
| Deployment | VirtualBox VMs | Docker containers |
| Network | 192.168.95.0/24 | Docker bridge or SPHERE testbed |
| Endpoints | 6 remote I/O servers | 1 controller (aggregated via bridge) |
| HMI | ScadaBR VM | ScadaBR container |
| Reproducibility | Manual VM setup | `docker compose up` |

## See Also

- [Tag Contract](../../tag_contract.yaml) — 17 canonical tags
- [Source Map](../../source_map.yaml) — Modbus register mapping
- [GRFICS Runbook](../../docs/GRFICS_RUNBOOK.md) — Full deployment guide
