# Research Needed for Process Model Validation

This document tracks research needed to ground the SPHERE process models in real-world data and standards.

## Current State

The process model documentation was created from:
1. **RoviSys FDS (USC24A-FDS-001 Rev B)** — tag names, wiring, P&ID topology
2. **SPHERE OpenPLC implementation** — control logic, physics equations we wrote
3. **Engineering estimates** — typical industrial values (initially unvalidated)
4. **Public standards research** — vendor datasheets, state design manuals, EPA guidance (Feb 2026)

The FDS **does not** provide:
- Control logic (state machines, level control)
- Physics equations (mass balance, flow rates)
- Timing parameters (valve delays, pump ramps)
- Numerical parameters (tank sizes, flow capacities)

## Research Status

| Process | Research Status | Notes |
|---------|----------------|-------|
| WT P1 (Raw Water) | **COMPLETE** | All key parameters validated |
| WT P2 (Chemical) | **COMPLETE** | All key parameters validated |
| WT P3 (Ultrafiltration) | **COMPLETE** | All key parameters validated |
| WD (All) | Pending | No research started |
| O&G (All) | Pending | No research started |
| Power (All) | Not started | No research started |

## Research Required by Process

### Water Treatment P1 (Raw Water)

| Parameter | Current Value | Research Value | Status |
|-----------|---------------|----------------|--------|
| Tank cross-section | (implicit) | 8–60 m² (default 12 m²) | **COMPLETE** |
| Pump max flow | 120 L/min | 10–800 gpm (default 150 gpm = 567 L/min) | **COMPLETE** |
| Valve delay | 500 ms | 4–180 s motorized (default 30 s) | **COMPLETE** (SPHERE models solenoid-fast) |
| Pump spinup lag | 800 ms | 1–3 s (default 2 s) | **COMPLETE** |
| VFD accel time | (not modeled) | 0–360 s (default 10 s) | **COMPLETE** |
| Sensor lag (level) | 0 s | 0.1–999 s (default 5 s) | **COMPLETE** |
| Alarm LL | 250 mm (17%) | 5–15% (default 10%) | **COMPLETE** |
| Alarm L | 500 mm (33%) | 10–30% (default 20%) | **COMPLETE** |
| Alarm H | 800 mm (53%) | 70–90% (default 80%) | **COMPLETE** |
| Alarm HH | 1200 mm (80%) | 90–98% (default 95%) | **COMPLETE** |

**Sources consulted:**
- USACE EM 1110‑2‑503 (small systems ≤100,000 gpd)
- Washington DOH Pub 331-620 (tank sizing examples)
- AUMA/Emerson/Bray actuator datasheets (valve timing)
- ABB ACQ580 drive guide (VFD ramp settings)
- VEGA/Endress+Hauser sensor manuals (level sensor lag)

### Water Treatment P2 (Chemical)

| Parameter | Current Value | Research Value | Status |
|-----------|---------------|----------------|--------|
| NaOCl tank capacity | 1000 mm height | 26–1000 L (default 114 L) | **COMPLETE** |
| HCl tank capacity | 1000 mm height | 26–189 L (default 114 L) | **COMPLETE** |
| NaCl tank capacity | 1000 mm height | 19–568 L (default 151 L) | **COMPLETE** |
| Dosing rate | 5 L/min | 0.0025–30 L/h (default ~3.8 L/h NaOCl) | **COMPLETE** (SPHERE value ~80× high) |
| Valve delay | 500 ms | 5–1400 ms solenoid (default 50 ms) | **COMPLETE** |
| Chlorine residual target | (not modeled) | 0.2–1.0 mg/L (default 0.5 mg/L) | **COMPLETE** |
| MRDL (max residual) | (not modeled) | 4.0 mg/L regulatory | **COMPLETE** |

**Sources consulted:**
- Pulsafeeder/Stenner/Blue-White metering pump catalogs (0.21–16.2 gph)
- ASCO/Bürkert solenoid valve specs (5–1400 ms response)
- EPA Stage 1 DBPR (MRDL 4.0 mg/L)
- Ten States Standards (0.2 mg/L minimum)
- California SWRCB continuous chlorination O&M guide

### Water Treatment P3 (Ultrafiltration)

| Parameter | Current Value | Research Value | Status |
|-----------|---------------|----------------|--------|
| Tank max level | 1200 mm | 500–1500 mm band (default 800 mm) | **COMPLETE** |
| Tank cross-section | (implicit) | 0.5–12 m² (default 6 m²) | **COMPLETE** |
| Drain/ROFT flow | 30 L/min | Flux × Area dependent | Estimate OK for simulation |
| Valve delay | 500 ms | 4–180 s motorized (default 30 s) | **COMPLETE** (SPHERE models solenoid-fast) |
| Membrane flux | (not modeled) | 40–140 LMH (default 70 LMH) | **COMPLETE** |
| Backwash interval | (not modeled) | 15–60 min (default 30 min) | **COMPLETE** |
| Backwash duration | (not modeled) | 30–120 s (default 60 s) | **COMPLETE** |
| Backwash flux | (not modeled) | 90–230 LMH (default 150 LMH) | **COMPLETE** |

**Sources consulted:**
- EPA Membrane Filtration Guidance Manual (15–60 min backwash interval)
- DOW/DuPont IntegraTec UF manuals (40–90 LMH ordinary, 230 LMH backwash)
- ZeeWeed 1500-X datasheet (55.7 m² module)
- OLTRECAP UF technical manual (>90 LMH usually not suggested)

### Water Distribution (All Processes)

| Parameter | Current Value | Source | Research Needed |
|-----------|---------------|--------|-----------------|
| All tank sizes | Estimates | - | Municipal system data |
| All flow rates | Not specified | - | EPANET examples |
| Head-flow relationships | Not implemented | - | EPANET modeling |
| Consumer demand | Not implemented | - | Diurnal patterns |

**Standards to consult:**
- AWWA M32 (Computer Modeling of Water Distribution)
- EPA EPANET User Manual
- AWWA M42 (Steel Water Storage)

## Research Workflow

When you (the user) are ready to research a domain:

1. **Gather sources**: Standards documents, vendor datasheets, EPANET examples, open datasets
2. **Extract key parameters**: Tank dimensions, flow rates, timing, control setpoints
3. **Document findings**: Add to the relevant process model doc under "Real-World Grounding"
4. **Update implementation**: Revise PLC code if parameters change significantly
5. **Validate**: Re-run golden scenarios, check invariants still pass

## Priority

1. ~~**WT P1-P3** (highest) — We have working PLC code, just need parameter validation~~ **COMPLETE**
2. **WD Supply/Grid/RWS** (now highest) — No PLC yet, need both parameters and control logic
3. **Future processes** (P4-P8, O&G, Power) — Research before implementation

## Open Questions

1. Do we have access to AWWA standards PDFs, or do we need summaries?
2. Any municipal utility operational data available?
3. Should we use EPANET example networks for WD parameters?
