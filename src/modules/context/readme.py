"""The shop's README as prompt context: the head, plus the conventions section.

A README often runs past the prompt budget. Cutting it at a fixed length drops the last section,
which is usually `## Quy ước` — the shop's own rules (a return is a negative line, `Tiền 0` is a
warranty ticket, a topping shares the item cell, ...). Those conventions are worth more than the
column list above them, so the excerpt keeps the head and always appends that section.
"""

import re

from src.utils.text import fold

README_CHARS = 4000
# section headings whose body holds shop-specific conventions, folded (no accents)
_KEEP_SECTIONS = ("quy uoc", "quy dinh", "quy tac", "luu y", "ghi chu", "cach ghi")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
_SEPARATOR = "\n\n[...]\n\n"


def _conventions(text: str) -> str:
    """From the first conventions heading to the end, or "" when there is none."""
    offset = 0
    for line in text.splitlines(keepends=True):
        match = _HEADING.match(line)
        if match and any(key in fold(match.group(1)) for key in _KEEP_SECTIONS):
            return text[offset:].strip()
        offset += len(line)
    return ""


def readme_excerpt(text: str, limit: int = README_CHARS) -> str:
    """The README, cut to `limit` characters but never losing its conventions section."""
    text = text.strip()
    if len(text) <= limit:
        return text
    tail = _conventions(text)
    if not tail:
        return text[:limit]
    tail = tail[: limit // 2]
    budget = limit - len(tail) - len(_SEPARATOR)
    if budget < 200:  # the conventions alone fill the budget
        return tail
    return text[:budget].rstrip() + _SEPARATOR + tail
