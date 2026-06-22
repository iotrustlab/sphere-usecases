# CTF1 P3 Ultrafiltration Evidence Checklist

This draft defines the first CTF1 evidence target for Water Treatment UC1
Process 3 (P3): Ultrafiltration.

The goal is not only to show that a valve changed state. The goal is to show
that the UF feed tank lost water through an unexpected drain path during a
normal filtration window.

## P3 Process Story

P3 models the ultrafiltration feed tank and filtration outlet paths:

1. The UF feed tank receives water from upstream P1/P2.
2. During normal forward operation, water should move toward the RO feed path.
3. Drain/backwash paths should only open during intended drain or cleaning
   behavior.
4. If the drain valve is forced open during filtration, the UF tank level should
   decrease unexpectedly.
5. This is a filtration-loss and contamination-risk scenario, not a proven water
   poisoning scenario, because UC1 does not model turbidity, pathogens,
   chlorine residual, pH, or downstream water quality.

## Core P3 Tags

| Tag | Role | Why it matters |
| --- | --- | --- |
| `SYS_RUNNING` | State/context | Useful if active, but the primary evidence is the event timeline plus P3 valve/level behavior. |
| `UF_UFFT_Tank_Level` | Sensor | UF feed tank level. |
| `UF_UFFT_Tank_Valve` | Command | Controller request for UF feed/inlet valve. |
| `UF_Drain_Valve` | Command | Controller request for UF drain path. |
| `UF_ROFT_Valve` | Command | Controller request for RO feed outlet path. |
| `UF_BWP_Valve` | Command | Controller request for backwash/permeate path. |
| `UF_UFFT_Tank_Valve_Sts` | Feedback | Simulated UF feed/inlet valve position. |
| `UF_Drain_Valve_Sts` | Feedback | Simulated drain valve position. |
| `UF_ROFT_Valve_Sts` | Feedback | Simulated RO feed outlet valve position. |
| `UF_BWP_Valve_Sts` | Feedback | Simulated backwash/permeate valve position. |

## CTF1 P3 Scenario Inventory

| Scenario ID | Attack/defense scenario | Observable physical/process effect | Primary tags/signals | Evidence artifacts |
| --- | --- | --- | --- | --- |
| `WT-P3-S01` | UF drain valve forced open during filtration | UF drain status becomes active and UF tank level decreases unexpectedly. | `UF_Drain_Valve`, `UF_Drain_Valve_Sts`, `UF_UFFT_Tank_Level`, `UF_ROFT_Valve_Sts`, `UF_BWP_Valve_Sts` | `tags.csv`, `events.json`, Viewer screenshot, detector report |
| `WT-P3-S02` | UF forward path blocked | UF tank level remains high or fails to discharge while forward path is expected. | `UF_ROFT_Valve`, `UF_ROFT_Valve_Sts`, `UF_UFFT_Tank_Level` | `tags.csv`, Viewer screenshot, detector report |
| `WT-P3-S03` | Backwash path opens at wrong time | Backwash/permeate status becomes active outside intended cleaning window. | `UF_BWP_Valve`, `UF_BWP_Valve_Sts`, `UF_UFFT_Tank_Level` | `tags.csv`, `events.json`, detector report |
| `WT-P3-D01` | Defense/detection with invariants | Detector identifies drain-active-during-filtration, status-without-command, or tank-level inconsistency. | Same tags as attacked scenario | `artifacts/invariant-check/report.json`, `summary.txt` |

## Scenario WT-P3-S01: UF Drain Valve Forced Open During Filtration

Attack idea: while UC1 is running, the attacker forces the UF drain path open.
Instead of retaining or forwarding filtered water, the UF feed tank loses water
to drain.

This scenario is focused on an OT process-loss path:

```
normal filtration / forward treatment expected
  -> drain valve status opens unexpectedly
  -> UF feed tank level decreases
  -> RO feed path is off, unavailable, or inconsistent
  -> drain-sabotage evidence artifact
```

