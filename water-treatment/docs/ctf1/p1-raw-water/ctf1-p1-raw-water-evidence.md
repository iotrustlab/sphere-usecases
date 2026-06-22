# How would I spin 6 nodes for the PLC's, we have the simulator for P1 and control for P2, create placeholder control logic

# If you have 


# CTF1 P1 Raw Water Evidence Checklist

This draft defines the first evidence target for CTF1 using Water Treatment
UC1 Process 1 (P1): Raw Water Intake.

The goal is not just to show that a cyber action occurred. The goal is to show
that the action produced, blocked, or revealed a physically meaningful process
effect.

## P1 Process Story

P1 moves raw water into and through the treatment process.

Normal cause-and-effect chain:

1. The system enters RUNNING state.
2. Controller commands raw-water valves and pump.
3. Simulator returns actuator status feedback.
4. Pump status and pump speed produce pump flow.
5. Flow changes raw-water and UF tank levels.
6. Unsafe levels trigger alarms or interlocks.

## Core Tags

Minimum P1 evidence tags:

| Tag | Role | Why it matters |
| --- | --- | --- |
| `SYS_IDLE` | State | Confirms system is not running. |
| `SYS_RUNNING` | State | Confirms control logic is active. |
| `RW_Tank_Level` | Sensor | Main physical variable for raw-water tank. |
| `UF_UFFT_Tank_Level` | Sensor | Downstream tank that drives pump demand. |
| `RW_Tank_PR_Valve` | Command | Controller request to open/close inlet valve. |
| `RW_Tank_PR_Valve_Sts` | Feedback | Physical/simulated inlet valve position. |
| `RW_Tank_P_Valve` | Command | Controller request to open/close outlet/process valve. |
| `RW_Tank_P_Valve_Sts` | Feedback | Physical/simulated process valve position. |
| `RW_Pump_Start` | Command | Controller request to start pump. |
| `RW_Pump_Stop` | Command | Controller request to stop pump. |
| `RW_Pump_Sts` | Feedback | Physical/simulated pump running status. |
| `RW_Pump_Speed` | Command | Pump speed setpoint. |
| `RW_Pump_Flow` | Sensor | Physical consequence of pump operation. |
| `RW_Pump_Fault` | Alarm/status | Indicates pump fault condition. |
| `Alarm_RW_Tank_HH` | Alarm | Indicates raw-water high-high condition. |

Optional supporting evidence:

| Evidence | Purpose |
| --- | --- |
| Modbus/CIP PCAP | Shows network-level command or spoofing activity. |
| Viewer screenshot | Shows what the operator saw. |
| Invariant report | Shows automated physical consistency checks. |
| Tool output under `artifacts/<tool>/` | Preserves attack or defense output. |

## CTF1 P1 Scenario Inventory

This table is the high-level mapping from CTF1 scenario to physical effect and
observable evidence. Scenario `WT-P1-S01` is expanded into a concrete checklist
below.

| Scenario ID | Attack/defense scenario | Observable physical/process effect | Primary tags/signals | Evidence artifacts |
| --- | --- | --- | --- | --- |
| `WT-P1-S01` | Spoof `RW_Tank_Level` | Reported tank level becomes impossible, misleading, or inconsistent with process behavior. | `RW_Tank_Level`, `RW_Pump_Sts`, `RW_Pump_Flow`, `RW_Tank_PR_Valve_Sts`, `Alarm_RW_Tank_HH` | `tags.csv`, `events.json`, `artifacts/tag-perturb/`, `artifacts/invariant-check/` |
| `WT-P1-S02` | Pump start/stop override | Pump command, status, speed, and flow disagree or cause unexpected tank movement. | `RW_Pump_Start`, `RW_Pump_Stop`, `RW_Pump_Sts`, `RW_Pump_Speed`, `RW_Pump_Flow` | `tags.csv`, detector report, optional PCAP |
| `WT-P1-S03` | Process valve override/status spoof | Valve command/status disagrees with flow or UF tank filling behavior. | `RW_Tank_P_Valve`, `RW_Tank_P_Valve_Sts`, `RW_Pump_Flow`, `UF_UFFT_Tank_Level` | `tags.csv`, detector report, optional PCAP |
| `WT-P1-S04` | High-high alarm suppression/spoof | Raw-water level crosses threshold but alarm evidence is missing, delayed, or inconsistent across views. | `RW_Tank_Level`, `Alarm_RW_Tank_HH`, `SYS_RUNNING` | `tags.csv`, `events.json`, screenshot, optional PCAP |
| `WT-P1-D01` | Defense/detection with invariants | Detector identifies range, rate, causality, correlation, or mass-balance violation. | Same tags as attacked scenario | `artifacts/invariant-check/report.json`, `summary.txt` |

