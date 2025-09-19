# Use Case Template (Single Process)

This template provides the standard structure for a single-process CPS use case in the SPHERE repository.

## Purpose
Brief description of the process, its safety considerations, and how to run different implementations.

## Structure
- `docs/` - Process documentation (P&ID, I/O maps, safety notes)
- `implementations/` - Implementation-specific code and scripts
  - `rockwell/` - For SPHERE testbed deployment (Studio 5000, L5X)
  - `openplc/` - For virtual simulation and local development
- `experiments/` - Security research experiments and perturbations

## Getting Started
1. Copy this template to create a new use case
2. Update the README with your specific process details
3. Add your implementation files to the appropriate directories
4. Run `validate.sh` scripts to check your implementation

## Safety Notes
- Always review safety considerations before deployment
- Test in simulation before physical deployment
- Follow SPHERE enclave protocols for testbed access
