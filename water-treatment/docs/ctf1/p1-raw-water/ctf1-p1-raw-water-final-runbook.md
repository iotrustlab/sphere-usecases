# CTF1 P1 Raw-Water Evidence Final Runbook

This is the final short runbook for executing and reviewing:

```
Scenario WT-P1-S01: Raw-Water Level Spoofing
Backend: OpenPLC
Evidence bundle: sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
```

The attack is executed by the OpenPLC validation harness. The CPS Enclave
Viewer is used afterward to replay the saved evidence.

## 1. Confirm OpenPLC Is Reachable

Run this from the OpenPLC implementation directory:

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

Expected result:

```
controller True
simulator True
```

If either line is `False`, start or restart the OpenPLC Docker containers before
continuing.

## 2. Execute The Attack And Capture The Bundle

This command runs the full `WT-P1-S01` scenario and writes the run bundle.

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc

.venv/bin/python -m scripts.validation_harness \
  --scenario scenarios/ctf1_p1_rw_level_spoof.yaml \
  --output ../../runs/ctf1-p1-s01-openplc \
  --controller localhost:502 \
  --simulator localhost:503 \
  --no-bridge
```

Expected scenario timeline:

```
2s:  set baseline RW_Tank_Level = 600
5s:  press HMI start
12s: spoof RW_Tank_Level = 1300
24s: restore RW_Tank_Level = 600
35s: press HMI stop
```

Expected output bundle:

```
sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc/
  meta.json
  events.json
  tags.csv
  artifacts/invariant-check/report.json
  artifacts/invariant-check/summary.txt
  artifacts/scenario/scenario.json
```

## 3. Validate The Run Bundle

```bash
cd $HOME/sphere

./cps-enclave-model/bin/validate-bundle \
  sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
```

Expected result:

```
PASS  sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
```

## 4. Download And Inspect The Evidence Bundle

The evidence is the full run bundle, not just one screenshot. Download or copy
this directory as the participant/reviewer artifact:

```
sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
```

If you are using VS Code over WSL/remote, right-click the bundle folder and use
`Download`. From a terminal, create a portable archive in the user's normal
Downloads folder:

```bash
cd $HOME/sphere

BUNDLE="ctf1-p1-s01-openplc"
RUNS_DIR="sphere-usecases/water-treatment/runs"

if command -v powershell.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
  EXPORT_DIR="$(wslpath "$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("UserProfile") + "\Downloads"' | tr -d '\r')")"
elif command -v xdg-user-dir >/dev/null 2>&1; then
  EXPORT_DIR="$(xdg-user-dir DOWNLOAD)"
else
  EXPORT_DIR="$HOME/Downloads"
fi

mkdir -p "$EXPORT_DIR"

tar -czf "$EXPORT_DIR/${BUNDLE}.tar.gz" \
  -C "$RUNS_DIR" \
  "$BUNDLE"

echo "Exported $EXPORT_DIR/${BUNDLE}.tar.gz"
```

After downloading or extracting the bundle, inspect these files:

```
meta.json
events.json
tags.csv
artifacts/invariant-check/report.json
artifacts/invariant-check/summary.txt
artifacts/scenario/scenario.json
```

In `events.json`, look for:

```
attack_start near 12s: RW_Tank_Level -> 1300
attack_stop near 24s: RW_Tank_Level -> 600
```

In `tags.csv`, focus on these fields:

```
timestamp_utc
RW_Tank_Level
RW_Pump_Flow
RW_Pump_Sts
SYS_RUNNING
Alarm_RW_Tank_HH
```

Open `tags.csv` from the downloaded/extracted bundle in a spreadsheet viewer
or text editor. Look for:

```
before attack: RW_Tank_Level near 600

attack_start near 12s: RW_Tank_Level jumps to 

during attack: RW_Tank_Level remains above the 1200 max
attack_stop near 24s: RW_Tank_Level returns to 600

alarm evidence: Alarm_RW_Tank_HH is useful if visible in the captured run

context evidence: RW_Pump_Flow, RW_Pump_Sts, and 
SYS_RUNNING help explain process state
```

In `artifacts/invariant-check/summary.txt`, look for:

```
range violations for RW_Tank_Level=1300
rate_of_change violations when the spoof starts and stops
```

Screenshots to capture for the evidence packet:

```
1. Viewer before attack: RW_Tank_Level near 600.
2. Viewer during attack: RW_Tank_Level at 1300 and Alarm_RW_Tank_HH visible.
3. Viewer after recovery: RW_Tank_Level back near 600.
4. Detector summary: range and rate_of_change findings visible.
5. Optional file evidence: events.json showing attack_start and attack_stop.
```

## 5. Open The Bundle In The CPS Enclave Viewer

Use port `8090` so it does not conflict with the OpenPLC controller WebUI on
port `8080`.

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

In the Viewer:

1. Select run `ctf1-p1-s01-openplc`.
2. Scrub to about `12s`.
3. Confirm `RW_Tank_Level` jumps to `1300`.
4. Compare that jump against `RW_Pump_Flow`, `RW_Pump_Sts`, valve status, and
   `Alarm_RW_Tank_HH`.
5. Scrub to about `24s` and confirm `RW_Tank_Level` returns to `600`.

## 6. Final Evidence Statement

Use this wording as the short evidence claim:

```
WT-P1-S01 demonstrates raw-water level spoofing against the OpenPLC UC1
simulation. The captured run bundle shows RW_Tank_Level jumping from baseline
to 1300, exceeding the 1200 maximum and changing faster than the process model
allows. The Viewer replay and invariant-check output provide the physical-
process evidence.
```
