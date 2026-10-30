#!/usr/bin/env bash
# usage: pub.sh LANG PORT NAME IDS_FILE   (public_test, k=3, no agreement gate: gated offline)
cd /workspace/DataMate-ZAIC2026
export PATH=$HOME/.local/bin:$PATH
export PROMPT_LANG=$1 LLM_BASE_URL=http://127.0.0.1:$2/v1 LLM_MODEL=Qwen/Qwen3.5-9B WORK_DIR=/tmp/dm-$3 FINAL_MODE=1
export PIPELINE=ca FEW_SHOT_K=0 CA_SAMPLES=3 CA_VARIANT_OFFSET=3 CA_MIN_AGREEMENT=0 MIN_CONFIDENCE=0.05 ANALYZE_MAX_TOKENS=10240
export ANALYZE_EXTRA_BODY="{\"chat_template_kwargs\": {\"enable_thinking\": true}, \"presence_penalty\": 1.5}"
export LLM_EXTRA_BODY="{\"chat_template_kwargs\": {\"enable_thinking\": false}}"
[ -d /tmp/dm-$3 ] || cp -r /tmp/datamate /tmp/dm-$3
uv run python -m src --data ./data --out /workspace/out/$3 --split public_test --ids $4 --workers 14
