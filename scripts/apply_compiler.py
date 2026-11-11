"""Replace a submission's answers with deterministic compiler answers where a family matches.

CPU only, no LLM. Used to turn an existing run into a compiler-augmented submission, and to
measure the gain when the split has gold (`--score`).

    uv run python -m scripts.apply_compiler --split public_test \
        --base /workspace/result/public-test/submission.jsonl \
        --out /workspace/result/public-compiler/submission.jsonl
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import duckdb
import pandas as pd

from src.config import settings
from src.data.layout import business_dir, calendar_file, load_gold, load_questions, split_dir
from src.evaluate.scorer import judge
from src.modules.questions.compiler import compile_question
from src.services.ingest import IngestService
from src.utils.format import format_result, is_money_question, round_money
from src.utils.timeparse import LunarCalendar, resolve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", default="public_test")
    parser.add_argument("--subset", type=Path, help="question ids to process, one per line")
    parser.add_argument("--base", type=Path, required=True, help="submission to replace answers in")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--families", nargs="*", help="only these compiler families")
    parser.add_argument("--score", action="store_true", help="the split has gold; print PA")
    args = parser.parse_args(argv)

    root = split_dir(settings.data_dir, args.split)
    questions = {q.id: q for q in load_questions(root)}
    ids = (
        [line.strip() for line in args.subset.read_text().splitlines() if line.strip()]
        if args.subset
        else list(questions)
    )
    base = {json.loads(line)["id"]: json.loads(line) for line in args.base.read_text().splitlines()}
    enabled = set(args.families) if args.families else None
    calendar_path = calendar_file(root)
    lunar = LunarCalendar.from_csv(calendar_path) if calendar_path else None
    ingest = IngestService(settings.work_dir, calendar=calendar_path)
    gold = load_gold(root)[0] if args.score else {}

    counts: Counter = Counter()
    used: Counter = Counter()
    scores: list[int] = []
    lines: list[dict] = []
    for qid in ids:
        question = questions[qid]
        row = base.get(qid) or {"id": qid, "type": "abstain"}
        context = ingest.load(question.business_id, business_dir(root, question.business_id))
        ranges = resolve(question.question, question.as_of_date, lunar)
        compiled = compile_question(
            question.question,
            ranges,
            any(item.startswith("v_sales(") for item in context.semantic),
            any(item.startswith("v_orders(") for item in context.semantic),
            as_of=question.as_of_date,
        )
        if compiled is not None and (enabled is None or compiled.family in enabled):
            try:
                conn = duckdb.connect(str(context.db_path), read_only=True)
                value = conn.execute(compiled.sql).fetchone()[0]
                conn.close()
                if value is not None:
                    answer = format_result(compiled.answer_type, pd.DataFrame({"answer": [value]}))
                    if compiled.answer_type == "number" and is_money_question(question.question):
                        answer = round_money(answer)
                    row = {"id": qid, "type": compiled.answer_type, "answer": answer}
                    used[compiled.family] += 1
            except Exception:  # a failed compiler keeps the base answer
                pass
        counts[row["type"]] += 1
        lines.append(row)
        if args.score:
            scores.append(judge(row, gold[qid])[0])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in lines:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(lines)} lines to {args.out}")
    print("types", counts.most_common())
    print("compiled", used.most_common())
    if args.score and scores:
        pa = sum(scores) / len(scores)
        print(
            f"PA {pa:.4f}: {scores.count(1)} correct, {scores.count(-1)} wrong,"
            f" {scores.count(0)} abstain"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
