# SPHERE Use Cases - Templates

This directory contains templates for creating new use cases in the SPHERE repository.

## Available Templates

### `single-process/`
The standard template for single-process CPS use cases. Use this for most MVP use cases.

**Structure:**
- `docs/` - Process documentation (P&ID, I/O maps, safety notes)
- `implementations/` - Implementation-specific code and scripts
  - `rockwell/` - For SPHERE testbed deployment (Studio 5000, L5X)
  - `openplc/` - For virtual simulation and local development
- `experiments/` - Security research experiments and perturbations

## How to Use

1. Copy the `single-process/` template to create your new use case:
   ```bash
   cp -r templates/single-process/ your-new-use-case/
   ```

2. Update the README.md with your specific process details

3. Add your implementation files:
   - Rockwell: Add L5X files to `implementations/rockwell/plc/`
   - OpenPLC: Add ST files to `implementations/openplc/plc_st/`

4. Create your process documentation in `docs/`

5. Add security experiments in `experiments/`

6. Test your implementation:
   ```bash
   ./implementations/rockwell/scripts/validate.sh
   ./implementations/openplc/scripts/run_local.sh
   ```

## Implementation Guidelines

### Rockwell Implementation
- Use Studio 5000 for development
- Export as L5X files (not L5K)
- Include both control and simulation programs
- Scripts should delegate to SPHERE enclave infrastructure

### OpenPLC Implementation
- Use Structured Text (ST) for PLC logic
- Include Python simulation models
- Scripts should run locally for development and testing

## Safety and Security

- Always include safety notes in your I/O maps
- Document security considerations in your experiments
- Test thoroughly in simulation before physical deployment
- Follow SPHERE enclave protocols for testbed access
