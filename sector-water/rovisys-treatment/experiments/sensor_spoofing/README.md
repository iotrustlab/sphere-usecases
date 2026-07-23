# Sensor Spoofing Experiments

This experiment demonstrates various sensor spoofing attacks on the water treatment system.

## Attack Scenarios

### 1. pH Sensor Spoofing
- **Objective**: Manipulate chemical dosing by spoofing pH readings
- **Method**: Inject false pH values to trigger incorrect chemical dosing
- **Impact**: Over/under-dosing of chemicals, potential system damage

### 2. Flow Rate Spoofing
- **Objective**: Disrupt process control by manipulating flow rate readings
- **Method**: Inject false flow rate values to confuse control algorithms
- **Impact**: Incorrect pump speeds, pressure variations, process instability

### 3. Level Sensor Attacks
- **Objective**: Cause tank overflow or underflow by spoofing level readings
- **Method**: Inject false tank level values
- **Impact**: Tank overflow, pump damage, system shutdown

## Files

- `ph_spoofing.py` - pH sensor spoofing attack implementation
- `flow_spoofing.py` - Flow rate spoofing attack implementation
- `level_spoofing.py` - Level sensor spoofing attack implementation
- `monitoring.py` - System monitoring during attacks
- `recovery.py` - System recovery procedures

## Safety Notes

- **CRITICAL**: Test in simulation only - never on physical systems
- Monitor system behavior continuously during experiments
- Have recovery procedures ready before starting experiments
- Document all observed effects and system responses
