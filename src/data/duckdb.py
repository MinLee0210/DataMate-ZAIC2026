import threading
from pathlib import Path

import duckdb
import pandas as pd
import sqlglot
from sqlglot import exp

from src.data.base import DataSource

# statements a candidate may run: plain reads only
_READ_ONLY = (exp.Select, exp.Union, exp.Intersect, exp.Except)


class UnsafeSQLError(ValueError):
    pass


def check_read_only(sql: str) -> None:
    """Raise UnsafeSQLError unless `sql` is a single SELECT / WITH ... SELECT statement."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except sqlglot.errors.ParseError as e:
        raise UnsafeSQLError(f"cannot parse SQL: {e}") from e
    if len(statements) != 1:
        raise UnsafeSQLError(f"expected one statement, got {len(statements)}")
    if not isinstance(statements[0], _READ_ONLY):
        raise UnsafeSQLError(f"only SELECT is allowed, got {statements[0].key.upper()}")


class DuckDBSource(DataSource):
    """One business's DuckDB file. Queries run read-only, with a timeout and a row cap."""

    def __init__(self, path: Path | str, read_only: bool = True) -> None:
        self.path = Path(path)
        self.read_only = read_only
        self.conn: duckdb.DuckDBPyConnection | None = None

    def connect(self) -> None:
        self.conn = duckdb.connect(str(self.path), read_only=self.read_only)
        if self.read_only:
            # no file or network access from generated SQL
            self.conn.execute("SET enable_external_access = false")

    def ping(self) -> None:
        if self.conn is None:
            raise RuntimeError("not connected")
        self.conn.execute("SELECT 1")

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def query(self, sql: str, timeout_s: float = 20.0, max_rows: int = 200) -> pd.DataFrame:
        """Run a read-only query; at most `max_rows` rows are returned."""
        if self.conn is None:
            raise RuntimeError("not connected")
        check_read_only(sql)
        # a cursor per query: a partly fetched result must not block the next query
        cursor = self.conn.cursor()
        timer = threading.Timer(timeout_s, cursor.interrupt)
        timer.start()
        try:
            cursor.execute(sql)
            columns = [d[0] for d in cursor.description]
            rows = cursor.fetchmany(max_rows)
        finally:
            timer.cancel()
            cursor.close()
        return pd.DataFrame(rows, columns=columns)
