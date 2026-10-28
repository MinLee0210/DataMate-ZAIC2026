"""Semantic layer: split-wide rulebook definitions as DuckDB views and macros.

Each `assets/semantic/*.sql` file holds `CREATE OR REPLACE VIEW|MACRO` statements written once
from the rulebook (valid_orders, revenue, cogs, overdue_debt, ...). They must be generic: a
statement that refers to tables or columns a business does not have fails and is skipped, so
every business gets the subset of the layer its schema supports.
"""

from pathlib import Path

import duckdb

from src.utils import get_logger

logger = get_logger(__name__)

SEMANTIC_DIR = Path(__file__).resolve().parents[2] / "assets" / "semantic"


def _statements(text: str) -> list[str]:
    """SQL statements of a file; `--` comment lines are dropped (a comment above a statement
    used to drop the statement too)."""
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("--"))
    return [s.strip() for s in code.split(";") if s.strip()]


def apply_semantic_layer(
    conn: duckdb.DuckDBPyConnection, semantic_dir: Path = SEMANTIC_DIR
) -> list[str]:
    """Create every view/macro this business supports. Returns the names created."""
    created = []
    for path in sorted(semantic_dir.glob("*.sql")):
        for statement in _statements(path.read_text()):
            try:
                conn.execute(statement)
                created.append(statement.split("(")[0].split()[-1])
            except duckdb.Error as e:
                logger.info("semantic %s: skipped a statement (%s)", path.name, str(e)[:120])
    return created
