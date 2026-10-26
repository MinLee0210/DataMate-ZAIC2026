from datetime import date

import pandas as pd
import pytest

from src.modules.format import FormatError, format_result, round_number


def frame(rows, columns=("a",)):
    return pd.DataFrame(rows, columns=list(columns))


@pytest.mark.parametrize(
    "value, expected",
    [
        (3, 3),
        (3.0, 3),
        (2.345, 2.35),
        (2.344, 2.34),
        (-1.005, -1.01),
        ("1,234.5", 1234.5),
        (0.1 + 0.2, 0.3),
    ],
)
def test_round_number(value, expected):
    assert round_number(value) == expected


@pytest.mark.parametrize("value", [float("nan"), "abc", True])
def test_round_number_rejects(value):
    with pytest.raises(FormatError):
        round_number(value)


def test_scalar_types():
    assert format_result("number", frame([[12.0]])) == 12
    assert format_result("percent", frame([[-12.3456]])) == -12.35
    assert format_result("string", frame([["  Cà phê sữa "]])) == "Cà phê sữa"
    assert format_result("date", frame([[pd.Timestamp("2026-10-05 13:00")]])) == "2026-10-05"
    assert format_result("date", frame([[date(2026, 1, 2)]])) == "2026-01-02"
    assert format_result("date", frame([["2026-09"]])) == "2026-09"
    assert format_result("boolean", frame([[1]])) is True
    assert format_result("boolean", frame([["không"]])) is False


def test_list_and_table_keep_row_order():
    rows = [["B", 2.5], ["A", 1.0]]
    assert format_result("list", frame(rows, ("p", "v"))) == ["B", "A"]
    assert format_result("table", frame(rows, ("p", "v"))) == [["B", 2.5], ["A", 1]]


@pytest.mark.parametrize(
    "answer_type, rows",
    [
        ("number", []),
        ("number", [[1], [2]]),
        ("number", [[None]]),
        ("boolean", [["maybe"]]),
        ("date", [["not a date"]]),
    ],
)
def test_shape_and_type_errors(answer_type, rows):
    with pytest.raises(FormatError):
        format_result(answer_type, frame(rows))
