# Process Model: Return Water System

## Overview

| Field | Value |
|-------|-------|
| **Domain** | Water Distribution |
| **Process ID** | WD-RWS |
| **Status** | Blueprint (synthetic runs, no PLC) |
| **Real-world reference** | AWWA M32 (research needed) |

### Description

The Return Water System (RWS) collects and recirculates water from the distribution grid back to the treatment or supply system. This process:

1. Collects low-pressure or excess water from the distribution grid
2. Stores it in the RWS tank
3. Pumps it back to the supply or treatment system

RWS helps maintain system pressure, reduces water waste, and enables water quality management through recirculation.

### Components

- **RWS Tank**: Return water collection tank (1500 mm max level)
- **RWS Pump**: VFD pump for return water (0-100% speed)
- **RWS Valve**: Tank outlet valve

### Process Diagram Reference

- P&ID: `assets/diagrams/water-distribution.yaml`
- Slice: `slices/wd-uc0-slice.yaml`

---

## State Variables

| Variable | Symbol | Units | Range | Initial | Description |
|----------|--------|-------|-------|---------|-------------|
| RWS tank level | L_rws | mm | [0, 1500] | 500 | Return water tank level |
| Pump running | pump_on | bool | - | false | RWS pump running state |
| Outlet valve open | v_outlet | bool | - | false | RWS tank outlet valve |

---

## Dynamic Model

### Governing Equations

**Tank mass balance:**

```
dL_rws/dt = (Q_in - Q_out) * (1000 / A_tank)
```

where:
- `Q_in` = return flow from distribution grid
- `Q_out` = pump discharge when pump running and valve open

**Pump flow model:**

```
Q_pump = (pump_speed / 100) * Q_max    when pump_on = true
Q_pump = 0                              when pump_on = false
```

### Parameters

| Parameter | Symbol | Value | Units | Source | Notes |
|-----------|--------|-------|-------|--------|-------|
| Max tank level | L_max | 1500 | mm | Estimated | Research needed |
| Valve delay | τ_valve | 500 | ms | Standard | Assumed |
| Pump delay | τ_pump | 800 | ms | Standard | Assumed |

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
| RWS_Pump_Speed | real | [0, 100] | % | Return pump speed setpoint |
| RWS_Tank_Valve | bool | - | - | Tank outlet valve command |

### Outputs (Sensors/Status to Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| RWS_Tank_Level | real | [0, 1500] | mm | Return water tank level |
| RWS_Pump_Sts | bool | - | - | Return pump running status |
| RWS_Tank_Valve_Sts | bool | - | - | Outlet valve status |

### Control Logic Summary

Basic level-based control:
1. When RWS tank level rises (return flow accumulating), pump starts
2. Pump returns water to supply system
3. Tank level drops, pump stops when low

---

## Validation Criteria

### Invariants

#### Range Bounds
| Tag | Min | Max | Violation Indicates |
|-----|-----|-----|---------------------|
| RWS_Tank_Level | 0 | 1500 | Sensor failure or spoofing |
| RWS_Pump_Speed | 0 | 100 | Command injection |

### Test Scenarios

| Scenario | Purpose | Key Assertions |
|----------|---------|----------------|
| `run-a-idle` | System idle | Pump off, level stable |
| `run-b-flow` | Normal flow | Pump cycles based on level |

---

## Real-World Grounding

### Source Attribution

| Element | Source | Notes |
|---------|--------|-------|
| Tag names | RoviSys FDS (USC24A-FDS-001 Rev B) | Canonical tag naming |
| Component topology | RoviSys FDS, Section 4.5.2 | P&ID diagram (page 19) |
| Return fraction | CT DEP, GBRA wastewater guidance | 60-90% of consumption |
| Tank sizing | Estimated from return flow | 200 gal buffer for 10 gpm pump |
| Pump sizing | Proportional to return fraction | 10 gpm (10% of supply) |

### Research-Grounded Parameters

#### Return Water Tank
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Tank volume | 200 gal (760 L) | 100-500 gal | Buffer for recirculation pump |
| Cross-section area | 0.3 m² | 0.1-0.5 m² | Calculated (2.5m depth) |
| Max level | 1500 mm | 1000-2000 mm | Design estimate |

#### Return Pump
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Max flow | 38 L/min (10 gpm) | 5-20 gpm | ~10% of supply pump capacity |
| Spinup time | 2 s | 1-3 s | ABB VFD quick ramps |
| VFD ramp | 10 s | 0-360 s | Standard VFD programming |

#### Return Flow Fraction
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Return fraction | 90% | 60-90% | CT DEP, Little East Lake WD |
| Notes | | | Outdoor irrigation reduces return in summer |

The return fraction represents the portion of potable water consumption that enters the sanitary sewer system. Values of 60-90% are documented in public wastewater planning guidance:
- **90%** is conservative for estimating sanitary flow (indoor-only consumption)
- **60%** accounts for significant outdoor/irrigation use
- The simulation uses 90% as a reasonable default for year-round average

#### Valve Timing
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Actuation time | 60 s | 30-110 s | AUMA motorized valve |

### Standards Reference

| Standard | Section | Relevance | Status |
|----------|---------|-----------|--------|
| CT DEP Planning | Wastewater | Return-to-sewer fractions | Consulted |
| GBRA/Caldwell | Wastewater flows | Potable-to-wastewater ratio | Consulted |
| Little East Lake WD | Usage estimate | 90% return assumption | Consulted |

**Note**: Return water systems vary significantly by utility. The parameters above are reasonable defaults for a simplified closed-loop mass balance model. Site-specific data should be used when available.

### Implementation Reference

- **FDS**: USC24A-FDS-001 Rev B — provides tag names only
- **P&ID**: FDS Section 4.5.2 (page 19) — shows Return_Tank, Return_Pump, Return_Mixer
- **PLC Program**: Not implemented

### Validation Data Source

- [x] Synthetic (generated by `genruns-wd`)
- [ ] Literature values (research needed)
- [ ] Field data (none available)

---

## Appendix

### Model Limitations

1. **Simplified dynamics**: No detailed hydraulics
2. **No water quality**: Residence time not modeled
3. **No source modeling**: Return flow source not specified

### Research Needed

- Typical return water system configurations
- Pump sizing for recirculation
- Control strategies for return systems

### Related Documents

- [WD-Supply: Supply Line](wd-supply-line.md) - Receives return water
- [WD-Grid: Distribution Grid](wd-distribution-grid.md) - Source of return water

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-02 | SPHERE Team | Initial blueprint from tag contract |
