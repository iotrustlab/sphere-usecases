#!/bin/bash
# Build and optionally push OpenPLC runtime images
#
# Usage:
#   ./build.sh                    # Build with default (master)
#   ./build.sh <version>          # Build specific version (commit SHA or branch)
#   ./build.sh <version> --push   # Build and push to registry
#
# Examples:
#   ./build.sh master
#   ./build.sh abc123def456       # Specific commit
#   ./build.sh master --push      # Push to default registry

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${1:-master}"
PUSH="${2:-}"

# Image naming
REGISTRY="${SPHERE_REGISTRY:-ghcr.io/sphere-project}"
IMAGE_NAME="sphere-openplc"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}"

echo "=== SPHERE OpenPLC Image Builder ==="
echo "Version: ${VERSION}"
echo "Image: ${FULL_IMAGE}:${VERSION}"
echo ""

# Build the image
echo "Building image..."
docker build \
    --build-arg OPENPLC_VERSION="${VERSION}" \
    -t "${FULL_IMAGE}:${VERSION}" \
    -t "${IMAGE_NAME}:${VERSION}" \
    -f "${SCRIPT_DIR}/Dockerfile" \
    "${SCRIPT_DIR}"

# If version is master, also tag as latest
if [ "${VERSION}" = "master" ]; then
    docker tag "${FULL_IMAGE}:${VERSION}" "${FULL_IMAGE}:latest"
    docker tag "${IMAGE_NAME}:${VERSION}" "${IMAGE_NAME}:latest"
    echo "Tagged as latest"
fi

echo ""
echo "Build complete: ${FULL_IMAGE}:${VERSION}"

# Get the actual commit from the built image
COMMIT=$(docker run --rm "${FULL_IMAGE}:${VERSION}" cat /opt/openplc/version.txt 2>/dev/null | tail -1 || echo "unknown")
echo "OpenPLC commit: ${COMMIT}"

# Push if requested
if [ "${PUSH}" = "--push" ]; then
    echo ""
    echo "Pushing to registry..."
    docker push "${FULL_IMAGE}:${VERSION}"
    if [ "${VERSION}" = "master" ]; then
        docker push "${FULL_IMAGE}:latest"
    fi
    echo "Push complete"
fi

echo ""
echo "To use this image in a scenario, set:"
echo "  backend_config:"
echo "    image: ${FULL_IMAGE}:${VERSION}"
