# Process Model: Chemical Treatment

## Overview

| Field | Value |
|-------|-------|
| **Domain** | Water Treatment |
| **Process ID** | WT-P2 |
| **Status** | Implemented |
| **Real-world reference** | USC24A-FDS-001 Rev B (RoviSys FDS) |

### Description

The Chemical Treatment process (P2) manages the dosing of treatment chemicals into the water stream. Three chemical storage tanks (NaCl, NaOCl, HCl) feed into the treatment process via individual dosing valves. Chemical dosing is essential for:

- **NaCl (Sodium Chloride)**: Salt for regeneration of ion exchange systems
- **NaOCl (Sodium Hypochlorite)**: Primary disinfectant for pathogen control
- **HCl (Hydrochloric Acid)**: pH adjustment

In the current UC1 implementation, the chemical tanks are modeled as simple reservoirs that drain when their valves are open. No automatic dosing control is implemented - valve commands are manual or triggered by external logic.

### Components

- **NaCl Tank**: Sodium chloride storage tank (1000 mm max level)
- **NaOCl Tank**: Sodium hypochlorite storage tank (1000 mm max level)
- **HCl Tank**: Hydrochloric acid storage tank (1000 mm max level)
- **NaCl Valve**: Dosing valve for NaCl injection
- **NaOCl Valve**: Dosing valve for NaOCl injection
- **HCl Valve**: Dosing valve for HCl injection

### Process Diagram Reference

- P&ID: `assets/diagrams/water-treatment-p2.yaml`
- Slice: `slices/wt-uc1-slice.yaml`

---

## State Variables

| Variable | Symbol | Units | Range | Initial | Description |
|----------|--------|-------|-------|---------|-------------|
| NaCl level | L_nacl | mm | [0, 1000] | 800 | NaCl tank level |
| NaOCl level | L_naocl | mm | [0, 1000] | 800 | NaOCl tank level |
| HCl level | L_hcl | mm | [0, 1000] | 800 | HCl tank level |
| NaCl valve open | v_nacl | bool | - | false | NaCl dosing valve position |
| NaOCl valve open | v_naocl | bool | - | false | NaOCl dosing valve position |
| HCl valve open | v_hcl | bool | - | false | HCl dosing valve position |

---

## Dynamic Model

### Governing Equations

**Tank drain model (no inflow):**

Each chemical tank drains at a fixed rate when its valve is open:

```
dL/dt = -Q_dose / A_tank    when valve = OPEN
dL/dt = 0                    when valve = CLOSED
```

where:
- `L` = tank level [mm]
- `Q_dose` = dosing flow rate [L/min]
- `A_tank` = tank cross-sectional area [m²]

**Discretized form (Forward Euler, dt = 100 ms):**

For the implemented simulator with implicit tank area normalization:

```
L[k+1] = L[k] - Q_dose * (dt / 60)    when valve open
       = L[k] - 5.0 * (0.1 / 60)
       = L[k] - 0.00833
```

**Saturation:**

```
L = max(0, min(L, L_max))
```

Tanks cannot go below 0 (empty) or above maximum capacity.

**Valve delay model:**

Same as P1 - valves transition with discrete delay:

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
| Max tank level | L_max | 1000 | mm | FDS | All chemical tanks |
| Dosing flow rate | Q_dose | 5 | L/min | Estimated | When valve fully open |
| Valve delay | τ_valve | 500 | ms | FDS | 5 cycles × 100 ms |
| Initial level | L_0 | 800 | mm | - | 80% full at startup |

### Timing Characteristics

| Component | Parameter | Value | Units | Notes |
|-----------|-----------|-------|-------|-------|
| Scan cycle | dt | 100 | ms | PLC scan interval |
| Valve delay | τ_valve | 0.5 | s | Cmd → status (5 cycles) |
| Sensor lag | τ_sensor | 0 | s | Level sensors assumed instantaneous |

### Discretization

- **Integration method**: Forward Euler
- **Timestep**: 100 ms (matches PLC scan)
- **Stability**: Unconditionally stable (drain-only model)

---

## Control Interface

### Inputs (Commands from Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| ChemTreat_NaCl_Valve | bool | - | - | NaCl dosing valve command |
| ChemTreat_NaOCl_Valve | bool | - | - | NaOCl dosing valve command |
| ChemTreat_HCl_Valve | bool | - | - | HCl dosing valve command |

### Outputs (Sensors/Status to Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| ChemTreat_NaCl_Level | real | [0, 1000] | mm | NaCl tank level |
| ChemTreat_NaOCl_Level | real | [0, 1000] | mm | NaOCl tank level |
| ChemTreat_HCl_Level | real | [0, 1000] | mm | HCl tank level |
| ChemTreat_NaCl_Valve_Sts | bool | - | - | NaCl valve actual position |
| ChemTreat_NaOCl_Valve_Sts | bool | - | - | NaOCl valve actual position |
| ChemTreat_HCl_Valve_Sts | bool | - | - | HCl valve actual position |

