#!/bin/bash
# SPHERE Experiment Setup for OpenPLC Water Treatment
#
# This script:
# 1. Creates a new SPHERE experiment
# 2. Pushes the network model
# 3. Realizes and materializes the experiment
# 4. Creates an XDC for access
# 5. Generates SSH config and Ansible inventory

set -e

EXPERIMENT_NAME="openplc-water"
PROJECT="$USER"  # Uses personal project

echo "=== SPHERE OpenPLC Water Treatment Setup ==="
echo ""

# Create experiment
echo "[1/6] Creating experiment..."
mrg new experiment ${EXPERIMENT_NAME}.${PROJECT} 'OpenPLC Water Treatment Demo' || true

# Create XDC
echo "[2/6] Creating XDC..."
mrg new xdc x0.${PROJECT} || true

# Push the network model
echo "[3/6] Pushing network model..."
REV=$(mrg push ./model.py ${EXPERIMENT_NAME}.${PROJECT} | grep -oE '[a-f0-9]{40}' | head -n 1)
echo "Model revision: $REV"

# Realize the experiment
echo "[4/6] Realizing experiment..."
mrg realize test.${EXPERIMENT_NAME}.${PROJECT} revision $REV

echo "[5/6] Materializing experiment..."
mrg mat test.${EXPERIMENT_NAME}.${PROJECT}

# Attach XDC
echo "[6/6] Attaching XDC..."
mrg xdc attach x0.${PROJECT} test.${EXPERIMENT_NAME}.${PROJECT}

# Generate SSH config
PWD_DIR=$(pwd)
cat > ssh_config <<EOF
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    User $USER

Host jump
    HostName jump.sphere-testbed.net
    Port 2022
    User $USER
    IdentityFile ~/.ssh/merge_key

Host x0-$USER
    HostName x0-$USER
    User $USER
    IdentityFile ~/.ssh/merge_key
    ProxyJump jump

Host controller
    HostName controller
    User $USER
    IdentityFile ~/.ssh/merge_key
    ProxyJump x0-$USER

Host simulator
    HostName simulator
    User $USER
    IdentityFile ~/.ssh/merge_key
    ProxyJump x0-$USER
EOF

# Generate Ansible inventory
cat > inventory.ini <<EOF
[all:vars]
ansible_ssh_common_args="-F ${PWD_DIR}/ssh_config"
ansible_python_interpreter=/usr/bin/python3

[plcs]
controller ansible_host=controller ansible_user=$USER
simulator ansible_host=simulator ansible_user=$USER

[plcs:vars]
# OpenPLC Docker image settings
openplc_image_name=sphere-openplc
openplc_image_tag=latest

# Network settings (must match model.py)
docker_network_name=openplc-net
docker_network_subnet=10.100.0.0/24

[controller]
controller

[simulator]
simulator
EOF

echo ""
echo "=== Setup Complete ==="
echo ""
echo "SSH config written to: ssh_config"
echo "Ansible inventory written to: inventory.ini"
echo ""
echo "Next steps:"
echo "  1. Test SSH access: ssh -F ssh_config controller"
echo "  2. Run Ansible: ./ansible.sh"
echo ""