## Attack Scenario Map

### Scenario WT-P1-S01: Raw-Water Level Spoofing

Attack idea: falsify `RW_Tank_Level`, the raw-water tank level sensor value
used by the controller/operator evidence path.

This scenario is the recommended first CTF1 P1 scenario because it is easy to
explain, easy to observe in `tags.csv`, and directly exercises the evidence
pipeline:

```
spoofed sensor value
  -> impossible or misleading tank level
  -> wrong/hidden alarm or physically inconsistent process behavior
  -> detector/evidence artifact
```

#### Attacker Objective

Show that a participant can alter the reported raw-water tank level during a
defined attack window.

Possible attacker claims:

- "I made the raw-water tank appear higher than it really was."
- "I made the raw-water tank level jump faster than the physical model allows."
- "I made the operator/evidence path see a high-high condition."
- "I hid or delayed the expected high-high alarm for the observed level."

#### Defender Objective

Show that a defender can detect or explain the spoof using physical-process
evidence.

Possible defender claims:

- "`RW_Tank_Level` exceeded the physical range."
- "`RW_Tank_Level` changed faster than the process model allows."
- "`RW_Tank_Level` no longer matched pump/flow/tank behavior."
- "The attack window in `events.json` aligns with detector output."

Expected process effects:

- The reported level may exceed the valid range `[0, 1200]`.
- The reported level may jump by more than the configured rate limit
  (`50 mm/sample` in `water-treatment.yaml`).
- The reported level may move in a direction that does not match pump/flow
  behavior.
- If the level crosses the high-high threshold, `Alarm_RW_Tank_HH` should be
  present unless the claim is alarm suppression or HMI/operator-view spoofing.

#### Effect-to-Tag Mapping

| Physical/process question | Tags/signals to inspect | What to look for |
| --- | --- | --- |
| Did the level value change during the attack? | `RW_Tank_Level` | Step change, offset, impossible value, or abnormal trend during attack window. |
| Was the system actually running? | `SYS_RUNNING`, `SYS_IDLE` | Interpret process effects only when the relevant state is active. |
| Did the tank exceed the HH threshold? | `RW_Tank_Level`, `Alarm_RW_Tank_HH` | `RW_Tank_Level > 1200` should correspond to HH alarm evidence unless alarm spoofing is part of the claim. |
| Did inlet control react? | `RW_Tank_PR_Valve`, `RW_Tank_PR_Valve_Sts` | Low level should lead toward inlet opening; high level should lead toward closing. |
| Did outlet/pump behavior explain level motion? | `RW_Tank_P_Valve_Sts`, `RW_Pump_Sts`, `RW_Pump_Speed`, `RW_Pump_Flow` | If pump is running and flow is nonzero, level changes should be physically plausible. |
| Did downstream tank behavior agree? | `UF_UFFT_Tank_Level`, `RW_Pump_Flow`, `RW_Tank_P_Valve_Sts` | If water is being pumped downstream, UF tank should trend consistently. |
| Did the detector flag it? | `artifacts/invariant-check/report.json`, `summary.txt` | Range, rate-of-change, or mass-balance violation at/near attack samples. |

Success evidence:

- `events.json` marks attack start and stop time.
- `tags.csv` shows the spoofed level behavior.
- Invariant report shows either expected violation or documented bypass.
- If HMI spoofing is involved, screenshot disagrees with run-bundle data.

#### Evidence Capture Requirements

Required artifacts:

| Artifact | Required contents |
| --- | --- |
| `meta.json` | `usecase_id`, run id/path, backend, start/end timestamps, poll interval. |
| `events.json` | Attack start time, attack stop time, recovery/detection event if present. |
| `tags.csv` | All core P1 tags, especially `RW_Tank_Level`, pump/valve status, `SYS_RUNNING`, and `Alarm_RW_Tank_HH`. |
| `artifacts/tag-perturb/manifest.json` | Required if using the replay-level perturbation tool. |
| `artifacts/tag-perturb/perturbed_tags.csv` | Required if using the replay-level perturbation tool. |
| `artifacts/invariant-check/report.json` | Detector output with sample-level violations. |
| `artifacts/invariant-check/summary.txt` | Human-readable detector summary. |

Optional artifacts:

| Artifact | When required |
| --- | --- |
| PCAP | Required for claims about network-level Modbus/CIP spoofing. |
| Screenshot | Required for claims about HMI/operator-view spoofing. |
| Tool logs | Required when an automated attack/defense tool is part of the claim. |

#### Live OpenPLC Test Procedure

