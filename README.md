# SPHERE Use Cases

This repository contains pre-configured cyber-physical system (CPS) use cases for security research and experimentation on the SPHERE CPS Enclave testbed.

## 🎯 Purpose

The SPHERE Use Cases repository provides ready-to-run CPS scenarios that enable:
- **Security Researchers** to conduct experiments on realistic industrial systems
- **Students** to learn ICS security through hands-on experimentation
- **Industry Practitioners** to test security tools and methodologies
- **Use Case Developers** to understand how to create new scenarios

## 🏭 Available Use Cases

### Water Treatment Plant
A comprehensive water treatment facility with multiple processes:
- **Process**: Multi-stage water purification with chemical dosing
- **Components**: Pumps, valves, sensors, chemical injectors
- **Security Scenarios**: Sensor spoofing, pump control manipulation, chemical dosing attacks
- **Complexity**: Advanced (16 I/O points, multiple control loops)

**Quick Start:**
```bash
# Validate the use case
python3 ../sphere-infra/validate_plc_xir.py \
  water-treatment/plc-programs/control.l5x \
  water-treatment/plc-programs/simulation.l5x \
  ../xir_model.json

# Deploy to testbed
../sphere-infra/scripts/deploy_water_treatment.sh
```

### Chemical Mixing Process
A chemical mixing facility with temperature and pH control:
- **Process**: Multi-component chemical mixing with temperature control
- **Components**: Mixers, heaters, pH sensors, temperature sensors
- **Security Scenarios**: Temperature sensor attacks, pH manipulation, mixing ratio attacks
- **Complexity**: Intermediate (12 I/O points, PID control loops)

**Quick Start:**
```bash
# Validate the use case
python3 ../sphere-infra/validate_plc_xir.py \
  chemical-mixing/plc-programs/control.l5x \
  chemical-mixing/plc-programs/simulation.l5x \
  ../xir_model.json

# Deploy to testbed
../sphere-infra/scripts/deploy_chemical_mixing.sh
```

### Power Distribution System
An electrical power distribution network:
- **Process**: Power distribution with load balancing
- **Components**: Circuit breakers, transformers, load sensors
- **Security Scenarios**: Load shedding attacks, circuit breaker manipulation
- **Complexity**: Advanced (20 I/O points, network topology)

### Manufacturing Automation
A flexible manufacturing system:
- **Process**: Multi-stage manufacturing with quality control
- **Components**: Conveyors, robots, quality sensors, sorting systems
- **Security Scenarios**: Quality sensor spoofing, robot control attacks
- **Complexity**: Expert (24 I/O points, complex automation)

## 📁 Repository Structure

```
sphere-usecases/
├── water-treatment/             # Water treatment use case
│   ├── diagrams/                # P&IDs and process diagrams
│   │   ├── process_flow.pdf
│   │   ├── piping_diagram.pdf
│   │   └── control_system.pdf
│   ├── plc-programs/            # L5X files
│   │   ├── control.l5x          # Control PLC program
│   │   └── simulation.l5x       # Simulation PLC program
│   ├── simulation/              # Simulation models
│   │   ├── process_model.py
│   │   ├── sensor_models.py
│   │   └── actuator_models.py
│   ├── security-experiments/    # Security experiment templates
│   │   ├── sensor_spoofing/
│   │   ├── pump_control_attack/
│   │   └── chemical_dosing_attack/
│   └── documentation/           # Use case specific docs
│       ├── README.md
│       ├── process_description.md
│       └── security_analysis.md
├── chemical-mixing/             # Chemical mixing use case
│   ├── diagrams/
│   ├── plc-programs/
│   ├── simulation/
│   ├── security-experiments/
│   └── documentation/
├── power-distribution/          # Power distribution use case
│   ├── diagrams/
│   ├── plc-programs/
│   ├── simulation/
│   ├── security-experiments/
│   └── documentation/
├── manufacturing/               # Manufacturing automation use case
│   ├── diagrams/
│   ├── plc-programs/
│   ├── simulation/
│   ├── security-experiments/
│   └── documentation/
├── templates/                   # Use case templates
│   ├── basic-process/           # Template for basic processes
│   │   ├── template_control.l5x
│   │   ├── template_simulation.l5x
│   │   └── template_documentation.md
│   └── advanced-process/        # Template for advanced processes
│       ├── template_control.l5x
│       ├── template_simulation.l5x
│       └── template_documentation.md
└── README.md                    # This file
```

