"""Semantic layer: rulebook definitions as DuckDB macros and views, per business.

Two parts:
- the static macros in `assets/semantic/*.sql`, written once from the rulebook (status spellings,
  walk-in customers, text folding). A statement that refers to a table or column a business does
  not have is skipped, so every business gets the subset its schema supports;
- the generated views in `bind.py`, built from the column roles of that business (`roles.py`):
  `v_sales`, `v_orders`, `v_products`, `v_stock`, `v_purchases`. They carry rulebook §1 and §3
  into SQL: valid orders, revenue by order date, a customer is a code.

`apply_semantic_layer` returns one description per object, which is what the prompt shows.
"""

import re
from pathlib import Path

import duckdb

from src.models import SchemaCard
from src.modules.semantic.bind import build_semantic_views
from src.utils import get_logger

logger = get_logger(__name__)

SEMANTIC_DIR = Path(__file__).resolve().parents[2] / "assets" / "semantic"
_MACRO = re.compile(r"MACRO\s+(\w+)\s*\(([^)]*)\)", re.IGNORECASE)
_VIEW = re.compile(r"VIEW\s+(\w+)", re.IGNORECASE)


def _statements(text: str) -> list[str]:
    """SQL statements of a file; `--` comment lines are dropped (a comment above a statement
    used to drop the statement too)."""
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("--"))
    return [s.strip() for s in code.split(";") if s.strip()]


def _describe_static(statement: str) -> str | None:
    """`is_cancelled(status)` or `view_name` for one CREATE statement."""
    if match := _MACRO.search(statement):
        args = ", ".join(part.strip().split()[0] for part in match.group(2).split(",") if part)
        return f"{match.group(1)}({args})"
    if match := _VIEW.search(statement):
        return match.group(1)
    return None


def apply_semantic_layer(
    conn: duckdb.DuckDBPyConnection,
    card: SchemaCard | None = None,
    semantic_dir: Path = SEMANTIC_DIR,
) -> list[str]:
    """Create every rulebook object this business supports. Returns their descriptions."""
    described: list[str] = []
    for path in sorted(semantic_dir.glob("*.sql")):
        for statement in _statements(path.read_text()):
            try:
                conn.execute(statement)
            except duckdb.Error as e:
                logger.info("semantic %s: skipped a statement (%s)", path.name, str(e)[:120])
                continue
            if description := _describe_static(statement):
                described.append(description)
    if card is not None:
        described.extend(build_semantic_views(conn, card))
    return described
