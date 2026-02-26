# GRFICSv3 Integration Runbook (SPHERE)

This runbook is the operational path to stand up GRFICSv3 and produce a replayable SPHERE run bundle in under 15 minutes once VMs are available.

## 1) VM Topology and Network Assumptions

GRFICSv3 uses a 4-VM VirtualBox deployment on host-only network `192.168.95.0/24`.

| VM | IP | Purpose |
|---|---|---|
| ChemicalPlant | `192.168.95.10-15` | C++ Tennessee Eastman simulation + 6 Remote I/O Modbus servers |
| plc | `192.168.95.2` | OpenPLC runtime + control logic |
| ScadaBR | `192.168.95.5` | HMI web UI (`:8080/ScadaBR/`) |
| Workstation | `192.168.95.6` | Operator/attack tooling host |

Network assumptions:
- All VMs are attached to `vboxnet0`.
- Host is reachable on `192.168.95.x` (commonly `192.168.95.111`).
- Startup order matters: `ChemicalPlant` -> `plc` -> `ScadaBR`.

## 2) Tennessee Eastman Plant Overview

GRFICSv3 models a Tennessee Eastman chemical process with:
- 4 control valves: Feed 1, Feed 2, Purge, Product
- Reactor tank pressure and level
- Purge composition analyzer (A/B/C fractions)
- Simplified chemistry centered on `A + C -> D`

Engineering units (from `tag_contract.yaml`):

| Measurement | Range | Units |
|---|---|---|
| Valve position | 0-100 | % |
| Flow rate | 0-500 | kmol/h |
| Tank pressure | 0-3200 | kPa |
| Tank level | 0-100 | % |
| Composition | 0-1 | mole fraction |

## 3) SPHERE Integration Glue

Core files:
- `grfics/tag_contract.yaml` — canonical 17 tags
- `grfics/source_map.yaml` — Modbus endpoint/register mapping
- `grfics/scripts/grfics_bridge.py` — live Modbus polling to run bundle
- `grfics/slices/grfics-te-full-slice.yaml` — viewer slice
- `cps-enclave-model/tools/defense/rules/grfics-te.yaml` — invariants

Modbus endpoint map (from `source_map.yaml`):

```text
feed1:    192.168.95.10:502 (slave 247)
feed2:    192.168.95.11:502 (slave 247)
purge:    192.168.95.12:502 (slave 247)
product:  192.168.95.13:502 (slave 247)
tank:     192.168.95.14:502 (slave 247)
analyzer: 192.168.95.15:502 (slave 247)
```

## 4) Start Here (Boot -> Run -> Replay)

### Prerequisites

```bash
# Host-only network present
VBoxManage list hostonlyifs | rg vboxnet0

# Python env for GRFICS bridge
cd /Users/lag/Development/sphere-usecases/grfics
python3 -m venv .venv
source .venv/bin/activate
pip install pymodbus pyyaml
```

### Boot VMs (order matters)

1. Start `ChemicalPlant`, wait ~30s
2. Start `plc`, wait ~30s
3. Start `ScadaBR`, wait ~60s

### Verify Connectivity

```bash
ping -c 1 192.168.95.10
ping -c 1 192.168.95.11
ping -c 1 192.168.95.12
ping -c 1 192.168.95.13
ping -c 1 192.168.95.14
ping -c 1 192.168.95.15
ping -c 1 192.168.95.2
ping -c 1 192.168.95.5
curl -s http://192.168.95.5:8080/ScadaBR/ | head -1
```

### Capture Run Bundle

```bash
cd /Users/lag/Development/sphere-usecases/grfics
source .venv/bin/activate

python scripts/grfics_bridge.py \
  --output runs/run-demo-01 \
  --duration 120 \
  --poll-ms 500 \
  --verbose
```

Verification checkpoint:

```bash
ls -la runs/run-demo-01
head -5 runs/run-demo-01/tags.csv
```

### Validate Bundle

```bash
cd /Users/lag/Development/cps-enclave-model
./bin/validate-bundle ../sphere-usecases/grfics/runs/run-demo-01
```

### Run Attack + Defense

```bash
cd /Users/lag/Development/cps-enclave-model

./scripts/toolbox-run.sh ../sphere-usecases/grfics/runs/run-demo-01 \
  --tag TE_Tank_Pressure \
  --offset 100 \
  --start 20 \
  --end 40 \
  --rules tools/defense/rules/grfics-te.yaml
```

Expected artifacts:
- `.../artifacts/tag-perturb/`
- `.../artifacts/invariant-check/`

### Replay in Viewer

```bash
cd /Users/lag/Development/cps-enclave-model

go run ./cps-enclave-viewer/cmd/viewer \
  -data ../sphere-usecases/grfics/runs \
  -assets-dir ../sphere-usecases/grfics/assets \
  -slice ../sphere-usecases/grfics/slices/grfics-te-full-slice.yaml \
  -addr :8085
```

Open: `http://localhost:8085`

### Access ScadaBR

Open: `http://192.168.95.5:8080/ScadaBR/`

Credentials:
- user: `admin`
- password: `admin`

## 5) Done vs Pending Checklist

Done:
- [x] Tag contract (`grfics/tag_contract.yaml`)
- [x] Source map (`grfics/source_map.yaml`)
- [x] Bridge script (`grfics/scripts/grfics_bridge.py`)
- [x] Invariant rules (`tools/defense/rules/grfics-te.yaml`)
- [x] Slice definition (`grfics/slices/grfics-te-full-slice.yaml`)
- [x] Demo profile (`grfics/profiles/demo.yaml`)
- [x] Demo guide (`cps-enclave-model/docs/demo/GRFICS_DEMO.md`)

Pending:
- [ ] P&ID SVG upgrade (replace placeholder `grfics/assets/grfics-te.svg`)
- [ ] Stable golden run generation path for GRFICS
- [ ] Full viewer overlay positioning validation
- [ ] Expanded attack scenario library
- [ ] Live VM validation cycle completion when endpoints are reachable

## Troubleshooting

- `pymodbus` import failure:
  - Re-activate `grfics/.venv` and reinstall dependencies.
- Missing values during polling:
  - Restart remote I/O services in GRFICS simulation VM.
- ScadaBR not loading:
  - Wait additional 60-90s; verify Java process in VM.
- Host-only network unstable/missing:
  - Recreate `vboxnet0` and reassign VM adapters.

## References

- [GRFICSv3 repository](https://github.com/Fortiphyd/GRFICSv3)
- `grfics/README.md`
- `grfics/tag_contract.yaml`
- `grfics/source_map.yaml`
- `grfics/scripts/grfics_bridge.py`
- `cps-enclave-model/tools/defense/rules/grfics-te.yaml`
