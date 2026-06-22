#!/bin/bash
# SPHERE HMI Demo Launcher
#
# Usage:
#   USECASE=wt ./start_demo.sh   # Water Treatment
#   USECASE=wd ./start_demo.sh   # Water Distribution
#   USECASE=ps ./start_demo.sh   # Power Hydro
#   ./start_demo.sh wt           # Alternative syntax

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HMI_DIR="$(dirname "$SCRIPT_DIR")"
USECASES_DIR="$(dirname "$HMI_DIR")"

# Accept use case from argument or environment
USECASE="${1:-${USECASE:-wt}}"

# Validate use case
case "$USECASE" in
    wt)
        echo "=== Starting Water Treatment UC1 Demo ==="
        CONTROLLER_ST="$USECASES_DIR/water-treatment/implementations/openplc/projects/controller_project/build/plc.st"
        SIMULATOR_ST="$USECASES_DIR/water-treatment/implementations/openplc/projects/simulator_project/build/plc.st"
        ;;
    wd)
        echo "=== Starting Water Distribution UC0 Demo ==="
        CONTROLLER_ST="$USECASES_DIR/water-distribution/implementations/openplc/st/wd_controller.st"
        SIMULATOR_ST="$USECASES_DIR/water-distribution/implementations/openplc/st/wd_simulator.st"
        ;;
    ps)
        echo "=== Starting Power Hydro PS-1 Demo ==="
        CONTROLLER_ST="$USECASES_DIR/power-hydro/implementations/openplc/st/ps_hydro_controller.st"
        SIMULATOR_ST="$USECASES_DIR/power-hydro/implementations/openplc/st/ps_hydro_simulator.st"
        ;;
    *)
        echo "Error: Unknown use case '$USECASE'"
        echo "Valid options: wt (Water Treatment), wd (Water Distribution), ps (Power Hydro)"
        exit 1
        ;;
esac

# Verify ST files exist
if [ ! -f "$CONTROLLER_ST" ]; then
    echo "Error: Controller ST file not found: $CONTROLLER_ST"
    exit 1
fi

if [ ! -f "$SIMULATOR_ST" ]; then
    echo "Error: Simulator ST file not found: $SIMULATOR_ST"
    exit 1
fi

echo "Controller: $CONTROLLER_ST"
echo "Simulator:  $SIMULATOR_ST"
echo ""

# Export environment variables
export USECASE
export CONTROLLER_ST_FILE="$CONTROLLER_ST"
export SIMULATOR_ST_FILE="$SIMULATOR_ST"

# Change to HMI directory for docker-compose
cd "$HMI_DIR"

# Build and start containers
echo "Building containers..."
docker compose build

echo ""
echo "Starting containers..."
docker compose up -d

echo ""
echo "Waiting for services to start..."
sleep 5

# Show container status
echo ""
echo "Container status:"
docker compose ps

echo ""
echo "=== Demo Started ==="
echo ""
echo "Endpoints:"
echo "  FUXA HMI:         http://localhost:1881"
echo "  Controller WebUI: http://localhost:8080"
echo "  Simulator WebUI:  http://localhost:8081"
echo ""
echo "To view logs:       docker compose logs -f"
echo "To stop:            ./scripts/stop_demo.sh"
echo ""
echo "Note: OpenPLC containers may take 60-90 seconds to compile and start."
echo "Check health status with: docker compose ps"
