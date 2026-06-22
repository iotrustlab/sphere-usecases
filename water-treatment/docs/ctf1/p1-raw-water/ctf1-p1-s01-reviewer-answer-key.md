# WT-P1-S01 Reviewer Answer Key Template

Use this template to review player submissions for:

```
Scenario: WT-P1-S01
Attack: Raw-Water Level Spoofing
Backend: OpenPLC
Reference bundle: sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc
Reference runbook: docs/ctf1/p1-raw-water/ctf1-p1-raw-water-final-runbook.md
```

This is a reviewer aid and CTF-maker worksheet. Fill in the placeholder
screenshots after capturing the official reference view from the CPS Enclave
Viewer.

## 1. Expected Reference Values

| Item | Expected value or location |
| --- | --- |
| Scenario ID | `WT-P1-S01` |
| Target tag | `RW_Tank_Level` |
| Baseline value | `[PLACEHOLDER: fill from reference Viewer/tags.csv]` |
| Spoofed value | `1300` |
| Restored value | `600` |
| Attack start | `[PLACEHOLDER: fill from events.json, about 12s]` |
| Attack stop | `[PLACEHOLDER: fill from events.json, about 24s]` |
| Required run bundle | `sphere-usecases/water-treatment/runs/ctf1-p1-s01-openplc` |

Expected invariant findings:

```
[PLACEHOLDER: paste official invariant summary excerpt]

Expected examples:
- range violation: RW_Tank_Level=1300 exceeds max=1200
- rate_of_change violation: RW_Tank_Level delta=700 exceeds max=50
```

## 2. CTF Maker Screenshot Checklist

Capture these reference screenshots from the Viewer and attach or link them
here. These are the images the reviewer can compare against player submissions.

### Maker Screenshot A: Baseline Context

Expected contents:

- Run selected: `ctf1-p1-s01-openplc`
- Time before attack, around `5-10s`
- `RW_Tank_Level` near baseline

Reference screenshot:

```
[PLACEHOLDER: insert/link official baseline Viewer screenshot]
```

### Maker Screenshot B: Attack Level Jump

Expected contents:

- Time near `12s`
- `RW_Tank_Level = 1300`
- P1 overlay or trend visible

Reference screenshot:

```
[PLACEHOLDER: insert/link official attack-level Viewer screenshot]
```

### Maker Screenshot C: Pump/Flow Comparison

Expected contents:

- Time during attack window, around `12-24s`
- `RW_Tank_Level`
- `RW_Pump_Flow` and/or `RW_Pump_Sts`
- Optional valve status or `Alarm_RW_Tank_HH`

Reference screenshot:

```
[PLACEHOLDER: insert/link official physical-plausibility screenshot]
```

### Maker Screenshot D: Alarm Observation

Expected contents:

- Attack window visible
- `RW_Tank_Level > 1200`
- `Alarm_RW_Tank_HH` visible

Reference screenshot:

```
[PLACEHOLDER: insert/link official alarm-observation screenshot]
```

Reviewer note:

```
[PLACEHOLDER: record whether Alarm_RW_Tank_HH activates in the reference run]
```

### Maker Screenshot E: Recovery

Expected contents:

- Time near `24s` or later
- `RW_Tank_Level` restored to baseline or toward baseline

Reference screenshot:

```
[PLACEHOLDER: insert/link official recovery screenshot]
```

### Maker Screenshot F: Invariant Summary

Expected contents:

- `range` violation
- `rate_of_change` violation

Reference screenshot or pasted text:

```
[PLACEHOLDER: insert/link official invariant-check summary screenshot]
```

## 3. Review Checklist

Mark each item `Complete`, `Partial`, or `Missing`.

| Evidence item | Complete / Partial / Missing | Reviewer notes |
| --- | --- | --- |
| Player identifies scenario `WT-P1-S01` | | |
| Player identifies target tag `RW_Tank_Level` | | |
| Player identifies attack start and stop window | | |
| Player shows `RW_Tank_Level` reaches `1300` | | |
| Player shows recovery/restoration after attack | | |
| Player includes `events.json` evidence | | |
| Player includes `tags.csv` evidence | | |
| Player includes invariant summary evidence | | |
| Player includes Viewer baseline screenshot | | |
| Player includes Viewer attack screenshot | | |
| Player includes Viewer recovery screenshot | | |
| Player compares level jump against pump/flow/status/alarm tags | | |
| Player explains why the level behavior is physically suspicious | | |
| Player records `Alarm_RW_Tank_HH` behavior without overclaiming | | |

## 4. Required Vs Optional Evidence

Required for a complete submission:

- Run bundle or exported files: `meta.json`, `events.json`, `tags.csv`
- Invariant summary or report
- Viewer screenshot during the attack
- Short physical-process explanation

Optional supporting evidence:

- OpenPLC WebUI screenshot
- File tree screenshot showing bundle contents
- PCAP or network capture
- Extra tool logs

## 5. Expected Reviewer Reasoning

A strong answer should explain:

```
RW_Tank_Level was spoofed to 1300, exceeding the expected maximum of 1200.
The jump from baseline to 1300 is too large for the process model's rate limit.
Pump/flow/status/alarm tags should be checked to determine whether any physical
process behavior explains the jump. If not, the evidence supports a raw-water
level spoofing claim.
```

Alarm handling:

```
Do not require Alarm_RW_Tank_HH activation as the sole pass condition. If the
alarm does not activate, treat it as an observation about the alarm/value path
and check whether the player documented it accurately.
```

## 6. Final Review Decision

Overall result:

```
Complete / Partial / Missing
```

Reviewer summary:

```

```

Follow-up requested from player:

```

```
