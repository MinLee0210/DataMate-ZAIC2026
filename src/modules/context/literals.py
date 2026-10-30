"""Check the string literals of a query against the values in the data.

Weak models guess values (`status IN ('khách hủy', 'Huỷ đơn')`) that the data does not contain, and
a filter on a missing value silently returns 0 rows or counts too much. After a query runs, every
literal compared with `=`, `IN` or `LIKE` is looked up (accent- and case-insensitive) in the string
columns of the business; a missing one is reported with the closest real values. Deterministic, no
LLM, generic across businesses.
"""

import difflib
import re
from collections.abc import Callable

import pandas as pd

from src.models import SchemaCard
from src.utils.text import fold

MAX_VALUES = 20000  # distinct values read per column
_STR = r"'((?:[^']|'')*)'"
_COMPARE = re.compile(rf"(?:=|<>|!=)\s*{_STR}")
_LIKE = re.compile(rf"\b(?:I?LIKE)\s+{_STR}", re.IGNORECASE)
_IN = re.compile(rf"\bIN\s*\(\s*({_STR}(?:\s*,\s*{_STR})*)\s*\)", re.IGNORECASE)
_ONE = re.compile(_STR)
_TEXTUAL = ("VARCHAR", "TEXT", "STRING", "CHAR")


def sql_literals(code: str) -> list[tuple[str, bool]]:
    """(literal, is_pattern) for each string compared with =, <>, IN or LIKE, in query order."""
    found: list[tuple[int, str, bool]] = []
    for m in _COMPARE.finditer(code):
        found.append((m.start(1), m.group(1).replace("''", "'"), False))
    for m in _LIKE.finditer(code):
        found.append((m.start(1), m.group(1).replace("''", "'"), True))
    for m in _IN.finditer(code):
        for item in _ONE.finditer(m.group(1)):
            found.append((m.start(1) + item.start(1), item.group(1).replace("''", "'"), False))
    seen: set[tuple[str, bool]] = set()
    out = []
    for _, text, pattern in sorted(found):
        if (text, pattern) not in seen:
            seen.add((text, pattern))
            out.append((text, pattern))
    return out


class ValueIndex:
    """The distinct string values of one business, folded for lookup."""

    def __init__(self, values: set[str]) -> None:
        self.by_fold: dict[str, str] = {}
        for v in sorted(values):
            self.by_fold.setdefault(fold(v), v)

    @classmethod
    def build(cls, card: SchemaCard, query: Callable[[str], pd.DataFrame]) -> "ValueIndex":
        values: set[str] = set()
        for table in card.tables:
            for column in table.columns:
                if not column.dtype.upper().startswith(_TEXTUAL):
                    continue
                sql = (
                    f'SELECT DISTINCT "{column.name}" FROM "{table.name}" '
                    f'WHERE "{column.name}" IS NOT NULL LIMIT {MAX_VALUES}'
                )
                try:
                    frame = query(sql)
                except Exception:  # an odd column must not break the answer
                    continue
                values.update(str(v) for v in frame.iloc[:, 0].tolist())
        return cls(values)

    def has(self, literal: str, pattern: bool) -> bool:
        key = fold(literal.replace("%", " ").replace("_", " " if pattern else "_"))
        if not key:
            return True  # nothing to check ("%" alone, punctuation)
        if not pattern:
            return key in self.by_fold
        return any(key in v for v in self.by_fold)

    def closest(self, literal: str, n: int = 5) -> list[str]:
        key = fold(literal.replace("%", " "))
        tokens = [t for t in key.split() if len(t) > 2]
        near = [v for v in self.by_fold if tokens and all(t in v for t in tokens)]
        near += difflib.get_close_matches(key, self.by_fold, n=n, cutoff=0.6)
        out: list[str] = []
        for v in near:
            original = self.by_fold[v]
            if original not in out:
                out.append(original)
        return out[:n]


_DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?")


def literal_warnings(code: str, index: ValueIndex) -> list[str]:
    """One line per literal of `code` that no column of the business contains."""
    lines = []
    for literal, pattern in sql_literals(code):
        if _DATE.match(literal) or index.has(literal, pattern):
            continue
        close = index.closest(literal)
        hint = f" Closest real values: {', '.join(repr(c) for c in close)}." if close else ""
        lines.append(f"The value {literal!r} does not occur in any column.{hint}")
    return lines
