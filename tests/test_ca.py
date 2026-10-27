import json

import pandas as pd
import pytest

from src.config import settings
from src.modules.python_exec import UnsafeCodeError, run_python
from tests.conftest import FakeLLM
from tests.test_qa import REVENUE_LAST_WEEK, question, service_for


def no_query(sql):
    raise AssertionError("not expected")


def test_python_reads_named_results():
    frame = pd.DataFrame({"sp": ["a", "b"], "sl": [3, 5]})
    out = run_python(
        "result = results['sales'].sort_values('sl', ascending=False)['sp'].tolist()",
        no_query,
        {"sales": frame},
    )
    assert out.iloc[:, 0].tolist() == ["b", "a"]


@pytest.mark.parametrize(
    "code",
    [
        "import os\nresult = 1",
        "result = open('x').read()",
        "result = ().__class__",
        "result = __import__('os')",
        "results['x'].to_csv('/tmp/x')",
    ],
)
def test_python_rejects_unsafe_code(code):
    with pytest.raises(UnsafeCodeError):
        run_python(code, no_query)


def test_python_needs_result():
    with pytest.raises(ValueError, match="result"):
        run_python("x = 1", no_query)


def ca_replies(final: dict):
    def reply(prompt):
        if "first step: reason over the schema" in prompt:
            return json.dumps(
                {
                    "thought": "doanh thu = sum(thanh_tien_vnd)",
                    "sample_fields": ["orders.ngay", "nope.x"],
                }
            )
        if "plan the data queries" in prompt:
            return json.dumps(
                {
                    "thought": "one query",
                    "data_queries": [
                        {"name": "rev", "question": "doanh thu", "sql": REVENUE_LAST_WEEK}
                    ],
                }
            )
        return json.dumps(final)

    return reply


def test_ca_pipeline_answers_from_a_named_result(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    llm = FakeLLM(
        ca_replies(
            {"thought": "ok", "action": "final", "answer_type": "number", "data_result": "rev"}
        )
    )
    answer, trace = service_for(toy_split, tmp_path, llm).answer(question())
    assert answer.type == "number" and isinstance(answer.value, int)
    kinds = [m["type"] for m in trace["messages"]]
    assert kinds == ["thought", "progress", "thought", "data", "thought", "final"]
    assert (
        "orders.ngay" in trace["messages"][1]["text"]
        and "rows after the as-of date" in trace["messages"][1]["text"]
    )
    assert trace["llm_steps"] == 3 and len(trace["llm"]) == 3


def test_ca_pipeline_runs_analysis_then_final(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    replies = iter(
        [
            {
                "thought": "check",
                "action": "analysis",
                "name": "doubled",
                "question": "x2",
                "code": "result = results['rev'].iloc[0, 0] * 2",
            },
            {"thought": "ok", "action": "final", "answer_type": "number", "data_result": "doubled"},
        ]
    )
    base = ca_replies({})
    llm = FakeLLM(
        lambda p: json.dumps(next(replies)) if "Reason over the results" in p else base(p)
    )
    answer, trace = service_for(toy_split, tmp_path, llm).answer(question())
    first, _ = service_for(
        toy_split,
        tmp_path,
        FakeLLM(
            ca_replies(
                {"thought": "ok", "action": "final", "answer_type": "number", "data_result": "rev"}
            )
        ),
    ).answer(question())
    assert answer.type == "number" and answer.value == 2 * first.value
    assert trace["llm_steps"] == 4
    assert [m["type"] for m in trace["messages"]].count("analysis") == 1


def test_ca_pipeline_abstains_on_bad_final(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    llm = FakeLLM(
        ca_replies(
            {"thought": "?", "action": "final", "answer_type": "number", "data_result": "missing"}
        )
    )
    answer, trace = service_for(toy_split, tmp_path, llm).answer(question())
    assert answer.type == "abstain"
    assert [m["type"] for m in trace["messages"]].count("error") == 2
