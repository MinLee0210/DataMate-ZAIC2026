#!/usr/bin/env bash
# Serve the target model with pinned vLLM settings (foreground). Used by `make vllm` and infer.sh.
# Change these settings only together with a determinism check (make rerun-check).
#
# Env (defaults are for the competition machine, 2x RTX 5090):
#   MODEL_PATH (/models/target)  SERVED_MODEL (LLM_MODEL)  VLLM_PORT (8001)  SEED (2026)
#   TP (2)                tensor parallel size; 1 on a single GPU (A40, one 5090)
#   QUANTIZATION ()       empty = as the checkpoint is (Qwen3-14B-FP8 is already fp8);
#                         fp8 quantizes a bf16 checkpoint when loading
#   KV_CACHE_DTYPE (auto) fp8 halves the KV cache
#   MAX_MODEL_LEN (40960) prompt + reply: Qwen3-14B's max_position_embeddings. dataAgent prompts
#                         reach ~28k tokens on public_test, plus ANALYZE_MAX_TOKENS of thinking.
#                         Longer needs YaRN (ROPE_YARN=1); not on by default, it hurts short texts.
#   MAX_NUM_SEQS (16)  GPU_MEMORY_UTILIZATION (0.90)
#
# Single A40 (48 GB) with the FP8 checkpoint:  TP=1 ./scripts/vllm.sh
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-/models/target}"
SERVED_MODEL="${SERVED_MODEL:-${LLM_MODEL:-Qwen/Qwen3-14B}}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-40960}"
NATIVE_LEN=40960
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
if [[ "${ROPE_YARN:-0}" == "1" ]] && (( MAX_MODEL_LEN > 32768 )); then
  # Qwen3 long context: static YaRN over the 32768 pre-training length (Qwen3 model card).
  # Not checked on vLLM 0.32 (transformers renamed rope_scaling); test before relying on it.
  NATIVE_LEN=32768
  factor=$(python3 -c "print(round(${MAX_MODEL_LEN} / ${NATIVE_LEN}, 4))")
  args+=(--hf-overrides "{\"rope_scaling\": {\"rope_type\": \"yarn\", \"factor\": ${factor}, \"original_max_position_embeddings\": ${NATIVE_LEN}}}")
fi

exec vllm serve "$MODEL_PATH" "${args[@]}"
