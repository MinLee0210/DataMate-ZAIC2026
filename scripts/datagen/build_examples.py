"""Build the few-shot store (src/assets/examples/train_examples.jsonl) from train eval runs.

    uv run python -m scripts.datagen.build_examples data/results/2026-10-28/*/raw

An example is kept only when the run's answer matched the train reference (scored.jsonl, score
+1) and the trace shows the SQL whose result became the answer. Hold-out businesses
(scripts/splits.py) are never kept. One example per question: the shortest verified SQL.
Train data only; no model is called here.
"""

import argparse
import json
from pathlib import Path

from scripts.splits import FAMILY, HOLDOUT, SECTOR
from src.modules.context.examples import EXAMPLES_PATH

ROOT = Path(__file__).resolve().parents[2]


def _jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def final_sql(trace: dict) -> str | None:
    """The SQL of the result the final answer came from."""
    messages = trace.get("messages") or []
    finals = [m for m in messages if m.get("type") == "thought" and m.get("action") == "final"]
    if not finals:
        return None
    ref = str(finals[-1].get("data_result") or "")
    runs = [m for m in messages if m.get("type") == "data" and not m.get("error")]
    named = [m for m in runs if m.get("name") == ref] or (runs[-1:] if len(runs) == 1 else [])
    return named[0]["code"] if named else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("raw_dirs", nargs="+", type=Path, help="data/results/<date>/<topic>/raw")
    parser.add_argument("--out", type=Path, default=EXAMPLES_PATH)
    args = parser.parse_args(argv)

    questions = {q["id"]: q for q in _jsonl(ROOT / "data/train/questions.jsonl")}
    best: dict[str, dict] = {}
    for raw in args.raw_dirs:
        topic, date = raw.parent.name, raw.parent.parent.name
        scored = {s["id"]: s for s in _jsonl(ROOT / f"docs/analysis/{date}/{topic}/scored.jsonl")}
        for trace in _jsonl(raw / "trace.jsonl"):
            qid = trace.get("id")
            q, s = questions.get(qid), scored.get(qid)
            if not q or not s or s.get("score") != 1 or q["business_id"] in HOLDOUT:
                continue
            if (s.get("pred") or {}).get("type") in (None, "abstain", "unanswerable"):
                continue
            sql = final_sql(trace)
            if not sql:
                continue
            row = {
                "id": qid,
                "business_id": q["business_id"],
                "family": f"f{FAMILY.get(q['business_id'], -1)}",
                "sector": SECTOR.get(q["business_id"], ""),
                "question": q["question"],
                "answer_type": s["pred"]["type"],
                "sql": sql.strip(),
                "source": f"{date}/{topic}",
            }
            if qid not in best or len(row["sql"]) < len(best[qid]["sql"]):
                best[qid] = row
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(best.values(), key=lambda r: r["id"])
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    print(f"{len(rows)} examples from {len(args.raw_dirs)} runs -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
