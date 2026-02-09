# Process Model: Raw Water Intake

## Overview

| Field | Value |
|-------|-------|
| **Domain** | Water Treatment |
| **Process ID** | WT-P1 |
| **Status** | Implemented |
| **Real-world reference** | USC24A-FDS-001 Rev B (RoviSys FDS) |

### Description

The Raw Water Intake process (P1) receives untreated water from an external source and stores it in the Raw Water (RW) tank. A variable-speed pump transfers water downstream to the Ultrafiltration Feed Tank (P3) through a process valve. The tank level is maintained between configurable setpoints by automatic control of the inlet (PR) valve and outlet pump.

This is the entry point for all water entering the treatment plant. The process implements protective interlocks to prevent pump dry-run (low-low level) and tank overflow (high-high level).

### Components

- **RW Tank**: Raw water storage tank (1500 mm max level)
- **RW Pump**: Variable-frequency drive (VFD) pump, 0-100% speed, 120 L/min max flow
- **PR Valve**: Pressure relief / inlet valve from external source
- **P6B Valve**: Secondary inlet valve (backup/bypass)
- **P Valve**: Process outlet valve to UF system

### Process Diagram Reference

- P&ID: `assets/diagrams/water-treatment-p1.yaml`
- Slice: `slices/wt-uc1-slice.yaml`

---

## State Variables

| Variable | Symbol | Units | Range | Initial | Description |
|----------|--------|-------|-------|---------|-------------|
| Tank level | L_rw | mm | [0, 1500] | 600 | Raw water tank level |
| Pump flow | Q_pump | L/min | [0, 120] | 0 | Current pump discharge flow |
| Pump running | pump_on | bool | - | false | Pump motor running state |
| PR valve open | v_pr | bool | - | false | Inlet valve actual position |
| P6B valve open | v_p6b | bool | - | false | Secondary inlet valve position |
| P valve open | v_p | bool | - | false | Process outlet valve position |

---

## Dynamic Model

### Governing Equations

**Tank mass balance:**

```
dL_rw/dt = (Q_in - Q_out) * (1000 / A_tank)
```

where:
- `L_rw` = tank level [mm]
- `Q_in` = inflow rate [L/min] = Q_pr when PR valve open, else 0
- `Q_out` = outflow rate [L/min] = Q_pump when pump running AND P valve open, else 0
- `A_tank` = tank cross-sectional area [m²]
- Factor `1000` converts from m to mm

**Discretized form (Forward Euler, dt = 100 ms):**

```
L_rw[k+1] = L_rw[k] + (Q_in - Q_out) * (dt / 60) * (1000 / A_tank)
```

For the implemented simulator with implicit tank area normalization:

```
L_rw[k+1] = L_rw[k] + (Q_in - Q_out) * (dt / 60)
         = L_rw[k] + (Q_in - Q_out) * (0.1 / 60)
         = L_rw[k] + (Q_in - Q_out) * 0.00167
```

**Pump flow model:**

```
Q_pump = (pump_speed / 100) * Q_max    when pump_on = true
Q_pump = 0                              when pump_on = false
```

where:
- `pump_speed` = commanded speed [%]
- `Q_max` = maximum flow at 100% speed = 120 L/min

**Valve delay model:**

Valves transition between open/closed with a discrete delay:

```
if cmd = OPEN and valve = CLOSED:
    timer := timer + 1
    if timer >= VALVE_DELAY:
        valve := OPEN
        timer := 0
```

Same logic applies for OPEN → CLOSED transitions.

**Pump delay model:**

Pump start/stop has a longer delay than valves:

```
if (start_cmd AND NOT stop_cmd) AND NOT pump_on:
    timer := timer + 1
    if timer >= PUMP_DELAY:
        pump_on := true
        timer := 0
```

### Parameters

| Parameter | Symbol | Value | Units | Source | Notes |
|-----------|--------|-------|-------|--------|-------|
| Max tank level | L_max | 1500 | mm | FDS | Physical tank height |
| Min tank level | L_min | 0 | mm | - | Empty tank |
| Max pump flow | Q_max | 120 | L/min | FDS | At 100% speed |
| External inflow rate | Q_pr | 50 | L/min | Estimated | PR valve fully open |
| Valve delay | τ_valve | 500 | ms | FDS | 5 cycles × 100 ms |
| Pump delay | τ_pump | 800 | ms | FDS | 8 cycles × 100 ms |
| Initial level | L_0 | 600 | mm | - | Mid-tank startup |

### Timing Characteristics

| Component | Parameter | Value | Units | Notes |
|-----------|-----------|-------|-------|-------|
| Scan cycle | dt | 100 | ms | PLC scan interval |
| Valve delay | τ_valve | 0.5 | s | Cmd → status (5 cycles) |
| Pump ramp | τ_pump | 0.8 | s | Start/stop delay (8 cycles) |
| Sensor lag | τ_sensor | 0 | s | Level sensor assumed instantaneous |

### Discretization