This procedure runs `WT-P1-S01` against the local UC1 OpenPLC deployment and
creates a reusable evidence bundle under `runs/`.

The live OpenPLC evidence path uses the UC1 bridge registers:

| Canonical tag | OpenPLC evidence path |
| --- | --- |
| `RW_Tank_Level` | bridge holding register `300` |
| `RW_Pump_Flow` | bridge holding register `301` |
| valve/pump feedback | bridge holding registers `320-331` |
| controller commands | controller coils `40-51` |
| system state | controller coils `56-60` |
| raw-water alarms | controller coils `64-67` |

Run from the OpenPLC implementation directory.

Use module mode (`-m scripts.validation_harness`) so Python does not confuse
`scripts/operator.py` with the standard-library `operator` module. Use
`--no-bridge` for this capture path because the harness writes the spoofed
level to both PLCs and avoids concurrent bridge traffic.

```bash
cd $HOME/sphere/sphere-usecases/water-treatment/implementations/openplc

.venv/bin/python -m scripts.validation_harness \
  --scenario scenarios/ctf1_p1_rw_level_spoof.yaml \
  --output ../../runs/ctf1-p1-s01-openplc \
  --controller localhost:502 \
  --simulator localhost:503 \
  --no-bridge
```

Expected output bundle:

```
sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc/
  meta.json
  events.json
  tags.csv
  artifacts/
    invariant-check/
      report.json
      summary.txt
    scenario/
      scenario.json
```

Expected evidence:

- `events.json` contains `attack_start` around `t=12s` and `attack_stop`
  around `t=24s`.
- `tags.csv` shows `RW_Tank_Level` forced to `1300` during the attack window.
- `artifacts/invariant-check/summary.txt` should report:
  - `range` violation for `RW_Tank_Level > 1200`
  - `rate_of_change` violation when the spoof starts
  - `rate_of_change` violation when the spoof stops

Quick inspection commands:

```bash
cd $HOME/sphere

cat sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc/events.json

python3 - <<'PY'
import csv
path = "sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc/tags.csv"
fields = ["timestamp_utc", "RW_Tank_Level", "RW_Pump_Flow", "SYS_RUNNING", "Alarm_RW_Tank_HH"]
with open(path, newline="") as f:
    reader = csv.DictReader(f)
    print(",".join(fields))
    for i, row in enumerate(reader):
        if i % 4 == 0:
            print(",".join(row.get(field, "") for field in fields))
PY

cat sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc/artifacts/invariant-check/summary.txt
```

What to observe:

- Before the attack, `RW_Tank_Level` should be near the baseline value.
- During the attack, `RW_Tank_Level` should jump to `1300`, which is above the
  documented physical maximum and HH threshold.
- After the attack, `RW_Tank_Level` should return to baseline.
- The detector should identify the spoof using physical-process evidence, not
  merely by saying that a command was run.

#### CPS Enclave Viewer Replay Procedure

This procedure shows the captured `WT-P1-S01` run bundle in the CPS Enclave
Viewer. The Viewer does not run the attack; it replays the saved evidence from
`meta.json`, `events.json`, and `tags.csv`.

Validate the captured bundle:

```bash
cd $HOME/sphere

./cps-enclave-model/bin/validate-bundle \
  sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
```

Start the Viewer on port `8090` so it does not conflict with the OpenPLC
controller WebUI on port `8080`:

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

- Select run `ctf1-p1-s01-openplc`.
- Scrub or play through the timeline.
- Watch `RW_Tank_Level` in the P1 overlay and trend chart.
- Around the attack window, confirm the level jumps to `1300`.
- Compare that jump against `RW_Pump_Flow`, `RW_Pump_Sts`, valve status, and
  `Alarm_RW_Tank_HH`.

Viewer interpretation:

- If `RW_Tank_Level` jumps while pump/flow/valve behavior does not explain it,
  the run shows telemetry/process inconsistency.
- If `Alarm_RW_Tank_HH` does not activate even though `RW_Tank_Level > 1200`,
  record that as an alarm-path observation instead of assuming the alarm failed.
- A useful screenshot should include the selected run name, timestamp near the
  attack window, `RW_Tank_Level`, and at least one supporting tag such as
  `RW_Pump_Flow` or `Alarm_RW_Tank_HH`.

#### Replay-Level Test Procedure

This procedure creates a temporary attacked bundle from an existing golden run.
It does not modify the original run.

Use startup data when you want to show a spoof during active process behavior:

