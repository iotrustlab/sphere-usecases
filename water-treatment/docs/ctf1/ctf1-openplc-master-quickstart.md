# CTF1 OpenPLC Master Quickstart

Use this guide to start the local OpenPLC Docker containers for the CTF1 Water
Treatment scenarios, then generate evidence bundles for P1, P2, and P3.

Canonical OpenPLC deployment details live in:

```
sphere-usecases/water-treatment/implementations/openplc/README.md
```

This file is the CTF1-friendly version: same startup idea, but focused on the
evidence scenarios.

## 1. Confirm Docker Works

Run:

```bash
docker version
docker ps
```

If WSL says Docker cannot be found, open Docker Desktop, enable WSL integration
for this distro, then close and reopen the terminal.

## 2. Start The OpenPLC Containers

Run this from the OpenPLC Ansible directory:

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc/ansible

CPS_ENCLAVE_MODEL_PATH=$HOME/sphere/cps-enclave-model \
../.venv/bin/ansible-playbook -i inventory/local.yml playbooks/deploy-local.yml
```

Expected containers:

```
openplc-controller   Modbus localhost:502   WebUI http://localhost:8080
openplc-simulator    Modbus localhost:503   WebUI http://localhost:8081
```

Check them:

```bash
docker ps
```

## 3. Confirm Modbus Reachability

Run:

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc

.venv/bin/python - <<'PY'
from pymodbus.client import ModbusTcpClient

for name, port in [("controller", 502), ("simulator", 503)]:
    client = ModbusTcpClient("localhost", port=port, timeout=3)
    print(name, client.connect())
    client.close()
PY
```

Expected:

```
controller True
simulator True
```

If either line is `False`, redeploy with Step 2, then retry this check.

## 4. Run A CTF1 Scenario

All scenario commands are run from:

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc
```

### P1: Raw-Water Level Spoofing

```bash
.venv/bin/python -m scripts.validation_harness \
  --scenario scenarios/ctf1_p1_rw_level_spoof.yaml \
  --output ../../runs/ctf1-p1-s01-openplc \
  --controller localhost:502 \
  --simulator localhost:503 \
  --no-bridge
```

Bundle:

```
sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
```

### P2: Wrong Chemical Valve Opened

```bash
.venv/bin/python -m scripts.validation_harness \
  --scenario scenarios/ctf1_p2_wrong_chemical_valve.yaml \
  --output ../../runs/ctf1-p2-s01-openplc \
  --controller localhost:502 \
  --simulator localhost:503 \
  --no-bridge
```

Bundle:

```
sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc
```

### P3: UF Drain Valve Forced Open

```bash
.venv/bin/python -m scripts.validation_harness \
  --scenario scenarios/ctf1_p3_uf_drain_forced_open.yaml \
  --output ../../runs/ctf1-p3-s01-openplc \
  --controller localhost:502 \
  --simulator localhost:503 \
  --no-bridge
```

Bundle:

```
sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc
```

## 5. Validate A Bundle

Run from the workspace root:

```bash
cd $HOME/sphere

./cps-enclave-model/bin/validate-bundle \
  sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
```

Swap the bundle path for P2 or P3:

```
sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc
sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc
```

Expected:

```
PASS  sphere-usecases/water-treatment/runs/<bundle-name>
```

## 6. Open A Bundle In The CPS Enclave Viewer

Run from `cps-enclave-model`:

```bash
cd $HOME/sphere/cps-enclave-model

./bin/viewer \
  -data ../sphere-usecases/water-treatment/runs \
  -webdir cps-enclave-viewer \
  -assets-dir ../sphere-usecases/water-treatment/assets \
  -slice ../sphere-usecases/water-treatment/slices/wt-uc1-slice.yaml \
  -addr :8090
```

Open:

```
http://localhost:8090
```

Use these focused slices when reviewing one process:

```
P1: ../sphere-usecases/water-treatment/slices/wt-uc1-p1-only-slice.yaml
P2: ../sphere-usecases/water-treatment/slices/wt-uc1-p2-only-slice.yaml
P3: ../sphere-usecases/water-treatment/slices/wt-uc1-p3-only-slice.yaml
```

## 7. Stop The Containers

When finished:

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc/ansible

../.venv/bin/ansible-playbook -i inventory/local.yml playbooks/teardown-local.yml
```

## Scenario Runbooks

Use the process-specific runbooks for the evidence details:

```
docs/ctf1/p1-raw-water/ctf1-p1-raw-water-final-runbook.md
docs/ctf1/p2-chemical-treatment/ctf1-p2-chemical-treatment-final-runbook.md
docs/ctf1/p3-ultrafiltration/ctf1-p3-ultrafiltration-final-runbook.md
```
