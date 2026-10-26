import pytest

from scripts.eval import normalize_string, score_line, subset_ids, tau_curve


def test_normalize_string_keeps_diacritics():
    assert normalize_string("  Cà-Phê   SỮA!! ") == "cà phê sữa"
    assert normalize_string("ca phe sua") != normalize_string("cà phê sữa")


@pytest.mark.parametrize(
    "pred, gold, score",
    [
        ({"type": "number", "answer": 12.0}, {"type": "number", "answer": 12}, 1),
        ({"type": "number", "answer": 12.004}, {"type": "number", "answer": 12}, 1),
        ({"type": "number", "answer": 12.01}, {"type": "number", "answer": 12}, -1),
        ({"type": "percent", "answer": -5.5}, {"type": "percent", "answer": 5.5}, -1),
        ({"type": "string", "answer": "cà phê sữa"}, {"type": "string", "answer": "Cà Phê Sữa"}, 1),
        ({"type": "string", "answer": "SP01"}, {"type": "string", "answer": ["Cà phê", "SP01"]}, 1),
        ({"type": "date", "answer": "2026-10"}, {"type": "date", "answer": "2026-10"}, 1),
        ({"type": "list", "answer": ["a", "b"]}, {"type": "list", "answer": ["b", "a"]}, -1),
        ({"type": "list", "answer": ["a", 2]}, {"type": "list", "answer": ["A", 2.0]}, 1),
        ({"type": "table", "answer": [["a", 1]]}, {"type": "table", "answer": [["a", 1.0]]}, 1),
        ({"type": "boolean", "answer": True}, {"type": "boolean", "answer": "true"}, 1),
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
    curve = dict(tau_curve(traces, golds))
    assert curve[0.0] == 0.0  # +1 - 1
    assert curve[0.6] == 0.5  # b abstains
    assert curve[1.0] == 0.5
