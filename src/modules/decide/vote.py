"""Decide from executed candidates: answer, abstain or unanswerable.

PA gives +1 / 0 / -1, so we answer only when we expect P(correct) > 0.5. Vote agreement
(share of the k candidates that reached the top answer) is the confidence estimate; tau is
calibrated on dev with the target model (see scripts/eval.py, the PA-vs-tau curve).
"""

import json
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from src.models import Answer

UNANSWERABLE = "unanswerable"


@dataclass
class Candidate:
    """One SQL candidate after execution. `answer_type` is 'unanswerable' when the model said so."""

    answer_type: str
    value: Any = None
    sql: str = ""
    error: str | None = None  # set when generation, execution or formatting failed

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class Decision:
    answer: Answer
    agreement: float
    # the answer that won the vote, even when abstaining (used for tau calibration)
    top: Answer | None = None
    votes: dict[str, int] = field(default_factory=dict)


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).strip().lower()
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def vote_key(candidate: Candidate) -> str:
    """Candidates with the same type and the same normalized value share a key."""
    if candidate.answer_type == UNANSWERABLE:
        return UNANSWERABLE
    return json.dumps([candidate.answer_type, _normalize(candidate.value)], ensure_ascii=False)


def decide(candidates: list[Candidate], tau: float) -> Decision:
    """Majority vote over successful candidates. Failed candidates count against agreement.

    Ties between keys are broken by first appearance (candidate order is fixed by seed), so
    the decision is deterministic.
    """
    total = len(candidates)
    valid = [c for c in candidates if c.ok]
    if not valid:
        return Decision(Answer(type="abstain"), 0.0)
    counts = Counter(vote_key(c) for c in valid)
    # Counter keeps first-seen order and max() returns the first maximum
    top_key = max(counts, key=counts.__getitem__)
    winner = next(c for c in valid if vote_key(c) == top_key)
    agreement = counts[top_key] / total
    top = (
        Answer(type="unanswerable")
        if top_key == UNANSWERABLE
        else Answer(type=winner.answer_type, value=winner.value)
    )
    answer = top if agreement >= tau else Answer(type="abstain")
    return Decision(answer, agreement, top, dict(counts))
