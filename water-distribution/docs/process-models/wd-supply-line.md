# Process Model: Supply Line

## Overview

| Field | Value |
|-------|-------|
| **Domain** | Water Distribution |
| **Process ID** | WD-Supply |
| **Status** | Blueprint (synthetic runs, no PLC) |
| **Real-world reference** | AWWA M32, EPA EPANET |

### Description

The Supply Line process provides treated water from the treatment plant to the distribution grid. It consists of:

1. **Supply Tank**: Clearwell receiving treated water from the treatment plant
2. **Chemical Dosing**: Secondary disinfection (NaOCl) and chloramine formation (NH4Cl) for distribution residual
3. **Supply Pump**: VFD-controlled pump to pressurize the distribution system
4. **Mixer**: Tank mixer to ensure chemical homogeneity

The supply pump maintains pressure in the distribution grid, controlled by tank level or downstream pressure feedback.

### Components

- **Supply Tank**: Treated water clearwell (1500 mm max level)
- **Supply Pump**: VFD pump, 0-100% speed, up to 200 L/min
- **Supply Tank Valve**: Outlet isolation valve
- **NaOCl Tank**: Secondary chlorination chemical storage (1000 mm)
- **NH4Cl Tank**: Ammonia for chloramine formation (1000 mm)
- **Mixer**: Tank mixer for chemical distribution

### Process Diagram Reference

- P&ID: `assets/diagrams/water-distribution.yaml`
- Slice: `slices/wd-uc0-slice.yaml`

---

## State Variables

| Variable | Symbol | Units | Range | Initial | Description |
|----------|--------|-------|-------|---------|-------------|
| Supply tank level | L_supply | mm | [0, 1500] | 1000 | Supply tank level |
| Pump flow | Q_pump | L/min | [0, 200] | 0 | Supply pump discharge flow |
| Pump running | pump_on | bool | - | false | Pump motor running state |
| NaOCl level | L_naocl | mm | [0, 1000] | 800 | NaOCl dosing tank level |
| NH4Cl level | L_nh4cl | mm | [0, 1000] | 800 | NH4Cl dosing tank level |
| Outlet valve open | v_outlet | bool | - | false | Supply tank outlet valve |
| Mixer running | mixer_on | bool | - | false | Tank mixer running state |

---

## Dynamic Model

### Governing Equations

**Tank mass balance:**

```
dL_supply/dt = (Q_in - Q_out) * (1000 / A_tank)
```

where:
- `L_supply` = supply tank level [mm]
- `Q_in` = inflow from treatment plant [L/min] (assumed constant or externally controlled)
- `Q_out` = pump discharge [L/min] when pump running and valve open
- `A_tank` = tank cross-sectional area [m²]

**Pump flow model:**

```
Q_pump = (pump_speed / 100) * Q_max    when pump_on = true
Q_pump = 0                              when pump_on = false
```

where:
- `pump_speed` = commanded speed [%]
- `Q_max` = maximum flow at 100% speed = 200 L/min

**Chemical tank drain:**

```
dL_chem/dt = -Q_dose / A_tank    when dosing active
```

### Parameters

| Parameter | Symbol | Value | Units | Source | Notes |
|-----------|--------|-------|-------|--------|-------|
| Max tank level | L_max | 1500 | mm | Estimated | Supply tank capacity |
| Max pump flow | Q_max | 200 | L/min | Estimated | At 100% speed |
| Valve delay | τ_valve | 500 | ms | Standard | Matches WT timing |
| Pump delay | τ_pump | 800 | ms | Standard | Matches WT timing |

### Timing Characteristics

| Component | Parameter | Value | Units | Notes |
|-----------|-----------|-------|-------|-------|
| Scan cycle | dt | 100 | ms | Standard PLC scan |
| Valve delay | τ_valve | 0.5 | s | Estimated |
| Pump ramp | τ_pump | 0.8 | s | Estimated |

---

## Control Interface

### Inputs (Commands from Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| Supply_Pump_Speed | real | [0, 100] | % | Pump speed setpoint |
| Supply_Tank_Valve | bool | - | - | Outlet valve command |

### Outputs (Sensors/Status to Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| Supply_Tank_Level | real | [0, 1500] | mm | Supply tank level |
| Supply_Pump_Flow | real | [0, 200] | L/min | Pump discharge flow |
| Supply_Pump_Sts | bool | - | - | Pump running status |
| Supply_Mixer_Sts | bool | - | - | Mixer running status |
| Supply_Tank_Valve_Sts | bool | - | - | Outlet valve status |
| Supply_NaOCl_Level | real | [0, 1000] | mm | NaOCl tank level |
| Supply_NH4Cl_Level | real | [0, 1000] | mm | NH4Cl tank level |

### Control Logic Summary

Basic level-based control:
1. When supply tank level drops, pump starts to draw from treatment
2. When level is adequate, pump modulates to maintain grid pressure
3. Chemical dosing proportional to flow rate (future enhancement)

---

## Validation Criteria

### Invariants

