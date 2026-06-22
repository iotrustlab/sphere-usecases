# Harvey Attack Surface Mapping for PS-1 Hydro Station

Reference: Soltan, et al., "Hey, My Malware Knows Physics!", NDSS 2017 (DOI: 10.14722/ndss.2017.23313).

This document maps Harvey's two-way PLC manipulation model to PS-1 (`power-hydro`).

## Harvey Core Model

Harvey combines two coordinated actions:

1. Command-path manipulation
- Replace legitimate control outputs with attacker-selected commands.

2. Sensor-path spoofing
- Inject physics-consistent fake measurements so operators and protection logic see normal behavior.

PS-1 implementation target:
- Command tags: `HY_Gate_Cmd`, `HY_Breaker_Cmd`
- Spoof tags: `HY_Speed_Pct`, `HY_Freq_Hz`, `HY_Power_MW`

## Physics Constraints Used by the Attack

From `docs/process-models/ps-hydro-station.md`:

- Mechanical turbine power:
  - `P_mech = 0.00981 * Q * H * eta_t`
- Electrical power when breaker closed:
  - `P_elec = P_mech * eta_g` (clamped by rating)
- Electrical power when breaker open:
  - `P_elec = 0`
- On-grid speed behavior:
  - `HY_Breaker_Sts=true` implies speed approximately synchronous (`HY_Speed_Pct ~= 100`)

Attack stealth requirement:
- Spoofed values should remain in expected bands and preserve cross-tag relationships seen by operators.

## Harvey-to-PS-1 Concept Map

| Harvey concept | PS-1 realization |
|---|---|
| Malicious command override | `HY_Gate_Cmd` and/or `HY_Breaker_Cmd` forced by attacker |
| Physics-informed sensor forgery | Spoof `HY_Speed_Pct`, `HY_Freq_Hz`, `HY_Power_MW` to match expected operating region |
| Process damage objective | Overspeed, unstable power output, or suppressed protection action |
| Stealth objective | Keep visible telemetry and alarms near nominal values |

## Scenarios

### 1) Overspeed induction

- Malicious action:
  - Open breaker while gate remains elevated.
- Physical effect:
  - Turbine unload causes speed rise.
- Spoof strategy:
  - Hold `HY_Speed_Pct` and `HY_Freq_Hz` near nominal to delay detection.

### 2) Power oscillation

- Malicious action:
  - Oscillate `HY_Gate_Cmd` around operating point.
- Physical effect:
  - Oscillatory `HY_Flow` and true `HY_Power_MW`.
- Spoof strategy:
  - Smooth/anchor reported `HY_Power_MW` near setpoint.

### 3) Trip suppression

- Malicious action:
  - Maintain unsafe command state during threshold exceedance.
- Physical effect:
  - Overspeed or overpressure persists.
- Spoof strategy:
  - Hide precursor measurements and suppress trip-visible conditions from operator view.

## Defender Checks

The following checks are expected to expose partial or failed spoofing:

- Command/status consistency:
  - `HY_Breaker_Cmd` should align with `HY_Breaker_Sts` after breaker timing delay.
- Correlation checks:
  - `HY_Breaker_Sts=true` should imply non-zero `HY_Power_MW`.
  - `HY_Gate_Pos`/`HY_Flow` trends should be consistent with `HY_Power_MW`.
- Safety thresholds:
  - Overspeed and overpressure conditions should trigger trip behavior.

## Artifact Targets

For each Harvey scenario run bundle:

- scenario definition (`power-hydro/scenarios/*.yaml`)
- attack artifact (perturbed `tags.csv` + manifest)
- invariant-check output describing detected violations or evasion behavior
