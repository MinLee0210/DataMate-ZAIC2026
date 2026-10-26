#!/usr/bin/env bash
# Build the image. Env: IMAGE (datamate), TAG (latest).
# Uses BuildKit, so dependency layers and the uv cache are reused between builds.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="${IMAGE:-datamate}"
TAG="${TAG:-latest}"

DOCKER_BUILDKIT=1 docker build -t "${IMAGE}:${TAG}" "$@" .
echo "built ${IMAGE}:${TAG}"
