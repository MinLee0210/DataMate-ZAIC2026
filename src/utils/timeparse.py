"""Resolve Vietnamese time expressions against `as_of_date`, deterministically.

Conventions follow rulebook §2 (see skills/time-expressions):
- weeks start on Monday;
- "N ngày gần nhất" is the N days ending on `as_of_date`, inclusive;
- "tháng này / quý này / năm nay / từ đầu năm" end on `as_of_date`, not on the period end;
- "tháng M" without a year is the latest month M not after `as_of_date`; a quarter without a year
  uses the same rule;
- Tết is read from the split's `calendar.csv` through `LunarCalendar`, never hard-coded.
"""

import calendar
import csv
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

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
_THIS_MONTH_PHRASES = {"thang nay", "thang hien tai"}
_PREV_MONTH_PHRASES = {"thang truoc", "thang roi", "thang qua", "thang vua roi", "thang vua qua"}
_TET = r"(?:dip |mua )?tet(?: am lich)?"
_NOT_SOLAR_NEW_YEAR = r"(?! duong lich)"

Span = tuple[date, date, str]
RuleValue = Span | Callable[..., Span | None] | None


@dataclass(frozen=True)
class TimeRange:
    phrase: str
    start: date
    end: date  # inclusive
    granularity: str  # day | week | month | quarter | year | range


@dataclass(frozen=True)
class LunarDay:
    """One `calendar.csv` row: a solar date and the lunar date that falls on it."""

    solar: date
    day: int
    month: int
    year: int
    leap: bool = False


class LunarCalendar:
    """Solar ↔ lunar lookup read from a split's `calendar.csv`, once and offline."""

    def __init__(self, days: Iterable[LunarDay]) -> None:
        self._by_lunar: dict[tuple[int, int, int, bool], date] = {}
        for item in days:
            key = (item.year, item.month, item.day, item.leap)
            known = self._by_lunar.get(key)
            if known is not None and known != item.solar:
                raise ValueError(f"lunar {key} maps to both {known} and {item.solar}")
            self._by_lunar[key] = item.solar

    @classmethod
    def from_csv(cls, path: Path) -> "LunarCalendar":
        """Read `date,lunar_day,lunar_month,lunar_year,lunar_leap` rows from `path`."""
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return cls.from_records(csv.DictReader(handle))

    @classmethod
    def from_records(cls, records: Iterable[Mapping[str, str | None]]) -> "LunarCalendar":
        days: list[LunarDay] = []
        for row in records:
            try:
                solar = date.fromisoformat((row["date"] or "").strip())
                day = int((row["lunar_day"] or "").strip())
                month = int((row["lunar_month"] or "").strip())
                year = int((row["lunar_year"] or "").strip())
            except (KeyError, ValueError) as e:
                raise ValueError(f"bad calendar row: {row!r}") from e
            leap = (row.get("lunar_leap") or "").strip().lower() in {"1", "true", "yes"}
            days.append(LunarDay(solar, day, month, year, leap))
        if not days:
            raise ValueError("empty lunar calendar")
        return cls(days)

    def solar_date(self, year: int, month: int, day: int, *, leap: bool = False) -> date | None:
        """Solar date of a lunar date, or None when the calendar does not cover it."""
        return self._by_lunar.get((year, month, day, leap))


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


def _tet_range(year: int, lunar: LunarCalendar) -> tuple[date, date] | None:
    """Solar span of Tết `year`: 23 tháng Chạp (lunar year-1) to 10 tháng Giêng (lunar year)."""
    start = lunar.solar_date(year - 1, 12, 23)
    end = lunar.solar_date(year, 1, 10)
    if start is None or end is None or end < start:
        return None
    return start, end


def _days_before(start: date, days: int) -> tuple[date, date] | None:
    """The `days` days immediately before `start`, inclusive."""
    if days <= 0:
        return None
    return start - timedelta(days=days), start - timedelta(days=1)


