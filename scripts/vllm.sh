#!/usr/bin/env bash
# Serve the target model with pinned vLLM settings (foreground). Used by `make vllm` and infer.sh.
# Change these settings only together with a determinism check (make rerun-check).
#
# Env (defaults are for the competition machine, 2x RTX 5090):
#   MODEL_PATH (/models/target)  SERVED_MODEL (LLM_MODEL)  VLLM_PORT (8001)  SEED (2026)
#   TP (2)                tensor parallel size; 1 on a single GPU (A40, one 5090)
#   QUANTIZATION ()       empty = bf16 weights; fp8 halves the weights (~15 GB for 14B)
#   KV_CACHE_DTYPE (auto) fp8 halves the KV cache
#   MAX_MODEL_LEN (49152) prompt + reply. dataAgent prompts reach ~28k tokens on public_test,
#                         plus thinking; above Qwen3's native 32768 YaRN is turned on.
#   MAX_NUM_SEQS (16)  GPU_MEMORY_UTILIZATION (0.90)
#
# Single A40 (48 GB):  TP=1 QUANTIZATION=fp8 ./scripts/vllm.sh
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-/models/target}"
SERVED_MODEL="${SERVED_MODEL:-${LLM_MODEL:-Qwen/Qwen3-14B}}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-49152}"
NATIVE_LEN=32768
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}" TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export VLLM_NO_USAGE_STATS=1

args=(
  --served-model-name "$SERVED_MODEL"
  --host 127.0.0.1 --port "${VLLM_PORT:-8001}"
  --tensor-parallel-size "${TP:-2}"
  --dtype bfloat16
  --max-model-len "$MAX_MODEL_LEN"
  --max-num-seqs "${MAX_NUM_SEQS:-16}"
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.90}"
  --kv-cache-dtype "${KV_CACHE_DTYPE:-auto}"
  # the rulebook and skills are the same prefix in every request
  --enable-prefix-caching
  --seed "${SEED:-2026}"
)
if [[ -n "${QUANTIZATION:-}" ]]; then
  args+=(--quantization "$QUANTIZATION")
fi
if (( MAX_MODEL_LEN > NATIVE_LEN )); then
  # Qwen3 long context: static YaRN, factor = max length / native length (Qwen3 model card)
  factor=$(python3 -c "print(round(${MAX_MODEL_LEN} / ${NATIVE_LEN}, 4))")
  args+=(--hf-overrides "{\"rope_scaling\": {\"rope_type\": \"yarn\", \"factor\": ${factor}, \"original_max_position_embeddings\": ${NATIVE_LEN}}}")
fi

exec vllm serve "$MODEL_PATH" "${args[@]}"
