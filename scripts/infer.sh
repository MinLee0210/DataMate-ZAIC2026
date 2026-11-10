#!/usr/bin/env bash
# Competition entrypoint: start the local vLLM server(s), wait for them, run batch inference.
# Settings come from scripts/final.env (anything already in the environment wins):
#      REPLICAS (2 = one vLLM per GPU, TP=1 each; 1 = one server, TP from scripts/vllm.sh),
#      VLLM_BASE_PORT (8011; replica i uses VLLM_BASE_PORT+i; with REPLICAS=1 VLLM_PORT, 8001),
#      DATA_DIR (/data), RESULT_DIR (/result), SPLIT (private_test),
#      START_VLLM (1; 0 = use servers that are already running), WORKERS,
#      PIPELINE (malt), ANALYZE_EXTRA_BODY (thinking on), ANALYZE_MAX_TOKENS,
#      MALT_SAMPLES / MALT_MIN_AGREEMENT / MALT_TYPE_GATES (vote and gates).
#      vLLM settings: scripts/vllm.sh (MAX_MODEL_LEN must hold the longest prompt, about 28k
#      tokens, plus ANALYZE_MAX_TOKENS).
set -euo pipefail
cd "$(dirname "$0")/.."

# defaults of the final run; the environment overrides them
if [[ -f scripts/final.env ]]; then
  # shellcheck disable=SC1091
  source scripts/final.env
fi

SERVED_MODEL="${SERVED_MODEL:-${LLM_MODEL:-Qwen/Qwen3.5-9B}}"
REPLICAS="${REPLICAS:-1}"
LOG_DIR="${WORK_DIR:-/tmp/datamate}/logs"
mkdir -p "$LOG_DIR"

export FINAL_MODE=1
export LLM_MODEL="$SERVED_MODEL" SERVED_MODEL
# Qwen3: thinking off by default; MALT turns it on for its reasoning steps only
if [[ -z "${LLM_EXTRA_BODY:-}" ]]; then
  export LLM_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": false}}'
fi
export PIPELINE="${PIPELINE:-malt}"
# default only when unset (a "${VAR-default}" with braces in the default corrupts a set value)
if [[ -z "${ANALYZE_EXTRA_BODY+set}" ]]; then
  export ANALYZE_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": true}}'
fi
export ANALYZE_MAX_TOKENS="${ANALYZE_MAX_TOKENS:-10240}"
export WORKERS="${WORKERS:-8}"

# server ports: one per replica
PORTS=()
if (( REPLICAS > 1 )); then
  for i in $(seq 0 $((REPLICAS - 1))); do PORTS+=("$(( ${VLLM_BASE_PORT:-8011} + i ))"); done
else
  PORTS+=("${VLLM_PORT:-8001}")
fi
URLS=()
for port in "${PORTS[@]}"; do URLS+=("http://127.0.0.1:${port}/v1"); done
export LLM_BASE_URL="${URLS[0]}"
export LLM_BASE_URLS="$(IFS=,; echo "${URLS[*]}")"

wait_for() {  # wait_for PORT PID
  local port="$1" pid="$2"
  for _ in $(seq 1 180); do
    curl -sf "http://127.0.0.1:${port}/v1/models" >/dev/null && return 0
    if [[ -n "$pid" ]] && ! kill -0 "$pid" 2>/dev/null; then
      echo "vLLM on :$port exited, see $LOG_DIR/vllm-$port.log" >&2
      return 1
    fi
    sleep 5
  done
  echo "vLLM on :$port not ready" >&2
  return 1
}

if [[ "${START_VLLM:-1}" == "1" ]]; then
  PIDS=()
  for i in "${!PORTS[@]}"; do
    port="${PORTS[$i]}"
    if (( REPLICAS > 1 )); then
      # one GPU per replica
      CUDA_VISIBLE_DEVICES="$i" TP=1 VLLM_PORT="$port" ./scripts/vllm.sh >"$LOG_DIR/vllm-$port.log" 2>&1 &
    else
      VLLM_PORT="$port" ./scripts/vllm.sh >"$LOG_DIR/vllm-$port.log" 2>&1 &
    fi
    PIDS+=("$!")
  done
  trap 'kill "${PIDS[@]}" 2>/dev/null || true' EXIT
  echo "waiting for vLLM on :${PORTS[*]}"
  for i in "${!PORTS[@]}"; do wait_for "${PORTS[$i]}" "${PIDS[$i]}"; done
else
  for port in "${PORTS[@]}"; do wait_for "$port" ""; done
fi

if [[ -x /app/.venv/bin/python ]]; then
  PY=(/app/.venv/bin/python)  # inside the image
else
  PY=(uv run python)
fi
"${PY[@]}" -m src --data "${DATA_DIR:-/data}" --out "${RESULT_DIR:-/result}" \
  --split "${SPLIT:-private_test}" --workers "$WORKERS"