#### Range Bounds
| Tag | Min | Max | Violation Indicates |
|-----|-----|-----|---------------------|
| Supply_Tank_Level | 0 | 1500 | Sensor failure or spoofing |
| Supply_Pump_Speed | 0 | 100 | Command injection |
| Supply_Pump_Flow | 0 | 200 | Sensor spoofing |

#### Correlation Rules
| Rule | Condition Tag | Check Tag | Check Op | Check Value |
|------|--------------|-----------|----------|-------------|
| pump-on-implies-flow | Supply_Pump_Sts = true | Supply_Pump_Flow | > | 0 |
| pump-off-no-flow | Supply_Pump_Sts = false | Supply_Pump_Flow | <= | 0.1 |

### Test Scenarios

| Scenario | Purpose | Key Assertions |
|----------|---------|----------------|
| `run-a-idle` | System idle state | Pump off, levels stable |
| `run-b-flow` | Normal flow | Pump running, flow > 0, levels change |

---

## Real-World Grounding

### Source Attribution

| Element | Source | Notes |
|---------|--------|-------|
| Tag names | RoviSys FDS (USC24A-FDS-001 Rev B) | Canonical tag naming |
| Component topology | RoviSys FDS, Section 4.5.2 | P&ID diagram (page 19) |
| Tank sizing | USACE EM 1110-2-503, Utah Admin Code R309-510-8 | 400 gal/connection equalization storage |
| Pump capacity | WV PWSDS, AWWA M32 | 100 gpm for ~100 connections |
| Valve timing | AUMA SA 07.1, Bray datasheets | 30-110s for motorized valves |
| Sensor response | VEGA/Siemens datasheets | 2-5s for level/flow transmitters |
| Chemical dosing | LMI metering pump catalogs | 1 GPH NaOCl, 0.5 GPH NH4Cl |

### Research-Grounded Parameters

#### Supply Tank
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Tank volume | 40,000 gal (151 m³) | 30,000-50,000 gal | Utah R309-510-8 (400 gal × 100 conn) |
| Cross-section area | 40 m² | 30-50 m² | Calculated (4m depth) |
| Max level | 1500 mm | 1000-2000 mm | Design estimate |

#### Supply Pump
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Max flow | 380 L/min (100 gpm) | 50-200 gpm | WV PWSDS Table 3.2 (100 homes = 100 gpm) |
| Spinup time | 2 s | 1-3 s | ABB VFD quick ramps guide |
| VFD ramp | 10 s | 0-360 s | Miami-Dade Water specs |

#### Motorized Valve
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Actuation time | 60 s | 30-110 s | Bray/AUMA quarter-turn valve datasheets |

#### Sensors
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Level sensor tau | 5 s | 2-999 s | VEGA ultrasonic (VEGASON) |
| Flow sensor tau | 2 s | 0.1-30 s | Siemens magmeter |
| Noise (level) | 2 mm | 1-5 mm | Typical transmitter accuracy |

#### Chemical Dosing
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| NaOCl dose rate | 0.063 L/min (1 GPH) | 1-10 GPH | LMI metering pump catalog |
| NH4Cl dose rate | 0.032 L/min (0.5 GPH) | 0.5-5 GPH | 1:4 Cl₂:NH₃ ratio |
| Day tank volume | 100 L | 50-200 L | Typical small-system sizing |

### Standards Reference

| Standard | Section | Relevance | Status |
|----------|---------|-----------|--------|
| USACE EM 1110-2-503 | Tables 1-1, 1-2 | Demand peaking, storage sizing | Consulted |
| Utah Admin Code R309-510-8 | Storage requirements | 400 gal/ERC equalization | Consulted |
| WV PWSDS | Table 3.2 | Peak design flows per home | Consulted |
| AUMA SA 07.1/16.1 | Datasheet | Valve actuation times | Consulted |
| ABB VFD Guide | Quick ramps | Pump acceleration times | Consulted |
| VEGA VEGASON | Datasheet | Level sensor response | Consulted |
| LMI Metering Pumps | Catalog | Chemical dosing rates | Consulted |

### Implementation Reference

- **FDS**: USC24A-FDS-001 Rev B — provides tag names and topology only
- **P&ID**: FDS Section 4.5.2 (page 19) — shows Supply_Tank, Supply_Pump, NaOCl/NH4Cl dosing
- **PLC Program**: Not implemented (synthetic runs only)

### Validation Data Source

- [x] Synthetic (generated by `genruns-wd`)
- [ ] Literature values (research needed)
- [ ] Field data (none available)

---

## Appendix

### Model Limitations

1. **No PLC implementation**: Tag contract exists, no running PLC
2. **Simplified dynamics**: No pressure modeling
3. **No demand modeling**: Consumer demand not simulated

### Related Documents

- [WD-Grid: Distribution Grid](wd-distribution-grid.md) - Downstream distribution
- [WD-RWS: Return Water](wd-return-water.md) - Return water recirculation

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-02 | SPHERE Team | Initial blueprint from tag contract |
