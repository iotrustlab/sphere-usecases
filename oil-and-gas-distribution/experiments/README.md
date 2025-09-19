# Oil & Gas Distribution Security Experiments

> **Status**: 🔄 Planned - These experiments are under development

This directory will contain security research experiments and perturbation scenarios for the oil and gas distribution use case.

## Planned Experiments

### Pressure Manipulation (`pressure_manipulation/`)
- **Pressure Sensor Attacks**: Inject false pressure readings to manipulate control systems
- **Flow Rate Spoofing**: Manipulate flow rate readings to disrupt process control
- **Safety Bypass**: Disable pressure safety interlocks

### Pipeline Bypass (`pipeline_bypass/`)
- **Direct Valve Control**: Bypass control logic to directly control valves
- **Pressure Override**: Manipulate pressure setpoints beyond safe ranges
- **Emergency Bypass**: Disable emergency shutdown systems

## Development Status

- [ ] Experiment design and documentation
- [ ] Attack script development
- [ ] Monitoring and data collection tools
- [ ] Recovery procedures
- [ ] Safety validation

## Experiment Guidelines

1. **Safety First**: Always test in simulation before physical deployment
2. **Documentation**: Document all attack vectors and their effects
3. **Recovery**: Include procedures for system recovery after experiments
4. **Monitoring**: Monitor system behavior during and after experiments

## Contributing New Experiments

1. Create a new directory for your experiment
2. Follow the naming convention: `descriptive_name/`
3. Include all required files (README, scripts, monitoring)
4. Test thoroughly in simulation before submission
5. Document safety considerations and recovery procedures
