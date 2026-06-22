# WT-P2-S01 Reviewer Answer Key Template

Use this template to review player submissions for:

```
Scenario: WT-P2-S01
Attack: Wrong Chemical Valve Opened
Backend: OpenPLC
Reference bundle: sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc
Reference runbook: docs/ctf1/p2-chemical-treatment/ctf1-p2-chemical-treatment-final-runbook.md
```

This is a reviewer aid and CTF-maker worksheet. Fill in the placeholders after
the official P2 reference run bundle is captured.

## 1. Expected Reference Values

| Item | Expected value or location |
| --- | --- |
| Scenario ID | `WT-P2-S01` |
| Intended chemical action | `NaOCl dosing expected` |
| Wrong chemical valve status | `ChemTreat_HCl_Valve_Sts` |
| Wrong chemical command comparison | `ChemTreat_HCl_Valve` |
| Wrong chemical level tag | `ChemTreat_HCl_Level` |
| Intended chemical level tag | `ChemTreat_NaOCl_Level` |
| Attack start | `[PLACEHOLDER: fill from events.json, about 12s]` |
| Attack stop | `[PLACEHOLDER: fill from events.json, about 24s]` |
| Required run bundle | `sphere-usecases/water-treatment/runs/ctf1-p2-s01-openplc` |

Expected findings:

```
[PLACEHOLDER: paste official detector or reviewer summary excerpt]

Expected examples:
- HCl valve status active when NaOCl dosing is expected
- HCl command remains inactive, supporting a status-without-command finding
- HCl tank level trends downward during wrong-valve window
- NaOCl tank level does not match the intended dosing story
```

## 2. CTF Maker Screenshot Checklist

### Maker Screenshot A: Baseline Context

Expected contents:

- Run selected: `ctf1-p2-s01-openplc`
- Time before attack, around `5-10s`
- NaOCl and HCl level/status tags visible if possible

Reference screenshot:

```
[PLACEHOLDER: insert/link official P2 baseline Viewer screenshot]
```

### Maker Screenshot B: Wrong Valve Active

Expected contents:

- Time near `12s`
- `ChemTreat_HCl_Valve_Sts` active
- `ChemTreat_HCl_Valve` visible for command/status comparison
- NaOCl intended action or scenario event visible if available

Reference screenshot:

```
[PLACEHOLDER: insert/link official wrong-valve Viewer screenshot]
```

### Maker Screenshot C: Chemical Level Comparison

Expected contents:

- Attack window visible, around `12-24s`
- `ChemTreat_HCl_Level`
- `ChemTreat_NaOCl_Level`
- HCl/NaOCl valve status comparison

Reference screenshot:

```
[PLACEHOLDER: insert/link official HCl-vs-NaOCl comparison screenshot]
```

### Maker Screenshot D: Related Chemical Tanks

Expected contents:

- `ChemTreat_NaCl_Level`
- `ChemTreat_NaOCl_Level`
- `ChemTreat_HCl_Level`

Reference screenshot:

```
[PLACEHOLDER: insert/link official P2 related-tanks screenshot]
```

### Maker Screenshot E: Recovery

Expected contents:

- Time near `24s` or later
- Wrong valve closes or returns to expected state

Reference screenshot:

```
[PLACEHOLDER: insert/link official P2 recovery screenshot]
```

### Maker Screenshot F: Detector Summary

Expected contents:

- Any causality, correlation, mass-balance, range, or rate finding related to
  the wrong chemical path

Reference screenshot or pasted text:

```
[PLACEHOLDER: insert/link official P2 detector summary screenshot]
```

## 3. Review Checklist

Mark each item `Complete`, `Partial`, or `Missing`.

| Evidence item | Complete / Partial / Missing | Reviewer notes |
| --- | --- | --- |
| Player identifies scenario `WT-P2-S01` | | |
| Player identifies intended NaOCl dosing action | | |
| Player identifies wrong HCl valve/path | | |
| Player identifies attack start and stop window | | |
| Player shows wrong valve/status active during attack | | |
| Player shows wrong chemical tank level response | | |
| Player compares HCl behavior against NaOCl behavior | | |
| Player includes `events.json` evidence | | |
| Player includes `tags.csv` evidence | | |
| Player includes detector summary/report evidence | | |
| Player includes Viewer baseline screenshot | | |
| Player includes Viewer wrong-valve screenshot | | |
| Player includes Viewer recovery screenshot | | |
| Player explains why wrong chemical actuation is physically suspicious | | |
| Player does not overclaim pH/chlorine-residual impact in UC1 | | |

## 4. Required Vs Optional Evidence

Required for a complete submission:

- Run bundle or exported files: `meta.json`, `events.json`, `tags.csv`
- Detector summary or report
- Viewer screenshot during wrong-valve actuation
- Short physical-process explanation

Optional supporting evidence:

- OpenPLC WebUI screenshot
- File tree screenshot showing bundle contents
- PCAP or network capture
- Extra tool logs

## 5. Expected Reviewer Reasoning

A strong answer should explain:

```
NaOCl dosing was expected, but the HCl valve status became active during the
attack window. If HCl level decreases while the HCl valve status is active, the
process evidence indicates that the wrong chemical path actuated. The reviewer
should compare HCl valve/level behavior against NaOCl valve/level behavior to
confirm the mismatch.
```

UC1 limitation:

```
Do not require pH, chlorine residual, or concentration evidence for this
scenario. UC1 P2 currently models chemical tank levels and valves, not chemical
quality outcomes.
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
