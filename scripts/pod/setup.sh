#!/usr/bin/env bash
# One-time setup of a GPU pod for dev_constraint runs (local vLLM, no hosted API).
# Run on the pod from the repo root, after the repo and data are copied (docs: scripts/pod/README.md).
#
# Env: MODEL_ID (Qwen/Qwen3-14B), MODEL_PATH (/models/target), VLLM_VERSION (empty = latest)
set -euo pipefail
cd "$(dirname "$0")/../.."

MODEL_ID="${MODEL_ID:-Qwen/Qwen3-14B}"
MODEL_PATH="${MODEL_PATH:-/models/target}"

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# project env (no vLLM inside: it only talks to the server over HTTP)
uv sync

# vLLM in its own venv, so its torch pin does not touch the project's
if [[ ! -x .venv-vllm/bin/vllm ]]; then
  uv venv .venv-vllm --python 3.12
  VIRTUAL_ENV=.venv-vllm uv pip install "vllm${VLLM_VERSION:+==$VLLM_VERSION}" huggingface_hub
fi

# weights, downloaded once (dev only: the competition image ships them)
if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  mkdir -p "$MODEL_PATH"
  .venv-vllm/bin/hf download "$MODEL_ID" --local-dir "$MODEL_PATH" \
    || .venv-vllm/bin/huggingface-cli download "$MODEL_ID" --local-dir "$MODEL_PATH"
fi

# ingest caches for both splits (the first run would build them anyway)
uv run python -m scripts.ingest --split train
uv run python -m scripts.ingest --split public_test
echo "setup done: start the server with  PATH=\$PWD/.venv-vllm/bin:\$PATH TP=1 QUANTIZATION=fp8 ./scripts/vllm.sh"
