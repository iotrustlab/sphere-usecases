# PS-1 Hydro Station — Attack Surface

This document defines a minimal, concrete attack surface for the PS‑1
hydro power use case. It is intended to guide toolbox integrations
(attack + defense) and to map expected artifacts into run bundles.

## Scope and Assumptions

- Scope: PS‑1 generic hydro station in `power-hydro/`
- Tags: must align with `power-hydro/tag_contract.yaml`
- Attacker model: can modify PLC outputs, spoof sensor measurements, or
  manipulate command/status channels
- Out of scope: firmware rootkits, network lateral movement, or HMI‑only
  deception without PLC impact

## System Model (PS‑1)

The control loop is simplified as:

- Operator/HMI commands: `HY_Start_Cmd`, `HY_Stop_Cmd`, `HY_Reset_Cmd`,
  `HY_Mode_Auto`, `HY_Run_Enable`, `HY_Power_Setpoint_MW`
- Actuators: `HY_Gate_Cmd`, `HY_Breaker_Cmd`, `HY_Spill_Cmd`
- Process feedback: `HY_Gate_Pos`, `HY_Breaker_Sts`, `HY_Spill_Sts`,
  `HY_Res_Level`, `HY_Head`, `HY_Flow`, `HY_Pressure`,
  `HY_Speed_Pct`, `HY_Freq_Hz`, `HY_Power_MW`
- Trips/alarms: `HY_Trip_*`, `HY_Alarm_*`
- State: `HY_State_*`, `HY_Permissives_Ready`

## Attack Goals

- Create unsafe physical conditions (overspeed, overfrequency, overpressure)
- Induce instability without obvious operator alarms
- Cause breaker misoperation or repeated open/close cycling
- Force power output away from operator setpoint

## Primary Attack Surfaces

### 1) Command Manipulation

Targets:
- `HY_Gate_Cmd`
- `HY_Breaker_Cmd`
- `HY_Power_Setpoint_MW`

Impact:
- Gate manipulation directly affects `HY_Flow`, `HY_Speed_Pct`, `HY_Freq_Hz`
- Breaker manipulation changes grid connection while the turbine runs
- Setpoint overrides alter power/frequency trajectories

### 2) Sensor Spoofing

Targets:
- `HY_Freq_Hz`, `HY_Speed_Pct`, `HY_Power_MW`
- `HY_Breaker_Sts`, `HY_Gate_Pos`
- `HY_Pressure`, `HY_Head`

Impact:
- Mask unsafe conditions while the physical system destabilizes
- Hide breaker open/close events or gate mismatches

### 3) Trip/Alarm Suppression

Targets:
- `HY_Trip_Overspeed`, `HY_Trip_Overpressure`, `HY_Trip_LowHead`
- `HY_Alarm_GateMismatch`, `HY_Alarm_BreakerMismatch`

Impact:
- Prevents protective responses or hides actuator mismatches

## Reference‑Inspired Scenarios (Harvey Paper)

The Harvey paper (“Hey, My Malware Knows Physics!”, NDSS 2017) presents
two power‑grid‑style attacks that map cleanly to PS‑1:

### Scenario A — Breaker Chatter With Stealthy Measurements

Mechanism:
- Rapidly toggle `HY_Breaker_Cmd` while spoofing `HY_Breaker_Sts` and
  stabilizing reported `HY_Freq_Hz` and `HY_Power_MW`

Expected physical effect:
- Frequency and power disturbances during repeated breaker open/close

Expected bundle artifacts:
- `artifacts/tag-perturb/` showing command manipulation and spoofed status
- `artifacts/invariant-check/` with violations if spoofing is absent

### Scenario B — Malicious Setpoint Override (OPF‑like Behavior)

Mechanism:
- Override `HY_Power_Setpoint_MW` or `HY_Gate_Cmd` to drive `HY_Freq_Hz`
  above nominal bounds while spoofing frequency telemetry to appear normal

Expected physical effect:
- Overspeed or overfrequency conditions

Expected bundle artifacts:
- Invariant violations on `HY_Freq_Hz` or `HY_Speed_Pct` if not spoofed
- Mismatch alarms if `HY_Gate_Pos` diverges from commanded behavior

## Defensive Signals and Expected Invariants

Detection should rely on correlations and timing relationships:

- `HY_Gate_Cmd` → `HY_Gate_Pos` should converge within actuator latency
- `HY_Breaker_Cmd` ↔ `HY_Breaker_Sts` should match within milliseconds
- `HY_Freq_Hz` and `HY_Speed_Pct` should remain within safe bounds
- `HY_Power_MW` should track `HY_Gate_Pos` and `HY_Flow`
- Trips should assert when thresholds are crossed (overspeed, pressure, low head)

## Toolbox Integration Targets

Attack tooling (examples):
- Sensor spoof on `HY_Freq_Hz`, `HY_Power_MW`, `HY_Breaker_Sts`
- Command override on `HY_Gate_Cmd`, `HY_Breaker_Cmd`
- Setpoint override on `HY_Power_Setpoint_MW`

Defense tooling (examples):
- Invariant checks on frequency, speed, and command/status correlation
- Rate‑of‑change bounds on `HY_Freq_Hz`, `HY_Power_MW`, `HY_Gate_Pos`

Expected artifacts in run bundles:
- `artifacts/tag-perturb/`
- `artifacts/invariant-check/`
- Optional future: `artifacts/model-validate/` for process‑model validation
