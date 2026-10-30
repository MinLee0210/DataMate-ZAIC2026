#!/usr/bin/env bash
# usage: ev9.sh PORT TOPIC IDS [SAMPLES]   (Qwen3.5-9B, thinking, en prompts)
cd /workspace/DataMate-ZAIC2026
export PATH=$HOME/.local/bin:$PATH
export PROMPT_LANG=en LLM_BASE_URL=http://127.0.0.1:$1/v1 LLM_MODEL=Qwen/Qwen3.5-9B WORK_DIR=/tmp/dm-$2
export MALT_LITERAL_CHECK=${LIT:-1}
export PIPELINE=${PIPE:-ca} FEW_SHOT_K=0 CA_SAMPLES=${4:-1} MALT_SAMPLES=${4:-1} CA_MIN_AGREEMENT=0 MALT_MIN_AGREEMENT=0 MIN_CONFIDENCE=0.05 ANALYZE_MAX_TOKENS=10240
export ANALYZE_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": true}, "presence_penalty": 1.5}'
export LLM_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": false}}'
uv run python -m scripts.eval --split train --subset $3 --topic $2 --workers 16
