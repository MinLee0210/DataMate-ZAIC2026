"""Resolve Vietnamese time expressions against `as_of_date`, deterministically.

Conventions (check them against the rulebook once it is available, see skills/time-expressions):
- weeks start on Monday;
- "N ngày qua" is the N days ending on `as_of_date`, inclusive;
- "tháng M" without a year is the latest month M that is not after `as_of_date`.
"""

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

from src.utils.text import fold

# common chat abbreviations, applied to folded text
_ABBREVIATIONS = {
    r"\bhnay\b": "hom nay",
    r"\bhqua\b": "hom qua",
    r"\bhkia\b": "hom kia",
    r"\btrc\b": "truoc",
    r"\bthg\b": "thang",
}
_PAST = r"(?:truoc|roi|qua|vua roi|vua qua)"
_THIS = r"(?:nay|hien tai)"


@dataclass(frozen=True)
class TimeRange:
    phrase: str
    start: date
    end: date  # inclusive
    granularity: str  # day | week | month | quarter | year | range


def _month_range(year: int, month: int) -> tuple[date, date]:
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _quarter_range(year: int, quarter: int) -> tuple[date, date]:
    start, _ = _month_range(year, 3 * quarter - 2)
    _, end = _month_range(year, 3 * quarter)
    return start, end


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def normalize(question: str) -> str:
    text = fold(question, keep="/-")
    for pattern, repl in _ABBREVIATIONS.items():
        text = re.sub(pattern, repl, text)
    return text


def _rules(today: date) -> list[tuple[str, object]]:
    y, m = today.year, today.month
    q = (m - 1) // 3 + 1
    week = _week_start(today)
    py, pm = _shift_month(y, m, -1)
    pq_year, pq = (y, q - 1) if q > 1 else (y - 1, 4)

    def latest_month(month: int, year: int | None) -> tuple[date, date, str]:
        if year is None:
            year = y if month <= m else y - 1
        return (*_month_range(year, month), "month")

    def explicit_day(dd: int, mm: int, yy: int | None = None) -> tuple[date, date, str]:
        d = date(yy if yy else y, mm, dd)
        return d, d, "day"

    return [
        # longer, more specific patterns first
        (r"\b(\d+) (ngay|tuan|thang) (?:qua|gan day|gan nhat|vua qua|truoc)\b", None),
        (r"\bngay (\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?\b", explicit_day),
        (r"\bthang (\d{1,2})(?:[/-]| nam )(\d{4})\b", lambda mm, yy: latest_month(mm, yy)),
        (r"\bthang (\d{1,2})\b", lambda mm: latest_month(mm, None)),
        (
            r"\bquy (\d)(?: nam (\d{4}))?\b",
            lambda qq, yy=None: (*_quarter_range(yy or y, qq), "quarter"),
        ),
        (r"\bnam (\d{4})\b", lambda yy: (date(yy, 1, 1), date(yy, 12, 31), "year")),
        (r"\bhom kia\b", (today - timedelta(days=2), today - timedelta(days=2), "day")),
        (r"\bhom qua\b", (today - timedelta(days=1), today - timedelta(days=1), "day")),
        (r"\bhom nay\b", (today, today, "day")),
        (rf"\btuan {_PAST}\b", (week - timedelta(days=7), week - timedelta(days=1), "week")),
        (rf"\btuan {_THIS}\b", (week, week + timedelta(days=6), "week")),
        (rf"\bthang {_PAST}\b", (*_month_range(py, pm), "month")),
        (rf"\bthang {_THIS}\b", (*_month_range(y, m), "month")),
        (rf"\bquy {_PAST}\b", (*_quarter_range(pq_year, pq), "quarter")),
        (rf"\bquy {_THIS}\b", (*_quarter_range(y, q), "quarter")),
        (r"\bnam (?:ngoai|truoc|roi|qua)\b", (date(y - 1, 1, 1), date(y - 1, 12, 31), "year")),
        (rf"\bnam {_THIS}\b", (date(y, 1, 1), date(y, 12, 31), "year")),
    ]


def _last_n(n: int, unit: str, today: date) -> tuple[date, date, str]:
    """'N ngày/tuần/tháng qua': the period of that length ending on `today`, inclusive."""
    if unit == "thang":  # calendar months back
        sy, sm = _shift_month(today.year, today.month, -n)
        day = min(today.day, calendar.monthrange(sy, sm)[1])
        return date(sy, sm, day) + timedelta(days=1), today, "range"
    days = n * (7 if unit == "tuan" else 1)
    return today - timedelta(days=days - 1), today, "range"


def resolve(question: str, as_of_date: date) -> list[TimeRange]:
    """All time expressions in `question`, in order of appearance, as inclusive date ranges."""
    text = normalize(question)
    taken: list[tuple[int, int]] = []
    found: list[tuple[int, TimeRange]] = []

    def free(span: tuple[int, int]) -> bool:
        return all(span[1] <= a or span[0] >= b for a, b in taken)

    for pattern, value in _rules(as_of_date):
        for match in re.finditer(pattern, text):
            if not free(match.span()):
                continue
            try:
                if value is None:  # "N ngày/tuần/tháng qua"
                    start, end, gran = _last_n(int(match.group(1)), match.group(2), as_of_date)
                elif callable(value):
                    args = [int(g) if g else None for g in match.groups()]
                    while args and args[-1] is None:
                        args.pop()
                    start, end, gran = value(*args)
                else:
                    start, end, gran = value
            except ValueError:  # e.g. "tháng 13" or "ngày 31/2"
                continue
            taken.append(match.span())
            found.append((match.start(), TimeRange(match.group(0), start, end, gran)))
    return [r for _, r in sorted(found, key=lambda x: x[0])]


def render_time_ranges(ranges: list[TimeRange], as_of_date: date) -> str:
    lines = [f"as_of_date: {as_of_date.isoformat()} ({_WEEKDAYS[as_of_date.weekday()]})"]
    lines += [
        f'- "{r.phrase}" -> {r.start.isoformat()} .. {r.end.isoformat()} ({r.granularity})'
        for r in ranges
    ]
    return "\n".join(lines)


_WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
