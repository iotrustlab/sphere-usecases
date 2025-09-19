# Water Treatment Use Case

A comprehensive water treatment facility with multiple processes, demonstrating realistic industrial control scenarios with multiple control loops, safety interlocks, and security considerations.

## 🏭 Process Overview

Multi-stage water purification with chemical dosing:
- **Raw Water Intake** → **Chemical Dosing** → **Mixing** → **Settling** → **Filtration** → **Disinfection** → **Storage**
- **16 I/O points**: 8 digital inputs, 4 digital outputs, 2 analog inputs, 2 analog outputs
- **Complexity**: Advanced (multiple control loops, safety interlocks)

See [docs/process_overview.md](docs/process_overview.md) for detailed process description.

## 🚀 Quick Start

### Rockwell Implementation (SPHERE Testbed)
```bash
# Validate the implementation
./implementations/rockwell/scripts/validate.sh

# Deploy to testbed (requires enclave access)
./implementations/rockwell/scripts/deploy.sh
```

### OpenPLC Implementation (Virtual)
```bash
# Run local simulation (when available)
./implementations/openplc/scripts/run_local.sh
```

## 📁 Structure

```
water-treatment/
├── README.md                          # This file
├── docs/                              # Process documentation
│   ├── process_overview.md            # Detailed process description
│   ├── io_map.csv                     # I/O mapping and tag definitions
│   └── pid.pdf                        # Process & Instrumentation Diagram
├── implementations/                   # Implementation-specific code
│   ├── rockwell/                      # SPHERE testbed deployment
│   │   ├── plc/                       # L5X files
│   │   │   ├── Controller_PLC.L5X     # Main control program
│   │   │   └── Simulator_PLC.L5X      # Simulation program
│   │   └── scripts/                   # Validation and deployment
│   │       ├── validate.sh            # Validate L5X files
│   │       └── deploy.sh              # Deploy to testbed
│   └── openplc/                       # Virtual simulation (planned)
│       ├── plc_st/                    # Structured Text programs
│       ├── sim/                       # Python simulation models
│       └── scripts/                   # Local execution scripts
└── experiments/                       # Security research experiments
    ├── sensor_spoofing/               # Sensor manipulation attacks
    └── pump_override/                 # Direct pump control attacks
```

## 🔧 Implementations

### Rockwell (Authoritative)
- **Purpose**: SPHERE testbed deployment
- **Files**: Studio 5000 L5X programs
- **Status**: ✅ Active - Ready for testbed deployment
- **Validation**: XIR checks, tag schema validation
- **Deployment**: Delegates to SPHERE enclave infrastructure

### OpenPLC (Optional/Virtual)
- **Purpose**: Local development and simulation
- **Files**: Structured Text programs, Python simulation models
- **Status**: 🔄 Planned - Virtual implementation for local testing
- **Execution**: Local simulation environment

## 🔬 Security Experiments

### Sensor Spoofing
- **pH Sensor Attacks**: Manipulate chemical dosing through false pH readings
- **Flow Rate Spoofing**: Disrupt process control with false flow data
- **Level Sensor Attacks**: Cause tank overflow/underflow scenarios

### Pump Override
- **Direct Control**: Bypass safety interlocks for direct pump control
- **Speed Manipulation**: Alter pump speeds beyond safe ranges
- **Emergency Bypass**: Disable emergency stop functionality

See [experiments/README.md](experiments/README.md) for detailed experiment descriptions.

## 🛡️ Safety Considerations

- **High/Low Level Alarms**: Prevent tank overflow/underflow
- **Pressure Relief**: Automatic pressure relief valves
- **Chemical Overdose Protection**: Limit chemical injection rates
- **Emergency Shutdown**: Manual and automatic shutdown capabilities

## 📊 I/O Mapping

| Tag | Address | Type | Units | Range | Safety Notes |
|-----|---------|------|-------|-------|--------------|
| RawWaterPump | DI_01 | Digital Input | Boolean | 0-1 | High priority - controls raw water intake |
| pH_Value | AI_01 | Analog Input | pH | 0-14 | CRITICAL - pH measurement for chemical dosing |
| ChemicalDose1 | AO_01 | Analog Output | % | 0-100 | Chemical dosing pump 1 speed control |

See [docs/io_map.csv](docs/io_map.csv) for complete I/O mapping.

## 🔗 Related

- **Templates**: Based on [templates/single-process/](../templates/single-process/)
- **Validation**: Uses SPHERE infrastructure validation tools
- **Deployment**: Integrates with SPHERE enclave infrastructure