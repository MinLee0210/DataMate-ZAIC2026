#!/usr/bin/env bash
# Tag and push the image to the pre-defined destination.
# Set IMAGE_REPO to the destination (e.g. ghcr.io/<org>/datamate).
# Env: IMAGE (local image name), TAG (latest), IMAGE_REPO (required).
set -euo pipefail

IMAGE="${IMAGE:-datamate}"
TAG="${TAG:-latest}"
IMAGE_REPO="${IMAGE_REPO:-}"

if [[ -z "$IMAGE_REPO" ]]; then
  echo "IMAGE_REPO is not set (e.g. IMAGE_REPO=ghcr.io/<org>/<image>)" >&2
  exit 1
fi

docker tag "${IMAGE}:${TAG}" "${IMAGE_REPO}:${TAG}"
docker push "${IMAGE_REPO}:${TAG}"
echo "pushed ${IMAGE_REPO}:${TAG}"
