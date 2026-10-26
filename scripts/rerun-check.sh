#!/usr/bin/env bash
# Run the image twice on the same data, offline, and diff the two submissions (determinism check).
# Env: IMAGE (datamate), TAG (latest), DATA (./data/train), SPLIT (train), OUT (/tmp/datamate-rerun).
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE="${IMAGE:-datamate}"
TAG="${TAG:-latest}"
DATA="$(realpath "${DATA:-./data}")"
OUT="${OUT:-/tmp/datamate-rerun}"

for run in 1 2; do
  mkdir -p "$OUT/run$run"
  rm -f "$OUT/run$run/submission.jsonl"
  docker run --rm --gpus all --network none \
    -e SPLIT="${SPLIT:-train}" \
    -v "$DATA":/data:ro -v "$OUT/run$run":/result \
    "${IMAGE}:${TAG}"
done

if diff -q "$OUT/run1/submission.jsonl" "$OUT/run2/submission.jsonl" >/dev/null; then
  echo "identical: $(wc -l <"$OUT/run1/submission.jsonl") lines"
else
  n=$(diff <(sort "$OUT/run1/submission.jsonl") <(sort "$OUT/run2/submission.jsonl") | grep -c '^<' || true)
  echo "runs differ on $n lines; score both with: python -m scripts.eval --pred <file>" >&2
  exit 1
fi
