#!/bin/bash
# Cleanup SPHERE experiment
#
# This script:
# 1. Detaches XDC
# 2. Dematerializes the experiment
# 3. Relinquishes resources

set -e

EXPERIMENT_NAME="openplc-water"
PROJECT="$USER"

echo "=== SPHERE OpenPLC Cleanup ==="
echo ""

# Detach XDC
echo "[1/3] Detaching XDC..."
mrg xdc detach x0.${PROJECT} || true

# Dematerialize
echo "[2/3] Dematerializing experiment..."
mrg demat test.${EXPERIMENT_NAME}.${PROJECT} || true

# Relinquish resources
echo "[3/3] Relinquishing resources..."
mrg relinquish test.${EXPERIMENT_NAME}.${PROJECT} || true

# Cleanup local files
rm -f ssh_config inventory.ini

echo ""
echo "=== Cleanup Complete ==="
echo ""
