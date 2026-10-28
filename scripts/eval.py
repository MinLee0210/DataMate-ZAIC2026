"""Eval runner: run the pipeline on a train subset and score it with src/evaluate/.

    uv run python -m scripts.eval --subset dev200 --topic baseline          # run + score
    uv run python -m scripts.eval --pred result/submission.jsonl --topic x   # score only

Writes docs/analysis/<yyyy-mm-dd>/<topic>/summary.md (+ scored.jsonl, metrics.json), appends a
row to docs/EXPERIMENTS.md and exports the run's submission to
data/results/<yyyy-mm-dd>/<topic>/submission.jsonl in the rulebook §9 format. Never copy numbers by
hand.
"""

import argparse
import json
import random
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.splits import HOLDOUT  # noqa: E402
from src.evaluate import (  # noqa: E402
    check_format,
    diagnostics,
    efficiency,
    read_submission,
    score_submission,
    summarize,
    tau_curve,
)
from src.models import SubmissionLine  # noqa: E402

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
    model: str = "",
    config: dict | None = None,
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
        f"Model: `{model or 'not recorded'}`",
        "",
        "Config: " + ", ".join(f"`{k}={v}`" for k, v in (config or {}).items()),
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
    by_type_summary = {name: summarize(scores) for name, scores in sorted(by_type.items())}
    metrics = {
        "config": {"model": model, **(config or {})},
        "pa": total,
        "by_answer_type": by_type_summary,
        "tau_curve": tau_curve(traces, golds, TAU_GRID) if traces else [],
        "verdicts": dict(reasons),
        "diagnostics": diag,
        "efficiency": eff,
    }
    (out / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n")

    experiments = ROOT / "docs" / "EXPERIMENTS.md"
    rel = out.relative_to(ROOT / "docs")
    with experiments.open("a") as f:
        f.write(
            f"| {date.today().isoformat()} | {topic} ({model or '-'}) | `{command}` | "
            f"PA {total['pa']} "
            f"({total['correct']}/{total['wrong']}/{total['abstain']}), "
            f"{eff['seconds_per_question'].get('mean', '-')} s/q, "
            f"{eff['tokens']['prompt_per_question'].get('mean', '-')} prompt tok/q, "
            f"[summary]({rel}/summary.md) |\n"
        )
    return out / "summary.md"


def export_submission(pred_path: Path, topic: str) -> Path:
    """Rewrite a submission in the rulebook §9 format under data/results/<date>/<topic>/.

    Each readable line is re-serialized through SubmissionLine (unanswerable gets a string
    `reason`); a line whose answer fails the type's format check raises, so a broken file is
    never exported. Lines are sorted by id, so a threaded run exports the same file as a serial one.
    """
    out = ROOT / "data" / "results" / date.today().isoformat() / topic / "submission.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    preds = read_submission(pred_path.read_text().splitlines())
    lines = []
    for pred in sorted(preds.values(), key=lambda p: p["id"]):
        line = SubmissionLine(id=pred["id"], type=pred["type"], answer=pred.get("answer"))
        if line.type != "abstain" and not check_format(line.type, line.answer):
            raise ValueError(f"bad {line.type} format for {line.id}: {line.answer!r}")
        lines.append(json.dumps(line.record(), ensure_ascii=False))
    out.write_text("\n".join(lines) + "\n" if lines else "")
    return out


# ---------------------------------------------------------------- runner


def subset_ids(
    ids: list[str], subset: str, seed: int = 2026, business_of: dict[str, str] | None = None
) -> list[str]:
    """'all', 'devN' (fixed random sample of N ids), 'holdout' / 'holdoutN' (questions of the
    hold-out businesses, scripts/splits.py) or a path to an ids file."""
    if subset == "all":
        return sorted(ids)
    if subset.startswith("holdout") and (subset == "holdout" or subset[7:].isdigit()):
        held = sorted(i for i in ids if (business_of or {}).get(i) in HOLDOUT)
        if subset == "holdout":
            return held
        return sorted(random.Random(seed).sample(held, min(int(subset[7:]), len(held))))
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
    parser.add_argument("--workers", type=int, default=settings.workers, help="question threads")
    parser.add_argument("--pred", type=Path, help="score this submission.jsonl instead of running")
    args = parser.parse_args(argv)

    root = split_dir(settings.data_dir, args.split)
    golds_all, questions = load_gold(root)
    business_of = {i: q.get("business_id") for i, q in questions.items()}
    ids = subset_ids(list(golds_all), args.subset, business_of=business_of)
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
                "--workers",
                str(args.workers),
            ],
            check=True,
            cwd=ROOT,
        )
        pred_path = run_dir / "submission.jsonl"
    if pred_path == run_dir / "submission.jsonl" and trace_path.is_file():
        # keep this run's traces next to its submission; the next run overwrites trace.jsonl
        shutil.copy(trace_path, run_dir / "trace.jsonl")
    traces = {t["id"]: t for t in _load_jsonl(trace_path)}
    preds = read_submission(pred_path.read_text().splitlines()) if pred_path.is_file() else {}
    config = {
        "split": args.split,
        "subset": args.subset,
        "pipeline": settings.pipeline,
        "thinking": bool(settings.analyze_body)
        if settings.pipeline == "ca" or settings.analyze
        else False,
        "analyze_extra_body": settings.analyze_extra_body,
        "analyze_max_tokens": settings.analyze_max_tokens,
        "k": settings.k,
        "tau": settings.tau,
        "workers": args.workers,
        "llm_base_url": settings.llm_base_url,
    }
    summary = report(
        preds, golds, traces, questions, args.topic, command, settings.llm_model, config
    )
    if pred_path.is_file():
        print(f"submission exported to {export_submission(pred_path, args.topic)}")
    print(summary.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
