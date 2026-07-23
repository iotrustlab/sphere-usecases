#!/bin/bash
# Run Ansible playbooks against SPHERE experiment
#
# Prerequisites:
# - Run up.sh first to create experiment and generate inventory
# - Ensure nodes are materialized and accessible

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANSIBLE_DIR="${SCRIPT_DIR}/../ansible"

# Check if inventory exists
if [ ! -f "${SCRIPT_DIR}/inventory.ini" ]; then
    echo "ERROR: inventory.ini not found. Run up.sh first."
    exit 1
fi

echo "=== SPHERE OpenPLC Deployment ==="
echo ""

# Activate venv if it exists
if [ -f "${SCRIPT_DIR}/../.venv/bin/activate" ]; then
    source "${SCRIPT_DIR}/../.venv/bin/activate"
fi

# Step 1: Install Docker on SPHERE nodes
echo "[1/3] Installing Docker on SPHERE nodes..."
ansible-playbook -i "${SCRIPT_DIR}/inventory.ini" \
    "${SCRIPT_DIR}/playbooks/install-docker.yml"

# Step 2: Build OpenPLC image on nodes
echo "[2/3] Building OpenPLC Docker image..."
ansible-playbook -i "${SCRIPT_DIR}/inventory.ini" \
    "${SCRIPT_DIR}/playbooks/build-openplc.yml"

# Step 3: Deploy OpenPLC containers
echo "[3/3] Deploying OpenPLC containers..."
ansible-playbook -i "${SCRIPT_DIR}/inventory.ini" \
    "${SCRIPT_DIR}/playbooks/deploy-sphere.yml"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Access points:"
echo "  Controller WebUI: http://controller:8080 (via SSH tunnel)"
echo "  Simulator WebUI:  http://simulator:8080 (via SSH tunnel)"
echo ""
echo "To create SSH tunnel for WebUI:"
echo "  ssh -F ssh_config -L 8080:localhost:8080 controller"
echo ""
echo "To test Modbus connectivity:"
echo "  ansible-playbook -i inventory.ini playbooks/test-modbus.yml"
echo ""
