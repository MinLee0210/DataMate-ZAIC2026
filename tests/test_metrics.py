from src.evaluate import auroc, describe, diagnostics, efficiency, percentile


def call(prompt=100, completion=20, ttft=0.1, latency=0.5, error=None):
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "ttft_s": ttft,
        "latency_s": latency,
        "error": error,
    }


def test_percentile_is_nearest_rank():
    assert percentile([], 50) is None
    assert percentile([3, 1, 2], 50) == 2
    assert percentile([1, 2, 3, 4], 90) == 4
    assert describe([None, 1, 3]) == {
        "n": 2,
        "total": 4.0,
        "mean": 2.0,
        "p50": 1.0,
        "p90": 3.0,
        "p95": 3.0,
        "max": 3.0,
    }
    assert describe([None]) == {"n": 0}


def test_efficiency_from_traces():
    traces = [
        {
            "seconds": 2.0,
            "repairs": 0,
            "llm": [call(), call(), call()],
            "timings": {"generate": 1.5, "execute": 0.2},
        },
        {
            "seconds": 4.0,
            "repairs": 2,
            "llm": [call(prompt=200), call(error="timeout")],
            "timings": {"generate": 1.0, "repair": 2.0},
        },
        {"seconds": 0.0, "error": "time budget"},  # skipped question: no LLM data
    ]
    eff = efficiency(traces)
    assert eff["questions"] == 3
    assert eff["llm_calls"]["total"] == 5
    assert eff["llm_calls"]["failed"] == 1
    assert eff["tokens"]["prompt_total"] == 300 + 200 + 100
    assert eff["tokens"]["completion_total"] == 100
    assert eff["llm_steps"]["per_question"]["max"] == 3.0
    assert eff["llm_steps"]["over_4"] == 0
    assert eff["ttft_seconds"]["mean"] == 0.1
    assert eff["decode_tokens_per_second"]["p50"] == 50.0  # 20 tokens / 0.4 s
    assert eff["stage_seconds"]["generate"]["total"] == 2.5
    assert eff["questions_per_6h_at_mean"] == 10800  # 2 s per question


def test_efficiency_handles_missing_usage():
    eff = efficiency(
        [{"seconds": 1.0, "repairs": 0, "llm": [call(prompt=None, completion=None, ttft=None)]}]
    )
    assert eff["tokens"]["prompt_total"] is None
    assert eff["ttft_seconds"] == {"n": 0}


def test_auroc():
    assert auroc([0.9, 0.8, 0.2], [True, True, False]) == 1.0
    assert auroc([0.5, 0.5], [True, False]) == 0.5
    assert auroc([0.5], [True]) is None


def test_diagnostics():
    golds = {
        "a": {"type": "number", "answer": 1},
        "b": {"type": "number", "answer": 2},
        "c": {"type": "unanswerable", "answer": None},
    }
    preds = {
        "a": {"id": "a", "type": "number", "answer": 1},
        "b": {"id": "b", "type": "abstain"},
        "c": {"id": "c", "type": "unanswerable"},
    }
    traces = {
        "a": {
            "agreement": 1.0,
            "top": {"type": "number", "value": 1},
            "repairs": 0,
            "candidates": [{"type": "number", "value": 1, "error": None}],
        },
        # abstained, but one candidate had the right answer: counts for oracle@k
        "b": {
            "agreement": 0.33,
            "top": {"type": "number", "value": 5},
            "repairs": 1,
            "candidates": [
                {"type": "number", "value": 5, "error": None},
                {"type": "number", "value": 2, "error": None},
                {"type": "number", "value": 2, "error": "boom"},
            ],
        },
        "c": {
            "agreement": 1.0,
            "top": {"type": "unanswerable", "value": None},
            "repairs": 0,
            "candidates": [{"type": "unanswerable", "value": None, "error": None}],
        },
    }
    d = diagnostics(preds, golds, traces)
    assert d["coverage"] == round(2 / 3, 4)
    assert d["selective_accuracy"] == 1.0
    assert d["oracle_at_k"] == 1.0
    assert d["top_accuracy"] == round(2 / 3, 4)
    assert d["agreement_auroc"] == 1.0
    assert d["repair_rate"] == round(1 / 3, 4)
    assert d["unanswerable_precision"] == 1.0
    assert d["unanswerable_recall"] == 1.0
