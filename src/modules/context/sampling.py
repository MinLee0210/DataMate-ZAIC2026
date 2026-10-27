"""Sample real values of the fields the agent asked for (CA-API's PROGRESS step, "Sampling data
for fields ..."), so the query filters on values that exist. Deterministic, no LLM.

Per field: number of distinct values; the most frequent values (text columns) or min / max
(number and date columns); and, for date columns, how many rows fall after the as-of date
(they exist but must not be counted).
"""

from datetime import date

from src.data.duckdb import DuckDBSource
from src.models import SchemaCard

MAX_FIELDS = 8
MAX_VALUES = 20
_DATE_TYPES = ("DATE", "TIMESTAMP")
_NUMBER_TYPES = ("INT", "DOUBLE", "FLOAT", "DECIMAL", "BIGINT", "HUGEINT", "REAL", "NUMERIC")


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def resolve_fields(card: SchemaCard, fields: list[str]) -> list[tuple[str, str, str]]:
    """`table.column` names that exist, as (table, column, dtype); unknown names are dropped."""
    columns = {
        (t.name.lower(), c.name.lower()): (t.name, c.name, c.dtype.upper())
        for t in card.tables
        for c in t.columns
    }
    found: list[tuple[str, str, str]] = []
    for field in fields:
        table, _, column = str(field).strip().strip('`"').partition(".")
        hit = columns.get((table.lower(), column.lower()))
        if hit and hit not in found:
            found.append(hit)
    return found[:MAX_FIELDS]


def sample_fields(
    source: DuckDBSource, card: SchemaCard, fields: list[str], as_of: date, timeout_s: float = 10.0
) -> str:
    """Markdown block of sampled values, one section per field."""
    sections: list[str] = []
    for table, column, dtype in resolve_fields(card, fields):
        t, c = _quote(table), _quote(column)
        try:
            distinct = source.query(f"SELECT count(DISTINCT {c}) FROM {t}", timeout_s).iat[0, 0]
            lines = [f"### Field: {table}.{column} ({dtype}, {distinct} distinct values)"]
            if dtype.startswith(_DATE_TYPES) or dtype.startswith(_NUMBER_TYPES):
                row = source.query(f"SELECT min({c}), max({c}) FROM {t}", timeout_s).iloc[0]
                lines.append(f"  - min {row.iloc[0]}, max {row.iloc[1]}")
            if dtype.startswith(_DATE_TYPES):
                after = source.query(
                    f"SELECT count(*) FROM {t} WHERE CAST({c} AS DATE) > DATE '{as_of}'",
                    timeout_s,
                ).iat[0, 0]
                lines.append(f"  - rows after the as-of date {as_of}: {after} (do not count them)")
            else:
                top = source.query(
                    f"SELECT {c} AS v, count(*) AS n FROM {t} GROUP BY 1 "
                    f"ORDER BY n DESC, v LIMIT {MAX_VALUES}",
                    timeout_s,
                )
                lines += [f"  - {v!r} ({n} rows)" for v, n in top.itertuples(index=False)]
        except Exception as e:  # a field that cannot be sampled is reported, not fatal
            lines = [f"### Field: {table}.{column}: could not sample ({type(e).__name__})"]
        sections.append("\n".join(lines))
    return "\n".join(sections) or "(no fields sampled)"