- **Integration method**: Forward Euler
- **Timestep**: 100 ms (matches PLC scan)
- **Stability**: Unconditionally stable for tank dynamics (no feedback in physics model)

---

## Control Interface

### Inputs (Commands from Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| RW_Tank_PR_Valve | bool | - | - | Inlet valve command (true = open) |
| RW_Tank_P6B_Valve | bool | - | - | Secondary inlet valve command |
| RW_Tank_P_Valve | bool | - | - | Process outlet valve command |
| RW_Pump_Start | bool | - | - | Pump start command |
| RW_Pump_Stop | bool | - | - | Pump stop command |
| RW_Pump_Speed | real | [0, 100] | % | Pump speed setpoint |

### Outputs (Sensors/Status to Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| RW_Tank_Level | real | [0, 1200] | mm | Tank level (clamped for alarm range) |
| RW_Pump_Flow | real | [0, 120] | L/min | Pump discharge flow |
| RW_Tank_PR_Valve_Sts | bool | - | - | Inlet valve actual position |
| RW_Tank_P6B_Valve_Sts | bool | - | - | Secondary inlet valve position |
| RW_Tank_P_Valve_Sts | bool | - | - | Process outlet valve position |
| RW_Pump_Sts | bool | - | - | Pump running status |
| RW_Pump_Fault | bool | - | - | Pump fault indicator |

### Control Logic Summary

The controller implements the following automatic control in RUNNING state:

1. **Level control (inlet):**
   - If `RW_Tank_Level ≤ 500 mm` (L alarm): Open PR valve
   - If `RW_Tank_Level ≥ 800 mm` (H alarm): Close PR valve

2. **Pump control (outlet to UF):**
   - If `UF_UFFT_Tank_Level ≤ 800 mm`: Start pump, open P valve
   - If `UF_UFFT_Tank_Level ≥ 1000 mm`: Stop pump, close P valve

3. **Protective interlocks:**
   - If `RW_Tank_Level ≤ 250 mm` (LL alarm): Stop pump (dry-run protection)

---

## Validation Criteria

### Invariants

#### Range Bounds
| Tag | Min | Max | Violation Indicates |
|-----|-----|-----|---------------------|
| RW_Tank_Level | 0 | 1200 | Sensor failure or spoofing |
| RW_Pump_Speed | 0 | 100 | Command injection |
| RW_Pump_Flow | 0 | 120 | Sensor spoofing |

#### Causality Rules
| Rule | Condition | Expected | Window |
|------|-----------|----------|--------|
| valve-cmd-response | PR_Valve = true | PR_Valve_Sts = true | 0.3-0.7 s |
| pump-start-response | Pump_Start = true | Pump_Sts = true | 0.5-1.2 s |
| pump-stop-response | Pump_Stop = true | Pump_Sts = false | 0.5-1.2 s |

#### Correlation Rules
| Rule | Condition Tag | Check Tag | Check Op | Check Value |
|------|--------------|-----------|----------|-------------|
| pump-on-implies-speed | RW_Pump_Sts = true | RW_Pump_Speed | > | 0 |
| pump-off-implies-no-flow | RW_Pump_Sts = false | RW_Pump_Flow | <= | 0.1 |

#### Rate-of-Change Limits
| Tag | Max Delta/Tick | Physical Basis |
|-----|----------------|----------------|
| RW_Tank_Level | 50 mm | Max fill/drain rate at dt=100ms |

### Acceptance Metrics

| Metric | Target | Tolerance | Test Scenario |
|--------|--------|-----------|---------------|
| Level tracks setpoint | Steady within [500, 800] | ±50 mm | `nominal_startup` |
| Pump responds to cmd | Flow > 0 within 1.5s | ±0.3s | `nominal_startup` |
| LL alarm stops pump | Pump stops at L ≤ 250 | 0 miss | `low_level_protection` |
| Valve delay | 500 ms nominal | ±200 ms | `valve_timing` |

### Test Scenarios

| Scenario | Purpose | Key Assertions |
|----------|---------|----------------|
| `nominal_startup` | Verify startup sequence | State transitions IDLE→START→RUNNING, pump starts when UF tank low |
| `nominal_shutdown` | Verify shutdown sequence | State transitions to SHUTDOWN, pump stops |
| `low_level_protection` | Verify LL interlock | Pump stops when RW level hits 250 mm |
| `high_level_control` | Verify inlet valve control | PR valve closes at 800 mm, opens at 500 mm |
| `pump_fault_injection` | Verify fault detection | Pump_Fault tag set, flow drops to 0 |

---

## Real-World Grounding

### Source Attribution

| Element | Source | Notes |
|---------|--------|-------|
| Tag names, wiring | RoviSys FDS (USC24A-FDS-001 Rev B) | Canonical tag naming |
| Component topology | RoviSys FDS, Section 4.5.1 | P&ID diagram |
| Tank mass balance equations | SPHERE implementation | Standard conservation of mass |
| Flow rates (Q_max, Q_pr) | SPHERE estimate | **Research needed** |
| Valve/pump timing (τ) | SPHERE estimate | **Research needed** |
| Alarm thresholds | SPHERE implementation | **Research needed** |
| Control logic | SPHERE implementation | State machine, level control |

