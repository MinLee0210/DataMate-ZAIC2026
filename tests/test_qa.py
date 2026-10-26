import json
from datetime import date

import pytest

from src.__main__ import main
from src.config import Settings, settings
from src.data.duckdb import UnsafeSQLError, check_read_only
from src.data.layout import business_dir
from src.models import Question
from src.modules.agents.sql_agent import PlanParseError, SQLAgent, parse_plan
from src.services.ingest import IngestService
from src.services.qa import QAService
from tests.conftest import FakeLLM, plan

REVENUE_LAST_WEEK = "SELECT sum(thanh_tien_vnd) FROM orders WHERE ngay BETWEEN DATE '2026-10-19' AND DATE '2026-10-25'"


def service_for(toy_split, tmp_path, llm):
    return QAService(
        IngestService(tmp_path / "work"),
        package_dir=lambda b: business_dir(toy_split, b),
        agent=SQLAgent(llm=llm),
    )


def question(text="doanh thu tuần rồi"):
    return Question(id="q1", business_id="shop1", question=text, as_of_date=date(2026, 10, 28))


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM orders",
        "SELECT 1; DROP TABLE orders",
        "COPY orders TO 'x.csv'",
        "INSTALL httpfs",
        "not sql at all (",
    ],
)
def test_only_single_select_is_allowed(sql):
    with pytest.raises(UnsafeSQLError):
        check_read_only(sql)


def test_with_select_is_allowed():
    check_read_only("WITH x AS (SELECT 1 AS a) SELECT a FROM x")


def test_parse_plan():
    assert (
        parse_plan("<think>hm</think> ```json\n" + plan("number", "SELECT 1;") + "\n```").sql
        == "SELECT 1"
    )
    assert parse_plan('{"answer_type": "unanswerable"}').answer_type == "unanswerable"
    for bad in ["no json", '{"answer_type": "number"}', '{"answer_type": "essay", "sql": "x"}']:
        with pytest.raises(PlanParseError):
            parse_plan(bad)


def test_answers_with_resolved_time_and_entities(toy_split, tmp_path):
    llm = FakeLLM(lambda prompt: plan("number", REVENUE_LAST_WEEK))
    answer, trace = service_for(toy_split, tmp_path, llm).answer(question())
    assert answer.type == "number" and answer.value == 2150000
    assert trace["agreement"] == 1.0
    # k candidates, each with its own prompt variant and seed
    assert len(llm.calls) == settings.k
    assert len({seed for _, seed in llm.calls}) == settings.k
    prompt = llm.calls[0][0]
    assert '"tuan roi" -> 2026-10-19 .. 2026-10-25 (week)' in prompt
    assert "orders" in prompt and "thanh_tien_vnd" in prompt


def test_entity_linking_reaches_the_prompt(toy_split, tmp_path):
    llm = FakeLLM(lambda prompt: plan("number", "SELECT 3"))
    service_for(toy_split, tmp_path, llm).answer(question("cà fê sữa bán bao nhiêu ly"))
    assert "products__san_pham.ten_san_pham = 'Cà phê sữa'" in llm.calls[0][0]


def test_failed_sql_is_repaired(toy_split, tmp_path):
    def reply(prompt):
        if "## Error" in prompt:
            return plan("number", REVENUE_LAST_WEEK)
        return plan("number", "SELECT sum(revenue) FROM orders")  # no such column

    llm = FakeLLM(reply)
    answer, trace = service_for(toy_split, tmp_path, llm).answer(question())
    assert answer.value == 2150000
    assert trace["repairs"] == 1
    assert len(llm.calls) == 2 * settings.k


def test_repairs_are_bounded_then_abstain(toy_split, tmp_path):
    llm = FakeLLM(lambda prompt: plan("number", "SELECT nope FROM orders"))
    answer, trace = service_for(toy_split, tmp_path, llm).answer(question())
    assert answer.type == "abstain"
    assert trace["repairs"] == settings.max_repairs
    assert len(llm.calls) == settings.k * (1 + settings.max_repairs)


def test_disagreement_abstains(toy_split, tmp_path):
    replies = [plan("number", "SELECT 1"), plan("number", "SELECT 2"), plan("number", "SELECT 3")]
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(replies)).answer(question())
    assert answer.type == "abstain"
    assert trace["top"] == {"type": "number", "value": 1}


def test_unanswerable(toy_split, tmp_path):
    llm = FakeLLM(lambda prompt: '{"answer_type": "unanswerable", "reason": "no cost column"}')
    answer, _ = service_for(toy_split, tmp_path, llm).answer(question("lợi nhuận tháng này"))
    assert answer.type == "unanswerable"


def test_provider_error_abstains(toy_split, tmp_path):
    answer, trace = service_for(toy_split, tmp_path, FakeLLM(error=RuntimeError("down"))).answer(
        question()
    )
    assert answer.type == "abstain" and "down" in trace["error"]


def test_batch_writes_one_line_per_question(toy_split, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "work_dir", tmp_path / "work")
    monkeypatch.setattr(
        "src.__main__.QAService",
        lambda ingest, package_dir: QAService(
            ingest, package_dir, agent=SQLAgent(llm=FakeLLM(lambda p: plan("number", "SELECT 3")))
        ),
    )
    out = tmp_path / "result"
    assert main(["--data", str(toy_split.parent), "--split", "train", "--out", str(out)]) == 0
    lines = [json.loads(line) for line in (out / "submission.jsonl").read_text().splitlines()]
    assert lines == [
        {"id": "q1", "type": "number", "answer": 3},
        {"id": "q2", "type": "number", "answer": 3},
    ]


def test_final_mode_requires_local_llm():
    Settings(final_mode=True, llm_base_url="http://127.0.0.1:8001/v1")
    with pytest.raises(ValueError, match="local"):
        Settings(final_mode=True, llm_base_url="https://openrouter.ai/api/v1")
