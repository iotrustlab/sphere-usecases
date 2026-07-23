# WBS 1.4.2.c - Functional and Quality Tests: Enclave

## Scope

This document records the test plan and current results for the Water Distribution UC0 enclave implementation. The scope is the OpenPLC controller, OpenPLC simulator, Modbus bridge, validation harness, run-bundle output, and invariant report artifacts used by the CPS Enclave model.

Out of scope for this WBS item:

- Rockwell hardware validation.
- Operator HMI or engineering workstation validation.
- Security attack/defense experiments beyond invariant checks on collected tags.

## Test Objectives

- Verify the controller and simulator can run as a closed-loop enclave through the Modbus bridge.
- Verify the canonical Water Distribution tag contract is observable in collected `tags.csv` output.
- Verify scenario timelines drive HMI inputs and simulator state changes.
- Verify each run writes a portable evidence bundle with `meta.json`, `events.json`, `tags.csv`, and validation artifacts when available.
- Verify quality gates: deterministic inputs, stable polling cadence, valid tag ranges, command-to-status causality, and alarm behavior.

## Test Assets

| Asset | Path | Purpose |
| --- | --- | --- |
| Controller ST | `implementations/openplc/st/wd_controller.st` | Water Distribution PLC control logic |
| Simulator ST | `implementations/openplc/st/wd_simulator.st` | Physical process simulator |
| Modbus map | `implementations/openplc/configs/openplc_map.yaml` | Register and coil mapping reference |
| Bridge | `implementations/openplc/scripts/modbus_bridge.py` | Controller-to-simulator signal exchange |
| Harness | `implementations/openplc/scripts/validation_harness.py` | Scenario orchestration, polling, bundle writing |
| Scenarios | `implementations/openplc/scenarios/*.yaml` | Functional test cases |
| Profiles | `profiles/demo.yaml`, `profiles/realistic.yaml` | Simulation parameter sets |
| Tag contract | `tag_contract.yaml` | Canonical Water Distribution tag interface |
| Invariant rules | `../cps-enclave-model/tools/defense/rules/water-distribution.yaml` | Quality and behavioral checks |

## Environment

Expected local enclave topology:

- Controller OpenPLC instance listening on `localhost:502`.
- Simulator OpenPLC instance listening on `localhost:503`.
- Python 3 environment with `pymodbus` and `PyYAML` installed.
- `cps-enclave-model` checked out next to `sphere-usecases` so the invariant checker and rules are available at the default harness paths.

Install harness dependencies from the OpenPLC implementation directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements.txt
```

Note: this avoids Debian/Ubuntu `externally-managed-environment` errors from attempting to install Python packages into the system Python.

## Execution Procedure

From `sphere-usecases/water-distribution/implementations/openplc/`:

```bash
python scripts/validation_harness.py \
  --scenario scenarios/idle.yaml \
  --output ../../runs/validate-idle \
  --controller localhost:502 \
  --simulator localhost:503
```

Repeat for each scenario:

```bash
python scripts/validation_harness.py \
  --scenario scenarios/nominal_startup.yaml \
  --output ../../runs/validate-nominal-startup \
  --controller localhost:502 \
  --simulator localhost:503

python scripts/validation_harness.py \
  --scenario scenarios/high_demand.yaml \
  --output ../../runs/validate-high-demand \
  --controller localhost:502 \
  --simulator localhost:503

python scripts/validation_harness.py \
  --scenario scenarios/alarm_hh.yaml \
  --output ../../runs/validate-alarm-hh \
  --controller localhost:502 \
  --simulator localhost:503
```

If the bridge is already running externally, add `--no-bridge`.

For local Docker-based OpenPLC testing, the expected runtime setup is:

```bash
cd /home/kingy/projects/sphere/cps-enclave-model/docker/openplc
sudo bash ./build.sh master

sudo docker run -d \
  --name wd-openplc-controller \
  -p 502:502 \
  -p 8081:8080 \
  -e OPENPLC_PROGRAM=/programs/wd_controller.st \
  -v /home/kingy/projects/sphere/sphere-usecases/water-distribution/implementations/openplc/st/wd_controller.st:/programs/wd_controller.st:ro \
  sphere-openplc:master

