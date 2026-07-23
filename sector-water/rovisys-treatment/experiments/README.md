# Water Treatment Security Experiments

This directory contains security research experiments and perturbation scenarios for the water treatment use case.

## Available Experiments

### Sensor Spoofing (`sensor_spoofing/`)
- **pH Sensor Attack**: Inject false pH readings to manipulate chemical dosing
- **Flow Rate Spoofing**: Manipulate flow rate readings to disrupt process control
- **Level Sensor Attacks**: Spoof tank level readings to cause overflow/underflow

### Pump Override (`pump_override/`)
- **Direct Pump Control**: Bypass control logic to directly control pumps
- **Pump Speed Manipulation**: Alter pump speeds beyond safe operating ranges
- **Emergency Stop Bypass**: Disable emergency stop functionality

## Experiment Guidelines

1. **Safety First**: Always test in simulation before physical deployment
2. **Documentation**: Document all attack vectors and their effects
3. **Recovery**: Include procedures for system recovery after experiments
4. **Monitoring**: Monitor system behavior during and after experiments

## Running Experiments

Each experiment directory contains:
- `README.md` - Experiment description and setup
- `attack_script.py` - Automated attack implementation
- `monitoring.py` - System monitoring and data collection
- `recovery.py` - System recovery procedures

## Contributing New Experiments

1. Create a new directory for your experiment
2. Follow the naming convention: `descriptive_name/`
3. Include all required files (README, scripts, monitoring)
4. Test thoroughly in simulation before submission
5. Document safety considerations and recovery procedures
