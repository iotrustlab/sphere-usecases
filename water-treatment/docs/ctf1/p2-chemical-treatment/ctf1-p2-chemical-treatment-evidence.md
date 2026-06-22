# CTF1 P2 Chemical Treatment Evidence Checklist

This draft defines the first CTF1 evidence target for Water Treatment UC1
Process 2 (P2): Chemical Treatment.

The goal is not only to show that a chemical valve changed state. The goal is
to show that the wrong chemical path actuated and created a physically
meaningful process inconsistency.

## P2 Process Story

P2 models three chemical storage tanks and their dosing valves:

1. NaCl, NaOCl, and HCl tanks start near their normal fill levels.
2. Valve commands open the chemical dosing valves.
3. Valve status should follow the intended valve command after a short delay.
4. If a valve is open, that chemical tank should slowly decrease.
5. If the wrong valve opens, the wrong chemical tank should drain while the
   intended chemical tank stays stable.

Current UC1 limitation: chemical dosing is simple. The model tracks tank levels
and valve status, but it does not yet model pH, chlorine residual, concentration,
or automatic flow-proportional dosing.

## Core P2 Tags

| Tag | Role | Why it matters |
| --- | --- | --- |
| `SYS_RUNNING` | State | Confirms the system is active. |
| `ChemTreat_NaCl_Level` | Sensor | NaCl tank level. |
| `ChemTreat_NaOCl_Level` | Sensor | NaOCl disinfectant tank level. |
| `ChemTreat_HCl_Level` | Sensor | HCl pH-adjustment tank level. |
| `ChemTreat_NaCl_Valve` | Command | Controller request for NaCl dosing valve. |
| `ChemTreat_NaOCl_Valve` | Command | Controller request for NaOCl dosing valve. |
| `ChemTreat_HCl_Valve` | Command | Controller request for HCl dosing valve. |
| `ChemTreat_NaCl_Valve_Sts` | Feedback | Simulated NaCl valve position. |
| `ChemTreat_NaOCl_Valve_Sts` | Feedback | Simulated NaOCl valve position. |
| `ChemTreat_HCl_Valve_Sts` | Feedback | Simulated HCl valve position. |

## CTF1 P2 Scenario Inventory

| Scenario ID | Attack/defense scenario | Observable physical/process effect | Primary tags/signals | Evidence artifacts |
| --- | --- | --- | --- | --- |
| `WT-P2-S01` | Wrong chemical valve opened | NaOCl dosing is expected, but HCl valve status changes and HCl tank drains instead. | `ChemTreat_NaOCl_Valve`, `ChemTreat_NaOCl_Valve_Sts`, `ChemTreat_NaOCl_Level`, `ChemTreat_HCl_Valve`, `ChemTreat_HCl_Valve_Sts`, `ChemTreat_HCl_Level` | `tags.csv`, `events.json`, Viewer screenshot, detector report |
| `WT-P2-S02` | NaOCl valve command/status mismatch | Valve command and status disagree or status changes outside expected timing. | `ChemTreat_NaOCl_Valve`, `ChemTreat_NaOCl_Valve_Sts` | `tags.csv`, Viewer screenshot, detector report |
| `WT-P2-S03` | Chemical drain inconsistency | Valve is open but tank level does not decrease, or tank level changes while valve is closed. | Chemical level tags plus matching valve status tags | `tags.csv`, invariant report |
| `WT-P2-D01` | Defense/detection with invariants | Detector identifies causality, correlation, rate, or mass-balance violation. | Same tags as attacked scenario | `artifacts/invariant-check/report.json`, `summary.txt` |

## Scenario WT-P2-S01: Wrong Chemical Valve Opened

Attack idea: an action intended for NaOCl disinfectant dosing is redirected,
overridden, or mis-mapped so that the HCl valve status opens instead.

This scenario is focused on an OT actuation path:

```
expected NaOCl dosing
  -> NaOCl command is present
  -> wrong valve status opens: HCl
  -> HCl tank level decreases
  -> NaOCl tank does not show the expected dosing behavior
  -> wrong-chemical evidence artifact
```

