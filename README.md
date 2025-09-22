# SPHERE Use Cases

> **SPHERE CPS Enclave (NSF infrastructure based at USC ISI)** provides the real hardware ICS environment; the **Utah-led CPS enclave** is designed, developed, and tested by **PI Garcia**, and this repository hosts the **use-case processes** that run on that enclave. Each use case may offer multiple implementations: **Rockwell** for enclave deployment and **OpenPLC (virtual)** for local exploration.

## 🎯 What This Repository Contains

This repository contains **self-contained CPS use cases** for security research and experimentation. Each use case includes:
- Process documentation (P&IDs, I/O maps, safety notes)
- Multiple implementations (Rockwell for testbed, OpenPLC for virtual)
- Security experiments and perturbation scenarios
- Validation and deployment scripts

## 🏭 Available Use Cases

| Use Case | Status | Rockwell | OpenPLC | Description |
|----------|--------|----------|---------|-------------|
| [**Water Treatment**](water-treatment/README.md) | ✅ Active | ✅ Testbed | ✅ Virtual | Multi-stage water purification with chemical dosing |
| [**Oil & Gas Distribution**](oil-and-gas-distribution/README.md) | 🔄 Planned | 🔄 Planned | 🔄 Planned | Pipeline distribution with pressure control |

## 🚀 Getting Started

1. **Pick a use case** from the table above
2. **Read its README** for specific setup instructions
3. **Choose your implementation**:
   - **Rockwell** = Real SPHERE testbed deployment (requires enclave access)
   - **OpenPLC** = Virtual simulation for local development

## 📁 Repository Structure

```
sphere-usecases/
├── README.md                          # This router
├── templates/                         # Golden skeletons for new use cases
├── water-treatment/                   # Water treatment use case
│   ├── README.md                      # Use case specific documentation
│   ├── docs/                          # Process docs, P&IDs, I/O maps
│   ├── implementations/               # Implementation-specific code
│   │   ├── rockwell/                  # SPHERE testbed deployment
│   │   └── openplc/                   # Virtual simulation
│   └── experiments/                   # Security research experiments
├── oil-and-gas-distribution/          # Oil & gas use case (planned)
└── [shared references]                # Global tag layouts, controller mappings
```

## 🛠️ For Contributors

### Creating New Use Cases
1. **Copy the template**: `cp -r templates/single-process/ your-new-use-case/`
2. **Follow the structure**: Each use case should be self-contained
3. **Add implementations**: Rockwell (testbed) and/or OpenPLC (virtual)
4. **Include experiments**: Security research scenarios
5. **Validate**: Run `validate.sh` scripts before submitting

### Implementation Guidelines
- **Rockwell**: Use Studio 5000, export as L5X files, delegate to SPHERE enclave infra
- **OpenPLC**: Use Structured Text, include Python simulation models
- **Scripts**: All implementations should expose `validate.sh` and appropriate deployment scripts

See [templates/README.md](templates/README.md) for detailed guidance.

## 🔗 Related Repositories

- **sphere-infra**: Validation tools and enclave infrastructure
- **sphere-control**: PLC programming libraries and examples
- **sphere-sim**: Simulation model libraries
- **sphere-standards**: Security and compliance standards

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/IOTrust-Lab/sphere-usecases/issues)
- **Documentation**: See individual use case READMEs and [templates/](templates/)
- **Contributing**: See [templates/README.md](templates/README.md) for development guidelines

---

*This repository focuses on **use cases only**. For infrastructure, deployment tools, and detailed documentation, see the related SPHERE repositories.*