### Research-Grounded Parameter Ranges

The following table compares SPHERE simulation parameters with publicly-documented values from state drinking-water design manuals, vendor datasheets, and engineering references.

| Parameter | SPHERE Value | Research Range | Recommended Default | Status |
|-----------|-------------|----------------|---------------------|--------|
| Tank cross-section area | (implicit) | 8–60 m² (small-system) | 12 m² | Research complete |
| Pump max flow (Q_max) | 120 L/min | 10–800 gpm (0.63–50 L/s) | 150 gpm (9.46 L/s = 567 L/min) | SPHERE value conservative |
| Valve actuation delay | 500 ms | 4–180 s (motorized ball) | 30 s | SPHERE simulates fast |
| Pump spinup lag | 800 ms | 1–3 s (to min speed) | 2 s | SPHERE value reasonable |
| VFD accel time | (not modeled) | 0–360 s (to base speed) | 10 s | Research complete |
| Sensor lag (level) | 0 s | 0.1–999 s (configurable τ) | 5 s | SPHERE assumes ideal |
| Alarm LL | 250 mm (17%) | 5–15% of span | 10% (150 mm at 1500 mm span) | Comparable |
| Alarm L | 500 mm (33%) | 10–30% of span | 20% (300 mm) | SPHERE slightly high |
| Alarm H | 800 mm (53%) | 70–90% of span | 80% (1200 mm) | SPHERE low |
| Alarm HH | 1200 mm (80%) | 90–98% of span | 95% (1425 mm) | SPHERE low |

**Sources**: USACE EM 1110‑2‑503 (small systems ≤100,000 gpd), Washington DOH Pub 331-620, AUMA/Emerson/Bray actuator datasheets, ABB ACQ580 drive guide, VEGA/Endress+Hauser sensor manuals.

**Key findings**:
- SPHERE's 500 ms valve delay is appropriate for **solenoid valves** but unrealistic for motorized ball/butterfly valves (typically 30+ seconds)
- Alarm bands in SPHERE are compressed compared to industry practice; real systems place HH close to overflow (95%+)
- Pump flow rates are within range but toward the lower end

### Standards Reference

| Standard | Section | Relevance | Status |
|----------|---------|-----------|--------|
| AWWA M36 | Ch. 3 | Tank level measurement standards | Covered by research |
| AWWA G200 | Distribution pumping | Pump sizing and VFD control | Covered by research |
| USACE EM 1110-2-503 | Small systems | Pump/storage sizing | **Consulted** |
| Washington DOH Pub 331-620 | Monitoring | Tank sizing examples | **Consulted** |

### Implementation Reference

- **FDS**: USC24A-FDS-001 Rev B — provides tag names and wiring only, not control logic or physics
- **I/O List**: USC24A-IOL-001 — Modbus/CIP address mapping
- **P&ID**: FDS Section 4.5.1 (page 18) — component topology
- **PLC Implementation**: `controller_final.st`, `simulator_final.st` — actual control logic and physics

### Validation Data Source

- [x] Synthetic (simulated only)
- [ ] Literature values (research needed)
- [ ] Field data (none available)

---

## Appendix

### PLC Implementation Details

**Controller** (`controller_final.st`):
- UDT: `P1_UDT` (lines 8-22)
- Control logic: `Raw_water_control` (lines 214-222), `Raw_water_pump` (lines 224-233)
- Modbus mapping: Coils 40-44 for valve/pump commands, HR 100 for pump speed

**Simulator** (`simulator_final.st`):
- Physics: Lines 332-343 (tank mass balance)
- Valve delays: Lines 89-150 (PR, P6B, P valves)
- Pump delay: Lines 302-318
- Constants: Lines 73-83

### Tag Mapping

| Tag Contract Name | Controller Modbus | Simulator Modbus |
|-------------------|-------------------|------------------|
| RW_Tank_Level | HR 300 (input) | QW 300 (output) |
| RW_Pump_Flow | HR 301 (input) | QW 301 (output) |
| RW_Pump_Speed | HR 100 (output) | QW 220 (input) |
| RW_Tank_PR_Valve | Coil 40 | QW 200 |
| RW_Tank_P6B_Valve | Coil 41 | QW 201 |
| RW_Tank_P_Valve | Coil 42 | QW 202 |
| RW_Pump_Start | Coil 43 | QW 203 |
| RW_Pump_Stop | Coil 44 | QW 204 |

### Related Documents

- [WT-P2: Chemical Treatment](wt-p2-chemical-treatment.md) - Downstream chemical dosing
- [WT-P3: Ultrafiltration](wt-p3-ultrafiltration.md) - Downstream filtration (receives P1 output)
- [System State Machine](wt-system-state.md) - IDLE/START/RUNNING/SHUTDOWN transitions

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-02 | SPHERE Team | Initial release from FDS + PLC code analysis |
| 1.1 | 2026-02 | SPHERE Team | Added research-grounded parameter ranges from public sources |
