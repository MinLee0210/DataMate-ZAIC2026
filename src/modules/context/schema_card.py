import duckdb
import yaml

from src.models import ColumnCard, SchemaCard, TableCard

TOP_K = 8
MAX_VALUE_CHARS = 60


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
    """YAML context for the prompt, in the shape of Conversational Analytics authored context."""
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
    return yaml.safe_dump({"tables": tables}, allow_unicode=True, sort_keys=False, width=1000)
