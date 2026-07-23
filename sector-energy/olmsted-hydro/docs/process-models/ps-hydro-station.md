# PS-1: Generic Hydro Station Process Model

## Overview

The generic hydro station model represents a conventional hydroelectric generating unit with the following major components:

```
Reservoir → Penstock → Wicket Gate → Turbine → Generator → Breaker → Grid
     ↓
  Spillway
```

This model is designed to be parameterized via profile overlays to support different site configurations (small hydro, run-of-river, high-head Francis, low-head Kaplan, etc.).

## Canonical Units

All internal calculations use SI units. Tag values are reported in engineering units as shown:

| Tag | Unit | Description |
|-----|------|-------------|
| HY_Res_Level | m | Reservoir/forebay water level |
| HY_Head | m | Net hydraulic head at turbine |
| HY_Flow | m³/s | Turbine water flow rate |
| HY_Pressure | kPa | Penstock pressure (≈ H × 9.81) |
| HY_Speed_Pct | % | Turbine speed as % of sync |
| HY_Freq_Hz | Hz | Generator electrical frequency |
| HY_Power_MW | MW | Generator electrical output |
| HY_Gate_Pos | % | Wicket gate position (0-100) |
| HY_Gate_Cmd | % | Wicket gate command (0-100) |
| HY_Power_Setpoint_MW | MW | Power control setpoint |
| HY_Breaker_* | 0/1 | Boolean status/command |
| HY_Spill_* | 0/1 | Boolean status/command |
| HY_State_* | 0/1 | Boolean state flags |
| HY_Trip_* | 0/1 | Boolean trip indicators |
| HY_Alarm_* | 0/1 | Boolean alarm flags |

## Physical Equations

### 1. Reservoir Mass Balance

The reservoir level changes based on inflow and outflow:

```
dV/dt = Q_inflow - Q_turbine - Q_spillway

dLevel/dt = (Q_inflow - Q_turbine - Q_spillway) / Area

Level(t+dt) = Level(t) + dLevel/dt * dt
```

Where:
- `Q_inflow` = natural river inflow [m³/s]
- `Q_turbine` = flow through turbine [m³/s]
- `Q_spillway` = spillway discharge [m³/s]
- `Area` = reservoir surface area [m²]

### 2. Hydraulic Head

Net head available at the turbine:

```
H_net = Level_reservoir + H_static - Level_tailwater - H_losses

H_losses ≈ k * Q² (friction losses, minor losses)
```

For the simplified model:
```
H = Level + H_static - Tailwater
```

### 3. Penstock Flow Dynamics

Flow through the penstock is modeled as a first-order lag (water inertia):

```
dQ/dt = (Q_target - Q) / τ_penstock

Q_target = k_q * (gate_pos/100) * √H

Q = min(Q_calculated, Q_max)
```

Where:
- `τ_penstock` = water time constant [s], typically L/(gA/Q_rated)
- `k_q` = flow coefficient (calibrated to match rated conditions)
- `gate_pos` = wicket gate position [%]

### 4. Turbine Mechanical Power

Mechanical power extracted by the turbine:

```
P_mech = ρ * g * Q * H * η_t

P_mech [MW] = 1000 * 9.81 * Q * H * η_t / 1,000,000
            = 0.00981 * Q * H * η_t
```

Where:
- `ρ` = water density [kg/m³] (1000 kg/m³)
- `g` = gravitational acceleration [m/s²] (9.81)
- `Q` = flow [m³/s]
- `H` = head [m]
- `η_t` = turbine efficiency (0.70-0.95 typical)

### 5. Generator Electrical Power

When connected to grid (breaker closed):

```
P_elec = min(P_mech * η_g, P_rated)
```

When disconnected (breaker open):
```
P_elec = 0
```

Where:
- `η_g` = generator efficiency (0.90-0.99 typical)
- `P_rated` = rated power capacity [MW]

### 6. Speed Dynamics

**On-Grid (Breaker Closed):**
Speed is locked to grid frequency:
```
Speed = 100% (synchronous)
Freq = 60 Hz (or 50 Hz)
```

**Off-Grid (Breaker Open):**
Speed determined by mechanical-electrical balance:
```
dSpeed/dt = (T_mech - T_friction) / J

T_mech ∝ P_mech / Speed
T_friction ∝ Speed
```

