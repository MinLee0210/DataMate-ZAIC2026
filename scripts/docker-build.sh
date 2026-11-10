#!/usr/bin/env bash
# Build the image. Env: IMAGE (datamate), TAG (latest), VLLM_IMAGE (required: the vLLM base image,
# pinned by digest; it must be the version that served the model on the 2x RTX 5090 pod).
# Uses BuildKit, so dependency layers and the uv cache are reused between builds.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="${IMAGE:-datamate}"
TAG="${TAG:-latest}"
: "${VLLM_IMAGE:?set VLLM_IMAGE to the vLLM base image that served Qwen3.5 on the pod (>= 0.17)}"

DOCKER_BUILDKIT=1 docker build --build-arg "VLLM_IMAGE=${VLLM_IMAGE}" -t "${IMAGE}:${TAG}" "$@" .
echo "built ${IMAGE}:${TAG}"
