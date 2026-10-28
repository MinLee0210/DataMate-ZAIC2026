"""Report evaluation results to Weights & Biases (project zaic2026-datamate). Dev only.

It reads what the eval already wrote, so nothing in src/ or scripts/eval.py imports wandb:

    W="uv run --extra tracking python -m scripts.devfree.wandb_report"

    # a train eval: docs/analysis/<date>/<topic>/ (metrics.json, summary.md)
    $W eval --date 2026-10-27 --topic ca-thinking
    $W eval --all                                   # every eval so far

    # a public_test run (no labels): submission and trace, plus the leaderboard PA if known
    $W test --name public-test-qwen3 \
        --submission data/results/<date>/public-test-qwen3/submission.jsonl \
        --trace data/results/<date>/public-test-qwen3/trace.jsonl \
        --model Qwen/Qwen3-14B-FP8 --pipeline ca --thinking --hardware "1x A40" \
        [--leaderboard-pa 0.12]

WANDB_API_KEY comes from the environment or .env. Test predictions are never uploaded, only
counts and timings; train runs upload their report files.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.evaluate import efficiency  # noqa: E402

PROJECT = "zaic2026-datamate"
ANALYSIS = ROOT / "docs" / "analysis"


def _api_key() -> None:
    if os.environ.get("WANDB_API_KEY"):
        return
    env = ROOT / ".env"
    if env.is_file():
        for line in env.read_text().splitlines():
            if line.startswith("WANDB_API_KEY="):
                os.environ["WANDB_API_KEY"] = line.split("=", 1)[1].strip()


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def _legacy_config(topic: str, summary: str) -> dict:
    """Config of evals run before metrics.json recorded it (2026-10-27), from the topic name."""
    model = re.search(r"Model: `([^`]+)`", summary)
    workers = re.search(r"--workers (\d+)", summary)
    return {
        "model": model.group(1) if model else "unknown",
        "pipeline": "ca" if topic.startswith("ca") else "vote",
        "thinking": "thinking" in topic,
        "subset": "dev200" if "abstain" not in topic else "ids file",
        "workers": int(workers.group(1)) if workers else 1,
        "split": "train",
    }


def _flat(prefix: str, value: object, out: dict) -> dict:
    if isinstance(value, dict):
        for key, sub in value.items():
            _flat(f"{prefix}/{key}" if prefix else str(key), sub, out)
    elif isinstance(value, int | float) and not isinstance(value, bool):
        out[prefix] = value
    return out


def report_eval(run_dir: Path) -> None:
    import wandb

    metrics = json.loads((run_dir / "metrics.json").read_text())
    summary = (run_dir / "summary.md").read_text()
    date, topic = run_dir.parent.name, run_dir.name
    config = {**_legacy_config(topic, summary), **metrics.get("config", {})}
    config.update(date=date, topic=topic)
    pa = metrics["pa"]
    answered = pa["correct"] + pa["wrong"]

    run = wandb.init(
        project=PROJECT,
        name=f"{date}/{topic}",
        job_type="eval-train",
        group=config.get("subset", "dev200"),
        tags=[
            config["model"],
            config["pipeline"],
            "thinking" if config["thinking"] else "no-thinking",
        ],
        config=config,
        reinit="finish_previous",
    )
    eff = metrics.get("efficiency", {})
    run.summary.update(
        {
            "pa": pa["pa"],
            "correct": pa["correct"],
            "wrong": pa["wrong"],
            "abstain": pa["abstain"],
            "n": pa["n"],
            "precision_answered": round(pa["correct"] / answered, 4) if answered else None,
            "seconds_per_question": eff.get("seconds_per_question", {}).get("mean"),
            "prompt_tokens_per_question": eff.get("tokens", {})
            .get("prompt_per_question", {})
            .get("mean"),
            "completion_tokens_per_question": eff.get("tokens", {})
            .get("completion_per_question", {})
            .get("mean"),
            **{f"verdict/{k}": v for k, v in metrics.get("verdicts", {}).items()},
            **_flat("diagnostics", metrics.get("diagnostics", {}), {}),
        }
    )
    by_type = metrics.get("by_answer_type") or _types_from_summary(summary)
    if by_type:
        table = wandb.Table(columns=["answer_type", "n", "pa", "correct", "wrong", "abstain"])
        for name, s in by_type.items():
            table.add_data(name, s["n"], s["pa"], s["correct"], s["wrong"], s["abstain"])
        run.log({"by_answer_type": table})
    curve = metrics.get("tau_curve") or _tau_from_summary(summary)
    if curve:
        table = wandb.Table(data=[[float(t), float(p)] for t, p in curve], columns=["tau", "pa"])
        run.log({"pa_vs_tau": wandb.plot.line(table, "tau", "pa", title="PA vs tau")})
    artifact = wandb.Artifact(f"eval-{date}-{topic}".replace("/", "-"), type="eval-report")
    for name in ("summary.md", "metrics.json", "scored.jsonl"):
        if (run_dir / name).is_file():
            artifact.add_file(str(run_dir / name))
    run.log_artifact(artifact)
    run.finish()
    print(f"reported {date}/{topic}: PA {pa['pa']}")


def _types_from_summary(summary: str) -> dict:
    """Per-type rows of the summary's 'By answer type' table (evals before 2026-10-28)."""
    part = summary.split("### By answer type", 1)[-1].split("###", 1)[0]
    rows = {}
    for line in part.splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == 6 and cells[1].isdigit():
            rows[cells[0]] = dict(
                zip(["n", "pa", "correct", "wrong", "abstain"], map(float, cells[1:]), strict=True)
            )
    return rows