sudo docker run -d \
  --name wd-openplc-simulator \
  -p 503:502 \
  -p 8082:8080 \
  -e OPENPLC_PROGRAM=/programs/wd_simulator.st \
  -v /home/kingy/projects/sphere/sphere-usecases/water-distribution/implementations/openplc/st/wd_simulator.st:/programs/wd_simulator.st:ro \
  sphere-openplc:master
```

## Planned Functional Tests

| ID | Scenario | Expected behavior | Evidence |
| --- | --- | --- | --- |
| F-01 | `idle.yaml` | System remains idle; HMI start/stop stay false; no spurious actuator commands or alarms. | `validate-idle/tags.csv`, `events.json`, invariant report |
| F-02 | `nominal_startup.yaml` | HMI start transitions system to running; pump and valve commands energize; HMI stop returns system to idle. | `validate-nominal-startup/tags.csv`, `events.json`, invariant report |
| F-03 | `high_demand.yaml` | Increased demand causes a measurable control response and remains within tank/flow limits. | `validate-high-demand/tags.csv`, `events.json`, invariant report |
| F-04 | `alarm_hh.yaml` | Supply tank high-high condition asserts `Alarm_Supply_Tank_HH`; shutdown clears or stabilizes outputs. | `validate-alarm-hh/tags.csv`, `events.json`, invariant report |
| F-05 | Bundle schema | Harness emits bundle files with schema version, tags, events, and optional model-validation artifacts. | `meta.json`, `tags.csv`, `events.json`, `artifacts/model-validate/` |

## Planned Quality Tests

| ID | Gate | Expected result | Evidence |
| --- | --- | --- | --- |
| Q-01 | Tag completeness | All 21 canonical Water Distribution tags are sampled or represented in `tags.csv`. | CSV header compared with `tag_contract.yaml` |
| Q-02 | Range checks | Tank levels, pump flows, and command values remain inside configured engineering ranges. | `report.json`, `report.md` |
| Q-03 | Causality | Commands precede matching status changes within the accepted delay window. | Invariant report |
| Q-04 | Polling cadence | Samples are collected at the scenario `poll_interval_ms` with no large unexplained gaps. | Timestamp deltas in `tags.csv` |
| Q-05 | Reproducibility | Re-running the same scenario/profile produces the same event sequence and comparable tag traces. | Bundle-to-bundle comparison |

## Current Results

| Item | Status | Result |
| --- | --- | --- |
| Harness inspection | Pass | `validation_harness.py` supports bridge startup, scenario loading, tag polling, bundle writing, and invariant-check invocation. |
| Bundle writer | Pass | Harness writes `meta.json`, `events.json`, `tags.csv`, and copies `report.json`/`report.md` into `artifacts/model-validate/` when the invariant checker runs. |
| Scenario inventory | Pass | Four scenarios exist: idle, nominal startup, high demand, and supply tank high-high alarm. |
| Python environment setup | Pass | Harness dependencies must be installed in `.venv`; system-level `pip install` is blocked by PEP 668 `externally-managed-environment`. |
| OpenPLC Docker image build | Pass | `sphere-openplc:master` was built locally after resolving Docker Hub TLS/certificate access to the Debian base image. |
| OpenPLC controller container | Blocked | Container starts but OpenPLC compilation of `st/wd_controller.st` fails: generated POU files exist, but `Config0.c`, `Config0.h`, and `Res0.c` are missing. |
| OpenPLC simulator container | Blocked | Container starts but OpenPLC compilation of `st/wd_simulator.st` fails with the same missing `Config0.c`, `Config0.h`, and `Res0.c` outputs. |
| Live OpenPLC execution | Blocked | No controller/simulator Modbus endpoints remained listening on `localhost:502` and `localhost:503` because both OpenPLC containers exited after compile errors. |
| `idle.yaml` readiness | Ready | Uses no timeline actions and is suitable for first closed-loop validation. |
| `nominal_startup.yaml` readiness | Ready | Uses supported `hmi_start` and `hmi_stop` actions. |
| `high_demand.yaml` readiness | Blocked | Uses `set_demand_mult:*`, which is not implemented by the current harness action dispatcher. |
| `alarm_hh.yaml` readiness | Blocked | Uses `set_sim_level:supply:1250`, but the current harness expects `set_sim_level:<register>:<value>` or `set_supply_tank_level:<value>`. |
| Invariant execution | Pending | Requires live or generated `tags.csv` plus the adjacent `cps-enclave-model` invariant checker/rules path. |
| Evidence bundle generation | Blocked | No live `validate-*` success bundle was generated because the bridge could not connect to live OpenPLC endpoints. Failure evidence is organized in `docs/evidence/wbs-1.4.2.c-enclave-blocked-openplc/`. |

## Attempt Log

Local validation was attempted with the repo-provided Docker OpenPLC runtime and Water Distribution ST files.

Observed sequence:

1. Harness runs before OpenPLC startup failed with `Connection refused` on both `localhost:502` and `localhost:503`.
2. Initial Docker runs failed because the user did not have direct access to `/var/run/docker.sock`; rerunning with `sudo docker` resolved Docker API access.
3. The OpenPLC image was not initially present locally; `sudo bash ./build.sh master` was required.
4. The first Docker image build attempt was blocked by a Docker Hub TLS/certificate validation issue while pulling `debian:trixie-20251020`; once Docker Hub access was corrected, the image built successfully.
5. Controller and simulator containers then started, copied the mounted ST files, and invoked OpenPLC compilation.
6. Both OpenPLC compilations failed during file movement because `Config0.c`, `Config0.h`, and `Res0.c` were not generated.

Interpretation:

- Docker and the OpenPLC image build path are usable.
- The Python harness path is usable when run from a virtual environment.
- The current Water Distribution ST files are POU-style `PROGRAM MainProgram` sources, but they do not currently compile as standalone OpenPLC runtime programs in the repo Docker image.
- The likely next implementation step is to add OpenPLC-ready wrapper programs, or regenerate valid OpenPLC project files, with the required top-level `CONFIGURATION` / `RESOURCE` / `TASK` structure and mapped variables.

## Evidence Bundle

Failure evidence for this blocked attempt is organized at:

`docs/evidence/wbs-1.4.2.c-enclave-blocked-openplc/`

Bundle contents:

- `README.md`
- `environment.txt`
- `attempted-commands.md`
- `openplc-compile-blocker.txt`
- `docker-access.txt`
- `blocker-summary.md`
- `github-status-comment.md`

No successful live run bundle exists yet because OpenPLC containers exited during compilation before the validation harness could collect `meta.json`, `events.json`, `tags.csv`, or invariant reports.

## Issues to Resolve

- Add harness support for `set_demand_mult:<float>` or revise `high_demand.yaml` to use currently supported simulator inputs.
- Revise `alarm_hh.yaml` action to `set_supply_tank_level:1250` or `set_sim_level:300:1250`.
- Add standalone OpenPLC-compatible controller and simulator wrapper files, or regenerate valid OpenPLC project artifacts, so the Docker runtime emits `Config0.c`, `Config0.h`, and `Res0.c` during compilation.
- Run `idle.yaml` and `nominal_startup.yaml` against live OpenPLC instances and attach the generated validation artifacts.
- Confirm the invariant rules file exists at the default path or pass `--invariant-rules` explicitly.

## Acceptance Criteria

WBS 1.4.2.c is complete when:

- `idle` and `nominal_startup` pass with zero critical invariant violations.
- `high_demand` and `alarm_hh` scenario actions are aligned with the harness and pass their expected functional checks.
- Each scenario has a retained run bundle with `meta.json`, `events.json`, `tags.csv`, and `artifacts/model-validate/report.json`.
- Any remaining invariant warnings are documented with rationale or remediation work items.


## Acceptance Status

| Acceptance criterion | Status | Notes |
| --- | --- | --- |
| Test plan documented | Complete | Scope, assets, procedures, functional tests, and quality gates are recorded in this document. |
| Test results recorded | Complete for attempted run | Results record harness inspection, Docker image build, Python environment setup, container compile failures, and blocked live execution. |
| Evidence bundle organized | Complete for blocked attempt | Failure evidence is organized in `docs/evidence/wbs-1.4.2.c-enclave-blocked-openplc/`; no successful live run bundle was produced. |
| WBS status updated in GitHub | Ready to update | Use `docs/evidence/wbs-1.4.2.c-enclave-blocked-openplc/github-status-comment.md` as the issue comment. |
