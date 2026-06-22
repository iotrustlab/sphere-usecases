# Contributing to SPHERE Use Cases

Thank you for your interest in contributing to the SPHERE Use Cases repository! This guide will help you understand how to contribute new use cases or improve existing ones.

## 🎯 What We're Looking For

- **New Use Cases**: Self-contained CPS processes with security research potential
- **Implementation Improvements**: Better Rockwell or OpenPLC implementations
- **Security Experiments**: New attack scenarios and perturbation techniques
- **Documentation**: Process descriptions, P&IDs, and safety analysis
- **Validation Tools**: Improved validation and testing scripts

## 🚀 Getting Started

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR-USERNAME/sphere-usecases.git
cd sphere-usecases
```

### 2. Choose Your Contribution Type

#### Creating a New Use Case
```bash
# Copy the template to the appropriate CISA sector
cp -r templates/usecase/ <sector>/<vendor>-<domain>/usecases/<instance>/

# Example: Create a new water treatment use case
cp -r templates/usecase/ water/acme-treatment/usecases/basic-demo/

# Update the README with your process details
vim water/acme-treatment/usecases/basic-demo/README.md
```

#### Improving an Existing Use Case
```bash
# Navigate to the use case
cd water/rovisys-treatment/usecases/p1-onboarding/

# Make your changes
vim implementations/rockwell/controller/Controller_PLC.L5X
```

## 📁 Use Case Structure Requirements

Every use case must follow this structure:

```
your-use-case/
├── README.md                          # Use case overview and quick start
├── docs/                              # Process documentation
│   ├── process_overview.md            # Detailed process description
│   ├── io_map.csv                     # I/O mapping and tag definitions
│   └── pid.pdf                        # Process & Instrumentation Diagram
├── implementations/                   # Implementation-specific code
│   ├── rockwell/                      # SPHERE testbed deployment
│   │   ├── plc/                       # L5X files
│   │   └── scripts/                   # Validation and deployment
│   └── openplc/                       # Virtual simulation
│       ├── plc_st/                    # Structured Text programs
│       ├── sim/                       # Python simulation models
│       └── scripts/                   # Local execution scripts
└── experiments/                       # Security research experiments
    ├── experiment1/                   # Individual experiment
    └── experiment2/                   # Individual experiment
```

## 📋 Required Files and Documentation

### Process Documentation
- **process_overview.md**: Detailed process description, components, control loops, safety systems
- **io_map.csv**: Complete I/O mapping with tag names, addresses, types, units, ranges, safety notes
- **pid.pdf**: Process & Instrumentation Diagram (or placeholder if not available)

### Implementation Files
- **Rockwell**: L5X files (not L5K), validation and deployment scripts
- **OpenPLC**: Structured Text programs, Python simulation models, local execution scripts

### Security Experiments
- **README.md**: Experiment description, attack scenarios, safety notes
- **Attack scripts**: Python or other implementation of attack scenarios
- **Monitoring**: System monitoring and data collection tools
- **Recovery**: System recovery procedures

## 🔧 Script Requirements

### Validation Scripts
All implementations must include a `validate.sh` script that:
- Checks for required files (L5X, ST, etc.)
- Validates I/O mapping consistency
- Runs basic simulation tests (when available)
- Returns non-zero exit code on failure

### Deployment Scripts
- **Rockwell**: `deploy.sh` should delegate to SPHERE enclave infrastructure
- **OpenPLC**: `run_local.sh` should start virtual simulation locally

### Script Standards
```bash
#!/usr/bin/env bash
set -e
echo "[use-case/implementation] action: description"

# Your validation/deployment logic here

exit 0  # or non-zero on failure
```

## 🛡️ Safety and Security Guidelines

### Safety Requirements
- **Document all safety considerations** in process overview and I/O maps
- **Include safety interlocks** in control logic
- **Test in simulation first** before any physical deployment
- **Provide recovery procedures** for all experiments

### Security Experiment Guidelines
- **Never test on physical systems** without proper authorization
- **Document attack vectors** and their potential impacts
- **Include monitoring** to observe system behavior
- **Provide recovery procedures** for system restoration

## 📝 Naming Conventions

### Directory Names
- Use lowercase with hyphens: `water-treatment`, `oil-and-gas-distribution`
- Be descriptive and concise

### File Names
- Use descriptive names: `Controller_PLC.L5X`, `process_overview.md`
- Follow platform conventions: `.L5X` for Rockwell, `.st` for OpenPLC

### Tag Names
- Use consistent prefixes: `WT_` for water treatment, `OG_` for oil and gas
- Follow pattern: `PREFIX_Component_Instance_Parameter`
- Example: `WT_Pump01_Status`, `OG_Valve02_Position`

## 🧪 Testing Requirements

### Before Submitting
1. **Run validation scripts**: `./implementations/*/scripts/validate.sh`
2. **Test in simulation**: Run OpenPLC simulations locally
3. **Check documentation**: Ensure all required files are present
4. **Verify safety**: Review safety considerations and interlocks

### Validation Checklist
- [ ] All required files present and properly named
- [ ] Validation scripts run successfully
- [ ] Documentation is complete and accurate
- [ ] Safety considerations are documented
- [ ] Security experiments include recovery procedures
- [ ] I/O mapping is consistent and complete

## 📤 Submitting Your Contribution

### 1. Create a Pull Request
```bash
git add .
git commit -m "Add new use case: your-use-case"
git push origin main
```

### 2. Use the PR Template
Fill out the pull request template with:
- Use case description and purpose
- Implementation status (Rockwell/OpenPLC)
- Security experiments included
- Testing performed
- Safety considerations

### 3. Review Process
- **Automated checks**: Validation scripts must pass
- **Manual review**: Process documentation and safety analysis
- **Testing**: Simulation and validation testing
- **Security review**: Attack scenarios and recovery procedures

## 🔍 Review Checklist

### For Reviewers
- [ ] Use case follows required structure
- [ ] All required files are present
- [ ] Validation scripts work correctly
- [ ] Documentation is complete and accurate
- [ ] Safety considerations are adequate
- [ ] Security experiments are well-documented
- [ ] I/O mapping is consistent
- [ ] Naming conventions are followed

## 🆘 Getting Help

- **Documentation**: Check [templates/README.md](templates/README.md) for detailed guidance
- **Issues**: Open a GitHub issue for questions or problems
- **Discussions**: Use GitHub Discussions for general questions
- **Email**: Contact the maintainers for sensitive or complex issues

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🙏 Thank You

Thank you for contributing to the SPHERE Use Cases repository! Your contributions help advance CPS security research and education.
