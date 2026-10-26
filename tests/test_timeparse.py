from datetime import date
from pathlib import Path

import pytest

from src.utils.timeparse import LunarCalendar, render_time_ranges, resolve

AS_OF = date(2026, 10, 28)  # a Wednesday
SKILL = (
    Path(__file__).resolve().parents[1] / "src/assets/skills/time-expressions/SKILL.md"
).read_text(encoding="utf-8")

# Tiny calendar fixture: only the two Tết boundaries that the resolver needs.
# Real values from the split's calendar.csv: 23 tháng Chạp and 10 tháng Giêng.
CALENDAR_ROWS = [
    "2025-01-22,3,23,12,2024,false,",
    "2025-02-07,5,10,1,2025,false,",
    "2026-02-10,2,23,12,2025,false,",
    "2026-02-26,4,10,1,2026,false,",
]


@pytest.fixture
def lunar(tmp_path) -> LunarCalendar:
    path = tmp_path / "calendar.csv"
    header = "date,weekday,lunar_day,lunar_month,lunar_year,lunar_leap,holiday\n"
    path.write_text(header + "\n".join(CALENDAR_ROWS) + "\n", encoding="utf-8")
    return LunarCalendar.from_csv(path)


def ranges(question, as_of=AS_OF, calendar=None):
    return [
        (r.start.isoformat(), r.end.isoformat(), r.granularity)
        for r in resolve(question, as_of, calendar)
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
        ("tháng trước", [("2026-09-01", "2026-09-30", "month")]),
        ("quý trước", [("2026-07-01", "2026-09-30", "quarter")]),
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


# Rulebook §2, row 2: "tuần này / tháng này / quý này / năm nay" end on the end of today.
@pytest.mark.parametrize(
    "question, expected",
    [
        ("tuần này", [("2026-10-26", "2026-10-28", "week")]),
        ("tháng này", [("2026-10-01", "2026-10-28", "month")]),
        ("quý này", [("2026-10-01", "2026-10-28", "quarter")]),
        ("năm nay", [("2026-01-01", "2026-10-28", "year")]),
    ],
)
def test_this_period_ends_today(question, expected):
    assert ranges(question) == expected


# Rulebook §2, row 3: "từ đầu năm (tới nay)" is 01/01 -> today.
@pytest.mark.parametrize(
    "question",
    ["từ đầu năm", "từ đầu năm tới nay", "tính từ đầu năm đến nay"],
)
def test_start_of_year_to_today(question):
    assert ranges(question) == [("2026-01-01", "2026-10-28", "year")]


# Rulebook §2, row 4: "tháng M / quý Q" without a year: this year if not after today, else last.
@pytest.mark.parametrize(
    "question, as_of, expected",
    [
        ("quý 4", AS_OF, ("2026-10-01", "2026-12-31", "quarter")),
        ("quý 1", AS_OF, ("2026-01-01", "2026-03-31", "quarter")),
        ("quý 4", date(2026, 2, 10), ("2025-10-01", "2025-12-31", "quarter")),
        ("quý 1", date(2026, 2, 10), ("2026-01-01", "2026-03-31", "quarter")),
        ("tháng 10", AS_OF, ("2026-10-01", "2026-10-31", "month")),
        ("tháng 12", AS_OF, ("2025-12-01", "2025-12-31", "month")),
    ],
)
def test_month_or_quarter_without_year(question, as_of, expected):
    assert ranges(question, as_of) == [expected]


# Rulebook §2, row 5: "tháng này so với tháng trước" keeps the same number of days.
def test_this_month_against_previous_month_same_days():
    assert ranges("tháng này so với tháng trước") == [
        ("2026-10-01", "2026-10-28", "month"),
        ("2026-09-01", "2026-09-28", "month"),
    ]


def test_previous_month_is_capped_at_its_last_day():
    assert ranges("so sánh tháng này với tháng trước", date(2026, 3, 31)) == [
        ("2026-03-01", "2026-03-31", "month"),
        ("2026-02-01", "2026-02-28", "month"),
    ]


def test_previous_month_alone_is_the_whole_month():
    assert ranges("tháng trước") == [("2026-09-01", "2026-09-30", "month")]


# Rulebook §2, row 6: "N ngày gần nhất" is N days including today.
@pytest.mark.parametrize(
    "question, expected",
    [
        ("1 ngày gần nhất", [("2026-10-28", "2026-10-28", "range")]),
        ("7 ngày gần nhất", [("2026-10-22", "2026-10-28", "range")]),
        ("2 tuần gần nhất", [("2026-10-15", "2026-10-28", "range")]),
    ],
)
def test_last_n_days_include_today(question, expected):
    assert ranges(question) == expected


# Rulebook §2, row 8: Tết is 23 tháng Chạp (lunar Y-1) -> 10 tháng Giêng (lunar Y).
@pytest.mark.parametrize(
    "question, expected",
    [
        ("doanh thu dịp Tết 2026", ("2026-02-10", "2026-02-26", "range")),
        ("dịp Tết âm lịch 2026", ("2026-02-10", "2026-02-26", "range")),
        ("Tết năm nay", ("2026-02-10", "2026-02-26", "range")),
        ("Tết năm ngoái", ("2025-01-22", "2025-02-07", "range")),
        ("17 ngày trước Tết", ("2026-01-24", "2026-02-09", "range")),
        ("trước Tết", ("2026-01-24", "2026-02-09", "range")),
        ("17 ngày trước Tết 2025", ("2025-01-05", "2025-01-21", "range")),
        ("trước Tết năm 2025", ("2025-01-05", "2025-01-21", "range")),
    ],
)
def test_tet_window_from_calendar(question, expected, lunar):
    assert ranges(question, date(2026, 6, 28), lunar) == [expected]


def test_tet_needs_the_calendar():
    assert ranges("doanh thu dịp Tết 2026", date(2026, 6, 28)) == []


def test_tet_and_its_run_up_together(lunar):
    question = "Dịp Tết âm lịch 2026 có doanh thu hơn hay kém 17 ngày trước Tết bao nhiêu %?"
    assert ranges(question, date(2026, 9, 14), lunar) == [
        ("2026-02-10", "2026-02-26", "range"),
        ("2026-01-24", "2026-02-09", "range"),
    ]


def test_solar_new_year_is_not_lunar_tet(lunar):
    assert ranges("Tết Dương lịch 2026", date(2026, 6, 28), lunar) == []


def test_calendar_lookup_and_missing_year(lunar):
    assert lunar.solar_date(2025, 12, 23) == date(2026, 2, 10)
    assert lunar.solar_date(2026, 1, 10) == date(2026, 2, 26)
    assert lunar.solar_date(2026, 1, 11) is None


# Rulebook §2, row 1: rows after as_of_date have not happened.
@pytest.mark.parametrize(
    "needle",
    [
        "Rows after `as_of_date` have not happened",
        "cancel/return status is read as written",
    ],
)
def test_skill_future_rows(needle):
    assert needle in SKILL


# Rulebook §2, row 7: comparison operators exclude or include N.
@pytest.mark.parametrize(
    "needle",
    [
        "**Quá N, hơn N, trên N, dưới N** exclude N",
        "**Từ N trở lên** includes N",
    ],
)
def test_skill_comparison_bounds(needle):
    assert needle in SKILL


# Rulebook §2, row 9: shifts are fixed by the order's creation time.
@pytest.mark.parametrize("needle", ["06:00–13:59", "14:00–21:59", "baseline is ca sáng"])
def test_skill_shifts(needle):
    assert needle in SKILL


# Rulebook §2, row 10: "đến hết ngày X" is a balance from the start of the data.
@pytest.mark.parametrize(
    "needle",
    [
        "state at the end\n    of X",
        "from the beginning of the data",
        'not the\n    "tháng này" period',
    ],
)
def test_skill_balance_to_date(needle):
    assert needle in SKILL


def test_quarter_wraps_to_previous_year():
    assert ranges("quý trước", date(2026, 2, 10)) == [("2025-10-01", "2025-12-31", "quarter")]


def test_month_wraps_to_previous_year():
    assert ranges("tháng trước", date(2026, 1, 15)) == [("2025-12-01", "2025-12-31", "month")]


def test_several_expressions_in_order():
    got = ranges("so sánh tháng này với tháng trước")
    assert got == [("2026-10-01", "2026-10-28", "month"), ("2026-09-01", "2026-09-28", "month")]


def test_invalid_date_is_ignored():
    assert ranges("ngày 31/2") == []


def test_render_includes_as_of_and_weekday():
    text = render_time_ranges(resolve("hôm qua", AS_OF), AS_OF)
    assert text.splitlines()[0] == "as_of_date: 2026-10-28 (Thứ Tư)"
    assert '"hom qua" -> 2026-10-27 .. 2026-10-27 (day)' in text
