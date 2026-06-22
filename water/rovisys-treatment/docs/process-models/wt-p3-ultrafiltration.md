# Process Model: Ultrafiltration

## Overview

| Field | Value |
|-------|-------|
| **Domain** | Water Treatment |
| **Process ID** | WT-P3 |
| **Status** | Implemented |
| **Real-world reference** | USC24A-FDS-001 Rev B (RoviSys FDS) |

### Description

The Ultrafiltration process (P3) filters chemically-treated water through membrane filtration to remove particulates, bacteria, and large molecules. The UF Feed Tank (UFFT) receives water from the Raw Water pump (P1) after chemical dosing (P2) and feeds downstream processes.

The UFFT tank level drives the P1 pump control: when the tank level drops below 800 mm, the RW pump starts to refill; when it rises above 1000 mm, the pump stops.

Filtered water exits through the ROFT (Reverse Osmosis Feed Tank) valve for further treatment, or through the drain valve for waste. The BWP (Backwash Permeate) valve is used during membrane cleaning cycles.

### Components

- **UFFT Tank**: Ultrafiltration feed tank (1200 mm max level)
- **UFFT Valve**: Inlet valve from P1 (process valve)
- **Drain Valve**: Waste outlet valve
- **ROFT Valve**: Outlet valve to Reverse Osmosis Feed Tank
- **BWP Valve**: Backwash permeate valve for membrane cleaning

### Process Diagram Reference

- P&ID: `assets/diagrams/water-treatment-p3.yaml`
- Slice: `slices/wt-uc1-slice.yaml`

---

## State Variables

| Variable | Symbol | Units | Range | Initial | Description |
|----------|--------|-------|-------|---------|-------------|
| Tank level | L_uf | mm | [0, 1200] | 400 | UF feed tank level |
| UFFT valve open | v_ufft | bool | - | false | Inlet valve from P1 |
| Drain valve open | v_drain | bool | - | false | Waste drain valve |
| ROFT valve open | v_roft | bool | - | false | RO feed tank outlet valve |
| BWP valve open | v_bwp | bool | - | false | Backwash permeate valve |

---

## Dynamic Model

### Governing Equations

**Tank mass balance:**

```
dL_uf/dt = (Q_in - Q_out) * (1000 / A_tank)
```

where:
- `L_uf` = UF tank level [mm]
- `Q_in` = inflow from P1 pump [L/min] (when P valve open and pump running)
- `Q_out` = outflow [L/min] = Q_drain + Q_roft (when respective valves open)
- `A_tank` = tank cross-sectional area [m²]

**Discretized form (Forward Euler, dt = 100 ms):**

For the implemented simulator with implicit tank area normalization:

```
// Inflow from P1 (when pump running AND P valve open)
L_uf[k+1] = L_uf[k] + Q_pump * (dt / 60)

// Outflow through drain valve
L_uf[k+1] = L_uf[k] - Q_drain * (dt / 60)    when drain valve open

// Outflow through ROFT valve
L_uf[k+1] = L_uf[k] - Q_roft * (dt / 60)     when ROFT valve open
```

**Saturation:**

```
L_uf = max(0, min(L_uf, L_max))
```

Tank level clamped to physical bounds.

**Valve delay model:**

Same as P1/P2 - valves transition with discrete delay:

```
if cmd = OPEN and valve = CLOSED:
    timer := timer + 1
    if timer >= VALVE_DELAY:
        valve := OPEN
        timer := 0
```

### Parameters

| Parameter | Symbol | Value | Units | Source | Notes |
|-----------|--------|-------|-------|--------|-------|
| Max tank level | L_max | 1200 | mm | FDS | Physical tank height |
| Min tank level | L_min | 0 | mm | - | Empty tank |
| Drain flow rate | Q_drain | 30 | L/min | Estimated | When drain valve fully open |
| ROFT flow rate | Q_roft | 30 | L/min | Estimated | When ROFT valve fully open |
| Valve delay | τ_valve | 500 | ms | FDS | 5 cycles × 100 ms |
| Initial level | L_0 | 400 | mm | - | Partially filled at startup |
| Pump start threshold | L_start | 800 | mm | FDS | Start P1 pump when below |
| Pump stop threshold | L_stop | 1000 | mm | FDS | Stop P1 pump when above |