### Attacker Objective

Show that a participant can cause water loss from the UF feed tank during a
defined attack window.

Possible attacker claims:

- "I forced the UF drain path open during filtration."
- "I caused the UF feed tank to lose water unexpectedly."
- "I disrupted forward treatment by diverting water to drain."

### Defender Objective

Show that a defender can detect or explain the drain actuation using
physical-process evidence.

Possible defender claims:

- "`UF_Drain_Valve_Sts` became active during a normal run window."
- "`UF_UFFT_Tank_Level` decreased while the drain valve status was active."
- "`UF_ROFT_Valve_Sts` was not the active forward path during the drain event."
- "The attack window in `events.json` aligns with the drain/status/level
  evidence."

Expected process effects:

- `events.json` records the intended normal filtration context before the attack.
- `UF_Drain_Valve_Sts` becomes active during the attack window.
- `UF_Drain_Valve` remains off while `UF_Drain_Valve_Sts` is active.
- `UF_UFFT_Tank_Level` trends downward while drain status is active.
- `UF_ROFT_Valve_Sts` may be off or inconsistent with normal forward operation.
- Detector output should identify drain-active-during-filtration,
  status-without-command, or tank-level inconsistency if rules are active.

## Effect-To-Tag Mapping

| Physical/process question | Tags/signals to inspect | What to look for |
| --- | --- | --- |
| Was normal filtration expected? | `events.json`, `SYS_RUNNING` if available | Intended process context before the drain event. |
| Did the drain path open? | `UF_Drain_Valve`, `UF_Drain_Valve_Sts` | Drain status active, especially if drain command is not expected. |
| Did the UF tank physically respond? | `UF_UFFT_Tank_Level`, `UF_Drain_Valve_Sts` | UF tank level decreases while drain status is active. |
| Was the forward path normal? | `UF_ROFT_Valve`, `UF_ROFT_Valve_Sts` | Forward/RO feed path off, blocked, or inconsistent during drain event. |
| Was this a backwash/cleaning event? | `UF_BWP_Valve`, `UF_BWP_Valve_Sts`, `events.json` | No intended backwash event should explain the drain. |
| Did the detector flag it? | `artifacts/invariant-check/report.json`, `summary.txt` | Drain/status/tank-level findings near attack samples. |

## OpenPLC Evidence Paths

| Canonical tag | OpenPLC evidence path |
| --- | --- |
| `UF_UFFT_Tank_Level` | bridge holding register `305` |
| `UF_UFFT_Tank_Valve` | controller coil `48` |
| `UF_Drain_Valve` | controller coil `49` |
| `UF_ROFT_Valve` | controller coil `50` |
| `UF_BWP_Valve` | controller coil `51` |
| `UF_UFFT_Tank_Valve_Sts` | bridge holding register `328` |
| `UF_Drain_Valve_Sts` | bridge holding register `329` |
| `UF_ROFT_Valve_Sts` | bridge holding register `330` |
| `UF_BWP_Valve_Sts` | bridge holding register `331` |

## Evidence Capture Requirements

Required artifacts:

| Artifact | Required contents |
| --- | --- |
| `meta.json` | Use case, scenario ID, backend, timestamps, tag list. |
| `events.json` | Intended filtration context, attack start, attack stop, recovery event. |
| `tags.csv` | P3 level tag and P3 valve command/status tags. |
| `artifacts/invariant-check/report.json` | Detector output with sample-level findings. |
| `artifacts/invariant-check/summary.txt` | Human-readable detector summary. |
| Viewer screenshot | Run selected, attack timestamp, P3 drain/status/level tags visible. |

Optional artifacts:

| Artifact | When useful |
| --- | --- |
| OpenPLC WebUI screenshot | Shows runtime status, but not primary evidence. |
| PCAP | Required for network-level command injection or replay claims. |
| Tool logs | Required when an automated attack/defense tool is part of the claim. |
