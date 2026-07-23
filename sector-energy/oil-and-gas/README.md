# Oil & Gas Distribution Use Case

> Repo-local planning note: this use case is still in incubation. Canonical prioritization lives in [`../../sphere-docs/BACKLOG.md`](../../sphere-docs/BACKLOG.md).

A pipeline distribution system with pressure control, demonstrating realistic oil and gas industry control scenarios with safety interlocks and security considerations.

## 🏭 Process Overview

Oil and gas pipeline distribution with pressure control:
- **Inlet Processing** → **Pressure Regulation** → **Distribution** → **Monitoring** → **Safety Systems**
- **Planned I/O points**: 12-16 I/O points with pressure, flow, and safety monitoring
- **Complexity**: Intermediate to Advanced (pressure control loops, safety interlocks)

## 🚀 Implementation Status

### Rockwell Implementation
- **Status**: 🔄 Planned
- **Purpose**: SPHERE testbed deployment
- **Files**: Studio 5000 L5X programs (to be developed)

### OpenPLC Implementation  
- **Status**: 🔄 Planned
- **Purpose**: Virtual simulation and local development
- **Files**: Structured Text programs, Python simulation models (to be developed)

## 📁 Structure

```
oil-and-gas/
├── README.md                          # This file
├── docs/                              # Process documentation (planned)
│   ├── process_overview.md            # Detailed process description
│   ├── io_map.csv                     # I/O mapping and tag definitions
│   └── pid.pdf                        # Process & Instrumentation Diagram
├── implementations/                   # Implementation-specific code
│   ├── rockwell/                      # SPHERE testbed deployment (planned)
│   │   ├── plc/                       # L5X files (to be developed)
│   │   └── scripts/                   # Validation and deployment
│   └── openplc/                       # Virtual simulation (planned)
│       ├── plc_st/                    # Structured Text programs
│       ├── sim/                       # Python simulation models
│       └── scripts/                   # Local execution scripts
└── experiments/                       # Security research experiments (planned)
    ├── pressure_manipulation/         # Pressure control attacks
    └── pipeline_bypass/               # Pipeline safety bypass attacks
```

## 🔧 Getting Started

This use case is currently in the planning phase. To contribute:

1. **Copy the template**: This use case is based on [templates/single-process/](../templates/single-process/)
2. **Develop the process**: Define the oil and gas distribution process
3. **Create implementations**: Add Rockwell and/or OpenPLC implementations
4. **Add experiments**: Develop security research scenarios

## 🛡️ Planned Safety Considerations

- **Pressure Relief**: Automatic pressure relief valves
- **Leak Detection**: Pipeline leak monitoring and alarms
- **Emergency Shutdown**: Manual and automatic shutdown capabilities
- **Flow Control**: Pressure and flow rate monitoring

## 🔬 Planned Security Experiments

### Pressure Manipulation
- **Pressure Sensor Attacks**: Manipulate pressure readings
- **Flow Rate Spoofing**: Disrupt flow control with false data
- **Safety Bypass**: Disable safety interlocks

### Pipeline Bypass
- **Direct Valve Control**: Bypass control logic for direct valve control
- **Pressure Override**: Manipulate pressure setpoints
- **Emergency Bypass**: Disable emergency shutdown systems

## 🔗 Related

- **Templates**: Based on [templates/single-process/](../templates/single-process/)
- **Development**: See [templates/README.md](../templates/README.md) for development guidelines
- **Contributing**: Follow the standard use case development process