def normalize(question: str) -> str:
    text = fold(question, keep="/-")
    for pattern, repl in _ABBREVIATIONS.items():
        text = re.sub(pattern, repl, text)
    return text


def _rules(today: date, lunar: LunarCalendar | None) -> list[tuple[str, RuleValue]]:
    y, m = today.year, today.month
    q = (m - 1) // 3 + 1
    week = _week_start(today)
    py, pm = _shift_month(y, m, -1)
    pq_year, pq = (y, q - 1) if q > 1 else (y - 1, 4)

    def latest_month(month: int, year: int | None) -> tuple[date, date, str]:
        if year is None:
            year = y if month <= m else y - 1
        return (*_month_range(year, month), "month")

    def quarter(number: int, year: int | None = None) -> tuple[date, date, str]:
        # No year: this year's quarter unless its start is after today, else last year's.
        chosen = year if year is not None else (y if number <= q else y - 1)
        return (*_quarter_range(chosen, number), "quarter")

    def explicit_day(dd: int, mm: int, yy: int | None = None) -> tuple[date, date, str]:
        d = date(yy if yy else y, mm, dd)
        return d, d, "day"

    def tet_span(year: int) -> tuple[date, date] | None:
        return None if lunar is None else _tet_range(year, lunar)

    def tet(year: int) -> tuple[date, date, str] | None:
        span = tet_span(year)
        return None if span is None else (*span, "range")

    def before_tet(year: int, days: int | None = None) -> tuple[date, date, str] | None:
        span = tet_span(year)
        if span is None:
            return None
        start, end = span
        count = days if days is not None else (end - start).days + 1
        before = _days_before(start, count)
        return None if before is None else (*before, "range")

    return [
        # Tết and its run-up: match before the generic "N ngày ... trước" rule
        (
            rf"\b(\d+) ngay truoc {_TET}(?: nam)? (\d{{4}})\b",
            lambda n, yy: before_tet(yy, n),
        ),
        (rf"\btruoc {_TET}(?: nam)? (\d{{4}})\b", lambda yy: before_tet(yy)),
        (rf"\b(\d+) ngay truoc {_TET}\b{_NOT_SOLAR_NEW_YEAR}", lambda n: before_tet(y, n)),
        (rf"\btruoc {_TET}\b{_NOT_SOLAR_NEW_YEAR}", lambda: before_tet(y)),
        (rf"\b{_TET}(?: nam)? (\d{{4}})\b", lambda yy: tet(yy)),
        (rf"\b{_TET} nam (?:nay)\b", lambda: tet(y)),
        (rf"\b{_TET} nam (?:truoc|ngoai|roi|qua)\b", lambda: tet(y - 1)),
        (rf"\b{_TET}\b{_NOT_SOLAR_NEW_YEAR}", lambda: tet(y)),
        # longer, more specific patterns first
        (r"\b(\d+) (ngay|tuan|thang) (?:qua|gan day|gan nhat|vua qua|truoc)\b", None),
        (r"\bngay (\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?\b", explicit_day),
        (r"\bthang (\d{1,2})(?:[/-]| nam )(\d{4})\b", lambda mm, yy: latest_month(mm, yy)),
        (r"\bthang (\d{1,2})\b", lambda mm: latest_month(mm, None)),
        (r"\bquy (\d)\s*[/ ]\s*(?:nam )?(\d{4})\b", quarter),
        (r"\bquy (\d)(?: nam (\d{4}))?\b", quarter),
        (r"\bnam (\d{4})\b", lambda yy: (date(yy, 1, 1), date(yy, 12, 31), "year")),
        (r"\bhom kia\b", (today - timedelta(days=2), today - timedelta(days=2), "day")),
        (r"\bhom qua\b", (today - timedelta(days=1), today - timedelta(days=1), "day")),
        (r"\bhom nay\b", (today, today, "day")),
        (rf"\btuan {_PAST}\b", (week - timedelta(days=7), week - timedelta(days=1), "week")),
        (rf"\btuan {_THIS}\b", (week, today, "week")),
        (rf"\bthang {_PAST}\b", (*_month_range(py, pm), "month")),
        (rf"\bthang {_THIS}\b", (date(y, m, 1), today, "month")),
        (rf"\bquy {_PAST}\b", (*_quarter_range(pq_year, pq), "quarter")),
        (rf"\bquy {_THIS}\b", (_quarter_range(y, q)[0], today, "quarter")),
        (r"\btu dau nam(?: (?:toi|den) (?:nay|hom nay))?\b", (date(y, 1, 1), today, "year")),
        (r"\bnam (?:ngoai|truoc|roi|qua)\b", (date(y - 1, 1, 1), date(y - 1, 12, 31), "year")),
        (rf"\bnam {_THIS}\b", (date(y, 1, 1), today, "year")),
    ]