## 🚀 Getting Started

### For Regular Users (Security Researchers, Students)

1. **Choose a Use Case:**
   ```bash
   # Browse available use cases
   ls sphere-usecases/
   ```

2. **Understand the Process:**
   ```bash
   # Read the use case documentation
   cat sphere-usecases/water-treatment/documentation/README.md
   ```

3. **Validate the Use Case:**
   ```bash
   # Ensure compatibility with testbed
   python3 ../sphere-infra/validate_plc_xir.py \
     sphere-usecases/water-treatment/plc-programs/control.l5x \
     sphere-usecases/water-treatment/plc-programs/simulation.l5x \
     ../xir_model.json
   ```

4. **Deploy and Experiment:**
   ```bash
   # Deploy to testbed
   ../sphere-infra/scripts/deploy_water_treatment.sh
   
   # Run security experiments
   cd sphere-usecases/water-treatment/security-experiments/
   python3 sensor_spoofing_experiment.py
   ```

### For Expert Users (Use Case Developers)

1. **Study Existing Use Cases:**
   ```bash
   # Examine water treatment use case structure
   tree sphere-usecases/water-treatment/
   ```

2. **Use Templates:**
   ```bash
   # Copy template for new use case
   cp -r sphere-usecases/templates/basic-process/ sphere-usecases/my-new-usecase/
   ```

3. **Develop Your Use Case:**
   ```bash
   # Edit PLC programs
   vim sphere-usecases/my-new-usecase/plc-programs/control.l5x
   
   # Develop simulation model
   vim sphere-usecases/my-new-usecase/simulation/process_model.py
   ```

4. **Validate and Deploy:**
   ```bash
   # Validate your use case
   python3 ../sphere-infra/validate_plc_xir.py \
     sphere-usecases/my-new-usecase/plc-programs/control.l5x \
     sphere-usecases/my-new-usecase/plc-programs/simulation.l5x \
     ../xir_model.json
   ```

## 📖 Use Case Documentation

Each use case includes comprehensive documentation:

### Process Documentation
- **Process Description**: Detailed explanation of the industrial process
- **P&ID Diagrams**: Process and instrumentation diagrams
- **Control System**: Description of control loops and automation
- **Safety Systems**: Safety interlocks and emergency procedures

### Technical Documentation
- **PLC Programs**: Structured Text and Ladder Logic code
- **I/O Mapping**: Tag definitions and physical I/O connections
- **Simulation Models**: Python models for process simulation
- **Configuration Files**: Network and system configurations

### Security Documentation
- **Threat Model**: Potential security threats and attack vectors
- **Vulnerability Analysis**: Known vulnerabilities and weaknesses
- **Security Experiments**: Pre-configured security test scenarios
- **Mitigation Strategies**: Recommended security controls

## 🔬 Security Experiments

Each use case includes pre-configured security experiments:

### Sensor Attacks
- **Sensor Spoofing**: Injecting false sensor readings
- **Sensor Replay**: Replaying recorded sensor data
- **Sensor Delay**: Introducing time delays in sensor readings

### Control Attacks
- **Setpoint Manipulation**: Changing control setpoints
- **Control Loop Bypass**: Bypassing control logic
- **Actuator Override**: Directly controlling actuators

### Network Attacks
- **Man-in-the-Middle**: Intercepting and modifying communications
- **Replay Attacks**: Replaying captured network traffic
- **Denial of Service**: Disrupting network communications