### Timing Characteristics

| Component | Parameter | Value | Units | Notes |
|-----------|-----------|-------|-------|-------|
| Scan cycle | dt | 100 | ms | PLC scan interval |
| Valve delay | τ_valve | 0.5 | s | Cmd → status (5 cycles) |
| Sensor lag | τ_sensor | 0 | s | Level sensor assumed instantaneous |

### Discretization

- **Integration method**: Forward Euler
- **Timestep**: 100 ms (matches PLC scan)
- **Stability**: Unconditionally stable for tank dynamics

---

## Control Interface

### Inputs (Commands from Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| UF_UFFT_Tank_Valve | bool | - | - | UF tank inlet valve command |
| UF_Drain_Valve | bool | - | - | Drain valve command |
| UF_ROFT_Valve | bool | - | - | RO feed tank outlet valve command |
| UF_BWP_Valve | bool | - | - | Backwash permeate valve command |

### Outputs (Sensors/Status to Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| UF_UFFT_Tank_Level | real | [0, 1200] | mm | UF feed tank level |
| UF_UFFT_Tank_Valve_Sts | bool | - | - | Inlet valve actual position |
| UF_Drain_Valve_Sts | bool | - | - | Drain valve actual position |
| UF_ROFT_Valve_Sts | bool | - | - | ROFT valve actual position |
| UF_BWP_Valve_Sts | bool | - | - | BWP valve actual position |

### Control Logic Summary

The UFFT tank level controls the P1 pump (in RUNNING state):

1. **Low level (L ≤ 800 mm)**:
   - Open P1 process valve (RW_Tank_P_Valve)
   - Start P1 pump (RW_Pump_Start)
   - Tank fills from P1 discharge

2. **High level (L ≥ 1000 mm)**:
   - Close P1 process valve
   - Stop P1 pump
   - Tank drains through outlet valves

3. **Valve control**:
   - UFFT inlet valve: Typically follows P valve state
   - Drain/ROFT/BWP valves: Manual or controlled by downstream logic (not in UC1)

---

## Validation Criteria

### Invariants

#### Range Bounds
| Tag | Min | Max | Violation Indicates |
|-----|-----|-----|---------------------|
| UF_UFFT_Tank_Level | 0 | 1200 | Sensor failure or spoofing |

#### Causality Rules
| Rule | Condition | Expected | Window |
|------|-----------|----------|--------|
| ufft-valve-cmd-response | UFFT_Valve = true | UFFT_Valve_Sts = true | 0.3-0.7 s |
| drain-valve-cmd-response | Drain_Valve = true | Drain_Valve_Sts = true | 0.3-0.7 s |
| roft-valve-cmd-response | ROFT_Valve = true | ROFT_Valve_Sts = true | 0.3-0.7 s |
| bwp-valve-cmd-response | BWP_Valve = true | BWP_Valve_Sts = true | 0.3-0.7 s |

#### Correlation Rules
| Rule | Condition Tag | Check Tag | Check Op | Check Value |
|------|--------------|-----------|----------|-------------|
| p1-pump-fills-uf | RW_Pump_Sts = true AND RW_Tank_P_Valve_Sts = true | dUF_Level/dt | > | 0 |
| drain-open-drains | UF_Drain_Valve_Sts = true | dUF_Level/dt | < | 0 |
| roft-open-drains | UF_ROFT_Valve_Sts = true | dUF_Level/dt | < | 0 |

#### Rate-of-Change Limits
| Tag | Max Delta/Tick | Physical Basis |
|-----|----------------|----------------|
| UF_UFFT_Tank_Level | 50 mm | Max fill/drain rate at dt=100ms |

### Acceptance Metrics

