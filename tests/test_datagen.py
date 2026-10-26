import pytest

pytest.importorskip("deepagents")

from scripts.datagen.teacher import build_tools, main  # noqa: E402
from src.data.duckdb import DuckDBSource  # noqa: E402
from src.services.ingest import IngestService  # noqa: E402


def test_teacher_refuses_test_splits():
    for split in ["public_test", "private_test"]:
        with pytest.raises(SystemExit, match="train businesses only"):
            main(["--split", split])


def test_submit_example_computes_the_answer(toy_split, tmp_path):
    business = IngestService(tmp_path / "work").load("shop1", toy_split / "businesses/shop1")
    source = DuckDBSource(business.db_path)
    source.connect()
    examples = []
    describe, run_sql, submit = build_tools(source, "shop1", examples, "schema")
    assert describe() == "schema"
    assert run_sql("SELECT count(*) AS n FROM orders").strip().splitlines() == ["n", "4"]
    assert run_sql("DROP TABLE orders").startswith("ERROR")
    ok = submit(
        "tổng doanh thu",
        "2026-10-28",
        "number",
        "SELECT sum(thanh_tien_vnd) FROM orders",
        "aggregate",
    )
    assert ok.startswith("OK #1")
    assert examples[0]["answer"] == 3200000 and examples[0]["type"] == "number"
    assert submit("x", "2026-10-28", "number", "SELECT nope", "aggregate").startswith("REJECTED")
    assert submit("x", "not a date", "number", "SELECT 1", "aggregate").startswith("REJECTED")
    source.close()
