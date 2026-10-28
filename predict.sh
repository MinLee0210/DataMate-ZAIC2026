#!/usr/bin/env bash
# Competition entrypoint inside the Docker image: read the test set from /data, write
# /result/submission.jsonl (one line per question, flushed as soon as it is decided) and the
# per-question logs in /result/logs/. Starts the local vLLM server first (scripts/infer.sh).
set -euo pipefail
cd "$(dirname "$0")"
export DATA_DIR="${DATA_DIR:-/data}" RESULT_DIR="${RESULT_DIR:-/result}"
# /data is the split folder itself (questions.jsonl, rulebook.md, data/<business_id>/)
export SPLIT="${SPLIT:-.}"
exec ./scripts/infer.sh