| Metric | Target | Tolerance | Test Scenario |
|--------|--------|-----------|---------------|
| Level maintained in band | [800, 1000] mm | ±50 mm | `nominal_operation` |
| Pump starts at low level | Start when L ≤ 800 | ±10 mm | `level_control` |
| Pump stops at high level | Stop when L ≥ 1000 | ±10 mm | `level_control` |
| Valve delay | 500 ms nominal | ±200 ms | `valve_timing` |

### Test Scenarios

| Scenario | Purpose | Key Assertions |
|----------|---------|----------------|
| `nominal_startup` | Verify level control | UF tank fills when P1 pump runs, level stabilizes |
| `level_control` | Verify pump start/stop thresholds | Pump starts at 800 mm, stops at 1000 mm |
| `drain_operation` | Verify drain valve behavior | Level decreases when drain valve open |
| `valve_timing` | Verify valve delays | Status follows command with ~500 ms delay |

---

## Real-World Grounding

### Source Attribution

| Element | Source | Notes |
|---------|--------|-------|
| Tag names, wiring | RoviSys FDS (USC24A-FDS-001 Rev B) | Canonical tag naming |
| Component topology | RoviSys FDS, Section 4.5.1 | P&ID diagram |
| Tank mass balance | SPHERE implementation | Standard conservation of mass |
| Drain/ROFT flow rate (30 L/min) | SPHERE estimate | **Research needed** |
| Pump start/stop thresholds (800/1000 mm) | SPHERE implementation | **Research needed** |
| Valve timing (τ = 500ms) | SPHERE estimate | **Research needed** |

### Research-Grounded Parameter Ranges

The following table compares SPHERE simulation parameters with publicly-documented values from UF vendor manuals, EPA membrane filtration guidance, and drinking-water module datasheets.

| Parameter | SPHERE Value | Research Range | Recommended Default | Status |
|-----------|-------------|----------------|---------------------|--------|
| Tank max level | 1200 mm | 500–1500 mm normal band | 800 mm band | SPHERE reasonable |
| Tank cross-section | (implicit) | 0.5–12 m² | 6 m² | Research complete |
| Drain/ROFT flow | 30 L/min | Varies by membrane area | Flux × Area | SPHERE estimate |
| Pump start threshold | 800 mm | (operational choice) | - | Site-specific |
| Pump stop threshold | 1000 mm | (operational choice) | - | Site-specific |
| Valve delay | 500 ms | 4–180 s (motorized) | 30 s | SPHERE simulates solenoid |
| Membrane flux | (not modeled) | 40–140 LMH | 70 LMH | Research complete |
| Backwash interval | (not modeled) | 15–60 min | 30 min | Research complete |
| Backwash duration | (not modeled) | 30–120 s | 60 s | Research complete |
| Backwash flux | (not modeled) | 90–230 LMH | 150 LMH | Research complete |

**Unit conversion notes**:
- LMH = L/m²·h (liters per square meter per hour)
- For a 64 m² module at 70 LMH flux: permeate flow = 64 × 70 / 60 = 74.7 L/min
- For backwash at 150 LMH: backwash flow = 64 × 150 / 60 = 160 L/min

**Tank sizing calculation** (from research):
- Minimum backwash volume = Q_BW × t_BW = (14.7 m³/h) × (60 s / 3600) = 0.245 m³ per step
- For top+bottom backwash: ~0.5 m³ per event per module
- Recommended tank usable volume: ≥1 backwash cycle + margin → 4.8 m³ (6 m² × 0.8 m)

**Sources**: EPA Membrane Filtration Guidance Manual (15–60 min backwash interval), DOW/DuPont IntegraTec UF manuals (40–90 LMH ordinary, 230 LMH backwash), ZeeWeed 1500-X datasheet (55.7 m² module), OLTRECAP UF technical manual (>90 LMH usually not suggested).

**Key findings**:
- SPHERE does not model membrane flux or backwash cycles (tank-only model)
- UF systems typically backwash every 15–60 minutes for 30–120 seconds
- Permeate/backwash tank must hold at least one backwash cycle volume plus safety margin

