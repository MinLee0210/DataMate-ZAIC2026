import re
from datetime import date

import duckdb
import yaml

from src.models import ColumnCard, SchemaCard, TableCard

TOP_K = 8
MAX_VALUE_CHARS = 60
# a transaction date column; birth dates, expiry dates and record-creation timestamps are not
# the shop's data window (a product created in 2023 does not mean the shop sold anything then)
_DATE_NAME = re.compile(r"ngay|thoi_gian|date|time")
# word-bounded: "han" (expiry) must not match "hang" in "ngay_dat_hang" (order date)
_NOT_WINDOW = re.compile(r"(^|_)(sinh|han|expiry|birth|tao|created|create)($|_)")


def data_window(card: SchemaCard) -> tuple[str | None, str | None]:
    """First and last date over the transaction-like date columns, ISO, or (None, None).

    A shop's birth-date column holds 1965 and its expiry-date column 2027; neither says when the
    shop has sales. The window is the widest range of a date column whose values reach 2020.
    """
    low: date | None = None
    high: date | None = None
    for table in card.tables:
        for column in table.columns:
            if not (column.min and column.max):
                continue
            if not _DATE_NAME.search(column.name) or _NOT_WINDOW.search(column.name):
                continue
            try:
                start = date.fromisoformat(column.min[:10])
                end = date.fromisoformat(column.max[:10])
            except ValueError:
                continue
            if end.year < 2020:
                continue
            low = start if low is None or start < low else low
            high = end if high is None or end > high else high
    return (
        low.isoformat() if low else None,
        high.isoformat() if high else None,
    )


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def build_table_card(
    conn: duckdb.DuckDBPyConnection, name: str, source: str, originals: list[str]
) -> TableCard:
    """Profile a DuckDB table: types, null ratio, distinct count, top values, min/max."""
    t = _quote(name)
    rows = conn.execute(f"SELECT count(*) FROM {t}").fetchall()[0][0]
    described = conn.execute(f"DESCRIBE {t}").fetchall()
    columns = []
    for (col, dtype, *_), original in zip(described, originals, strict=False):
        c = _quote(col)
        nulls, distinct = conn.execute(
            f"SELECT count(*) - count({c}), count(DISTINCT {c}) FROM {t}"
        ).fetchall()[0]
        card = ColumnCard(
            name=col,
            original=original,
            dtype=dtype,
            null_ratio=round(nulls / rows, 3) if rows else 0.0,
            distinct=distinct,
        )
        if dtype in {"VARCHAR", "BOOLEAN"}:
            top = conn.execute(
                f"SELECT {c} FROM {t} WHERE {c} IS NOT NULL "
                f"GROUP BY {c} ORDER BY count(*) DESC, {c} LIMIT {TOP_K}"
            ).fetchall()
            card.top_values = [str(v[0])[:MAX_VALUE_CHARS] for v in top]
        else:
            lo, hi = conn.execute(f"SELECT min({c}), max({c}) FROM {t}").fetchall()[0]
            card.min, card.max = (
                (str(lo) if lo is not None else None),
                (str(hi) if hi is not None else None),
            )
        columns.append(card)
    return TableCard(name=name, source=source, rows=rows, columns=columns)


def render_schema_card(card: SchemaCard) -> str:
    """YAML context for the prompt, as authored context."""
    tables = []
    for table in card.tables:
        fields = []
        for col in table.columns:
            field: dict = {"name": col.name, "type": col.dtype}
            if col.original != col.name:
                field["header"] = col.original
            if col.top_values:
                field["values"] = col.top_values
                if col.distinct > len(col.top_values):
                    field["distinct"] = col.distinct
            if col.min is not None:
                field["range"] = [col.min, col.max]
            if col.null_ratio:
                field["null_ratio"] = col.null_ratio
            fields.append(field)
        tables.append(
            {"table": table.name, "source": table.source, "rows": table.rows, "fields": fields}
        )
    payload: dict = {"tables": tables}
    if card.data_start and card.data_end:
        payload["data_window"] = {"first_date": card.data_start, "last_date": card.data_end}
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000)
