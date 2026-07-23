# Pipeline Bypass Experiments

> **Status**: 🔄 Planned - This experiment is under development

This experiment will demonstrate direct pipeline control attacks that bypass normal control logic and safety systems.

## Planned Attack Scenarios

### 1. Direct Valve Control
- **Objective**: Take direct control of valves, bypassing safety interlocks
- **Method**: Send direct control commands to valve actuators
- **Impact**: Uncontrolled valve operation, potential equipment damage

### 2. Pressure Override
- **Objective**: Manipulate pressure setpoints beyond safe operating ranges
- **Method**: Override pressure control setpoints or direct pressure control
- **Impact**: Excessive pressure, potential pipeline damage, safety system activation

### 3. Emergency Bypass
- **Objective**: Disable emergency shutdown functionality
- **Method**: Override or disable emergency shutdown signals
- **Impact**: Inability to stop system during emergencies

## Planned Files

- `valve_control.py` - Direct valve control attack implementation
- `pressure_override.py` - Pressure override attack implementation
- `emergency_bypass.py` - Emergency shutdown bypass attack
- `monitoring.py` - System monitoring during attacks
- `recovery.py` - System recovery procedures

## Safety Notes

- **CRITICAL**: Test in simulation only - never on physical systems
- Monitor pressure and flow rates continuously during experiments
- Have manual override procedures ready
- Document all observed effects and system responses
- Ensure emergency shutdown functionality is restored after experiments
- Verify pressure relief systems are operational