```bash
cd $HOME/sphere

cp -r sphere-usecases/water-treatment/runs/run-b-startup /tmp/wt-level-spoof-demo

python3 cps-enclave-model/tools/attack/tag_perturb.py \
  --bundle /tmp/wt-level-spoof-demo \
  --tag RW_Tank_Level \
  --offset 400 \
  --start-sample 20 \
  --end-sample 40

cp /tmp/wt-level-spoof-demo/artifacts/tag-perturb/perturbed_tags.csv \
  /tmp/wt-level-spoof-demo/tags.csv

python3 cps-enclave-model/tools/defense/invariant_check.py \
  --bundle /tmp/wt-level-spoof-demo \
  --rules cps-enclave-model/tools/defense/rules/water-treatment.yaml \
  --output-dir /tmp/wt-level-spoof-demo/artifacts/invariant-check

cat /tmp/wt-level-spoof-demo/artifacts/invariant-check/summary.txt
```

Expected detector evidence for this example:

- `rate_of_change` violation when the spoof starts.
- `rate_of_change` violation when the spoof ends.
- possible `mass_balance` violation because the reported tank movement no
  longer matches the expected direction.

Use idle data when you want a very obvious out-of-range spoof:

```bash
cd $HOME/sphere

cp -r sphere-usecases/water-treatment/runs/run-a-idle /tmp/wt-idle-spoof-demo

python3 cps-enclave-model/tools/attack/tag_perturb.py \
  --bundle /tmp/wt-idle-spoof-demo \
  --tag RW_Tank_Level \
  --offset 700 \
  --start-sample 20 \
  --end-sample 40

cp /tmp/wt-idle-spoof-demo/artifacts/tag-perturb/perturbed_tags.csv \
  /tmp/wt-idle-spoof-demo/tags.csv

python3 cps-enclave-model/tools/defense/invariant_check.py \
  --bundle /tmp/wt-idle-spoof-demo \
  --rules cps-enclave-model/tools/defense/rules/water-treatment.yaml \
  --output-dir /tmp/wt-idle-spoof-demo/artifacts/invariant-check

cat /tmp/wt-idle-spoof-demo/artifacts/invariant-check/summary.txt
```

Expected detector evidence for this example:

- `range` violations for `RW_Tank_Level > 1200`.
- `rate_of_change` violation when the spoof starts.
- `rate_of_change` violation when the spoof ends.

#### Participant Checklist

Before submission:

- [ ] Identify the attack window in `events.json`.
- [ ] Include `tags.csv` from the attacked or defended run.
- [ ] Confirm `RW_Tank_Level` changes during the attack window.
- [ ] Compare `RW_Tank_Level` against `RW_Pump_Sts`, `RW_Pump_Flow`, valve
  status, and `UF_UFFT_Tank_Level`.
- [ ] Run invariant checking and include `report.json` plus `summary.txt`.
- [ ] Include PCAP if claiming network-level spoofing.
- [ ] Include screenshot if claiming HMI/operator-view spoofing.

Judging pass/fail questions:

- Did the submitted evidence show a clear attack/defense window?
- Did `RW_Tank_Level` deviate from expected physical behavior?
- Did at least one observable signal or detector output support the claim?
- Were the artifacts sufficient to reproduce or inspect the claim?
- If the participant claims stealth, did they explain which detector or evidence
  source did not catch the spoof and why?



### Scenario 2: Pump Start/Stop Override

Attack idea: force or block `RW_Pump_Start`, `RW_Pump_Stop`, or `RW_Pump_Sts`.

Expected process effects:

- Pump command and pump status may disagree.
- Pump running with speed should produce flow.
- Pump off should produce near-zero flow.
- Tank levels should respond to flow direction.

Evidence tags:

- `RW_Pump_Start`
- `RW_Pump_Stop`
- `RW_Pump_Sts`
- `RW_Pump_Speed`
- `RW_Pump_Flow`
- `RW_Tank_P_Valve`
- `RW_Tank_P_Valve_Sts`
- `RW_Tank_Level`
- `UF_UFFT_Tank_Level`

Success evidence:

- Command/status mismatch or unexpected status transition is visible.
- Flow is physically inconsistent with pump state, or tank-level movement is
  inconsistent with flow.
- Invariant report highlights correlation, causality, or mass-balance impact.

### Scenario 3: Process Valve Override

Attack idea: force `RW_Tank_P_Valve` or spoof `RW_Tank_P_Valve_Sts`.

Expected process effects:

- If pump is running and process valve is open, UF tank should fill.
- If valve status says closed while flow/UF level still rises, evidence is
  inconsistent.
- If valve command is open but status never follows, command-to-status
  causality fails.

Evidence tags:

