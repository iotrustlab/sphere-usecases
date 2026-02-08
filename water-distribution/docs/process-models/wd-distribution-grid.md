# Process Model: Distribution Grid

## Overview

| Field | Value |
|-------|-------|
| **Domain** | Water Distribution |
| **Process ID** | WD-Grid |
| **Status** | Blueprint (synthetic runs, no PLC) |
| **Real-world reference** | AWWA M32, EPA EPANET (research needed) |

### Description

The Distribution Grid process models the storage and delivery infrastructure between the supply system and consumers. It includes:

1. **Elevated Storage Tank**: Gravity-fed storage for pressure regulation and peak demand
2. **Consumer Storage Tank**: Local storage representing aggregate consumer demand

Water flows from the supply pump through the elevated tank (when valve open) and gravity-feeds to the consumer tank. The elevated tank provides pressure head and buffer capacity.

### Components

- **Elevated Tank**: Elevated storage tank (2000 mm max level)
- **Consumer Tank**: Ground-level consumer storage (2000 mm max level)
- **Elevated Valve**: Inlet valve to elevated tank

### Process Diagram Reference

- P&ID: `assets/diagrams/water-distribution.yaml`
- Slice: `slices/wd-uc0-slice.yaml`

---

## State Variables

| Variable | Symbol | Units | Range | Initial | Description |
|----------|--------|-------|-------|---------|-------------|
| Elevated tank level | L_elev | mm | [0, 2000] | 1500 | Elevated storage tank level |
| Consumer tank level | L_cons | mm | [0, 2000] | 1200 | Consumer storage tank level |
| Elevated valve open | v_elev | bool | - | false | Elevated tank inlet valve |

---

## Dynamic Model

### Governing Equations

**Elevated tank mass balance:**

```
dL_elev/dt = (Q_in - Q_out) * (1000 / A_tank)
```

where:
- `Q_in` = flow from supply pump (when elevated valve open)
- `Q_out` = gravity flow to consumer tank (proportional to head difference)

**Consumer tank mass balance:**

```
dL_cons/dt = (Q_in - Q_demand) * (1000 / A_tank)
```

where:
- `Q_in` = gravity flow from elevated tank
- `Q_demand` = consumer withdrawal (external demand profile)

**Note**: Detailed hydraulic modeling (head-flow relationships) requires EPANET-style calculations. Current implementation uses simplified flow rates.

### Parameters

| Parameter | Symbol | Value | Units | Source | Notes |
|-----------|--------|-------|-------|--------|-------|
| Elevated tank max | L_max_elev | 2000 | mm | Estimated | Research needed |
| Consumer tank max | L_max_cons | 2000 | mm | Estimated | Research needed |
| Valve delay | τ_valve | 500 | ms | Standard | Assumed |

### Timing Characteristics

| Component | Parameter | Value | Units | Notes |
|-----------|-----------|-------|-------|-------|
| Scan cycle | dt | 100 | ms | Standard PLC scan |
| Valve delay | τ_valve | 0.5 | s | Estimated |

---

## Control Interface

### Inputs (Commands from Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| Grid_Elev_Valve | bool | - | - | Elevated tank inlet valve command |

### Outputs (Sensors/Status to Controller)

| Tag | Type | Range | Units | Description |
|-----|------|-------|-------|-------------|
| Grid_Elev_Tank_Level | real | [0, 2000] | mm | Elevated tank level |
| Grid_Consum_Tank_Level | real | [0, 2000] | mm | Consumer tank level |
| Grid_Elev_Valve_Sts | bool | - | - | Elevated valve status |

### Control Logic Summary

Basic level-based control:
1. Open elevated valve when supply pump running to fill elevated tank
2. Consumer tank fills via gravity from elevated tank
3. Consumer demand draws down consumer tank

---

## Validation Criteria

### Invariants

#### Range Bounds
| Tag | Min | Max | Violation Indicates |
|-----|-----|-----|---------------------|
| Grid_Elev_Tank_Level | 0 | 2000 | Sensor failure or spoofing |
| Grid_Consum_Tank_Level | 0 | 2000 | Sensor failure or spoofing |

### Test Scenarios

