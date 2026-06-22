# CTF1 P3 Ultrafiltration Evidence Runbook

This is the starter runbook for:

```
Scenario: WT-P3-S01
Attack: UF Drain Valve Forced Open During Filtration
Backend: OpenPLC
Evidence bundle: sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc
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

## 2. Execute The P3 Attack

Scenario behavior:

```
2s:  set baseline UF_UFFT_Tank_Level near 900
5s:  press HMI start
10s: record intended action: normal forward filtration expected
12s: attack starts: UF drain valve status opens unexpectedly
16s: UF tank level drops to 860
20s: UF tank level drops to 820
24s: attack stops: UF drain valve status clears
35s: press HMI stop
```

Expected physical story:

```
The run records a normal forward-filtration expectation, but the drain path
becomes active during that evidence window. UF_UFFT_Tank_Level should decrease
while UF_Drain_Valve_Sts is active.
This demonstrates filtration loss / contamination risk, not proven chemical
poisoning, because UC1 does not model water-quality variables.
```

Implemented scenario file:

```
sphere-usecases/water-treatment/implementations/openplc/scenarios/ctf1_p3_uf_drain_forced_open.yaml
```

Run the attack and create the bundle:

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc

.venv/bin/python -m scripts.validation_harness \
  --scenario scenarios/ctf1_p3_uf_drain_forced_open.yaml \
  --output ../../runs/ctf1-p3-s01-openplc \
  --controller localhost:502 \
  --simulator localhost:503 \
  --no-bridge
```

## 3. Validate The Run Bundle

```bash
cd $HOME/sphere

./cps-enclave-model/bin/validate-bundle \
  sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc
```

Expected result:

```
PASS  sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc
```

## 4. Download And Inspect The Evidence Bundle

The evidence should be the full run bundle, not just the Viewer replay. Download
or copy this directory as the participant/reviewer artifact:

```
sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc
```

From a terminal, create a portable archive in the user's normal Downloads
folder:

```bash
cd $HOME/sphere

BUNDLE="ctf1-p3-s01-openplc"
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
intended_action near 10s: normal forward filtration expected
attack_start near 12s: UF drain valve status opens unexpectedly
physical_effect near 16s: UF_UFFT_Tank_Level drops to 860
physical_effect near 20s: UF_UFFT_Tank_Level drops to 820
attack_stop near 24s: UF drain valve status clears
```

Useful CSV fields:

```
timestamp_utc
UF_UFFT_Tank_Level
UF_Drain_Valve
UF_Drain_Valve_Sts
UF_ROFT_Valve
UF_ROFT_Valve_Sts
UF_BWP_Valve
UF_BWP_Valve_Sts
```

Expected detector or reviewer evidence:

```
events.json records intended normal filtration context near 10s
UF drain status active during the attack window
UF tank level decreases while drain status is active
UF drain status-without-command correlation violation
RO feed / backwash tags do not explain the drain event
```

Screenshots to capture for the evidence packet:

```
1. Viewer before attack: UF_UFFT_Tank_Level stable and UF_Drain_Valve_Sts OFF.
2. Viewer during attack: UF_Drain_Valve_Sts ON.
3. Viewer physical effect: UF_UFFT_Tank_Level decreasing during the attack window.
4. Viewer comparison: UF_ROFT_Valve_Sts and UF_BWP_Valve_Sts visible for context.
5. Viewer after recovery: UF_Drain_Valve_Sts returns OFF.
6. Detector summary: drain/status/tank-level findings visible.
7. Optional file evidence: events.json showing intended_action, attack_start,
   physical_effect, and attack_stop.
```

Expected P3 attack bundle values:

```
Before attack: UF_UFFT_Tank_Level = 900, UF_Drain_Valve_Sts = 0
During attack: UF_Drain_Valve = 0, UF_Drain_Valve_Sts = 1
Physical effect: UF_UFFT_Tank_Level drops 900 -> 860 -> 820
Detector evidence: uf-drain-status-requires-command violations near samples 24-47
Recovery: UF_Drain_Valve_Sts returns to 0
```

## 5. Open The Bundle In The CPS Enclave Viewer

Use the P3-only slice when focusing on ultrafiltration:

```bash
cd $HOME/sphere/cps-enclave-model

./bin/viewer \
  -data ../sphere-usecases/water-treatment/runs \
  -webdir cps-enclave-viewer \
  -assets-dir ../sphere-usecases/water-treatment/assets \
  -slice ../sphere-usecases/water-treatment/slices/wt-uc1-p3-only-slice.yaml \
  -addr :8090
```

Open:

```
http://localhost:8090
```

In the Viewer:

1. Select run `ctf1-p3-s01-openplc`.
2. Scrub to about `10-12s`.
3. Confirm `events.json` shows the intended normal filtration note near `10s`.
4. Confirm `UF_Drain_Valve_Sts` becomes active while `UF_Drain_Valve` remains off.
5. Compare `UF_UFFT_Tank_Level` before and during the drain event.
6. Confirm `UF_ROFT_Valve_Sts` and `UF_BWP_Valve_Sts` do not explain the drain.
7. Scrub to about `24s` and confirm recovery/return to normal.

For the generated reference bundle, the attack should be visible around samples
`24-47`, or about `12-24s` into the run. After sample `48`, the drain status
returns to `OFF`; by the final sample the UF level remains at `820`, but the
valves are already recovered.

## 6. Final Evidence Statement

Use this wording after the P3 bundle is captured:

```
WT-P3-S01 demonstrates UF drain sabotage against the OpenPLC UC1
ultrafiltration process. The captured run bundle shows a normal filtration
context where the UF drain valve status activates unexpectedly and the UF feed
tank level decreases. The Viewer replay and detector output support the
physical-process claim.
```