Simplified model:
```
IF flow > 0 THEN
    dSpeed/dt = (P_mech/P_rated_fraction - Speed/decay_const) / H_inertia
ELSE
    dSpeed/dt = -Speed / (H_inertia * 10)  (* coast down *)
```

### 7. Gate Actuator Dynamics

First-order servo response with slew limiting:

```
Gate_velocity = (Gate_cmd - Gate_pos) / τ_servo
Gate_velocity = clamp(Gate_velocity, -slew_max, +slew_max)
Gate_pos = Gate_pos + Gate_velocity * dt
Gate_pos = clamp(Gate_pos, 0, 100)
```

Where:
- `τ_servo` = servo time constant [s] (0.5-5s typical)
- `slew_max` = maximum gate velocity [%/s] (3-20%/s typical)

### 8. Breaker Dynamics

Simple timing model:
```
IF close_cmd AND NOT closed THEN
    timer += dt
    IF timer >= close_time AND speed_in_sync THEN
        closed := TRUE
    END_IF
ELSIF open_cmd AND closed THEN
    timer += dt
    IF timer >= open_time THEN
        closed := FALSE
    END_IF
END_IF
```

Typical times: 50-100ms for HV generator breakers (IEEE C37.013).

## Control State Machine

### States

| State | Description | Entry Condition |
|-------|-------------|-----------------|
| IDLE | Unit stopped, gate closed, breaker open | Power-on default, or after SHUTDOWN/RESET |
| STARTUP | Ramping gate, synchronizing | Start command with permissives OK |
| RUNNING | On-grid, tracking power setpoint | Breaker closes after sync |
| SHUTDOWN | Orderly power reduction | Stop command |
| TRIPPED | Emergency stop, latched | Any trip condition |

### State Transitions

```
           Start_Cmd + Permissives
    IDLE ──────────────────────────→ STARTUP
      ↑                                   │
      │                     Speed ≈ Sync + Breaker Closes
      │                                   ↓
      │ Gate Closed              ←─── RUNNING
      │ Breaker Open                      │
      │                                   │ Stop_Cmd
      │         Any Trip                  ↓
 TRIPPED ←──────────────────── SHUTDOWN
      │                                   │
      │ Reset_Cmd                         │ Gate Closed + Breaker Open
      └───────────────────────────────────┘
                    IDLE
```

### Permissives

Before transitioning from IDLE to STARTUP:

1. **Level OK**: Reservoir level > minimum (e.g., 8m)
2. **Head OK**: Net head > minimum (e.g., 10m)
3. **No Trips**: All trip latches cleared
4. **Run Enable**: Operator permissive active

### Trip Conditions

| Trip | Threshold | Source |
|------|-----------|--------|
| Overspeed | Speed > 110% | Industry standard |
| Overpressure | Pressure > 150% static | DOE/EPRI guidelines |
| Low Head | Head < 10m | Site-specific |
| Manual | Operator-initiated | Emergency stop |

### Trip Response

On any trip:
1. Open breaker immediately
2. Fast-close gate (emergency rate)
3. Open spillway (on overspeed)
4. Latch trip status
5. Transition to TRIPPED state
6. Require manual reset after conditions clear

## Profile Hierarchy

Profiles follow a hierarchy with inheritance:

```
generic.yaml (base)
    └── demo.yaml (10x speedup)
    └── realistic.yaml (research-grounded)
            └── olmsted.yaml (site-specific overlay)
```

### Timing Constants by Profile

| Parameter | Realistic | Demo | Unit |
|-----------|-----------|------|------|
| Gate travel time | 10.0 | 1.0 | s |
| Gate tau (servo) | 1.0 | 0.1 | s |
| Penstock tau | 5.0 | 0.5 | s |
| Breaker open | 0.06 | 0.2 | s |
| Breaker close | 0.05 | 0.2 | s |
| Speed sensor tau | 0.005 | 0.001 | s |
| Flow sensor tau | 0.05 | 0.01 | s |
| Level sensor tau | 0.5 | 0.1 | s |

### Realistic Profile

- Gate travel time: 10s (research-grounded)
- Penstock tau: 5s (typical L/gA)
- Sensor noise: Present (realistic instrumentation)
- Breaker timing: 50-60ms (IEEE C37.013)

