# WT-P2-S01 Player Evidence Template

Use this template to submit evidence for:

```
Scenario: WT-P2-S01
Attack: Wrong Chemical Valve Opened
Backend: OpenPLC
Reference runbook: docs/ctf1/p2-chemical-treatment/ctf1-p2-chemical-treatment-final-runbook.md
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
| Which chemical action was expected? | |
| Which wrong chemical valve opened? | |
| What time/sample did the wrong valve open? | |
| What time/sample did the wrong valve close or recover? | |
| Which chemical tank level changed during the attack? | |
| Which intended chemical tank stayed stable or behaved unexpectedly? | |

Short claim:

```
NaOCl dosing was expected during WT-P2-S01, but __________ opened instead and
__________ changed during the attack window.
```

## 3. Physical-Process Explanation

Why is the observed valve behavior physically/process-suspicious?

```

```

Did the wrong chemical tank level move in a way that matches the wrong valve
opening?

```

```

Did the intended NaOCl path behave differently from what was expected?

```

```

Note: UC1 does not model pH, chlorine residual, concentration, or automatic
dosing control. Keep the claim focused on level/valve physical evidence.

## 4. Required Evidence Checklist

| Required evidence | Submitted? | Path or filename |
| --- | --- | --- |
| Run bundle directory | [ ] | |
| `meta.json` | [ ] | |
| `events.json` | [ ] | |
| `tags.csv` | [ ] | |
| `artifacts/invariant-check/summary.txt` or report | [ ] | |
| Viewer screenshot before attack | [ ] | |
| Viewer screenshot during wrong-valve actuation | [ ] | |
| Viewer screenshot after recovery | [ ] | |

Recommended screenshot names:

```
screenshot-a-p2-baseline.png
screenshot-b-p2-wrong-hcl-valve-open.png
screenshot-c-p2-hcl-vs-naocl-levels.png
screenshot-d-p2-recovery.png
screenshot-e-p2-invariant-summary.png
```

## 5. Viewer Screenshot Prompts

### Screenshot A: Baseline

Required contents:

- Viewer run selected: `ctf1-p2-s01-openplc`
- Time before attack, around `5-10s`
- NaOCl and HCl valve/status/level tags visible if possible

Attachment:

```

```

### Screenshot B: Wrong Valve Active

Required contents:

- Time near `12s`
- `ChemTreat_HCl_Valve_Sts` active
- `ChemTreat_HCl_Valve` visible for command/status comparison
- NaOCl intended action or event visible if available

Attachment:

```

```

### Screenshot C: Wrong Chemical Level Effect

Required contents:

- Same attack window, around `12-24s`
- `ChemTreat_HCl_Level`
- `ChemTreat_NaOCl_Level`
- HCl/NaOCl valve status comparison

Attachment:

```

```

### Screenshot D: Recovery

Required contents:

- Time near `24s` or later
- Wrong valve closes or returns to expected state

Attachment:

```

```

### Screenshot E: Detector Summary

Required contents:

- Any causality, correlation, mass-balance, range, or rate finding related to
  the wrong chemical path

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
