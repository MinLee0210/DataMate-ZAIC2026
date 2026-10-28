#!/usr/bin/env bash
# Competition entrypoint: start the local vLLM server, wait for it, run batch inference.
# Env: VLLM_PORT (8001), DATA_DIR (/data), RESULT_DIR (/result), SPLIT (private_test),
#      START_VLLM (1; 0 = use a server that is already running), WORKERS (8),
#      PIPELINE (ca = dataAgent), ANALYZE_EXTRA_BODY (thinking on for the reasoning steps),
#      ANALYZE_MAX_TOKENS (10240). vLLM settings: scripts/vllm.sh (MAX_MODEL_LEN must hold the
#      longest prompt, about 28k tokens, plus ANALYZE_MAX_TOKENS).
set -euo pipefail
cd "$(dirname "$0")/.."

SERVED_MODEL="${SERVED_MODEL:-${LLM_MODEL:-Qwen/Qwen3-14B}}"
VLLM_PORT="${VLLM_PORT:-8001}"
LOG_DIR="${WORK_DIR:-/tmp/datamate}/logs"
mkdir -p "$LOG_DIR"

export FINAL_MODE=1
export LLM_BASE_URL="http://127.0.0.1:${VLLM_PORT}/v1"
export LLM_MODEL="$SERVED_MODEL" SERVED_MODEL VLLM_PORT
# Qwen3: thinking off by default; dataAgent turns it on for its reasoning steps only
if [[ -z "${LLM_EXTRA_BODY:-}" ]]; then
  export LLM_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": false}}'
fi
export PIPELINE="${PIPELINE:-ca}"
# default only when unset (a "${VAR-default}" with braces in the default corrupts a set value)
if [[ -z "${ANALYZE_EXTRA_BODY+set}" ]]; then
  export ANALYZE_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": true}}'
fi
export ANALYZE_MAX_TOKENS="${ANALYZE_MAX_TOKENS:-10240}"
export WORKERS="${WORKERS:-8}"

if [[ "${START_VLLM:-1}" == "1" ]]; then
  ./scripts/vllm.sh >"$LOG_DIR/vllm.log" 2>&1 &
  VLLM_PID=$!
  trap 'kill $VLLM_PID 2>/dev/null || true' EXIT

  echo "waiting for vLLM on :$VLLM_PORT"
  for _ in $(seq 1 180); do
    curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" >/dev/null && break
    kill -0 "$VLLM_PID" 2>/dev/null || { echo "vLLM exited, see $LOG_DIR/vllm.log" >&2; exit 1; }
    sleep 5
  done
  curl -sf "http://127.0.0.1:${VLLM_PORT}/v1/models" >/dev/null || { echo "vLLM not ready" >&2; exit 1; }
fi

if [[ -x /app/.venv/bin/python ]]; then
  PY=(/app/.venv/bin/python)  # inside the image
else
  PY=(uv run python)
fi
"${PY[@]}" -m src --data "${DATA_DIR:-/data}" --out "${RESULT_DIR:-/result}" \
  --split "${SPLIT:-private_test}" --workers "$WORKERS"
