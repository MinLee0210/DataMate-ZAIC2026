#!/usr/bin/env bash
# usage: ab.sh LANG PORT TOPIC
cd /workspace/DataMate-ZAIC2026
export PATH=$HOME/.local/bin:$PATH
export PROMPT_LANG=$1 LLM_BASE_URL=http://127.0.0.1:$2/v1 LLM_MODEL=Qwen/Qwen3.5-9B WORK_DIR=/tmp/dm-$1
export PIPELINE=ca FEW_SHOT_K=0 CA_SAMPLES=1 MIN_CONFIDENCE=0.05 ANALYZE_MAX_TOKENS=10240
export ANALYZE_EXTRA_BODY="{\"chat_template_kwargs\": {\"enable_thinking\": true}, \"presence_penalty\": 1.5}"
export LLM_EXTRA_BODY="{\"chat_template_kwargs\": {\"enable_thinking\": false}}"
uv run python -m scripts.eval --split train --subset dev200 --topic $3 --workers 14