### Standards Reference

| Standard | Section | Relevance | Status |
|----------|---------|-----------|--------|
| AWWA B110 | Membrane Filtration | UF system requirements | Covered by research |
| EPA Membrane Filtration Guidance | LT2ESWTR | Backwash timing, productivity | **Consulted** |
| DuPont IntegraTec Manual | Process Design | Flux, backwash parameters | **Consulted** |
| DOW UF Product Manual | Operation | Backwash 20–60 min, 40–120 s | **Consulted** |

### Implementation Reference

- **FDS**: USC24A-FDS-001 Rev B — provides tag names and wiring only
- **I/O List**: USC24A-IOL-001 — Modbus/CIP address mapping
- **P&ID**: FDS Section 4.5.1 (page 18) — shows UF tank, drain, ROFT, BWP valves
- **PLC Implementation**: `simulator_final.st` lines 372-382 — tank physics; `controller_final.st` lines 225-233 — pump control

### Validation Data Source

- [x] Synthetic (simulated only)
- [ ] Literature values (research needed)
- [ ] Field data (none available)

---

## Appendix

### PLC Implementation Details

**Controller** (`controller_final.st`):
- UDT: `P3_UDT` (lines 34-44)
- Level-based pump control: Lines 225-233 (Raw_water_pump rung)
- Permissive check: Line 237 (`P1_SYS.Permissives[1] := UF_Level < 1000`)
- Valve wiring: Lines 203-206 (valve commands to outputs)
- Modbus mapping: Coils 48-51 for valve commands

**Simulator** (`simulator_final.st`):
- Tank physics (inflow): Lines 372-374
- Tank physics (drain outflow): Lines 375-377
- Tank physics (ROFT outflow): Lines 378-380
- Valve delays: Lines 216-297 (UF, drain, ROFT, BWP valves)
- Constants: Line 77 (UF_DRAIN_RATE = 30 L/min), Line 81 (UF_TANK_MAX = 1200)

### Tag Mapping

| Tag Contract Name | Controller Modbus | Simulator Modbus |
|-------------------|-------------------|------------------|
| UF_UFFT_Tank_Level | HR 305 (input) | QW 305 (output) |
| UF_UFFT_Tank_Valve | Coil 48 | QW 208 |
| UF_Drain_Valve | Coil 49 | QW 209 |
| UF_ROFT_Valve | Coil 50 | QW 210 |
| UF_BWP_Valve | Coil 51 | QW 211 |
| UF_UFFT_Tank_Valve_Sts | HR 328 (input) | QW 328 (output) |
| UF_Drain_Valve_Sts | HR 329 (input) | QW 329 (output) |
| UF_ROFT_Valve_Sts | HR 330 (input) | QW 330 (output) |
| UF_BWP_Valve_Sts | HR 331 (input) | QW 331 (output) |

### Model Limitations

1. **No membrane pressure modeling**: Only level tracked, not transmembrane pressure
2. **No backwash cycle**: BWP valve exists but no automatic backwash logic
3. **No fouling model**: Membrane permeability assumed constant
4. **No permeate quality**: No turbidity or particle count modeling

### Future Enhancements (UC2+)

- Add transmembrane pressure (TMP) measurement
- Implement automatic backwash cycle based on TMP or timer
- Add permeate turbidity sensor and quality alarms
- Model membrane fouling and cleaning effectiveness
- Add connection to P5 (Reverse Osmosis)

### Related Documents

- [WT-P1: Raw Water Intake](wt-p1-raw-water.md) - Upstream water source (feeds this tank)
- [WT-P2: Chemical Treatment](wt-p2-chemical-treatment.md) - Chemical dosing (inline)
- [WT-P5: Reverse Osmosis](wt-p5-reverse-osmosis.md) (planned) - Downstream treatment
- [System State Machine](wt-system-state.md) - System-wide state transitions

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-02 | SPHERE Team | Initial release from FDS + PLC code analysis |
| 1.1 | 2026-02 | SPHERE Team | Added research-grounded parameter ranges from public sources |