### Control Logic Summary

In UC1, the chemical dosing valves are **not automatically controlled**. The controller exposes them as manual commands. Future use cases may implement:

1. **Flow-proportional dosing**: Dose rate proportional to main flow rate
2. **pH feedback control**: HCl dosing based on downstream pH sensor
3. **Residual chlorine control**: NaOCl dosing based on chlorine analyzer

---

## Validation Criteria

### Invariants

#### Range Bounds
| Tag | Min | Max | Violation Indicates |
|-----|-----|-----|---------------------|
| ChemTreat_NaCl_Level | 0 | 1200 | Sensor failure or spoofing |
| ChemTreat_NaOCl_Level | 0 | 1200 | Sensor failure or spoofing |
| ChemTreat_HCl_Level | 0 | 1200 | Sensor failure or spoofing |

#### Causality Rules
| Rule | Condition | Expected | Window |
|------|-----------|----------|--------|
| nacl-valve-cmd-response | NaCl_Valve = true | NaCl_Valve_Sts = true | 0.3-0.7 s |
| naocl-valve-cmd-response | NaOCl_Valve = true | NaOCl_Valve_Sts = true | 0.3-0.7 s |
| hcl-valve-cmd-response | HCl_Valve = true | HCl_Valve_Sts = true | 0.3-0.7 s |

#### Correlation Rules
| Rule | Condition Tag | Check Tag | Check Op | Check Value |
|------|--------------|-----------|----------|-------------|
| nacl-valve-open-drains | NaCl_Valve_Sts = true | dNaCl_Level/dt | < | 0 |
| naocl-valve-open-drains | NaOCl_Valve_Sts = true | dNaOCl_Level/dt | < | 0 |
| hcl-valve-open-drains | HCl_Valve_Sts = true | dHCl_Level/dt | < | 0 |

#### Rate-of-Change Limits
| Tag | Max Delta/Tick | Physical Basis |
|-----|----------------|----------------|
| ChemTreat_NaCl_Level | 30 mm | Max drain rate at dt=100ms |
| ChemTreat_NaOCl_Level | 30 mm | Max drain rate at dt=100ms |
| ChemTreat_HCl_Level | 30 mm | Max drain rate at dt=100ms |

### Acceptance Metrics

| Metric | Target | Tolerance | Test Scenario |
|--------|--------|-----------|---------------|
| Level decreases when valve open | Monotonic decrease | ±1 mm noise | `chemical_dosing` |
| Level stable when valve closed | No change | ±0.5 mm | `idle` |
| Valve delay | 500 ms nominal | ±200 ms | `valve_timing` |

### Test Scenarios

| Scenario | Purpose | Key Assertions |
|----------|---------|----------------|
| `chemical_dosing` | Verify valve opens and tank drains | Level decreases monotonically when valve commanded |
| `low_chemical_level` | Verify low-level behavior | Tank stops draining at 0 mm (no negative levels) |
| `valve_timing` | Verify valve delay | Status follows command with ~500 ms delay |

---

## Real-World Grounding

### Source Attribution

| Element | Source | Notes |
|---------|--------|-------|
| Tag names, wiring | RoviSys FDS (USC24A-FDS-001 Rev B) | Canonical tag naming |
| Component topology | RoviSys FDS, Section 4.5.1 | P&ID diagram |
| Tank drain model | SPHERE implementation | Simple level depletion |
| Dosing rate (Q_dose = 5 L/min) | SPHERE estimate | **Research needed** |
| Valve timing (τ = 500ms) | SPHERE estimate | **Research needed** |

### Research-Grounded Parameter Ranges

The following table compares SPHERE simulation parameters with publicly-documented values from vendor datasheets, state operator training materials, and EPA guidance.

| Parameter | SPHERE Value | Research Range | Recommended Default | Status |
|-----------|-------------|----------------|---------------------|--------|
| NaOCl tank capacity | 1000 mm height | 26–1000 L (day tank) | 114 L (≈30 gal) | SPHERE uses height not volume |
| HCl tank capacity | 1000 mm height | 26–189 L (day tank) | 114 L (≈30 gal) | SPHERE uses height not volume |
| NaCl tank capacity | 1000 mm height | 19–568 L (brine tank) | 151 L (≈40 gal) | SPHERE uses height not volume |
| Dosing rate (Q_dose) | 5 L/min | 0.0025–30 L/h metering pumps | NaOCl: 3.8 L/h, HCl: 7.6 L/h | SPHERE value very high |
| Valve delay | 500 ms | 5–1400 ms (solenoid) | 50 ms | SPHERE reasonable |
| Chlorine residual target | (not modeled) | 0.2–1.0 mg/L distribution | 0.5 mg/L | Research complete |
| MRDL (max) | (not modeled) | 4.0 mg/L (regulatory) | 4.0 mg/L | Research complete |

