# CTF1 P2 Chemical Treatment Evidence Runbook

This is the starter runbook for:

```
Scenario: WT-P2-S01
Attack: Wrong Chemical Valve Opened
Backend: OpenPLC
Evidence bundle: sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc
```

Status: scenario YAML and harness action exist. Run the command below to create
or refresh the local evidence bundle.

## 1. Confirm OpenPLC Is Reachable

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

## 2. Execute The P2 Attack

Scenario behavior:

```
2s:  set baseline chemical levels near 800
5s:  press HMI start
10s: record intended action: NaOCl dosing expected
12s: attack starts: NaOCl command is expected, but HCl status opens instead
16s: HCl level drops to 790
20s: HCl level drops to 780
24s: attack stops: HCl valve status clears and chemical path returns to normal
35s: press HMI stop
```

Expected physical story:

```
NaOCl dosing is the intended action, but HCl valve status becomes active.
HCl tank level should trend downward during the attack window.
NaOCl level should not show the expected dosing behavior.
```

Implemented scenario file:

```
sphere-usecases/water-treatment/implementations/openplc/scenarios/ctf1_p2_wrong_chemical_valve.yaml
```

Run the attack and create the bundle:

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc

.venv/bin/python -m scripts.validation_harness \
  --scenario scenarios/ctf1_p2_wrong_chemical_valve.yaml \
  --output ../../runs/ctf1-p2-s01-openplc \
  --controller localhost:502 \
  --simulator localhost:503 \
  --no-bridge
```

## 3. Validate The Run Bundle

```bash
cd $HOME/sphere

./cps-enclave-model/bin/validate-bundle \
  sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc
```

Expected result:

```
PASS  sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc
```

## 4. Download And Inspect The Evidence Bundle

The evidence is the full run bundle, not just the Viewer replay. Download or
copy this directory as the participant/reviewer artifact:

```
sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc
```

If you are using VS Code over WSL/remote, right-click the bundle folder and use
`Download`. From a terminal, create a portable archive in the user's normal
Downloads folder:

```bash
Copy the entire terminal command below:

cd $HOME/sphere

BUNDLE="ctf1-p2-s01-openplc"
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

Expected attack timeline in `events.json`:

```
intended_action near 10s: NaOCl dosing expected
attack_start near 12s: HCl valve status opens instead
physical_effect near 16s: HCl level drops to 790
physical_effect near 20s: HCl level drops to 780
attack_stop near 24s: HCl valve status clears / normal path restored
```

Useful CSV fields:

```
timestamp_utc
ChemTreat_NaOCl_Valve
ChemTreat_NaOCl_Valve_Sts
ChemTreat_NaOCl_Level
ChemTreat_HCl_Valve
ChemTreat_HCl_Valve_Sts
ChemTreat_HCl_Level
ChemTreat_NaCl_Level
SYS_RUNNING
```

Open `tags.csv` from the downloaded/extracted bundle in a spreadsheet viewer
or text editor. Look for:

```
before attack: ChemTreat_NaOCl_Level = 800 and ChemTreat_HCl_Level = 800

attack_start near 12s: ChemTreat_NaOCl_Valve = 1
attack_start near 12s: ChemTreat_NaOCl_Valve_Sts = 0
attack_start near 12s: ChemTreat_HCl_Valve = 0
attack_start near 12s: ChemTreat_HCl_Valve_Sts = 1

physical effect near 16s: ChemTreat_HCl_Level drops to 790

physical effect near 20s: ChemTreat_HCl_Level drops to 780

recovery near 24s: ChemTreat_HCl_Valve_Sts returns to 0
comparison evidence: ChemTreat_NaOCl_Level stays flat while HCl level drops
```

Expected detector or reviewer evidence:

```
HCl status active during the attack window
HCl level decreases when HCl valve is active
NaOCl command/status causality violation
HCl status-without-command correlation violation
NaOCl behavior does not match the intended dosing action
```

Screenshots to capture for the evidence packet:

```
1. Viewer before attack: NaOCl/HCl levels both near 800 and valve statuses OFF.
2. Viewer during attack: ChemTreat_NaOCl_Valve = ON but ChemTreat_NaOCl_Valve_Sts = OFF.
3. Viewer during attack: ChemTreat_HCl_Valve = OFF but ChemTreat_HCl_Valve_Sts = ON.
4. Viewer physical effect: ChemTreat_HCl_Level drops 800 -> 790 -> 780 while NaOCl level stays flat.
5. Viewer after recovery: HCl valve status returns OFF and HCl level remains at 780.
6. Detector summary: naocl-valve-cmd-implies-status and hcl-status-requires-command findings visible.
7. Optional file evidence: events.json showing intended_action, attack_start, physical_effect, and attack_stop.
```

## 5. Open The Bundle In The CPS Enclave Viewer

Use the P2-only slice when focusing on chemical treatment:

```bash
cd $HOME/sphere/cps-enclave-model

./bin/viewer \
  -data ../sphere-usecases/water-treatment/runs \
  -webdir cps-enclave-viewer \
  -assets-dir ../sphere-usecases/water-treatment/assets \
  -slice ../sphere-usecases/water-treatment/slices/wt-uc1-p2-only-slice.yaml \
  -addr :8090
```

Open:

```
http://localhost:8090
```

In the Viewer:

1. Select run `ctf1-p2-s01-openplc`.
2. Scrub to about `10-12s`.
3. Confirm the intended action is NaOCl dosing.
4. Confirm `ChemTreat_NaOCl_Valve` is the intended command evidence.
5. Confirm `ChemTreat_HCl_Valve_Sts` becomes active instead.
6. Compare `ChemTreat_HCl_Level` against `ChemTreat_NaOCl_Level`.
7. Scrub to about `24s` and confirm recovery/return to normal.

For the generated reference bundle, the attack is visible around samples
`24-47`, or roughly timestamps `18:06:22` through `18:06:34` in the current
local run. After sample `48`, the valve statuses return to `OFF`; by the final
sample the HCl level remains at `780`, but the valves are already recovered.


Expected P2 attack bundle values:

```
Before attack: ChemTreat_NaOCl_Level = 800, ChemTreat_HCl_Level = 800
During attack: ChemTreat_NaOCl_Valve = 1, ChemTreat_NaOCl_Valve_Sts = 0
During attack: ChemTreat_HCl_Valve = 0, ChemTreat_HCl_Valve_Sts = 1
Physical effect: ChemTreat_HCl_Level drops 800 -> 790 -> 780
Recovery: ChemTreat_HCl_Valve_Sts returns to 0
```

## 6. Final Evidence Statement

Use this wording after the P2 bundle is captured:

```
WT-P2-S01 demonstrates wrong-chemical valve actuation against the OpenPLC UC1
chemical-treatment process. The captured run bundle shows an intended NaOCl
dosing window where HCl valve status activates instead, and the HCl tank level
provides physical-process evidence of the wrong chemical path. The Viewer replay
and detector output support the claim.
```
