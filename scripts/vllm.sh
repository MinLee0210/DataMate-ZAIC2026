#!/usr/bin/env bash
# Serve the target model with pinned vLLM settings (foreground). Used by `make vllm` and infer.sh.
# Env: MODEL_PATH (/models/target), SERVED_MODEL (LLM_MODEL), VLLM_PORT (8001), TP (2), SEED (2026).
# Change these settings only together with a determinism check (make rerun-check).
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-/models/target}"
SERVED_MODEL="${SERVED_MODEL:-${LLM_MODEL:-Qwen/Qwen3-14B}}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_NO_USAGE_STATS=1

exec vllm serve "$MODEL_PATH" \
  --served-model-name "$SERVED_MODEL" \
  --host 127.0.0.1 --port "${VLLM_PORT:-8001}" \
  --tensor-parallel-size "${TP:-2}" \
  --dtype bfloat16 \
  --max-model-len 16384 \
  --max-num-seqs 16 \
  --gpu-memory-utilization 0.90 \
  --seed "${SEED:-2026}"