### Attacker Objective

Show that a participant can cause the wrong P2 chemical path to actuate during a
defined attack window.

Possible attacker claims:

- "I caused HCl dosing behavior when NaOCl was expected."
- "I redirected or overrode the chemical valve path."
- "I made the wrong chemical tank drain during the attack window."

### Defender Objective

Show that a defender can detect or explain the wrong actuation using
physical-process evidence.

Possible defender claims:

- "`ChemTreat_HCl_Valve_Sts` changed when NaOCl dosing was expected."
- "`ChemTreat_HCl_Level` decreased during the attack window."
- "`ChemTreat_NaOCl_Level` did not show the expected dosing behavior."
- "The attack window in `events.json` aligns with the wrong-valve evidence."

Expected process effects:

- NaOCl command becomes active as the intended chemical action.
- HCl valve status becomes active during the attack window.
- HCl tank level trends downward if HCl valve status is open.
- NaOCl command/status/level does not match the intended dosing story.
- Detector output should show NaOCl command/status causality and HCl
  status-without-command correlation findings.

## Effect-To-Tag Mapping

| Physical/process question | Tags/signals to inspect | What to look for |
| --- | --- | --- |
| Was NaOCl dosing expected? | `ChemTreat_NaOCl_Valve`, `events.json` | NaOCl intended action or scenario event. |
| Did the wrong valve open? | `ChemTreat_HCl_Valve`, `ChemTreat_HCl_Valve_Sts` | HCl status active during the attack window, even though HCl command is not the intended action. |
| Did the wrong tank physically respond? | `ChemTreat_HCl_Level`, `ChemTreat_HCl_Valve_Sts` | HCl level decreases while HCl valve status is open. |
| Did the intended chemical remain stable? | `ChemTreat_NaOCl_Level`, `ChemTreat_NaOCl_Valve_Sts` | NaOCl does not drain as expected, or status does not match intent. |
| Did other tanks help isolate the effect? | `ChemTreat_NaCl_Level`, `ChemTreat_HCl_Level`, `ChemTreat_NaOCl_Level` | HCl changes while the others remain comparatively stable. |
| Did the detector flag it? | `artifacts/invariant-check/report.json`, `summary.txt` | NaOCl command/status causality and HCl status-without-command correlation findings near attack samples. |

## OpenPLC Evidence Paths

| Canonical tag | OpenPLC evidence path |
| --- | --- |
| `ChemTreat_NaCl_Level` | bridge holding register `302` |
| `ChemTreat_NaOCl_Level` | bridge holding register `303` |
| `ChemTreat_HCl_Level` | bridge holding register `304` |
| `ChemTreat_NaCl_Valve` | controller coil `45` |
| `ChemTreat_NaOCl_Valve` | controller coil `46` |
| `ChemTreat_HCl_Valve` | controller coil `47` |
| `ChemTreat_NaCl_Valve_Sts` | bridge holding register `325` |
| `ChemTreat_NaOCl_Valve_Sts` | bridge holding register `326` |
| `ChemTreat_HCl_Valve_Sts` | bridge holding register `327` |

## Evidence Capture Requirements

Required artifacts:

| Artifact | Required contents |
| --- | --- |
| `meta.json` | Use case, scenario ID, backend, timestamps, tag list. |
| `events.json` | Expected chemical action, attack start, attack stop, recovery event. |
| `tags.csv` | P2 level tags, P2 valve command/status tags, `SYS_RUNNING`. |
| `artifacts/invariant-check/report.json` | Detector output with sample-level findings. |
| `artifacts/invariant-check/summary.txt` | Human-readable detector summary. |
| Viewer screenshot | Run selected, attack timestamp, NaOCl/HCl tags visible. |

Optional artifacts:

| Artifact | When useful |
| --- | --- |
| OpenPLC WebUI screenshot | Shows runtime status, but not primary evidence. |
| PCAP | Required for network-level command-redirection or injection claims. |
| Tool logs | Required when an automated attack/defense tool is part of the claim. |
