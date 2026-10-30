import pytest

from src.config import Settings, settings
from src.modules.agents.sql_writer import SQLWriter, extract_sql
from tests.conftest import FakeLLM
from tests.test_malt import malt_replies
from tests.test_qa import REVENUE_LAST_WEEK, question, service_for

FINAL = {"thought": "ok", "action": "final", "answer_type": "number", "data_result": "rev"}


@pytest.mark.parametrize(
    ("reply", "sql"),
    [
        ("```sql\nSELECT 1;\n```", "SELECT 1"),
        (
            "Here:\n```\nWITH a AS (SELECT 1) SELECT * FROM a\n```\nDone",
            "WITH a AS (SELECT 1) SELECT * FROM a",
        ),
        ("<think>SELECT 9</think>SELECT 2", "SELECT 2"),
        ("no query here", None),
    ],
)
def test_extract_sql(reply, sql):
    assert extract_sql(reply) == sql


class FakeWriter(SQLWriter):
    def __init__(self, sql):
        self.sql = sql
        self.calls = []

    def write(self, values, seed):
        self.calls.append(values["question"])
        return self.sql


def _run(toy_split, tmp_path, monkeypatch, writer):
    monkeypatch.setattr(settings, "pipeline", "malt")
    llm = FakeLLM(malt_replies(FINAL))
    service = service_for(toy_split, tmp_path, llm)
    service.malt.sql_writer = writer
    return service.answer(question())


def test_the_specialist_sql_replaces_the_analysts(toy_split, tmp_path, monkeypatch):
    writer = FakeWriter(REVENUE_LAST_WEEK + " -- specialist")
    answer, trace = _run(toy_split, tmp_path, monkeypatch, writer)
    data = [m for m in trace["messages"] if m["type"] == "data"]
    assert writer.calls == ["doanh thu"] and "specialist" in data[0]["code"]
    assert answer.type == "number"


def test_a_broken_specialist_query_falls_back_to_the_analysts(toy_split, tmp_path, monkeypatch):
    writer = FakeWriter("SELECT nope FROM missing_table")
    answer, trace = _run(toy_split, tmp_path, monkeypatch, writer)
    data = [m for m in trace["messages"] if m["type"] == "data"]
    assert "missing_table" not in data[0]["code"] and answer.type == "number"


def test_no_specialist_answer_falls_back_to_the_analysts(toy_split, tmp_path, monkeypatch):
    answer, _ = _run(toy_split, tmp_path, monkeypatch, FakeWriter(None))
    assert answer.type == "number"


def test_final_mode_needs_a_local_sql_endpoint():
    with pytest.raises(ValueError, match="SQL_LLM_BASE_URL"):
        Settings(
            final_mode=True,
            llm_base_url="http://127.0.0.1:8001/v1",
            sql_llm_base_url="https://api.example.com/v1",
        )
