import re
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import openpyxl
import pandas as pd

from src.modules.ingest.clean import fill_grouped_rows, frame_from_raw, infer_types, to_identifier
from src.utils import get_logger

logger = get_logger(__name__)

TABLE_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".sqlite", ".sqlite3", ".db"}
_CSV_ENCODINGS = ("utf-8-sig", "utf-16", "cp1258", "latin-1")


class Table:
    """A cleaned table ready for DuckDB."""

    def __init__(self, name: str, source: str, frame: pd.DataFrame, originals: list[str]):
        self.name = name
        self.source = source
        self.frame = frame
        self.originals = originals


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in _CSV_ENCODINGS:
        try:
            # header=None: the header row is detected later; sep=None sniffs , ; or tab
            return pd.read_csv(
                path, header=None, dtype=str, encoding=encoding, sep=None, engine="python"
            )
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise ValueError(f"cannot decode {path}")


def _sheet_values(sheet) -> pd.DataFrame:
    """Sheet cells as a frame; a merged range repeats its top-left value in every cell."""
    rows = [list(r) for r in sheet.iter_rows(values_only=True)]
    for merged in sheet.merged_cells.ranges:
        top = rows[merged.min_row - 1][merged.min_col - 1] if rows else None
        for r in range(merged.min_row - 1, min(merged.max_row, len(rows))):
            for c in range(merged.min_col - 1, merged.max_col):
                if c < len(rows[r]):
                    rows[r][c] = top
    return pd.DataFrame(rows)


def _read_xlsx(path: Path) -> Iterator[tuple[str, pd.DataFrame]]:
    # not read_only: merged cell ranges are only available on a fully loaded workbook
    book = openpyxl.load_workbook(path, data_only=True)
    try:
        for sheet in book.worksheets:
            if sheet.sheet_state == "visible":
                yield sheet.title, _sheet_values(sheet)
    finally:
        book.close()


def _read_sqlite(path: Path) -> Iterator[tuple[str, pd.DataFrame]]:
    # sqlite3 instead of the DuckDB sqlite extension: the extension is downloaded on first use,
    # which fails offline
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        names = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for name in names:
            yield name, pd.read_sql_query(f'SELECT * FROM "{name}"', conn)
    finally:
        conn.close()


def read_tables(path: Path, infer: bool = True) -> list[Table]:
    """Read one data file into cleaned tables (one per CSV, sheet or SQLite table).

    With `infer=False` the cells stay as read; `merge_split_tables` then infers types after
    merging, so one column gets one type across all its sheets."""
    suffix = path.suffix.lower()
    stem = to_identifier(path.stem)
    tables: list[Table] = []
    if suffix == ".csv":
        frame, originals = frame_from_raw(_read_csv(path))
        tables.append(Table(stem, path.name, frame, originals))
    elif suffix in {".xlsx", ".xlsm"}:
        sheets = list(_read_xlsx(path))
        for title, raw in sheets:
            frame, originals = frame_from_raw(raw)
            name = stem if len(sheets) == 1 else f"{stem}__{to_identifier(title)}"
            tables.append(Table(name, f"{path.name}#{title}", frame, originals))
    elif suffix in {".sqlite", ".sqlite3", ".db"}:
        for name, frame in _read_sqlite(path):
            originals = [str(c) for c in frame.columns]
            frame.columns = [to_identifier(c) for c in originals]
            tables.append(Table(to_identifier(name), f"{path.name}#{name}", frame, originals))
    else:
        raise ValueError(f"unsupported file type: {path}")
    out = []
    for table in tables:
        if table.frame.empty:
            logger.warning("skipping empty table %s", table.source)
            continue
        table.frame = fill_grouped_rows(table.frame)
        if infer:
            table.frame = infer_types(table.frame)
        out.append(table)
    return out


SOURCE_COLUMN = "nguon"
_SPLIT_SUFFIX = re.compile(r"(_\d+)+$")


def _base_name(name: str) -> str:
    """'donhang_chitiet_1__t01_2025' -> 'donhang_chitiet': sheet and numeric file suffixes off."""
    return _SPLIT_SUFFIX.sub("", name.split("__", 1)[0]) or name


def merge_split_tables(tables: list[Table]) -> list[Table]:
    """Merge tables split by month, period or part (one sheet per month, File_1 / File_2, ...).

    Tables with the same base name and the same columns become one table named after the base,
    with a `nguon` column holding each row's file and sheet. Types are inferred after merging.
    """
    groups: dict[tuple[str, tuple[str, ...]], list[Table]] = {}
    for table in tables:
        key = (_base_name(table.name), tuple(table.frame.columns))
        groups.setdefault(key, []).append(table)
    out: list[Table] = []
    for (base, _), group in groups.items():
        if len(group) == 1:
            table = group[0]
            table.frame = infer_types(table.frame)
            out.append(table)
            continue
        frame = pd.concat(
            [t.frame.assign(**{SOURCE_COLUMN: t.source}) for t in group], ignore_index=True
        )
        merged = Table(
            base,
            "; ".join(t.source for t in group),
            infer_types(frame),
            [*group[0].originals, "Nguồn (file#sheet)"],
        )
        logger.info("merged %d split tables into %s", len(group), base)
        out.append(merged)
    return out
