# I/O Contract: Water Treatment Process One

This document defines the communication contract between the Controller and Simulator PLCs for the Water Treatment Process One scenario.

## Overview

```
┌─────────────────┐     Modbus TCP      ┌─────────────────┐
│                 │◄───────────────────►│                 │
│   Controller    │     Port 502/503    │   Simulator     │
│   (OpenPLC)     │                     │   (OpenPLC)     │
│                 │                     │                 │
└─────────────────┘                     └─────────────────┘
       │                                       │
       │ Reads:                                │ Reads:
       │ - Tank levels                         │ - Valve commands
       │ - Valve status                        │ - Pump commands
       │ - Pump status                         │
       │                                       │
       │ Writes:                               │ Writes:
       │ - Valve commands                      │ - Tank levels
       │ - Pump commands                       │ - Valve status
       │                                       │ - Pump status
```

## Communication Protocol

- **Protocol**: Modbus TCP
- **Controller Port**: 502
- **Simulator Port**: 503
- **Scan Rate**: 50ms (configurable)

For future agent integration, the recommended contract is the host-side
testbed wrapper in `scripts/openplc_testbed.py`, which exposes normalized
observations and actions while keeping the PLC/runtime details inside the
testbed.

## Data Exchange

### Controller → Simulator (Commands)

| Signal | Modbus Type | Address | IEC Address | Description |
|--------|-------------|---------|-------------|-------------|
| RW_Tank_PR_Valve | Coil | 40 | %QX5.0 | PR valve open command |
| RW_Tank_P6B_Valve | Coil | 41 | %QX5.1 | P6B valve open command |
| RW_Tank_P_Valve | Coil | 42 | %QX5.2 | Process valve open command |
| RW_Pump_Start | Coil | 43 | %QX5.3 | Pump start command |
| RW_Pump_Stop | Coil | 44 | %QX5.4 | Pump stop command |
| RW_Pump_Speed | Holding Reg | 100 | %QW100 | Pump speed setpoint (%) |
| HMI_Reset_PB | Coil | 4 | %QX0.4 | Testbed reset button |

### Agent / Process Control Plane

The host-side testbed wrapper exposes a small process-aware control plane on
controller coils for future runtime agents:

| Signal | Modbus Type | Address | IEC Address | Description |
|--------|-------------|---------|-------------|-------------|
| P2_Selected | Coil | 8 | %QX1.0 | Select Process 2 manual dosing path |
| P2_NaCl_Cmd | Coil | 9 | %QX1.1 | Manual NaCl dosing command |
| P2_NaOCl_Cmd | Coil | 10 | %QX1.2 | Manual NaOCl dosing command |
| P2_HCl_Cmd | Coil | 11 | %QX1.3 | Manual HCl dosing command |

### Simulator → Controller (Feedback)

| Signal | Modbus Type | Address | IEC Address | Description |
|--------|-------------|---------|-------------|-------------|
| RW_Tank_Level | Input Reg | 70 | %IW70 | Tank level (0-1200 mm) |
| RW_Pump_Flow | Input Reg | 71 | %IW71 | Pump flow rate (L/min) |
| RW_Tank_PR_Valve_Sts | Discrete In | 16 | %IX2.0 | PR valve position feedback |
| RW_Tank_P6B_Valve_Sts | Discrete In | 17 | %IX2.1 | P6B valve position feedback |
| RW_Tank_P_Valve_Sts | Discrete In | 18 | %IX2.2 | Process valve feedback |
| RW_Pump_Sts | Discrete In | 19 | %IX2.3 | Pump running status |
| RW_Pump_Fault | Discrete In | 20 | %IX2.4 | Pump fault status |

### Testbed Admin Plane

To support fast scenario execution without rebuilding containers, the
simulator exposes a small admin plane on holding registers:

| Signal | Address | Description |
|--------|---------|-------------|
| Admin_Init_* | 340-344 | Baseline levels applied on reset |
| Admin_Reset_Seq | 349 | Increment to reset the simulator state |
| Admin_Apply_* | 360-364 | Runtime level override values |
| Admin_Apply_*_Flag | 365-369 | Select which runtime override values to apply |
| Admin_Apply_Seq | 370 | Increment to apply runtime overrides |

The host-side testbed controller uses these registers as part of its reset and
runtime-control path while keeping the Docker stack warm.

Important note: the validated external contract today is still the
action/state surface used by the default readiness suite:

- observe current process state
- apply HMI-style actions (`hmi_start`, `hmi_stop`, `hmi_estop`, `hmi_reset`)
- apply process-scoped Process 2 actions (`select_process`, `set_manual_valve`)
- collect per-run observations/events/results

Non-default initial conditions and arbitrary runtime level forcing remain
experimental on the externally reachable Modbus plane and should not yet be
treated as the primary agent interface.

## State Machine

The controller implements a state machine with the following states:

```
    ┌──────────────────────────────────────────────┐
    │                                              │
    ▼                                              │
┌───────┐  Start_PB   ┌───────┐  Permissives  ┌────────┐
│ IDLE  │────────────►│ START │──────────────►│RUNNING │
└───────┘             └───────┘               └────────┘
    ▲                     │                       │
    │                     │ Stop_PB               │ Stop_PB
    │                     ▼                       ▼
    │               ┌──────────┐            ┌──────────┐
    └───────────────│ SHUTDOWN │◄───────────│ SHUTDOWN │
                    └──────────┘            └──────────┘
```

### Permissives (START → RUNNING)

1. RW_Tank_Level > 250 mm (not critically low)
2. UF_UFFT_Tank_Level < 1000 mm (destination tank has capacity)

## Alarm Levels

| Alarm | Level (mm) | Action |
|-------|------------|--------|
| LL (Low-Low) | 250 | Stop pump, raise alarm |
| L (Low) | 500 | Open inlet valve |
| H (High) | 800 | Close inlet valve |
| HH (High-High) | 1200 | Raise alarm |

## Timing Considerations

- **Scan Cycle**: 50ms default
- **Valve Response**: Simulated as instantaneous (can add delay in simulator)
- **Pump Ramp**: Simulated as instantaneous (can add ramp in simulator)
- **Tank Dynamics**: Level changes based on flow rate and time step

## Error Handling

- **Communication Loss**: Controller continues with last known values
- **Invalid Values**: Out-of-range values trigger input validation alarms
- **Pump Fault**: Controller transitions to SHUTDOWN state