- `RW_Tank_P_Valve`
- `RW_Tank_P_Valve_Sts`
- `RW_Pump_Sts`
- `RW_Pump_Speed`
- `RW_Pump_Flow`
- `UF_UFFT_Tank_Level`

Success evidence:

- Valve command/status timing is abnormal, or physical flow/tank behavior does
  not match the reported valve state.

### Scenario 4: High-High Alarm Suppression

Attack idea: hide, suppress, or fail to report `Alarm_RW_Tank_HH` while
`RW_Tank_Level` exceeds the alarm threshold.

Expected process effects:

- `RW_Tank_Level` crosses the high-high threshold.
- `Alarm_RW_Tank_HH` should turn on.
- If operator view is spoofed, screenshot may show normal while tags show alarm.

Evidence tags:

- `RW_Tank_Level`
- `Alarm_RW_Tank_HH`
- `RW_Tank_PR_Valve`
- `RW_Tank_PR_Valve_Sts`
- `SYS_RUNNING`

Success evidence:

- The level exceeds threshold and alarm behavior is missing, delayed, or hidden.
- PCAP or tool output shows where suppression occurred.
- Viewer/HMI screenshot is included if operator-view spoofing is claimed.

### Scenario 5: Defense/Detection

Defense idea: detect process inconsistency using invariant checks or another
tool.

Expected process effects:

- Attack produces an observable tag inconsistency.
- Defense emits a report identifying the rule, time/sample, and affected tags.

Evidence tags:

- Same tags as the attack scenario.
- `events.json` should mark attack and detection windows.

Success evidence:

- `artifacts/invariant-check/report.json` or another detector output exists.
- Report identifies the attacked tag(s) and physical rule violation.
- Report timing aligns with `events.json` and `tags.csv`.

## Capture Requirements

Every CTF1 P1 submission should include:

| Required file | Requirement |
| --- | --- |
| `meta.json` | Use case, run id, backend, timestamps, schema/profile if available. |
| `events.json` | Operator actions, attack start/stop, recovery, detector output time. |
| `tags.csv` | Timestamped samples for all minimum P1 tags. |
| `artifacts/invariant-check/` | At least `summary.txt` or `report.json` when using invariant defense. |

Recommended:

| Optional file | Requirement |
| --- | --- |
| `pcap/` | Required for network/protocol-level claims. |
| Screenshots | Required for HMI/operator-view spoofing claims. |
| `artifacts/<attack-tool>/` | Required when using an automated attack tool. |

Sampling guidance:

- Poll interval: 500 ms or faster.
- Capture window: at least 10 seconds before attack, through recovery or stop.
- Events must use timestamps that can be aligned with `tags.csv`.

## First Test-Run Observations

Use existing golden runs before running live infrastructure.

### Idle Baseline

Bundle: `runs/run-a-idle`

Expected observations:

- `SYS_IDLE = 1`, `SYS_RUNNING = 0`.
- Pump commands, valve commands, statuses, speed, and flow remain off/zero.
- Tank levels show only small noise/drift.
- No high-high alarm.

### Startup Baseline

Bundle: `runs/run-b-startup`

Expected observations:

- System transitions from idle to running.
- Pump and valve statuses turn on.
- `RW_Pump_Flow` rises once pump is running.
- `RW_Tank_Level` and `UF_UFFT_Tank_Level` rise during flow.
- No high-high alarm.

Note: current bundled data may show minor invariant violations because the
existing synthetic data has small nonzero/noisy flow while pump status is off.
Treat this as useful evidence that thresholds and run quality need review.

### Alarm Baseline

Bundle: `runs/run-c-alarm`

Expected observations:

- System starts in running state.
- Pump and valves are active.
- `RW_Tank_Level` crosses 1200 mm.
- `Alarm_RW_Tank_HH` turns on after the high-high threshold is crossed.
- Range invariant violations are expected because this is an alarm scenario.

## Participant Evidence Template

Use this structure for a participant-facing checklist.

```
Scenario name:
Participant/team:
Run id:
Backend: OpenPLC / Rockwell / replay / synthetic

Claim:
What attack or defense succeeded?

Attack or defense window:
Start timestamp:
Stop timestamp:

Expected physical/process effect:
What should change in the plant?

Required tags/signals:
- ...

Observed evidence:
- tags.csv:
- events.json:
- invariant/detector report:
- pcap:
- screenshots:

Judging checks:
- Did command changes have matching or intentionally mismatched status?
- Did pump state, speed, and flow agree?
- Did tank levels move in a physically plausible direction?
- Did alarms/interlocks trigger, fail, or get hidden as claimed?
- Do events, tags, screenshots, and pcaps line up in time?

Verdict:
Pass / Fail / Needs review

Reviewer notes:
...
```
