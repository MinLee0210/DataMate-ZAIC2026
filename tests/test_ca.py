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
    assert kinds == ["thought", "progress", "examples", "thought", "data", "thought", "final"]
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


def test_ca_pipeline_uses_the_only_result_when_the_name_is_wrong(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    final = {"thought": "?", "action": "final", "answer_type": "number", "data_result": "missing"}
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(ca_replies(final))).answer(question())
    assert answer.type == "number"


def test_ca_pipeline_abstains_when_the_final_cannot_be_formatted(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    final = {"thought": "?", "action": "final", "answer_type": "date", "data_result": "rev"}
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(ca_replies(final))).answer(question())
    assert answer.type == "abstain"
    assert [m["type"] for m in trace["messages"]].count("error") == 2


def _results(**frames):
    from src.services.qa.ca import DataResult

    return {n: DataResult(n, "", "sql", "SELECT 1", pd.DataFrame(f)) for n, f in frames.items()}


@pytest.mark.parametrize(
    "ref, expected",
    [
        ("total_revenue", 42149500),
        ("Total_Revenue", 42149500),
        ("1", 42149500),  # an index, 0-based
        ("42149500", 42149500),  # the value instead of the name
        ("42149500.0", 42149500),
        ("Cty Trương Hoa", "Cty Trương Hoa"),  # a cell of a larger result
        (None, None),  # several results, no name: no answer
        ("WITH x AS (SELECT 1) SELECT 2", None),
    ],
)
def test_resolve_result(ref, expected):
    from src.services.qa.ca import resolve_result

    results = _results(
        top_customers={"khach": ["Cty Trương Hoa", "An"], "tien": [9, 5]},
        total_revenue={"doanh_thu": [42149500]},
    )
    hit = resolve_result(results, ref)
    assert (hit.frame.iat[0, 0] if hit else None) == expected


def test_first_json_object_repairs_invalid_escapes():
    from src.modules.agents.sql_agent import first_json_object

    reply = r'{"sql": "SELECT regexp_matches(x, \'\d+\')", "ok": "a\\d"}'
    assert first_json_object(reply) == {"sql": r"SELECT regexp_matches(x, '\d+')", "ok": r"a\d"}


def test_low_confidence_abstains_but_keeps_the_answer_for_the_tau_curve(
    toy_split, tmp_path, monkeypatch
):
    monkeypatch.setattr(settings, "pipeline", "ca")
    monkeypatch.setattr(settings, "min_confidence", 0.6)
    final = {"thought": "?", "action": "final", "answer_type": "number", "data_result": "rev",
             "confidence": 0.3}  # fmt: skip
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(ca_replies(final))).answer(question())
    assert answer.type == "abstain"
    assert trace["top"]["type"] == "number" and trace["agreement"] == 0.3


def test_confidence_above_the_gate_answers(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    monkeypatch.setattr(settings, "min_confidence", 0.6)
    final = {
        "thought": "ok",
        "action": "final",
        "answer_type": "number",
        "data_result": "rev",
        "confidence": 85,
    }  # fmt: skip  (0-100 read as a percent)
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(ca_replies(final))).answer(question())
    assert answer.type == "number" and trace["agreement"] == 0.85


def test_unanswerable_without_evidence_gets_zero_confidence(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    monkeypatch.setattr(settings, "min_confidence", 0.5)
    final = {"thought": "?", "action": "final", "answer_type": "unanswerable", "reason": "no data",
             "confidence": 0.9}  # fmt: skip
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(ca_replies(final))).answer(question())
    assert answer.type == "abstain" and trace["agreement"] == 0.0
    final["evidence"] = "no column records the delivery date"
    answer, _ = service_for(toy_split, tmp_path, FakeLLM(ca_replies(final))).answer(question())
    assert answer.type == "unanswerable"