### Demo Profile

- Gate travel time: 1s (10x faster)
- Penstock tau: 0.5s (10x faster)
- Sensor noise: Reduced (cleaner visualization)
- Breaker timing: 200ms (visible in UI)

### Olmsted Profile

Site-specific overlay for Olmsted Hydroelectric:
- Unit 1: 8.032 MW, 8.5 m³/s, 100m head
- Unit 2: 3.304 MW, 3.4 m³/s, 103m head
- Unit 3: 0.272 MW (micro)
- Unit 4: 0.160 MW (micro)

## k_q Calibration

The flow coefficient `k_q` relates gate position, head, and flow:

```
Q = k_q × (gate/100) × √H
```

### Derivation

At rated conditions (full gate, rated head):
```
Q_max = k_q × (100/100) × √H_rated
k_q = Q_max / √H_rated
```

For the generic model (Q_max = 100 m³/s, H_rated = 100m):
```
k_q = 100 / √100 = 100 / 10 = 10
```

### Verification

At 50% gate, 100m head:
```
Q = 10 × 0.5 × √100 = 10 × 0.5 × 10 = 50 m³/s ✓
```

At full gate, 64m head (low reservoir):
```
Q = 10 × 1.0 × √64 = 10 × 8 = 80 m³/s ✓ (reduced flow at lower head)
```

## Known Simplifications

The generic hydro model makes several simplifying assumptions:

### 1. Frequency Locked on Grid

When breaker is closed, generator frequency is locked to grid (60 Hz nominal). No governor dynamics or frequency regulation modeled.

**Impact**: Cannot simulate frequency response or AGC participation.

### 2. Constant Head Assumption

Head loss through penstock is not modeled. Effective head depends only on reservoir level and static head difference.

**Impact**: Overestimates flow and power at high flow rates.

### 3. No Water Hammer

Pressure transients from rapid gate closure are not modeled. Penstock pressure is approximated as `H × 9.81` kPa.

**Impact**: Cannot simulate overpressure trips from fast gate operations.

### 4. No Cavitation

Suction side pressure limits (tailwater submergence, sigma) not checked.

**Impact**: Cannot detect cavitation conditions at low tailwater or high power.

### 5. Single Operating Point Efficiency

Turbine and generator efficiencies are constant, not curves.

**Impact**: Overestimates efficiency at partial loads.

### 6. Simplified Reservoir

No hydrograph input—inflow is constant. Reservoir is modeled as prismatic (constant area).

**Impact**: Cannot simulate flood events or seasonal variations.

### Future Enhancements (PS-2)

- Speed state with governor dynamics
- Head loss toggle for penstock friction
- Efficiency curves for turbine/generator
- Water hammer model for pressure transients

## Invariant Rules Rationale

### Range Rules

Based on physical limits and tag contract ranges:
- `HY_Res_Level`: 0-30m covers typical forebay depths
- `HY_Speed_Pct`: 0-150% allows overspeed detection
- `HY_Freq_Hz`: 55-65 Hz covers under/over-frequency scenarios

### Correlation Rules

- **Breaker-Power**: When breaker closed, power must be > 0 (generating)
- **Gate-Flow**: When gate > 5%, flow must be > 0 (water passing)
- **State-Breaker**: Running state requires breaker closed

### Rate-of-Change Rules

- **Gate**: Max 5%/sample (10%/s @ 500ms = 5%/sample)
- **Flow**: Max 10 m³/s/sample (penstock inertia limits)
- **Speed**: Max 5%/sample (generator inertia limits)

### Causality Rules

- **Gate-Pos**: Gate command → position within 20 samples (~10s)
- **Breaker-Sts**: Breaker command → status within 2 samples (~100ms)
- **Flow-Power**: Flow + breaker → power within 4 samples (~2s)

## References

1. DOE Hydropower Handbook (DOE/ID-10338)
2. IEEE C37.013 - AC High-Voltage Generator Circuit Breakers
3. PNNL Governor Studies (PNNL-28563)
4. ASCE/EPRI Guides for Design of Conventional Hydro Power Plants
5. Olmsted Hydroelectric Poster (Public Data)
