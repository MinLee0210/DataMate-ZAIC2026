import json

import pytest

import scripts.eval
from scripts.eval import export_submission, subset_ids
from src.evaluate import (
    check_format,
    judge,
    normalize_string,
    parse_line,
    read_submission,
    score_line,
    score_submission,
    summarize,
    tau_curve,
)
from src.models import SubmissionLine

TABLE = {"columns": ["khach_hang", "so_tien_no"], "rows": [["Chị Lan", 3200000], ["Anh Ba", 500]]}


def test_normalize_string_keeps_diacritics():
    assert normalize_string("  Cà-Phê   SỮA!! ") == "cà phê sữa"
    assert normalize_string("ca phe sua") != normalize_string("cà phê sữa")


@pytest.mark.parametrize(
    "pred, gold, score",
    [
        # number / percent: JSON number, exact up to float error
        ({"type": "number", "answer": 12.0}, {"type": "number", "answer": 12}, 1),
        ({"type": "number", "answer": 12.0000000001}, {"type": "number", "answer": 12}, 1),
        ({"type": "number", "answer": 12.004}, {"type": "number", "answer": 12}, -1),
        ({"type": "number", "answer": "4820000"}, {"type": "number", "answer": 4820000}, -1),
        ({"type": "number", "answer": True}, {"type": "number", "answer": 1}, -1),
        ({"type": "percent", "answer": -5.5}, {"type": "percent", "answer": 5.5}, -1),
        ({"type": "percent", "answer": 0.124}, {"type": "percent", "answer": 12.4}, -1),
        ({"type": "percent", "answer": "12.4%"}, {"type": "percent", "answer": 12.4}, -1),
        ({"type": "number", "answer": 12.4}, {"type": "percent", "answer": 12.4}, -1),
        # string: case / punctuation ignored, diacritics count, aliases accepted
        ({"type": "string", "answer": "cà phê sữa"}, {"type": "string", "answer": "Cà Phê Sữa"}, 1),
        (
            {"type": "string", "answer": "Sting dầu 330ml"},
            {"type": "string", "answer": "Sting dâu 330ml"},
            -1,
        ),
        (
            {"type": "string", "answer": "sp0001"},
            {"type": "string", "answer": "Xi măng", "alias": ["SP0001"]},
            1,
        ),
        ({"type": "string", "answer": ["Xi măng"]}, {"type": "string", "answer": "Xi măng"}, -1),
        # date / boolean
        ({"type": "date", "answer": "2026-10"}, {"type": "date", "answer": "2026-10"}, 1),
        ({"type": "date", "answer": "15/08/2026"}, {"type": "date", "answer": "2026-08-15"}, -1),
        ({"type": "boolean", "answer": False}, {"type": "boolean", "answer": False}, 1),
        ({"type": "boolean", "answer": "true"}, {"type": "boolean", "answer": True}, -1),
        ({"type": "boolean", "answer": 1}, {"type": "boolean", "answer": True}, -1),
        # list: ordered, per-position aliases
        ({"type": "list", "answer": ["a", "b"]}, {"type": "list", "answer": ["b", "a"]}, -1),
        ({"type": "list", "answer": ["A", 2.0]}, {"type": "list", "answer": ["a", 2]}, 1),
        (
            {"type": "list", "answer": ["SP0003", "Cà phê đen (M)"]},
            {
                "type": "list",
                "answer": ["Cà phê sữa (M)", "Cà phê đen (M)"],
                "alias": [["SP0003"], ["SP0001"]],
            },
            1,
        ),
        ({"type": "list", "answer": "a, b"}, {"type": "list", "answer": ["a", "b"]}, -1),
        # table: rows unordered, columns by name else position, row-name aliases
        ({"type": "table", "answer": TABLE}, {"type": "table", "answer": TABLE}, 1),
        (
            {
                "type": "table",
                "answer": {
                    "columns": ["khach_hang", "so_tien_no"],
                    "rows": [["anh ba", 500], ["chị lan", 3200000.0]],
                },
            },
            {"type": "table", "answer": TABLE},
            1,
        ),
        (
            {
                "type": "table",
                "answer": {
                    "columns": ["so_tien_no", "khach_hang"],
                    "rows": [[3200000, "Chị Lan"], [500, "Anh Ba"]],
                },
            },
            {"type": "table", "answer": TABLE},
            1,
        ),
        (
            {
                "type": "table",
                "answer": {
                    "columns": ["ten", "tien"],
                    "rows": [["KH01", 3200000], ["Anh Ba", 500]],
                },
            },
            {"type": "table", "answer": TABLE, "alias": [["KH01"], ["KH02"]]},
            1,
        ),
        (
            {
                "type": "table",
                "answer": {
                    "columns": ["khach_hang", "so_tien_no"],
                    "rows": [["Chị Lan", "3.200.000đ"], ["Anh Ba", 500]],
                },
            },
            {"type": "table", "answer": TABLE},
            -1,
        ),
        ({"type": "table", "answer": TABLE["rows"]}, {"type": "table", "answer": TABLE}, -1),
        # abstain, missing, unanswerable
        ({"type": "abstain", "answer": None}, {"type": "number", "answer": 1}, 0),
        (None, {"type": "number", "answer": 1}, 0),
        ({"type": "number", "answer": 1}, {"type": "unanswerable", "answer": None}, -1),
        ({"type": "unanswerable", "answer": None}, {"type": "unanswerable", "answer": None}, 1),
        ({"type": "unanswerable", "answer": None}, {"type": "number", "answer": 1}, -1),
        ({"type": "string", "answer": "1"}, {"type": "number", "answer": 1}, -1),
    ],
)
def test_score_line(pred, gold, score):
    assert score_line(pred, gold) == score


