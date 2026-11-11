from datetime import date

from src.models import SchemaCard
from src.modules.questions.premise import check_premise
from src.utils.timeparse import TimeRange


def card(start: str | None = "2025-02-01", end: str | None = "2026-06-30") -> SchemaCard:
    return SchemaCard(business_id="b", data_start=start, data_end=end)


def span(start: str, end: str) -> TimeRange:
    return TimeRange("x", date.fromisoformat(start), date.fromisoformat(end), "month")


def test_a_period_outside_the_data_is_unanswerable():
    premise = check_premise([span("2024-12-01", "2024-12-31")], card())
    assert premise is not None and "outside the data" in premise.reason


def test_a_period_inside_or_overlapping_the_data_is_not_flagged():
    assert check_premise([span("2025-03-01", "2025-03-31")], card()) is None
    # rulebook §7: a partly overlapping period is computed on the overlapping part
    assert check_premise([span("2025-01-01", "2025-02-28")], card()) is None
    assert check_premise([span("2026-06-01", "2026-07-31")], card()) is None


def test_one_answerable_period_is_enough():
    ranges = [span("2024-01-01", "2024-01-31"), span("2025-05-01", "2025-05-31")]
    assert check_premise(ranges, card()) is None


def test_no_period_or_no_window_means_no_check():
    assert check_premise([], card()) is None
    assert check_premise([span("2024-12-01", "2024-12-31")], card(None, None)) is None
