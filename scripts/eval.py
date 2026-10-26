"""Local Penalized Accuracy scorer and eval runner.

    uv run python -m scripts.eval --subset dev200 --topic baseline          # run + score
    uv run python -m scripts.eval --pred result/submission.jsonl --topic x   # score only

Writes docs/analysis/<yyyy-mm-dd>/<topic>/summary.md (+ scored.jsonl) and appends a row to
docs/EXPERIMENTS.md. Never copy numbers by hand.
"""

import argparse
import json
import math
import random
import re
import subprocess
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TAU_GRID = [round(0.05 * i, 2) for i in range(21)]


# ------------------------------------------------------- scorer (rules: docs/PROJECT.md §2)


def normalize_string(text: Any) -> str:
    """NFC, lowercase, non-alphanumeric -> space, collapse spaces; diacritics are kept."""
    text = unicodedata.normalize("NFC", str(text)).lower()
    text = "".join(c if c.isalnum() else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()


def _number(value: Any) -> float | None:
    try:
        x = float(str(value).replace(",", "").strip().rstrip("%"))
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else x


def _same_number(pred: Any, gold: Any) -> bool:
    a, b = _number(pred), _number(gold)
    return a is not None and b is not None and round(a, 2) == round(b, 2)


def _same_scalar(pred: Any, gold: Any) -> bool:
    """Element of a list or table: numbers by value, everything else as a normalized string."""
    if isinstance(gold, list):  # accepted spellings
        return any(_same_scalar(pred, g) for g in gold)
    if _number(gold) is not None and _number(pred) is not None:
        return _same_number(pred, gold)
    return normalize_string(pred) == normalize_string(gold)


def match_value(answer_type: str, pred: Any, gold: Any) -> bool:
    if answer_type in ("number", "percent"):
        return _same_number(pred, gold)
    if answer_type == "string":
        golds = gold if isinstance(gold, list) else [gold]
        return any(normalize_string(pred) == normalize_string(g) for g in golds)
    if answer_type == "date":
        return str(pred).strip() == str(gold).strip()
    if answer_type == "boolean":
        return str(pred).strip().lower() == str(gold).strip().lower()
    if answer_type == "list":
        return (
            isinstance(pred, list)
            and isinstance(gold, list)
            and len(pred) == len(gold)
            and all(_same_scalar(p, g) for p, g in zip(pred, gold, strict=True))
        )
    if answer_type == "table":
        return (
            isinstance(pred, list)
            and isinstance(gold, list)
            and len(pred) == len(gold)
            and all(
                isinstance(p, list)
                and len(p) == len(g)
                and all(_same_scalar(a, b) for a, b in zip(p, g, strict=True))
                for p, g in zip(pred, gold, strict=True)
            )
        )
    return False


def score_line(pred: dict | None, gold: dict) -> int:
    """+1 correct, 0 abstain or missing, -1 wrong (answering an unanswerable one is wrong)."""
    if pred is None or pred.get("type") == "abstain":
        return 0
    if gold["type"] == "unanswerable" or pred["type"] == "unanswerable":
        return 1 if pred["type"] == gold["type"] else -1
    if pred["type"] != gold["type"] and {pred["type"], gold["type"]} != {"number", "percent"}:
        return -1
    return 1 if match_value(gold["type"], pred.get("answer"), gold.get("answer")) else -1


# ---------------------------------------------------------------- report


def _load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _summary(scores: list[int]) -> dict:
    n = len(scores)
    return {
        "n": n,
        "pa": round(sum(scores) / n, 4) if n else 0.0,
        "correct": scores.count(1),
        "wrong": scores.count(-1),
        "abstain": scores.count(0),
    }


def tau_curve(traces: dict[str, dict], golds: dict[str, dict]) -> list[tuple[float, float]]:
    """PA if we had answered the vote winner only when agreement >= tau."""
    curve = []
    for tau in TAU_GRID:
        scores = []
        for qid, gold in golds.items():
            t = traces.get(qid) or {}
            top = t.get("top")
            if top is None or t.get("agreement", 0.0) < tau:
                scores.append(0)
            else:
                scores.append(score_line({"type": top["type"], "answer": top.get("value")}, gold))
        curve.append((tau, round(sum(scores) / len(scores), 4) if scores else 0.0))
    return curve


def _table(title: str, groups: dict[str, list[int]]) -> list[str]:
    lines = [
        f"### By {title}",
        "",
        "| group | n | PA | correct | wrong | abstain |",
        "|---|---|---|---|---|---|",
    ]
    for name in sorted(groups):
        s = _summary(groups[name])
        lines.append(
            f"| {name} | {s['n']} | {s['pa']} | {s['correct']} | {s['wrong']} | {s['abstain']} |"
        )
    return lines + [""]


def report(
    preds: list[dict],
    golds: dict[str, dict],
    traces: dict[str, dict],
    questions: dict[str, dict],
    topic: str,
    command: str,
) -> Path:
    by_id = {p["id"]: p for p in preds}
    scored = []
    by_type: dict[str, list[int]] = defaultdict(list)
    by_category: dict[str, list[int]] = defaultdict(list)
    for qid, gold in golds.items():
        s = score_line(by_id.get(qid), gold)
        scored.append({"id": qid, "score": s, "pred": by_id.get(qid), "gold": gold})
        by_type[gold["type"]].append(s)
        by_category[str(questions.get(qid, {}).get("category") or "unknown")].append(s)
    total = _summary([r["score"] for r in scored])

    out = ROOT / "docs" / "analysis" / date.today().isoformat() / topic
    out.mkdir(parents=True, exist_ok=True)
    with (out / "scored.jsonl").open("w") as f:
        for row in scored:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    lines = [
        f"# Eval: {topic}",
        "",
        f"Command: `{command}`",
        "",
        f"**PA {total['pa']}** on {total['n']} questions: {total['correct']} correct, "
        f"{total['wrong']} wrong, {total['abstain']} abstain.",
        "",
    ]
    lines += _table("answer type", by_type) + _table("question category", by_category)
    if traces:
        lines += ["### PA vs tau (vote agreement threshold)", "", "| tau | PA |", "|---|---|"]
        lines += [f"| {tau} | {pa} |" for tau, pa in tau_curve(traces, golds)] + [""]
    (out / "summary.md").write_text("\n".join(lines))

    experiments = ROOT / "docs" / "EXPERIMENTS.md"
    rel = out.relative_to(ROOT / "docs")
    with experiments.open("a") as f:
        f.write(
            f"| {date.today().isoformat()} | {topic} | `{command}` | PA {total['pa']} "
            f"({total['correct']}/{total['wrong']}/{total['abstain']}), "
            f"[summary]({rel}/summary.md) |\n"
        )
    return out / "summary.md"


# ---------------------------------------------------------------- runner


def subset_ids(ids: list[str], subset: str, seed: int = 2026) -> list[str]:
    """'all', 'devN' (fixed random sample of N ids) or a path to an ids file."""
    if subset == "all":
        return sorted(ids)
    if subset.startswith("dev") and subset[3:].isdigit():
        n = int(subset[3:])
        return sorted(random.Random(seed).sample(sorted(ids), min(n, len(ids))))
    return [line.strip() for line in Path(subset).read_text().splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    sys.path.insert(0, str(ROOT))
    from src.config import settings
    from src.data.layout import load_gold, split_dir

    parser = argparse.ArgumentParser(description="Score a run with Penalized Accuracy.")
    parser.add_argument("--split", default="train")
    parser.add_argument("--subset", default="dev200")
    parser.add_argument("--topic", default="eval")
    parser.add_argument("--pred", type=Path, help="score this submission.jsonl instead of running")
    args = parser.parse_args(argv)

    root = split_dir(settings.data_dir, args.split)
    golds_all, questions = load_gold(root)
    ids = subset_ids(list(golds_all), args.subset)
    golds = {i: golds_all[i] for i in ids}
    command = " ".join(["python -m scripts.eval", *(argv or sys.argv[1:])])

    run_dir = settings.work_dir / "eval" / args.topic
    pred_path = args.pred
    trace_path = settings.work_dir / "trace.jsonl"
    if pred_path is None:
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "ids.txt").write_text("\n".join(ids) + "\n")
        trace_path.unlink(missing_ok=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "src",
                "--data",
                str(settings.data_dir),
                "--split",
                args.split,
                "--out",
                str(run_dir),
                "--ids",
                str(run_dir / "ids.txt"),
            ],
            check=True,
            cwd=ROOT,
        )
        pred_path = run_dir / "submission.jsonl"
    traces = {t["id"]: t for t in _load_jsonl(trace_path)}
    summary = report(_load_jsonl(pred_path), golds, traces, questions, args.topic, command)
    print(summary.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
