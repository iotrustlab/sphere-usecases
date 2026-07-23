#!/usr/bin/env bash
set -e

# Change to script directory to ensure relative paths work
cd "$(dirname "$0")"

echo "[template/rockwell] validate: run schema checks & validation"

# Validate I/O mapping (if exists)
if [ -f "../../../docs/io_map.csv" ]; then
    echo "🔍 Validating I/O mapping..."
    python3 ../../../../../tools/validate_io_map.py ../../../docs/io_map.csv
else
    echo "⚠️  I/O mapping not found - add docs/io_map.csv to your use case"
fi

# Validate PLC programs (if exist)
if [ -f "../plc/Controller_PLC.L5X" ]; then
    echo "🔍 Validating PLC programs..."
    python3 ../../../../../tools/validate_xir.py ../plc/Controller_PLC.L5X
    if [ -f "../plc/Simulator_PLC.L5X" ]; then
        python3 ../../../../../tools/validate_xir.py ../plc/Simulator_PLC.L5X
    fi
else
    echo "⚠️  PLC programs not found - add L5X files to plc/ directory"
fi

echo "✓ Template validation complete"
exit 0
