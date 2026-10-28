#!/usr/bin/env bash
# One-time setup of a GPU pod for dev_constraint runs (local vLLM, no hosted API).
# Run on the pod from the repo root, after the repo and data are copied (docs: scripts/pod/README.md).
#
# Env: MODEL_ID (Qwen/Qwen3-14B-FP8: official FP8 weights, 16.3 GB instead of 29.6 GB),
#      MODEL_PATH (/models/target), VLLM_VERSION (empty = latest)
# Disk: about 16 GB weights + 8 GB vLLM env + 1 GB project, data and caches. No download cache
# is kept (uv --no-cache, weights straight to MODEL_PATH).
set -euo pipefail
cd "$(dirname "$0")/../.."

MODEL_ID="${MODEL_ID:-Qwen/Qwen3-14B-FP8}"
MODEL_PATH="${MODEL_PATH:-/models/target}"

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
mkdir -p "$MODEL_PATH"
df -h "$MODEL_PATH" . | sed 's/^/disk: /'
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# project env (no vLLM inside: it only talks to the server over HTTP)
uv sync --no-cache

# vLLM in its own venv, so its torch pin does not touch the project's
if [[ ! -x .venv-vllm/bin/vllm ]]; then
  uv venv .venv-vllm --python 3.12
  VIRTUAL_ENV=.venv-vllm uv pip install --no-cache "vllm${VLLM_VERSION:+==$VLLM_VERSION}" huggingface_hub
fi

# weights, downloaded once (dev only: the competition image ships them)
if [[ ! -f "$MODEL_PATH/config.json" ]]; then
  .venv-vllm/bin/hf download "$MODEL_ID" --local-dir "$MODEL_PATH" \
    || .venv-vllm/bin/huggingface-cli download "$MODEL_ID" --local-dir "$MODEL_PATH"
fi

# ingest caches for both splits (the first run would build them anyway)
uv run python -m scripts.ingest --split train
uv run python -m scripts.ingest --split public_test
rm -rf "$MODEL_PATH/.cache"   # download metadata only
du -sh "$MODEL_PATH" .venv .venv-vllm 2>/dev/null | sed 's/^/size: /'
echo "setup done: start the server with  PATH=\$PWD/.venv-vllm/bin:\$PATH TP=1 ./scripts/vllm.sh"
