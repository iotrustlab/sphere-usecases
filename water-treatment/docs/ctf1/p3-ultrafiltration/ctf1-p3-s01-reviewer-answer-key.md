# WT-P3-S01 Reviewer Answer Key Template

Use this template to review player submissions for:

```
Scenario: WT-P3-S01
Attack: UF Drain Valve Forced Open During Filtration
Backend: OpenPLC
Reference bundle: sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc
Reference runbook: docs/ctf1/p3-ultrafiltration/ctf1-p3-ultrafiltration-final-runbook.md
```

This is a reviewer aid and CTF-maker worksheet. Use the reference values below
when comparing player submissions against the official P3 reference bundle.

## 1. Expected Reference Values

| Item | Expected value or location |
| --- | --- |
| Scenario ID | `WT-P3-S01` |
| Intended process context | `normal forward filtration expected` |
| Unexpected drain status | `UF_Drain_Valve_Sts` |
| Drain command comparison | `UF_Drain_Valve` |
| Physical-effect tag | `UF_UFFT_Tank_Level` |
| Forward-path context | `UF_ROFT_Valve_Sts` |
| Backwash context | `UF_BWP_Valve_Sts` |
| Attack start | `events.json`: about `12s`, `force_uf_drain_open` |
| Physical effects | `events.json`: about `16s` and `20s`, `UF_UFFT_Tank_Level` drops `900 -> 860 -> 820` |
| Attack stop | `events.json`: about `24s`, `restore_uf_drain_open` |
| Detector finding | `artifacts/invariant-check/summary.txt`: `uf-drain-status-requires-command` |
| Required run bundle | `sphere-usecases/water-treatment/runs/ctf1-p3-s01-openplc` |

Expected findings:

```
UF_Drain_Valve_Sts becomes active during the attack window.
UF_Drain_Valve remains 0 while UF_Drain_Valve_Sts is 1.
UF_UFFT_Tank_Level drops from 900 to 860 to 820.
Detector output reports uf-drain-status-requires-command violations.
RO feed/backwash tags do not explain the drain event.
Player frames this as filtration loss / contamination risk, not proven poisoning.
```

## 2. CTF Maker Screenshot Checklist

### Maker Screenshot A: Baseline Context

Expected contents:

- Run selected: `ctf1-p3-s01-openplc`
- Time before attack, around `5-10s`
- `UF_UFFT_Tank_Level`
- `UF_Drain_Valve_Sts` OFF
- Reference value: `UF_UFFT_Tank_Level = 900`, `UF_Drain_Valve_Sts = 0`

Reference screenshot:

```
[PLACEHOLDER: insert/link official P3 baseline Viewer screenshot]
```

### Maker Screenshot B: Drain Valve Active

Expected contents:

- Time near `12s`
- `UF_Drain_Valve_Sts` active
- `UF_Drain_Valve` visible for command/status comparison
- Reference value: `UF_Drain_Valve = 0`, `UF_Drain_Valve_Sts = 1`

Reference screenshot:

```
[PLACEHOLDER: insert/link official P3 drain-active Viewer screenshot]
```

### Maker Screenshot C: UF Level Drop

Expected contents:

- Attack window visible, around `12-24s`
- `UF_UFFT_Tank_Level`
- `UF_Drain_Valve_Sts`
- Decreasing UF tank level visible
- Reference value: `UF_UFFT_Tank_Level` drops `900 -> 860 -> 820`

Reference screenshot:

```
[PLACEHOLDER: insert/link official P3 UF-level-drop screenshot]
```

### Maker Screenshot D: ROFT / Backwash Context

Expected contents:

- `UF_ROFT_Valve_Sts`
- `UF_BWP_Valve_Sts`
- Enough context to show normal forward/backwash behavior does not explain the
  drain event

Reference screenshot:

```
[PLACEHOLDER: insert/link official P3 ROFT/BWP context screenshot]
```

### Maker Screenshot E: Recovery

Expected contents:

- Time near `24s` or later
- Drain valve status returns OFF
- Reference value: `UF_Drain_Valve_Sts = 0`

Reference screenshot:

```
[PLACEHOLDER: insert/link official P3 recovery screenshot]
```

### Maker Screenshot F: Detector Summary

Expected contents:

- `uf-drain-status-requires-command` correlation finding related to P3
- Reference bundle shows `24` correlation violations near samples `24-47`

Reference screenshot or pasted text:

```
[PLACEHOLDER: insert/link official P3 detector summary screenshot]
```

## 3. Review Checklist

Mark each item `Complete`, `Partial`, or `Missing`.

| Evidence item | Complete / Partial / Missing | Reviewer notes |
| --- | --- | --- |
| Player identifies scenario `WT-P3-S01` | | |
| Player identifies normal filtration context | | |
| Player identifies unexpected UF drain path | | |
| Player identifies attack start and stop window | | |
| Player shows drain valve/status active during attack | | |
| Player shows UF tank level response | | |
| Player compares drain behavior against ROFT/backwash context | | |
| Player includes `events.json` evidence | | |
| Player includes `tags.csv` evidence | | |
| Player includes detector summary/report evidence | | |
| Player includes Viewer baseline screenshot | | |
| Player includes Viewer drain-active screenshot | | |
| Player includes Viewer recovery screenshot | | |
| Player explains why drain actuation is physically suspicious | | |
| Player does not overclaim poisoning/water-quality impact in UC1 | | |

## 4. Required Vs Optional Evidence

Required for a complete submission:

- Run bundle or exported files: `meta.json`, `events.json`, `tags.csv`
- Detector summary or report
- Viewer screenshot during drain-valve actuation
- Short physical-process explanation

Optional supporting evidence:

- OpenPLC WebUI screenshot
- File tree screenshot showing bundle contents
- PCAP or network capture
- Extra tool logs

## 5. Expected Reviewer Reasoning

A strong answer should explain:

```
Normal UF filtration or forward treatment was expected, but the UF drain valve
status became active during the attack window. If UF_UFFT_Tank_Level decreases
while the drain valve status is active, the process evidence indicates that
water was diverted to drain. The reviewer should compare the drain evidence
against ROFT and backwash tags to confirm the event was not normal forward
operation or a planned cleaning cycle.
```

UC1 limitation:

```
Do not require turbidity, pathogen, chlorine residual, pH, or concentration
evidence for this scenario. UC1 P3 currently models UF tank level and valve
states, not water quality outcomes.
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