def test_judge_reasons():
    gold = {"type": "number", "answer": 5}
    assert judge({"type": "percent", "answer": 5}, gold) == (-1, "wrong_type")
    assert judge({"type": "number", "answer": "5"}, gold) == (-1, "bad_format")
    assert judge({"type": "number", "answer": 6}, gold) == (-1, "wrong_value")
    assert judge(None, gold) == (0, "missing")


def test_check_format():
    assert check_format("date", "2025-09")
    assert not check_format("date", "tháng 9/2025")
    assert check_format("table", {"columns": [], "rows": []})
    assert not check_format("table", {"columns": ["a"], "rows": ["x"]})


@pytest.mark.parametrize(
    "raw, readable",
    [
        ('{"id": "q1", "type": "number", "answer": 3}', True),
        ('{"id": "q1", "type": "unanswerable", "reason": "no data"}', True),
        ('{"id": "q1", "type": "unanswerable", "reason": 3}', False),  # rulebook: counts as blank
        ('{"id": "q1", "type": "money", "answer": 3}', False),
        ('{"type": "number", "answer": 3}', False),
        ("not json", False),
    ],
)
def test_parse_line(raw, readable):
    assert (parse_line(raw) is not None) == readable


def test_submission_record_matches_portal_format():
    assert SubmissionLine(id="q1", type="unanswerable").record() == {
        "id": "q1",
        "type": "unanswerable",
        "reason": "Dữ liệu không có thông tin cần thiết để trả lời câu hỏi",
    }
    assert SubmissionLine(id="q1", type="abstain").record() == {"id": "q1", "type": "abstain"}
    record = SubmissionLine(id="q1", type="number", answer=48250000).record()
    assert record == {"id": "q1", "type": "number", "answer": 48250000}
    for r in (SubmissionLine(id="q1", type=t).record() for t in ("unanswerable", "abstain")):
        assert parse_line(json.dumps(r, ensure_ascii=False)) is not None


