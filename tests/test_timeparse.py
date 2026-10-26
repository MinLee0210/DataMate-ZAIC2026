from datetime import date

import pytest

from src.modules.timeparse import render_time_ranges, resolve

AS_OF = date(2026, 10, 28)  # a Wednesday


def ranges(question, as_of=AS_OF):
    return [
        (r.start.isoformat(), r.end.isoformat(), r.granularity) for r in resolve(question, as_of)
    ]


@pytest.mark.parametrize(
    "question, expected",
    [
        ("doanh thu hôm nay", [("2026-10-28", "2026-10-28", "day")]),
        ("doanh thu hnay", [("2026-10-28", "2026-10-28", "day")]),
        ("hqua bán bao nhiêu", [("2026-10-27", "2026-10-27", "day")]),
        ("hôm kia", [("2026-10-26", "2026-10-26", "day")]),
        ("sp bán dc nhiều nhất tuần rồi", [("2026-10-19", "2026-10-25", "week")]),
        ("tuần trc", [("2026-10-19", "2026-10-25", "week")]),
        ("tuần này", [("2026-10-26", "2026-11-01", "week")]),
        ("tháng trước", [("2026-09-01", "2026-09-30", "month")]),
        ("tháng này", [("2026-10-01", "2026-10-31", "month")]),
        ("quý này", [("2026-10-01", "2026-12-31", "quarter")]),
        ("quý trước", [("2026-07-01", "2026-09-30", "quarter")]),
        ("năm nay", [("2026-01-01", "2026-12-31", "year")]),
        ("năm ngoái", [("2025-01-01", "2025-12-31", "year")]),
        ("7 ngày qua", [("2026-10-22", "2026-10-28", "range")]),
        ("2 tuần gần đây", [("2026-10-15", "2026-10-28", "range")]),
        ("3 tháng qua", [("2026-07-29", "2026-10-28", "range")]),
        ("tháng 3", [("2026-03-01", "2026-03-31", "month")]),
        ("tháng 11", [("2025-11-01", "2025-11-30", "month")]),  # not in the future
        ("tháng 2/2024", [("2024-02-01", "2024-02-29", "month")]),
        ("tháng 2 năm 2025", [("2025-02-01", "2025-02-28", "month")]),
        ("quý 2 năm 2025", [("2025-04-01", "2025-06-30", "quarter")]),
        ("năm 2025", [("2025-01-01", "2025-12-31", "year")]),
        ("ngày 5/10", [("2026-10-05", "2026-10-05", "day")]),
        ("ngày 31/12/2025", [("2025-12-31", "2025-12-31", "day")]),
        ("tổng số khách hàng", []),
    ],
)
def test_resolve(question, expected):
    assert ranges(question) == expected


def test_quarter_wraps_to_previous_year():
    assert ranges("quý trước", date(2026, 2, 10)) == [("2025-10-01", "2025-12-31", "quarter")]


def test_month_wraps_to_previous_year():
    assert ranges("tháng trước", date(2026, 1, 15)) == [("2025-12-01", "2025-12-31", "month")]


def test_several_expressions_in_order():
    got = ranges("so sánh tháng này với tháng trước")
    assert got == [("2026-10-01", "2026-10-31", "month"), ("2026-09-01", "2026-09-30", "month")]


def test_invalid_date_is_ignored():
    assert ranges("ngày 31/2") == []


def test_render_includes_as_of_and_weekday():
    text = render_time_ranges(resolve("hôm qua", AS_OF), AS_OF)
    assert text.splitlines()[0] == "as_of_date: 2026-10-28 (Thứ Tư)"
    assert '"hom qua" -> 2026-10-27 .. 2026-10-27 (day)' in text
