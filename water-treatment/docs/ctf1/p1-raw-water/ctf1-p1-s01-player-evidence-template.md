# WT-P1-S01 Player Evidence Template

Use this template to submit evidence for:

```
Scenario: WT-P1-S01
Attack: Raw-Water Level Spoofing
Backend: OpenPLC
Reference runbook: docs/ctf1/p1-raw-water/ctf1-p1-raw-water-final-runbook.md
```

## 1. Submission Info

Player/team:

Run bundle path:

Date/time executed:

Backend used:

```
OpenPLC / replay / Rockwell / other:
```

## 2. Attack Claim

Fill in the values you observed.

| Question | Player answer |
| --- | --- |
| What tag did you spoof? | |
| What value did you spoof it to? | |
| What was the baseline value before the attack? | |
| What time/sample did the attack start? | |
| What time/sample did the attack stop? | |
| What value did the tag return to after restore? | |

Short claim:

```
I spoofed __________ during WT-P1-S01 and observed __________.
```

## 3. Physical-Process Explanation

Answer in 1-3 sentences.

Why is the observed `RW_Tank_Level` behavior physically suspicious?

```

```

Compare the level jump against pump, flow, and valve behavior. Did those tags
physically explain the jump?

```

```

Record the alarm behavior. Did `Alarm_RW_Tank_HH` change during the attack
window?

```

```

Note: `Alarm_RW_Tank_HH` may or may not trigger depending on whether the alarm
path uses the same value path as the spoofed evidence tag. Record what you saw;
do not assume alarm activation is required for success.

## 4. Required Evidence Checklist

Check each item and give the file path or screenshot name.

| Required evidence | Submitted? | Path or filename |
| --- | --- | --- |
| Run bundle directory | [ ] | |
| `meta.json` | [ ] | |
| `events.json` | [ ] | |
| `tags.csv` | [ ] | |
| `artifacts/invariant-check/summary.txt` | [ ] | |
| Viewer screenshot before attack | [ ] | |
| Viewer screenshot during attack | [ ] | |
| Viewer screenshot after restore | [ ] | |

Recommended screenshot names:

```
screenshot-a-baseline.png
screenshot-b-attack-level-1300.png
screenshot-c-pump-flow-comparison.png
screenshot-d-recovery.png
screenshot-e-invariant-summary.png
```

## 5. Viewer Screenshot Prompts

Attach screenshots or paste image links below each prompt.

### Screenshot A: Baseline

Required contents:

- Viewer run selected: `ctf1-p1-s01-openplc`
- Time before attack, around `5-10s`
- `RW_Tank_Level` near baseline

Attachment:

```

```

### Screenshot B: Attack Level

Required contents:

- Time near `12s`
- `RW_Tank_Level` at or near `1300`
- P1 overlay or trend visible

Attachment:

```

```

### Screenshot C: Pump/Flow Comparison

Required contents:

- Same attack window, around `12-24s`
- `RW_Tank_Level`
- At least one supporting tag: `RW_Pump_Flow`, `RW_Pump_Sts`, valve status, or
  `Alarm_RW_Tank_HH`

Attachment:

```

```

### Screenshot D: Recovery

Required contents:

- Time near `24s` or later
- `RW_Tank_Level` restored toward baseline

Attachment:

```

```

### Screenshot E: Invariant Summary

Required contents:

- `range` violation for `RW_Tank_Level`
- `rate_of_change` violation for the spoof start or stop

Attachment:

```

```

## 6. Optional Evidence

| Optional evidence | Submitted? | Notes |
| --- | --- | --- |
| OpenPLC WebUI screenshot | [ ] | |
| File tree screenshot showing bundle files | [ ] | |
| PCAP or network capture | [ ] | |
| Extra tool logs | [ ] | |

## 7. Final Evidence Statement

Write your final answer in 2-4 sentences.

```

```