def test_a_failed_extra_query_earns_one_more_step(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    replies = iter(
        [
            {
                "thought": "fix",
                "action": "data_query",
                "name": "bad",
                "sql": "SELECT nope FROM orders",
            },
            {"thought": "fix again", "action": "data_query", "name": "good", "sql": "SELECT 7"},
            {"thought": "ok", "action": "final", "answer_type": "number", "data_result": "good"},
        ]
    )
    base = ca_replies({})
    llm = FakeLLM(
        lambda p: json.dumps(next(replies)) if "Reason over the results" in p else base(p)
    )
    answer, trace = service_for(toy_split, tmp_path, llm).answer(question())
    assert answer.type == "number" and answer.value == 7
    assert trace["llm_steps"] == 5
    bad = [m for m in trace["messages"] if m.get("name") == "bad"][0]
    assert "Columns of orders" in bad["error"]  # the hint lists the real columns


@pytest.mark.parametrize(
    "reply, action",
    [
        ({"action": "Final"}, "final"),
        ({"answer_type": "number", "data_result": "rev"}, "final"),
        ({"sql": "SELECT 1"}, "data_query"),
        ({"code": "result = 1"}, "analysis"),
        ({"reason": "not sure"}, ""),
    ],
)
def test_infer_action(reply, action):
    from src.services.qa.ca import infer_action

    assert infer_action(reply) == action


def test_example_store_masks_numbers_and_skips_the_asking_family():
    from src.modules.context.examples import Example, ExampleStore, render_examples

    def ex(i, biz, fam, q):
        return Example(i, biz, fam, q, "number", f"SELECT {i}")

    store = ExampleStore(
        [
            ex("a", "biz_1", "f1", "doanh thu tháng 5/2025 là bao nhiêu"),
            ex("b", "biz_2", "f2", "doanh thu tháng 11/2026 là bao nhiêu"),
            ex("c", "biz_3", "f3", "mặt hàng nào bán chạy nhất tuần rồi"),
        ]
    )
    hits = store.search("doanh thu tháng 2/2026 bao nhiêu", "biz_9", k=2)
    assert [h.id for h in hits] == ["a", "b"]  # numbers masked: both months match equally
    assert [h.id for h in store.search("doanh thu tháng 2/2026", "biz_1", k=3)] == ["b"]
    assert "SELECT a" in render_examples(hits)
    assert ExampleStore([]).search("x", "biz_1") == []


def test_self_consistency_votes_over_approaches(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")
    monkeypatch.setattr(settings, "ca_samples", 3)
    monkeypatch.setattr(settings, "ca_min_agreement", 0.6)
    # the third approach ("Verify independently") picks a different query result
    replies = []

    def reply(prompt):
        if "first step: reason over the schema" in prompt:
            return json.dumps({"thought": "t", "sample_fields": []})
        if "plan the data queries" in prompt:
            sql = "SELECT 9" if "Verify independently" in prompt else "SELECT 5"
            return json.dumps({"thought": "q", "data_queries": [{"name": "r", "sql": sql}]})
        replies.append(prompt)
        return json.dumps(
            {"thought": "ok", "action": "final", "answer_type": "number", "data_result": "r"}
        )

    answer, trace = service_for(toy_split, tmp_path, FakeLLM(reply)).answer(question())
    assert answer.type == "number" and answer.value == 5
    assert trace["agreement"] == round(2 / 3, 4) and len(trace["samples"]) == 3
    monkeypatch.setattr(settings, "ca_min_agreement", 0.9)
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(reply)).answer(question())
    assert answer.type == "abstain" and trace["top"]["value"] == 5


def test_money_answers_are_rounded_to_whole_vnd_in_the_pipeline(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "pipeline", "ca")

    def reply(prompt):
        if "first step: reason over the schema" in prompt:
            return json.dumps({"thought": "t", "sample_fields": []})
        if "plan the data queries" in prompt:
            return json.dumps(
                {"thought": "q", "data_queries": [{"name": "avg", "sql": "SELECT 169724.73"}]}
            )
        return json.dumps(
            {"thought": "ok", "action": "final", "answer_type": "number", "data_result": "avg"}
        )

    # "doanh thu" is a money question: an average order value is money, whole VND
    answer, _ = service_for(toy_split, tmp_path, FakeLLM(reply)).answer(question())
    assert answer.value == 169725
