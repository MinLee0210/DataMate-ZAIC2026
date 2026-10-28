"""Turn an executed query result into a typed answer value, deterministically.

Output conventions (verify against the official answer examples):
- number, percent: rounded to 2 dp; integral values become int. Percent is in percentage points
  (12.5 means 12.5%), the SQL is asked to multiply by 100.
- date: 'yyyy-mm-dd', or 'yyyy-mm' when the query returns a month.
- boolean: true / false.
- list: values of the first column, in row order.
- table: {"columns": [...], "rows": [[...], ...]} (rulebook §9); column 1 is the object name.
"""

import math
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from src.utils.text import fold

_MONTH = re.compile(r"^\d{4}-\d{2}$")
_TRUE = {"true", "1", "yes", "co", "có", "đúng", "dung", "t"}
_FALSE = {"false", "0", "no", "khong", "không", "sai", "f"}


class FormatError(ValueError):
    """The result does not have the shape or type the answer type needs."""


def round_number(value: Any) -> int | float:
    if isinstance(value, bool):
        raise FormatError("boolean is not a number")
    if isinstance(value, str):
        value = value.strip().replace(",", "")
    try:
        x = float(Decimal(str(value)))
    except Exception as e:
        raise FormatError(f"not a number: {value!r}") from e
    if math.isnan(x) or math.isinf(x):
        raise FormatError(f"not a finite number: {value!r}")
    # round half away from zero on the decimal representation, not on binary floats
    rounded = float(Decimal(str(x)).quantize(Decimal("0.01"), rounding="ROUND_HALF_UP"))
    return int(rounded) if rounded.is_integer() else rounded


def format_date(value: Any) -> str:
    if isinstance(value, pd.Timestamp | datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if _MONTH.match(text):
        return text
    try:
        return pd.Timestamp(text).date().isoformat()
    except (ValueError, TypeError) as e:
        raise FormatError(f"not a date: {value!r}") from e


def format_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float) and value in (0, 1):
        return bool(value)
    text = str(value).strip().lower()
    if text in _TRUE:
        return True
    if text in _FALSE:
        return False
    raise FormatError(f"not a boolean: {value!r}")


def format_scalar(value: Any) -> Any:
    """A cell inside a list or table: numbers rounded, dates ISO, the rest as text."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int | float | Decimal):
        return round_number(value)
    if isinstance(value, pd.Timestamp | datetime | date):
        return format_date(value)
    return str(value).strip()


def format_result(answer_type: str, frame: pd.DataFrame) -> Any:
    """Typed answer value from a query result. Raises FormatError on a shape or type mismatch."""
    if frame.empty or frame.shape[1] == 0:
        raise FormatError("empty result")
    if answer_type == "list":
        return [format_scalar(v) for v in frame.iloc[:, 0].tolist()]
    if answer_type == "table":
        return {
            "columns": [str(c) for c in frame.columns],
            "rows": [[format_scalar(v) for v in row] for row in frame.itertuples(index=False)],
        }
    if frame.shape[0] != 1:
        raise FormatError(f"{answer_type} needs one row, got {frame.shape[0]}")
    value = frame.iat[0, 0]
    if value is None or (isinstance(value, float) and math.isnan(value)) or value is pd.NaT:
        raise FormatError("null result")
    if answer_type in ("number", "percent"):
        return round_number(value)
    if answer_type == "date":
        return format_date(value)
    if answer_type == "boolean":
        return format_boolean(value)
    if answer_type == "string":
        return str(value).strip()
    raise FormatError(f"unknown answer type {answer_type!r}")


# money words, folded (utils.text.fold): a number answer to such a question is whole VND
_MONEY = re.compile(
    r"\b(tien|doanh thu|dthu|doanh so|gia|chi phi|loi nhuan|lai gop|lai rong|von|no|cong no"
    r"|vnd|dong tien|thu ve|ban duoc bao nhieu tien)\b"
)
# questions that ask for a count or a quantity, even when a money word appears ("số đơn", "mấy ly")
_COUNT = re.compile(
    r"\b(so don|bao nhieu don|may don|so bill|so luong|bao nhieu ly|may ly|so khach)\b"
)


def is_money_question(question: str) -> bool:
    """Rulebook §9: money is whole VND, and an average of money is money too."""
    text = fold(question)
    return bool(_MONEY.search(text)) and not _COUNT.search(text)


def round_money(value: int | float) -> int:
    """Whole VND, half up (rulebook §3: nửa đồng làm tròn lên)."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding="ROUND_HALF_UP"))
