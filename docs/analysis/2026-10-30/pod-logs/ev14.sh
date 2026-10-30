#!/usr/bin/env bash
# usage: ev14.sh PORT TOPIC IDS   (Qwen3-14B-FP8, k=3, thinking, dev200 half)
cd /workspace/DataMate-ZAIC2026
export PATH=$HOME/.local/bin:$PATH
export PROMPT_LANG=en LLM_BASE_URL=http://127.0.0.1:$1/v1 LLM_MODEL=Qwen/Qwen3-14B-FP8 WORK_DIR=/tmp/dm-$2
export PIPELINE=ca FEW_SHOT_K=0 CA_SAMPLES=3 CA_MIN_AGREEMENT=0 MIN_CONFIDENCE=0.05 ANALYZE_MAX_TOKENS=10240
export ANALYZE_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": true}}'
export LLM_EXTRA_BODY='{"chat_template_kwargs": {"enable_thinking": false}}'
uv run python -m scripts.eval --split train --subset $3 --topic $2 --workers 16