**Unit conversion notes**:
- SPHERE models tank level in mm, not volume; real day tanks are typically 30-gallon class (≈114 L)
- Research default dosing: NaOCl = 0.00105 L/s (1 gph), HCl = 0.00211 L/s (2 gph)
- SPHERE's 5 L/min = 0.083 L/s is ~80× higher than typical metering pump rates

**Sources**: Pulsafeeder/Stenner/Blue-White metering pump catalogs (0.21–16.2 gph), ASCO/Bürkert solenoid valve specs (5–1400 ms), EPA Stage 1 DBPR (MRDL 4.0 mg/L), Ten States Standards (0.2 mg/L minimum), California SWRCB continuous chlorination O&M guide.

**Key findings**:
- SPHERE's dosing rate of 5 L/min is unrealistically high for metering pumps (typical: 1–2 gph)
- Solenoid valve timing is appropriate (50 ms typical, up to 1.4 s for large pilot-operated)
- Chemical day tanks are commonly 30-gallon class for packaged systems

### Standards Reference

| Standard | Section | Relevance | Status |
|----------|---------|-----------|--------|
| AWWA B300 | Hypochlorites | NaOCl storage, dosing rates | Covered by research |
| EPA Stage 1 DBPR | MRDL | Maximum residual levels | **Consulted** |
| Ten States Standards | Distribution | Minimum 0.2 mg/L residual | **Consulted** |
| California SWRCB | Chlorination O&M | 0.2–1.0 mg/L targets | **Consulted** |

### Implementation Reference

- **FDS**: USC24A-FDS-001 Rev B — provides tag names and wiring only, not dosing logic
- **I/O List**: USC24A-IOL-001 — Modbus/CIP address mapping
- **P&ID**: FDS Section 4.5.1 (page 18) — shows NaCl, NaOCl, HCl tanks
- **PLC Implementation**: `simulator_final.st` lines 349-365 — tank drain physics

### Validation Data Source

- [x] Synthetic (simulated only)
- [ ] Literature values (research needed)
- [ ] Field data (none available)

---

## Appendix

### PLC Implementation Details

**Controller** (`controller_final.st`):
- UDT: `P2_UDT` (lines 23-33)
- Valve wiring: Lines 199-201 (valve commands to outputs)
- Modbus mapping: Coils 45-47 for valve commands

**Simulator** (`simulator_final.st`):
- Tank drain physics: Lines 349-365
- Valve delays: Lines 153-213 (NaCl, NaOCl, HCl valves)
- Constants: Line 76 (DOSING_RATE = 5.0 L/min), Line 82 (CHEM_TANK_MAX = 1000)

### Tag Mapping

| Tag Contract Name | Controller Modbus | Simulator Modbus |
|-------------------|-------------------|------------------|
| ChemTreat_NaCl_Level | HR 302 (input) | QW 302 (output) |
| ChemTreat_NaOCl_Level | HR 303 (input) | QW 303 (output) |
| ChemTreat_HCl_Level | HR 304 (input) | QW 304 (output) |
| ChemTreat_NaCl_Valve | Coil 45 | QW 205 |
| ChemTreat_NaOCl_Valve | Coil 46 | QW 206 |
| ChemTreat_HCl_Valve | Coil 47 | QW 207 |
| ChemTreat_NaCl_Valve_Sts | HR 325 (input) | QW 325 (output) |
| ChemTreat_NaOCl_Valve_Sts | HR 326 (input) | QW 326 (output) |
| ChemTreat_HCl_Valve_Sts | HR 327 (input) | QW 327 (output) |

### Model Limitations

1. **No inflow modeled**: Chemical tanks only drain, no refill simulation
2. **No concentration modeling**: Only level tracked, not chemical concentration
3. **No dosing control**: Valves are manual, no flow-proportional or feedback control
4. **No chemical interactions**: pH, chlorine residual not modeled in UC1

### Future Enhancements (UC2+)

- Add chemical concentration state variables
- Implement flow-proportional dosing logic
- Add pH sensor and feedback control for HCl
- Add chlorine analyzer and residual control for NaOCl
- Model chemical refill operations

### Related Documents

- [WT-P1: Raw Water Intake](wt-p1-raw-water.md) - Upstream water source
- [WT-P3: Ultrafiltration](wt-p3-ultrafiltration.md) - Downstream filtration (receives dosed water)
- [System State Machine](wt-system-state.md) - System-wide state transitions

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-02 | SPHERE Team | Initial release from FDS + PLC code analysis |
| 1.1 | 2026-02 | SPHERE Team | Added research-grounded parameter ranges from public sources |
