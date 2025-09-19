# SPHERE Use Cases - Shared Tools

This directory contains shared validation and utility tools used across all use cases.

## Available Tools

### Validation Tools
- **validate_xir.py** - XIR model validation (planned)
- **validate_tags.py** - Tag schema validation (planned)
- **validate_io_map.py** - I/O mapping validation (planned)

### Utility Tools
- **generate_io_map.py** - Generate I/O maps from PLC programs (planned)
- **convert_l5x_to_st.py** - Convert Rockwell L5X to OpenPLC ST (planned)

## Script Contracts

All implementation scripts must follow these contracts:

### validate.sh Contract
```bash
#!/usr/bin/env bash
set -e

# Required: Print implementation identifier
echo "[use-case/implementation] validate: description"

# Required: Check for required files
# Required: Validate I/O mapping consistency
# Required: Run basic simulation tests (when available)
# Required: Return non-zero exit code on failure

exit 0  # or non-zero on failure
```

### deploy.sh Contract (Rockwell only)
```bash
#!/usr/bin/env bash
set -e

# Required: Print implementation identifier
echo "[use-case/implementation] deploy: description"

# Required: Check enclave environment
# Required: Delegate to SPHERE enclave infrastructure
# Required: Verify testbed connectivity
# Required: Handle non-enclave environments gracefully

exit 0  # or non-zero on failure
```

### run_local.sh Contract (OpenPLC only)
```bash
#!/usr/bin/env bash
set -e

# Required: Print implementation identifier
echo "[use-case/implementation] run_local: description"

# Required: Start virtual simulation
# Required: Run Python simulation models
# Required: Provide local development environment
# Required: Handle errors gracefully

exit 0  # or non-zero on failure
```

## Usage

### From Use Case Scripts
```bash
# In validate.sh
python3 ../../../tools/validate_io_map.py docs/io_map.csv

# In deploy.sh
python3 ../../../tools/validate_xir.py plc/Controller_PLC.L5X
```

### Direct Usage
```bash
# Validate I/O mapping
python3 tools/validate_io_map.py water-treatment/docs/io_map.csv

# Validate XIR model
python3 tools/validate_xir.py water-treatment/implementations/rockwell/plc/Controller_PLC.L5X
```

## Development Status

- [ ] XIR validation tool
- [ ] Tag schema validation tool
- [ ] I/O mapping validation tool
- [ ] PLC program conversion tools
- [ ] Simulation model validation tools

## Contributing

When adding new tools:
1. Follow the script contract requirements
2. Include comprehensive error handling
3. Provide clear usage documentation
4. Test with existing use cases
5. Update this README with new tool information
