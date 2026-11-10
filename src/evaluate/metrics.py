"""Extra metrics, not scored by the challenge: cost, latency and diagnostics, from the trace.

Each trace line (written by `src/__main__.py` and `QAService.answer`) may hold:
`seconds` (wall time of the question), `ingest_s`, `timings` (seconds per graph node), `llm`
(one record per chat call: prompt / completion tokens, time to first token, latency, error),
`agreement`, `top`, `repairs`, `candidates`. Missing fields are skipped, so old traces still work.

Why these matter here:
- Inference time is the official tie-break, and the private run has a 6 h limit (PROJECT.md §3).
- At most 4 LLM steps per question (CLAUDE.md). `llm_steps` counts graph LLM nodes (generate,
  repair); `llm_calls` counts requests (k per step).
- PA rewards abstaining when P(correct) <= 0.5, so calibration diagnostics sit next to PA.
"""

import math
from collections.abc import Iterable
from typing import Any

from src.evaluate.scorer import judge

SIX_HOURS_S = 6 * 3600


def percentile(values: list[float], q: float) -> float | None:
    """Nearest-rank percentile (deterministic, no interpolation); None for no values."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(q / 100 * len(ordered)))
    return ordered[rank - 1]


def describe(values: Iterable[float | None]) -> dict:
    """n, total, mean, p50, p90, p95, max over the non-null values."""
    xs = [float(v) for v in values if v is not None]
    if not xs:
        return {"n": 0}
    return {
        "n": len(xs),
        "total": round(sum(xs), 4),
        "mean": round(sum(xs) / len(xs), 4),
        "p50": round(percentile(xs, 50), 4),
        "p90": round(percentile(xs, 90), 4),
        "p95": round(percentile(xs, 95), 4),
        "max": round(max(xs), 4),
    }


def _calls(trace: dict) -> list[dict]:
    return trace.get("llm") or []


def _sum(values: Iterable[Any]) -> int | None:
    xs = [v for v in values if v is not None]
    return sum(xs) if xs else None


def _llm_steps(trace: dict) -> int:
    """Graph LLM steps: one generate plus one per repair round."""
    if "llm_steps" in trace:  # the MALT pipeline counts its own steps
        return int(trace["llm_steps"])
    if "repairs" not in trace and not _calls(trace):
        return 0
    return 1 + int(trace.get("repairs") or 0)


def efficiency(traces: list[dict], max_llm_steps: int = 4) -> dict:
    """Time, tokens and LLM-call statistics over the given question traces."""
    calls = [c for t in traces for c in _calls(t)]
    per_q_prompt = [_sum(c.get("prompt_tokens") for c in _calls(t)) for t in traces]
    per_q_completion = [_sum(c.get("completion_tokens") for c in _calls(t)) for t in traces]
    decode_tps = [
        c["completion_tokens"] / (c["latency_s"] - c["ttft_s"])
        for c in calls
        if c.get("completion_tokens")
        and c.get("ttft_s") is not None
        and c.get("latency_s", 0) > c["ttft_s"]
    ]
    seconds = [t.get("seconds") for t in traces]
    llm_seconds = [_sum(c.get("latency_s") for c in _calls(t)) for t in traces]
    stages: dict[str, list[float]] = {}
    for t in traces:
        for name, s in (t.get("timings") or {}).items():
            stages.setdefault(name, []).append(s)
    sec = describe(seconds)
    steps = [_llm_steps(t) for t in traces]
    return {
        "questions": len(traces),
        "seconds_per_question": sec,
        "questions_per_6h_at_mean": int(SIX_HOURS_S / sec["mean"]) if sec.get("mean") else None,
        "llm_seconds_per_question": describe(llm_seconds),
        "llm_time_share": (
            round(sum(x for x in llm_seconds if x) / sec["total"], 4) if sec.get("total") else None
        ),
        "ingest_seconds": describe(t.get("ingest_s") for t in traces),
        "stage_seconds": {name: describe(v) for name, v in sorted(stages.items())},
        "llm_calls": {
            "total": len(calls),
            "per_question": describe(len(_calls(t)) for t in traces),
            "failed": sum(1 for c in calls if c.get("error")),
        },
        "llm_steps": {
            "per_question": describe(steps),
            f"over_{max_llm_steps}": sum(1 for s in steps if s > max_llm_steps),
        },
        "tokens": {
            "prompt_total": _sum(per_q_prompt),
            "completion_total": _sum(per_q_completion),
            "prompt_per_question": describe(per_q_prompt),
            "completion_per_question": describe(per_q_completion),
            "prompt_per_call": describe(c.get("prompt_tokens") for c in calls),
            "completion_per_call": describe(c.get("completion_tokens") for c in calls),
        },
        "ttft_seconds": describe(c.get("ttft_s") for c in calls),
        "call_latency_seconds": describe(c.get("latency_s") for c in calls),
        "decode_tokens_per_second": describe(decode_tps),
    }


def auroc(scores: list[float], labels: list[bool]) -> float | None:
    """P(score of a random positive > score of a random negative), ties count half."""
    pos = [s for s, y in zip(scores, labels, strict=True) if y]
    neg = [s for s, y in zip(scores, labels, strict=True) if not y]
    if not pos or not neg:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return round(wins / (len(pos) * len(neg)), 4)


def diagnostics(preds: dict[str, dict], golds: dict[str, dict], traces: dict[str, dict]) -> dict:
    """Quality signals beyond PA: coverage, selective accuracy, oracle@k, calibration."""
    answered = correct = 0
    pred_unans = true_unans = gold_unans = 0
    oracle_hits = with_candidates = 0
    agreement, top_correct = [], []
    for qid, gold in golds.items():
        pred = preds.get(qid)
        score, _ = judge(pred, gold)
        if pred is not None and pred.get("type") != "abstain":
            answered += 1
            correct += score == 1
        gold_unans += gold["type"] == "unanswerable"
        if pred is not None and pred.get("type") == "unanswerable":
            pred_unans += 1
            true_unans += gold["type"] == "unanswerable"
        trace = traces.get(qid) or {}
        ok = [c for c in trace.get("candidates") or [] if not c.get("error")]
        if trace.get("candidates") is not None:
            with_candidates += 1
            oracle_hits += any(
                judge({"type": c["type"], "answer": c.get("value")}, gold)[0] == 1 for c in ok
            )
        top = trace.get("top")
        if top is not None and "agreement" in trace:
            agreement.append(trace["agreement"])
            top_correct.append(
                judge({"type": top["type"], "answer": top.get("value")}, gold)[0] == 1
            )
    n = len(golds)
    return {
        "coverage": round(answered / n, 4) if n else None,
        "selective_accuracy": round(correct / answered, 4) if answered else None,
        "oracle_at_k": round(oracle_hits / with_candidates, 4) if with_candidates else None,
        "top_accuracy": round(sum(top_correct) / len(top_correct), 4) if top_correct else None,
        "agreement_auroc": auroc(agreement, top_correct),
        "repair_rate": (
            round(sum(1 for t in traces.values() if t.get("repairs")) / len(traces), 4)
            if traces
            else None
        ),
        "unanswerable_precision": round(true_unans / pred_unans, 4) if pred_unans else None,
        "unanswerable_recall": round(true_unans / gold_unans, 4) if gold_unans else None,
        "errors": sum(1 for t in traces.values() if t.get("error")),
    }
