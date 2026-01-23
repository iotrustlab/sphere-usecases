#!/bin/bash
# OpenPLC Container Entrypoint
# Compiles the provided ST/XML program and starts the runtime
#
# This entrypoint works with the official OpenPLC installation structure:
# - /workdir: OpenPLC installation directory
# - /workdir/.venv: Python virtual environment
# - /docker_persistent: Persistent storage for programs/config

set -e

PROGRAM_FILE="${OPENPLC_PROGRAM:-/programs/program.st}"
MODBUS_PORT="${OPENPLC_MODBUS_PORT:-502}"
WEBUI_PORT="${OPENPLC_WEBUI_PORT:-8080}"
SCAN_CYCLE="${OPENPLC_SCAN_CYCLE_MS:-50}"
AUTOSTART="${OPENPLC_AUTOSTART:-true}"

OPENPLC_DIR="/workdir"
VENV_PYTHON="$OPENPLC_DIR/.venv/bin/python3"

echo "=== SPHERE OpenPLC Runtime ==="
echo "Program: $PROGRAM_FILE"
echo "Modbus Port: $MODBUS_PORT"
echo "WebUI Port: $WEBUI_PORT"
echo "Scan Cycle: ${SCAN_CYCLE}ms"
echo ""

# Initialize persistent storage (from official start_openplc.sh)
if [ -d "/docker_persistent" ]; then
    mkdir -p /docker_persistent/st_files
    cp -n /workdir/webserver/dnp3_default.cfg /docker_persistent/dnp3.cfg 2>/dev/null || true
    cp -n /workdir/webserver/openplc_default.db /docker_persistent/openplc.db 2>/dev/null || true
    cp -n /workdir/webserver/active_program_default /docker_persistent/active_program 2>/dev/null || true
    cp -n /workdir/webserver/st_files_default/* /docker_persistent/st_files/ 2>/dev/null || true
    touch /docker_persistent/persistent.file
    touch /docker_persistent/mbconfig.cfg
fi

# Check if program file exists
if [ ! -f "$PROGRAM_FILE" ]; then
    echo "WARNING: Program file not found: $PROGRAM_FILE"
    echo "Starting OpenPLC webserver without program..."
    echo "You can upload a program via the WebUI at port $WEBUI_PORT"
    echo ""
    cd "$OPENPLC_DIR/webserver"
    exec "$VENV_PYTHON" webserver.py
fi

# Determine file extension and basename
EXT="${PROGRAM_FILE##*.}"
BASENAME=$(basename "$PROGRAM_FILE")

cd "$OPENPLC_DIR/webserver"

# Copy program to st_files directory
echo "Copying program to OpenPLC..."
cp "$PROGRAM_FILE" ./st_files/

# Compile the program
echo "Compiling program..."
cd scripts
./compile_program.sh "$BASENAME"
COMPILE_RESULT=$?
cd ..

if [ $COMPILE_RESULT -ne 0 ]; then
    echo "ERROR: Compilation failed"
    echo "Starting OpenPLC webserver anyway for debugging..."
    echo "Check the WebUI to see compilation errors."
    exec "$VENV_PYTHON" webserver.py
fi

echo "Compilation successful"
echo ""

# Configure settings in database
echo "Configuring OpenPLC settings..."
sqlite3 openplc.db <<EOF
UPDATE settings SET Value='$MODBUS_PORT' WHERE Key='Modbus_port';
UPDATE settings SET Value='$SCAN_CYCLE' WHERE Key='Slave_polling';
UPDATE settings SET Value='true' WHERE Key='Start_run_mode';
EOF

# Register program in Programs table (required for run_http to work)
PROGRAM_NAME="${BASENAME%.*}"
UPLOAD_TIME=$(date +%s)
echo "Registering program in database..."
sqlite3 openplc.db <<EOF
DELETE FROM Programs WHERE File='$BASENAME';
INSERT INTO Programs (Name, Description, File, Date_upload)
VALUES ('$PROGRAM_NAME', 'SPHERE Auto-deployed program', '$BASENAME', $UPLOAD_TIME);
EOF

# Update active program
echo "$BASENAME" > /docker_persistent/active_program 2>/dev/null || echo "$BASENAME" > ./active_program

# Start the runtime
echo "Starting OpenPLC runtime..."
echo ""

# If running in foreground mode (no arguments), start webserver
if [ $# -eq 0 ]; then
    exec "$VENV_PYTHON" webserver.py
else
    # Pass any arguments to the runtime
    exec "$@"
fi
