# Pump Override Experiments

This experiment demonstrates direct pump control attacks that bypass normal control logic.

## Attack Scenarios

### 1. Direct Pump Control
- **Objective**: Take direct control of pumps, bypassing safety interlocks
- **Method**: Send direct control commands to pump actuators
- **Impact**: Uncontrolled pump operation, potential equipment damage

### 2. Pump Speed Manipulation
- **Objective**: Alter pump speeds beyond safe operating ranges
- **Method**: Modify pump speed setpoints or direct speed control
- **Impact**: Excessive flow rates, pressure spikes, cavitation damage

### 3. Emergency Stop Bypass
- **Objective**: Disable emergency stop functionality
- **Method**: Override or disable emergency stop signals
- **Impact**: Inability to stop system during emergencies

## Files

- `direct_control.py` - Direct pump control attack implementation
- `speed_manipulation.py` - Pump speed manipulation attack
- `emergency_bypass.py` - Emergency stop bypass attack
- `monitoring.py` - System monitoring during attacks
- `recovery.py` - System recovery procedures

## Safety Notes

- **CRITICAL**: Test in simulation only - never on physical systems
- Monitor pump speeds and system pressures continuously
- Have manual override procedures ready
- Document all observed effects and system responses
- Ensure emergency stop functionality is restored after experiments
