# WT-P3-S01 Player Evidence Template

Use this template to submit evidence for:

```
Scenario: WT-P3-S01
Attack: UF Drain Valve Forced Open During Filtration
Backend: OpenPLC
Reference runbook: docs/ctf1/p3-ultrafiltration/ctf1-p3-ultrafiltration-final-runbook.md
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

| Question | Player answer |
| --- | --- |
| What filtration state or action was expected? | |
| Which drain/UF path changed unexpectedly? | |
| What time/sample did the drain event start? | |
| What time/sample did the drain event stop or recover? | |
| What happened to `UF_UFFT_Tank_Level` during the attack? | |
| What RO feed or backwash evidence helps rule out normal operation? | |

Short claim:

```
Normal UF filtration was expected during WT-P3-S01, but __________ opened and
__________ changed during the attack window.
```

## 3. Physical-Process Explanation

Why is drain valve activity suspicious during this window?

```

```

Did the UF feed tank level move in a way that matches the drain opening?

```

```

Does the evidence prove poisoning, or only filtration loss / contamination risk?

```

```

Note: UC1 does not model turbidity, pathogen removal, chlorine residual, pH, or
chemical concentration. Keep the claim focused on drain status, UF tank level,
and filtration-bypass/contamination risk.

## 4. Required Evidence Checklist

| Required evidence | Submitted? | Path or filename |
| --- | --- | --- |
| Run bundle directory | [ ] | |
| `meta.json` | [ ] | |
| `events.json` | [ ] | |
| `tags.csv` | [ ] | |
| `artifacts/invariant-check/summary.txt` or report | [ ] | |
| Viewer screenshot before attack | [ ] | |
| Viewer screenshot during drain actuation | [ ] | |
| Viewer screenshot after recovery | [ ] | |

Recommended screenshot names:

```
screenshot-a-p3-baseline.png
screenshot-b-p3-drain-valve-open.png
screenshot-c-p3-uf-level-drop.png
screenshot-d-p3-roft-bwp-context.png
screenshot-e-p3-recovery.png
screenshot-f-p3-invariant-summary.png
```

## 5. Viewer Screenshot Prompts

### Screenshot A: Baseline

Required contents:

- Viewer run selected: `ctf1-p3-s01-openplc`
- Time before attack, around `5-10s`
- `UF_UFFT_Tank_Level`
- `UF_Drain_Valve_Sts` OFF
- `SYS_RUNNING` visible if possible

Attachment:

```

```

### Screenshot B: Drain Valve Active

Required contents:

- Time near `12s`
- `UF_Drain_Valve_Sts` ON
- `UF_Drain_Valve` visible for command/status comparison

Attachment:

```

```

### Screenshot C: UF Level Effect

Required contents:

- Same attack window, around `12-24s`
- `UF_UFFT_Tank_Level`
- `UF_Drain_Valve_Sts`
- Tank level decrease visible in trend or overlay

Attachment:

```

```

### Screenshot D: ROFT / Backwash Context

Required contents:

- `UF_ROFT_Valve_Sts`
- `UF_BWP_Valve_Sts`
- Explanation of whether either tag explains the observed drain event

Attachment:

```

```

### Screenshot E: Recovery

Required contents:

- Time near `24s` or later
- Drain valve status returns OFF

Attachment:

```

```

### Screenshot F: Detector Summary

Required contents:

- Any drain-active, status-without-command, tank-level, range, rate, or
  causality finding related to P3

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

