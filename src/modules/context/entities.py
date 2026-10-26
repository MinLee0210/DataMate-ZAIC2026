import re
import unicodedata
from dataclasses import dataclass

import duckdb
from rapidfuzz import fuzz, process

from src.models import SchemaCard

# text columns with more distinct values than this are free text (notes, addresses), not entities
MAX_ENTITY_VALUES = 5000
MIN_SCORE = 88.0
MAX_NGRAM = 5


@dataclass(frozen=True)
class Entity:
    value: str
    table: str
    column: str


@dataclass(frozen=True)
class EntityMatch:
    mention: str
    entity: Entity
    score: float


def fold(text: str, keep: str = "") -> str:
    """Lowercase, drop diacritics, collapse non-alphanumerics: 'Cà phê sữa' -> 'ca phe sua'.

    Characters in `keep` (e.g. '/-' for dates) are not collapsed.
    """
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    return re.sub(rf"[^a-z0-9{re.escape(keep)}]+", " ", text).strip()


# chat spellings mapped to one canonical form, applied to both sides of a match
_PHONETIC = ((re.compile(r"ph"), "f"), (re.compile(r"k"), "c"), (re.compile(r"z"), "d"))


def phonetic(folded: str) -> str:
    """'ca phe' and 'ca fe' -> 'ca fe'; 'kem' -> 'cem'. Input is already folded."""
    for pattern, repl in _PHONETIC:
        folded = pattern.sub(repl, folded)
    return folded


def build_entity_dict(conn: duckdb.DuckDBPyConnection, card: SchemaCard) -> list[Entity]:
    entities = []
    for table in card.tables:
        for col in table.columns:
            if col.dtype != "VARCHAR" or not 0 < col.distinct <= MAX_ENTITY_VALUES:
                continue
            values = conn.execute(
                f'SELECT DISTINCT "{col.name}" FROM "{table.name}" '
                f'WHERE "{col.name}" IS NOT NULL ORDER BY 1'
            ).fetchall()
            entities.extend(Entity(str(v[0]), table.name, col.name) for v in values)
    return entities


def _ngrams(tokens: list[str]) -> list[str]:
    return [
        " ".join(tokens[i : i + n])
        for n in range(1, MAX_NGRAM + 1)
        for i in range(len(tokens) - n + 1)
    ]


def link_entities(question: str, entities: list[Entity], limit: int = 10) -> list[EntityMatch]:
    """Fuzzy-match question n-grams to known cell values.

    Insensitive to diacritics, case and chat spellings (phonetic()).

    Deterministic: ties are broken by value, table and column.
    """
    if not entities:
        return []
    folded = [phonetic(fold(e.value)) for e in entities]
    best: dict[Entity, EntityMatch] = {}
    for gram in _ngrams(phonetic(fold(question)).split()):
        if len(gram) < 3:
            continue
        for _, score, idx in process.extract(
            gram, folded, scorer=fuzz.ratio, score_cutoff=MIN_SCORE, limit=5
        ):
            entity = entities[idx]
            if entity not in best or score > best[entity].score:
                best[entity] = EntityMatch(gram, entity, score)
    ranked = sorted(
        best.values(),
        key=lambda m: (-m.score, -len(m.mention), m.entity.value, m.entity.table, m.entity.column),
    )
    return ranked[:limit]


def render_entity_matches(matches: list[EntityMatch]) -> str:
    if not matches:
        return "(none)"
    return "\n".join(
        f"- \"{m.mention}\" -> {m.entity.table}.{m.entity.column} = '{m.entity.value}'"
        for m in matches
    )