def _last_n(n: int, unit: str, today: date) -> tuple[date, date, str]:
    """'N ngày/tuần/tháng qua': the period of that length ending on `today`, inclusive."""
    if unit == "thang":  # calendar months back
        sy, sm = _shift_month(today.year, today.month, -n)
        day = min(today.day, calendar.monthrange(sy, sm)[1])
        return date(sy, sm, day) + timedelta(days=1), today, "range"
    days = n * (7 if unit == "tuan" else 1)
    return today - timedelta(days=days - 1), today, "range"


def _cap_previous_month(found: list[tuple[int, TimeRange]], today: date) -> None:
    """Rulebook §2: with "tháng này", "tháng trước" keeps only the same number of days."""
    if not any(r.granularity == "month" and r.phrase in _THIS_MONTH_PHRASES for _, r in found):
        return
    for i, (position, item) in enumerate(found):
        if item.granularity != "month" or item.phrase not in _PREV_MONTH_PHRASES:
            continue
        last = calendar.monthrange(item.start.year, item.start.month)[1]
        end = date(item.start.year, item.start.month, min(today.day, last))
        found[i] = (position, TimeRange(item.phrase, item.start, end, item.granularity))


def resolve(question: str, as_of_date: date, lunar: LunarCalendar | None = None) -> list[TimeRange]:
    """All time expressions in `question`, in order of appearance, as inclusive date ranges.

    `lunar` supplies the split's calendar for Tết; without it Tết expressions are left unresolved.
    """
    text = normalize(question)
    taken: list[tuple[int, int]] = []
    found: list[tuple[int, TimeRange]] = []

    def free(span: tuple[int, int]) -> bool:
        return all(span[1] <= a or span[0] >= b for a, b in taken)

    for pattern, value in _rules(as_of_date, lunar):
        for match in re.finditer(pattern, text):
            if not free(match.span()):
                continue
            try:
                if value is None:  # "N ngày/tuần/tháng qua"
                    result: Span | None = _last_n(int(match.group(1)), match.group(2), as_of_date)
                elif callable(value):
                    args = [int(g) if g else None for g in match.groups()]
                    while args and args[-1] is None:
                        args.pop()
                    result = value(*args)
                else:
                    result = value
            except ValueError:  # e.g. "tháng 13" or "ngày 31/2"
                continue
            if result is None:  # e.g. Tết without a calendar
                continue
            start, end, gran = result
            taken.append(match.span())
            found.append((match.start(), TimeRange(match.group(0), start, end, gran)))
    _cap_previous_month(found, as_of_date)
    return [r for _, r in sorted(found, key=lambda x: x[0])]


def render_time_ranges(ranges: list[TimeRange], as_of_date: date) -> str:
    lines = [f"as_of_date: {as_of_date.isoformat()} ({_WEEKDAYS[as_of_date.weekday()]})"]
    lines += [
        f'- "{r.phrase}" -> {r.start.isoformat()} .. {r.end.isoformat()} ({r.granularity})'
        for r in ranges
    ]
    return "\n".join(lines)


_WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
