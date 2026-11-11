"""Score the deterministic family compilers on a train subset. No LLM, no GPU.

    uv run python -m scripts.compiler_eval --split train --subset /workspace/dev500.txt \
        --base data/results/.../submission.jsonl

Per family it prints n / correct / wrong / precision. With `--base`, questions the compiler does
not handle fall back to that submission, so the printed PA is the end-to-end estimate of adding
the compilers to the pipeline.
"""

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd

from src.config import settings
from src.data.layout import business_dir, calendar_file, load_gold, split_dir
from src.evaluate.scorer import judge
from src.modules.questions.compiler import compile_question
from src.services.ingest import IngestService
from src.utils.format import format_result, is_money_question, round_money
from src.utils.timeparse import LunarCalendar, resolve


def _same(pred: dict | None, base: dict | None) -> bool:
    """The compiler and the model agree on the same value (numbers within 1 %)."""
    if not pred or not base or base.get("type") in ("abstain", "unanswerable"):
        return False
    if pred.get("type") != base.get("type"):
        return False
    left, right = pred.get("answer"), base.get("answer")
    if isinstance(left, int | float) and isinstance(right, int | float):
        return abs(left - right) <= max(1.0, 0.01 * abs(right))
    return left == right


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", default="train")
    parser.add_argument("--subset", type=Path, help="file with one question id per line")
    parser.add_argument("--base", type=Path, help="submission used for questions with no compiler")
    parser.add_argument("--families", nargs="*", help="only these compiler families are used")
    args = parser.parse_args(argv)

    root = split_dir(settings.data_dir, args.split)
    gold, questions = load_gold(root)
    ids = (
        [line.strip() for line in args.subset.read_text().splitlines() if line.strip()]
        if args.subset
        else sorted(questions)
    )
    calendar_path = calendar_file(root)
    lunar = LunarCalendar.from_csv(calendar_path) if calendar_path else None
    ingest = IngestService(settings.work_dir, calendar=calendar_path)
    enabled = set(args.families) if args.families else None
    base = {}
    if args.base:
        base = {
            json.loads(line)["id"]: json.loads(line) for line in args.base.read_text().splitlines()
        }

    stats: dict[str, Counter] = defaultdict(Counter)
    combined: Counter = Counter()
    voted: Counter = Counter()
    failures: list[str] = []
    examples: dict[str, list[str]] = defaultdict(list)
    for qid in ids:
        question = questions[qid]
        context = ingest.load(question["business_id"], business_dir(root, question["business_id"]))
        ranges = resolve(question["question"], date.fromisoformat(question["as_of_date"]), lunar)
        has_sales = any(item.startswith("v_sales(") for item in context.semantic)
        has_orders = any(item.startswith("v_orders(") for item in context.semantic)
        compiled = compile_question(
            question["question"],
            ranges,
            has_sales,
            has_orders,
            as_of=date.fromisoformat(question["as_of_date"]),
        )
        if compiled is not None and enabled is not None and compiled.family not in enabled:
            compiled = None
        pred = None
        family = compiled.family if compiled else "none"
        stats[family]["n"] += 1
        if compiled is not None:
            try:
                conn = duckdb.connect(str(context.db_path), read_only=True)
                row = conn.execute(compiled.sql).fetchone()
                conn.close()
                value = row[0] if row else None
                if value is not None:
                    answer = format_result(compiled.answer_type, pd.DataFrame({"answer": [value]}))
                    if compiled.answer_type == "number" and is_money_question(question["question"]):
                        answer = round_money(answer)
                    pred = {"type": compiled.answer_type, "answer": answer}
            except Exception as error:  # a failed compile is a miss, not a crash
                failures.append(f"{qid} {family}: {type(error).__name__}: {error}")
        if pred is None:
            stats[family]["none"] += 1
        score, _ = judge(pred, gold[qid])
        stats[family]["correct" if score == 1 else "wrong" if score == -1 else "abstain"] += 1
        if compiled is not None and score == -1 and len(examples[family]) < 5:
            examples[family].append(
                f"{qid} | {question['question'][:90]} | gold {gold[qid].get('answer')!r}"
                f" | pred {pred} | {compiled.sql[:140]}"
            )
        chosen = pred if pred is not None else base.get(qid)
        cscore, _ = judge(chosen, gold[qid])
        combined[cscore] += 1
        if compiled is not None:
            vote = pred if _same(pred, base.get(qid)) else None
        else:
            vote = base.get(qid)
        vote_score, _ = judge(vote, gold[qid])
        voted[vote_score] += 1

    print(f"{'family':24s} {'n':>5s} {'ok':>4s} {'wrong':>5s} {'none':>5s} {'prec':>6s}")
    for family in sorted(stats, key=lambda name: -stats[name]["n"]):
        row = stats[family]
        answered = row["correct"] + row["wrong"]
        precision = row["correct"] / answered if answered else 0.0
        print(
            f"{family:24s} {row['n']:5d} {row['correct']:4d} {row['wrong']:5d}"
            f" {row['none']:5d} {precision:6.2f}"
        )
    total = sum(combined.values())
    print(
        f"\ncombined PA {((combined[1] - combined[-1]) / total):.4f}"
        f" on {total}: {combined[1]} correct, {combined[-1]} wrong, {combined[0]} abstain"
    )
    total_vote = sum(voted.values())
    print(
        f"vote PA {((voted[1] - voted[-1]) / total_vote):.4f}"
        f" on {total_vote}: {voted[1]} correct, {voted[-1]} wrong, {voted[0]} abstain"
    )
    for failure in failures[:10]:
        print("  FAIL", failure)
    for family, items in sorted(examples.items()):
        print(f"\n== wrong {family}")
        for item in items:
            print("  ", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
