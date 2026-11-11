"""Premise checks: questions the released data provably cannot answer.

Rulebook §7: a period entirely outside the shop's data is *unanswerable*, not 0. The time
resolver already produces the period; the schema card holds the shop's data window (first and
last transaction date). No overlap means no LLM call is needed, and the answer is certain.

Deliberately narrow: only a period with no overlap at all is flagged. A period that overlaps
partly is computed on the overlapping part (rulebook §7), so it must still go through the agent.
"""

from dataclasses import dataclass
from datetime import date

from src.models import SchemaCard
from src.utils.timeparse import TimeRange


@dataclass(frozen=True)
class Premise:
    reason: str


def check_premise(ranges: list[TimeRange], card: SchemaCard) -> Premise | None:
    """A reason when every resolved period lies outside the data, else None."""
    if not ranges or not (card.data_start and card.data_end):
        return None
    try:
        first = date.fromisoformat(card.data_start)
        last = date.fromisoformat(card.data_end)
    except ValueError:
        return None
    if any(not (item.end < first or item.start > last) for item in ranges):
        return None
    asked = ", ".join(f"{item.start.isoformat()}..{item.end.isoformat()}" for item in ranges)
    return Premise(
        f"every period in the question ({asked}) lies outside the data"
        f" ({first.isoformat()}..{last.isoformat()})"
    )
