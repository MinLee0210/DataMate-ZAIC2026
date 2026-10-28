"""Few-shot examples: solved train questions (question, answer type, verified SQL) retrieved by
BM25 on the question text, shown to the query step as patterns from other shops.

The store is `assets/examples/train_examples.jsonl`, built offline from train runs whose answer
matched the reference (`scripts/datagen/build_examples.py`); hold-out businesses never enter it.
Each record carries its business's schema family: examples from the asking business's family are
left out, so an evaluation never sees its own export template, and the model learns to adapt
patterns across formats. A test business is in no family, so nothing is left out for it.

Matching is on folded text with numbers and dates masked, so "doanh thu tháng 5/2025" and
"doanh thu tháng 11/2026" look alike. Deterministic, no model.
"""

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.utils.text import fold

EXAMPLES_PATH = Path(__file__).resolve().parents[2] / "assets" / "examples" / "train_examples.jsonl"
_NUMBER = re.compile(r"\d+")


def _tokens(text: str) -> list[str]:
    words = _NUMBER.sub("#", fold(text)).split()
    return words + [f"{a}_{b}" for a, b in zip(words, words[1:], strict=False)]


@dataclass
class Example:
    id: str
    business_id: str
    family: str
    question: str
    answer_type: str
    sql: str


class ExampleStore:
    """BM25 (k1=1.5, b=0.75) over the examples' questions."""

    def __init__(self, examples: list[Example]) -> None:
        self.examples = examples
        self.family_of = {e.business_id: e.family for e in examples}
        self.docs = [_tokens(e.question) for e in examples]
        self.avg_len = sum(map(len, self.docs)) / max(len(self.docs), 1)
        df: Counter[str] = Counter()
        for doc in self.docs:
            df.update(set(doc))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [Counter(doc) for doc in self.docs]

    @classmethod
    def load(cls, path: Path = EXAMPLES_PATH) -> "ExampleStore":
        if not path.is_file():
            return cls([])
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        return cls([Example(**{k: r[k] for k in Example.__dataclass_fields__}) for r in rows])

    def search(self, question: str, business_id: str, k: int = 3) -> list[Example]:
        """Top-k examples for the question, never from the asking business's family."""
        if not self.examples or k <= 0:
            return []
        family = self.family_of.get(business_id)
        query = set(_tokens(question))
        scored = []
        for i, example in enumerate(self.examples):
            if example.business_id == business_id or (family and example.family == family):
                continue
            tf, length = self.tf[i], len(self.docs[i])
            score = sum(
                self.idf[t] * tf[t] * 2.5 / (tf[t] + 1.5 * (0.25 + 0.75 * length / self.avg_len))
                for t in query
                if t in tf
            )
            if score > 0:
                scored.append((score, example.id, example))
        scored.sort(key=lambda s: (-s[0], s[1]))
        return [example for _, _, example in scored[:k]]


def render_examples(examples: list[Example]) -> str:
    if not examples:
        return "(none)"
    blocks = []
    for e in examples:
        blocks.append(f"Question: {e.question}\nAnswer type: {e.answer_type}\n```sql\n{e.sql}\n```")
    return "\n\n".join(blocks)
