"""Eval runner: run the pipeline on a train subset and score it with src/evaluate/.

    uv run python -m scripts.eval --subset dev200 --topic baseline          # run + score
    uv run python -m scripts.eval --pred result/submission.jsonl --topic x   # score only

Writes docs/analysis/<yyyy-mm-dd>/<topic>/summary.md (+ scored.jsonl, metrics.json) and appends a
row to docs/EXPERIMENTS.md. Never copy numbers by hand.
"""

import argparse
import json
import random
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluate import (  # noqa: E402
    diagnostics,
    efficiency,
    read_submission,
    score_submission,
    summarize,
    tau_curve,
)

TAU_GRID = [round(0.05 * i, 2) for i in range(21)]


# ---------------------------------------------------------------- report


def _load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _table(title: str, groups: dict[str, list[int]]) -> list[str]:
    lines = [
        f"### By {title}",
        "",
        "| group | n | PA | correct | wrong | abstain |",
        "|---|---|---|---|---|---|",
    ]
    for name in sorted(groups):
        s = summarize(groups[name])
        lines.append(
            f"| {name} | {s['n']} | {s['pa']} | {s['correct']} | {s['wrong']} | {s['abstain']} |"
        )
    return lines + [""]


def _metric_rows(prefix: str, value: object) -> list[str]:
    """Flatten nested metric dicts into `| name | value |` rows."""
    if isinstance(value, dict):
        rows = []
        for key, sub in value.items():
            rows += _metric_rows(f"{prefix}.{key}" if prefix else key, sub)
        return rows
    return [f"| {prefix} | {value} |"]


def _describe_table(title: str, stats: dict[str, dict]) -> list[str]:
    cols = ["n", "total", "mean", "p50", "p90", "p95", "max"]
    lines = [f"#### {title}", "", "| metric | " + " | ".join(cols) + " |"]
    lines.append("|---" * (len(cols) + 1) + "|")
    for name, d in stats.items():
        lines.append(f"| {name} | " + " | ".join(str(d.get(c, "")) for c in cols) + " |")
    return lines + [""]


def efficiency_section(eff: dict) -> list[str]:
    lines = [
        "### Efficiency (not scored; inference time is the official tie-break)",
        "",
        f"- questions: {eff['questions']}; at the mean pace, "
        f"{eff['questions_per_6h_at_mean']} questions fit in 6 h",
        f"- LLM time share of wall time: {eff['llm_time_share']}",
        f"- LLM calls: {eff['llm_calls']['total']} ({eff['llm_calls']['failed']} failed); "
        f"questions over the 4-step limit: {eff['llm_steps']['over_4']}",
        f"- tokens: {eff['tokens']['prompt_total']} prompt, "
        f"{eff['tokens']['completion_total']} completion",
        "",
    ]
    lines += _describe_table(
        "Per question",
        {
            "seconds": eff["seconds_per_question"],
            "llm seconds": eff["llm_seconds_per_question"],
            "ingest seconds": eff["ingest_seconds"],
            "llm calls": eff["llm_calls"]["per_question"],
            "llm steps": eff["llm_steps"]["per_question"],
            "prompt tokens": eff["tokens"]["prompt_per_question"],
            "completion tokens": eff["tokens"]["completion_per_question"],
        },
    )
    lines += _describe_table(
        "Per LLM call",
        {
            "time to first token (s)": eff["ttft_seconds"],
            "latency (s)": eff["call_latency_seconds"],
            "decode tokens/s": eff["decode_tokens_per_second"],
            "prompt tokens": eff["tokens"]["prompt_per_call"],
            "completion tokens": eff["tokens"]["completion_per_call"],
        },
    )
    if eff["stage_seconds"]:
        lines += _describe_table("Per graph node (seconds)", eff["stage_seconds"])
    return lines


def report(
    preds: dict[str, dict],
    golds: dict[str, dict],
    traces: dict[str, dict],
    questions: dict[str, dict],
    topic: str,
    command: str,
) -> Path:
    scored = []
    by_type: dict[str, list[int]] = defaultdict(list)
    by_category: dict[str, list[int]] = defaultdict(list)
    for row in score_submission(preds, golds):
        gold = golds[row.id]
        scored.append(
            {
                "id": row.id,
                "score": row.score,
                "reason": row.reason,
                "pred": preds.get(row.id),
                "gold": gold,
            }
        )
        by_type[gold["type"]].append(row.score)
        by_category[str(questions.get(row.id, {}).get("category") or "unknown")].append(row.score)
    total = summarize([r["score"] for r in scored])
    reasons = Counter(r["reason"] for r in scored)

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
    lines += ["### By verdict", "", "| verdict | n |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(reasons.items())] + [""]
    lines += _table("answer type", by_type) + _table("question category", by_category)
    run_traces = [traces[i] for i in golds if i in traces]
    diag = diagnostics(preds, golds, traces)
    eff = efficiency(run_traces)
    lines += ["### Diagnostics (not scored)", "", "| metric | value |", "|---|---|"]
    lines += _metric_rows("", diag) + [""]
    if traces:
        lines += ["### PA vs tau (vote agreement threshold)", "", "| tau | PA |", "|---|---|"]
        lines += [f"| {tau} | {pa} |" for tau, pa in tau_curve(traces, golds, TAU_GRID)] + [""]
    if run_traces:
        lines += efficiency_section(eff)
    (out / "summary.md").write_text("\n".join(lines))
    metrics = {"pa": total, "verdicts": dict(reasons), "diagnostics": diag, "efficiency": eff}
    (out / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))

    experiments = ROOT / "docs" / "EXPERIMENTS.md"
    rel = out.relative_to(ROOT / "docs")
    with experiments.open("a") as f:
        f.write(
            f"| {date.today().isoformat()} | {topic} | `{command}` | PA {total['pa']} "
            f"({total['correct']}/{total['wrong']}/{total['abstain']}), "
            f"{eff['seconds_per_question'].get('mean', '-')} s/q, "
            f"{eff['tokens']['prompt_per_question'].get('mean', '-')} prompt tok/q, "
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
    preds = read_submission(pred_path.read_text().splitlines()) if pred_path.is_file() else {}
    summary = report(preds, golds, traces, questions, args.topic, command)
    print(summary.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