| Scenario | Purpose | Key Assertions |
|----------|---------|----------------|
| `run-a-idle` | System idle | Levels stable |
| `run-b-flow` | Normal flow | Elevated fills, consumer draws |

---

## Real-World Grounding

### Source Attribution

| Element | Source | Notes |
|---------|--------|-------|
| Tag names | RoviSys FDS (USC24A-FDS-001 Rev B) | Canonical tag naming |
| Component topology | RoviSys FDS, Section 4.5.2 | P&ID diagram (page 19) |
| Elevated tank sizing | USACE EM 1110-2-503, Ten States Standards | 100,000 gal for ~100 connections |
| Consumer demand | WA DOH, USACE EM 1110-2-503 | 400 gpd/connection, MDD=2.0 |
| Diurnal pattern | EPA EPANET examples | 24-hour residential multipliers |
| Pressure requirements | Ten States Standards | 20-80 psi operating range |

### Research-Grounded Parameters

#### Elevated Storage Tank
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Tank volume | 100,000 gal (379 m³) | 50,000-200,000 gal | Ten States Standards (equalization) |
| Cross-section area | 60 m² | 40-80 m² | Calculated (6m water depth) |
| Water depth | 6 m (20 ft) | 5-10 m | Ten States (~25-30 ft level swing max) |
| Pressure head | 40-80 psi | 35-100 psi | Ten States Standards |

#### Consumer Storage Tank
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Tank volume | 10,000 gal (38 m³) | 5,000-20,000 gal | Zone buffer estimate |
| Cross-section area | 10 m² | 5-15 m² | Calculated (4m depth) |
| Water depth | 4 m | 3-5 m | Standard ground tank |

#### Consumer Demand
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Base demand | 400 gpd/connection | 150-1000 gpd | WA DOH, WV DHHR |
| MDD/ADD ratio | 2.0 | 1.35-4.2 | USACE EM 1110-2-503 |
| PHD/ADD ratio | 4.5 | 2.25-12.1 | USACE EM 1110-2-503 |
| Peak cluster flow | 100 gpm | 14-200 gpm | WV PWSDS (100 homes) |

#### Diurnal Pattern (EPANET-style)
| Hour | Multiplier | Hour | Multiplier |
|------|------------|------|------------|
| 00:00 | 0.5 | 12:00 | 1.1 |
| 06:00 | 1.0 | 18:00 | 1.4 |
| 08:00 | 1.3 | 22:00 | 0.8 |

#### Valve Timing
| Parameter | Value | Range | Source |
|-----------|-------|-------|--------|
| Actuation time | 60 s | 30-110 s | AUMA motorized valve |

### Standards Reference

| Standard | Section | Relevance | Status |
|----------|---------|-----------|--------|
| Ten States Standards | Ch. 8 | Storage requirements, pressure limits | Consulted |
| USACE EM 1110-2-503 | Table 2-1 | Demand peaking factors | Consulted |
| WA DOH Design Manual | Section 4 | Demand estimation, pressure | Consulted |
| EPA EPANET | Ch. 6 | Demand patterns | Consulted |
| WV PWSDS | Table 3.2 | Peak design flows | Consulted |

### Implementation Reference

- **FDS**: USC24A-FDS-001 Rev B — provides tag names only
- **P&ID**: FDS Section 4.5.2 (page 19) — shows PRMGrid_Elev_Tank, PRMGrid_Consum_Tank
- **PLC Program**: Not implemented

### Validation Data Source

- [x] Synthetic (generated by `genruns-wd`)
- [ ] Literature values (research needed)
- [ ] Field data (none available)

---

## Appendix

### Model Limitations

1. **Simplified hydraulics**: No pressure-flow relationships
2. **No demand profiles**: Consumer demand not modeled
3. **No water quality**: Residence time, chlorine decay not modeled

### Research Needed

- Typical elevated tank sizes and geometries
- Head-flow relationships for gravity distribution
- Consumer demand diurnal patterns
- Chlorine decay coefficients in distribution

### Related Documents

- [WD-Supply: Supply Line](wd-supply-line.md) - Upstream supply
- [WD-RWS: Return Water](wd-return-water.md) - Return water system

### Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-02 | SPHERE Team | Initial blueprint from tag contract |
