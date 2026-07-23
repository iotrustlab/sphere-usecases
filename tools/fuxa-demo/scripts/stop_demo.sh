#!/bin/bash
# SPHERE HMI Demo Stopper
#
# Stops all demo containers and optionally cleans up volumes.
#
# Usage:
#   ./stop_demo.sh          # Stop containers
#   ./stop_demo.sh --clean  # Stop containers and remove volumes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HMI_DIR="$(dirname "$SCRIPT_DIR")"

cd "$HMI_DIR"

echo "=== Stopping SPHERE HMI Demo ==="

if [ "$1" == "--clean" ]; then
    echo "Stopping containers and removing volumes..."
    docker compose down -v
    echo "Cleaned up volumes."
else
    echo "Stopping containers..."
    docker compose down
fi

echo ""
echo "=== Demo Stopped ==="