def test_read_submission_first_line_wins_and_skips_garbage():
    lines = [
        json.dumps({"id": "a", "type": "number", "answer": 1}),
        "{broken",
        json.dumps({"id": "a", "type": "number", "answer": 2}),
        "",
    ]
    assert read_submission(lines) == {"a": {"id": "a", "type": "number", "answer": 1}}


def test_score_submission_and_summary():
    golds = {
        "a": {"type": "number", "answer": 1},
        "b": {"type": "number", "answer": 2},
        "c": {"type": "unanswerable", "answer": None},
    }
    preds = {
        "a": {"id": "a", "type": "number", "answer": 1},
        "c": {"id": "c", "type": "number", "answer": 0},
        "zzz": {"id": "zzz", "type": "number", "answer": 0},  # not in gold: ignored
    }
    scores = [s.score for s in score_submission(preds, golds)]
    assert scores == [1, 0, -1]
    assert summarize(scores) == {"n": 3, "pa": 0.0, "correct": 1, "wrong": 1, "abstain": 1}


def test_subset_is_fixed():
    ids = [f"q{i}" for i in range(1000)]
    assert subset_ids(ids, "dev200") == subset_ids(list(reversed(ids)), "dev200")
    assert len(subset_ids(ids, "dev200")) == 200
    assert subset_ids(ids[:5], "dev200") == sorted(ids[:5])


def test_tau_curve():
    golds = {"a": {"type": "number", "answer": 1}, "b": {"type": "number", "answer": 2}}
    traces = {
        "a": {"agreement": 1.0, "top": {"type": "number", "value": 1}},
        "b": {"agreement": 0.5, "top": {"type": "number", "value": 3}},
    }
    curve = dict(tau_curve(traces, golds, [0.0, 0.6, 1.0]))
    assert curve[0.0] == 0.0  # +1 - 1
    assert curve[0.6] == 0.5  # b abstains
    assert curve[1.0] == 0.5


def test_export_submission(tmp_path, monkeypatch):
    monkeypatch.setattr(scripts.eval, "ROOT", tmp_path)
    pred = tmp_path / "pred.jsonl"
    rows = [
        {"id": "c", "type": "abstain", "answer": None},
        {"id": "a", "type": "number", "answer": 3},
        {"id": "b", "type": "unanswerable", "answer": None},
    ]
    pred.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    out = export_submission(pred, "topic")
    assert out.parent.parent.parent == tmp_path / "data" / "results"
    lines = [json.loads(line) for line in out.read_text().splitlines()]
    assert [line["id"] for line in lines] == ["a", "b", "c"]
    assert isinstance(lines[1]["reason"], str)
    assert "answer" not in lines[1] and lines[2] == {"id": "c", "type": "abstain"}

    pred.write_text(json.dumps({"id": "a", "type": "number", "answer": "3"}) + "\n")
    with pytest.raises(ValueError):
        export_submission(pred, "topic")


def test_holdout_subset_takes_only_holdout_businesses():
    from scripts.splits import HOLDOUT

    business_of = {"q1": HOLDOUT[0], "q2": "biz_x", "q3": HOLDOUT[1]}
    assert subset_ids(list(business_of), "holdout", business_of=business_of) == ["q1", "q3"]
    assert len(subset_ids(list(business_of), "holdout1", business_of=business_of)) == 1


def test_holdout_keeps_whole_schema_families_and_folds_do_too():
    from scripts.splits import FAMILIES, HOLDOUT, SECTOR, dev_folds

    for family in FAMILIES:
        held = {b in HOLDOUT for b in family}
        assert len(held) == 1, f"family split across hold-out and development: {family}"
    covered = {SECTOR[b] for b in HOLDOUT}
    assert {"grocery", "cafe", "pharmacy", "restaurant", "building_materials"} <= covered
    folds = dev_folds({b: 100 for f in FAMILIES for b in f})
    for family in FAMILIES:
        if not set(family) & set(HOLDOUT):
            assert len({folds[b] for b in family}) == 1