### Process Attacks
- **Chemical Dosing**: Manipulating chemical injection rates
- **Temperature Control**: Disrupting temperature control systems
- **Flow Control**: Manipulating flow rates and pressures

## 🛠️ Development Guidelines

### Creating New Use Cases

1. **Choose a Template:**
   - Use `templates/basic-process/` for simple processes
   - Use `templates/advanced-process/` for complex processes

2. **Follow Naming Conventions:**
   - Use lowercase with hyphens for directory names
   - Use descriptive names for files and components
   - Follow IEC 61131-3 naming conventions for PLC tags

3. **Documentation Requirements:**
   - Process description and diagrams
   - Technical specifications and I/O mapping
   - Security analysis and threat model
   - Usage instructions and examples

4. **Validation Requirements:**
   - PLC programs must pass validation
   - Simulation models must be tested
   - Security experiments must be documented
   - Performance must be acceptable

### Contributing Use Cases

1. **Fork the Repository:**
   ```bash
   git clone https://github.com/IOTrust-Lab/sphere-usecases.git
   ```

2. **Create Your Use Case:**
   ```bash
   # Create new use case directory
   mkdir sphere-usecases/my-new-usecase
   
   # Copy template
   cp -r sphere-usecases/templates/basic-process/* sphere-usecases/my-new-usecase/
   ```

3. **Develop and Test:**
   ```bash
   # Develop your use case
   # Test with validation tool
   # Run security experiments
   ```

4. **Submit Pull Request:**
   ```bash
   git add .
   git commit -m "Add new use case: my-new-usecase"
   git push origin main
   ```

## 🔗 Integration

### With Other SPHERE Repositories
- **sphere-infra**: Validation and deployment tools
- **sphere-control**: PLC programming templates and examples
- **sphere-sim**: Simulation model libraries
- **sphere-standards**: Compliance and security standards
- **sphere-docs**: Documentation and tutorials

### With External Tools
- **Rockwell Studio 5000**: For PLC programming
- **Python**: For simulation and analysis
- **Wireshark**: For network analysis
- **Security Tools**: Various security testing tools

## 📋 Roadmap

### Phase 1: Core Use Cases (Current)
- [x] Water treatment plant
- [x] Chemical mixing process
- [ ] Power distribution system
- [ ] Manufacturing automation

### Phase 2: Advanced Use Cases
- [ ] Oil and gas pipeline
- [ ] Nuclear power plant
- [ ] Smart grid system
- [ ] Pharmaceutical manufacturing

### Phase 3: Specialized Use Cases
- [ ] Transportation systems
- [ ] Building automation
- [ ] Agricultural systems
- [ ] Mining operations

## 🐛 Troubleshooting

### Common Issues

**Validation Errors:**
```bash
# Check I/O mapping
python3 ../sphere-infra/validate_plc_xir.py --help

# Verify XIR model
ls ../xir_model.json
```

**Deployment Failures:**
```bash
# Check testbed connectivity
../sphere-infra/scripts/check_testbed.sh

# Verify use case configuration
cat usecase/config.json
```

**Simulation Issues:**
```bash
# Check Python dependencies
pip install -r requirements.txt

# Test simulation model
python3 simulation/test_model.py
```

For more detailed troubleshooting, see [Troubleshooting Guide](../sphere-docs/troubleshooting.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- SPHERE CPS Enclave team for the physical infrastructure
- Industrial partners for process expertise
- Security researchers for threat modeling
- Community contributors for use case development

## 📞 Support

- **Documentation**: [sphere-docs](https://github.com/IOTrust-Lab/sphere-docs)
- **Issues**: [GitHub Issues](https://github.com/IOTrust-Lab/sphere-usecases/issues)
- **Discussions**: [GitHub Discussions](https://github.com/IOTrust-Lab/sphere-usecases/discussions)
- **Email**: sphere-usecases@example.com
