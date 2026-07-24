#!/usr/bin/env bash
set -e

# Change to script directory to ensure relative paths work
cd "$(dirname "$0")"

echo "[water-treatment/rockwell] validate: (stub) run XIR/tag checks; verify L5X present"

# Check if L5X files exist
if [ ! -f "../controller/Controller_PLC.L5X" ]; then
    echo "ERROR: Controller_PLC.L5X not found"
    exit 1
fi

if [ ! -f "../simulator/Simulator_PLC.L5X" ]; then
    echo "ERROR: Simulator_PLC.L5X not found"
    exit 1
fi

echo "✓ L5X files present"

# Validate I/O mapping
echo "🔍 Validating I/O mapping..."
python3 ../../../../tools/validate_io_map.py ../../../docs/io_map.csv

# Validate PLC programs against XIR (placeholder)
echo "🔍 Validating PLC programs..."
python3 ../../../../tools/validate_xir.py ../controller/Controller_PLC.L5X
python3 ../../../../tools/validate_xir.py ../simulator/Simulator_PLC.L5X

echo "✓ Validation complete"
exit 0
