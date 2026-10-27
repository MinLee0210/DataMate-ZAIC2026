"""Export a run's submission in the portal format, sorted by id and format-checked.

    uv run python -m scripts.export --pred result/submission.jsonl --topic public-test-qwen3

Writes data/results/<yyyy-mm-dd>/<topic>/submission.jsonl (same as `make eval` does for train).
"""

import argparse
from pathlib import Path

from scripts.eval import export_submission


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pred", type=Path, required=True, help="submission.jsonl of a run")
    parser.add_argument("--topic", required=True, help="folder name under data/results/<date>/")
    args = parser.parse_args(argv)
    out = export_submission(args.pred, args.topic)
    lines = sum(1 for line in out.read_text().splitlines() if line.strip())
    print(f"{lines} lines -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