def _tau_from_summary(summary: str) -> list[tuple[float, float]]:
    part = summary.split("### PA vs tau", 1)[-1].split("###", 1)[0]
    rows = re.findall(r"^\| ([0-9.]+) \| (-?[0-9.]+) \|$", part, flags=re.M)
    return [(float(t), float(p)) for t, p in rows]


def report_test(args: argparse.Namespace) -> None:
    import wandb

    lines = _jsonl(args.submission)
    types = Counter(line["type"] for line in lines)
    traces = _jsonl(args.trace) if args.trace and args.trace.is_file() else []
    eff = efficiency(traces) if traces else {}
    config = {
        "split": args.split,
        "model": args.model,
        "pipeline": args.pipeline,
        "thinking": args.thinking,
        "hardware": args.hardware,
        "workers": args.workers,
    }
    run = wandb.init(
        project=PROJECT,
        name=args.name,
        job_type="test-run",
        group=args.split,
        tags=[
            args.model,
            args.pipeline,
            "thinking" if args.thinking else "no-thinking",
            args.split,
        ],
        config=config,
        reinit="finish_previous",
    )
    answered = sum(n for t, n in types.items() if t != "abstain")
    run.summary.update(
        {
            "lines": len(lines),
            "answered": answered,
            "abstain": types.get("abstain", 0),
            "answer_rate": round(answered / len(lines), 4) if lines else None,
            **{f"type/{t}": n for t, n in sorted(types.items())},
            "question_errors": sum(1 for t in traces if t.get("error")),
            "seconds_per_question": eff.get("seconds_per_question", {}).get("mean"),
            "completion_tokens_per_question": eff.get("tokens", {})
            .get("completion_per_question", {})
            .get("mean"),
        }
    )
    if args.leaderboard_pa is not None:
        run.summary["leaderboard_pa"] = args.leaderboard_pa
    run.finish()
    print(f"reported {args.name}: {len(lines)} lines, {answered} answered")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="kind", required=True)
    ev = sub.add_parser("eval", help="a train eval written by scripts/eval.py")
    ev.add_argument("--date")
    ev.add_argument("--topic")
    ev.add_argument("--all", action="store_true", help="every docs/analysis/<date>/<topic>")
    te = sub.add_parser("test", help="a public or private test run (no labels)")
    te.add_argument("--name", required=True)
    te.add_argument("--submission", type=Path, required=True)
    te.add_argument("--trace", type=Path)
    te.add_argument("--split", default="public_test")
    te.add_argument("--model", default="Qwen/Qwen3-14B-FP8")
    te.add_argument("--pipeline", default="ca")
    te.add_argument("--thinking", action="store_true")
    te.add_argument("--hardware", default="")
    te.add_argument("--workers", type=int, default=0)
    te.add_argument("--leaderboard-pa", type=float)
    args = parser.parse_args(argv)

    _api_key()
    if args.kind == "test":
        report_test(args)
        return 0
    if args.all:
        runs = sorted(p.parent for p in ANALYSIS.glob("*/*/metrics.json"))
    else:
        if not (args.date and args.topic):
            parser.error("eval needs --date and --topic, or --all")
        runs = [ANALYSIS / args.date / args.topic]
    for run_dir in runs:
        report_eval(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
