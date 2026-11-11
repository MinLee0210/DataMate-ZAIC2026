"""The answer's shape, read from the question (rulebook §9), deterministically.

The pipeline used to let the model choose `answer_type`, and it often chose a table where the
rulebook asks for a list: 24 of 1,000 development questions. The cue is in the wording ("liệt kê",
"top 5", "kèm số nợ của từng người"), so it is cheaper and steadier to read it here.

`infer_shape` is deliberately conservative: it returns a shape only when the wording is explicit
(`strong`). Anything else keeps the model's choice, so the router cannot turn an unusual question
into a wrong shape. `coerce` only converts between shapes where the rulebook leaves no choice
(a two-column table where the question asks for one list).
"""

import re
from dataclasses import dataclass

import pandas as pd

from src.utils.text import fold

_OBJECT = r"(khach|mat hang|san pham|mon|hang|nhan vien|nha cung cap|tho|xe|dong may)"
_MEASURE = (
    r"(so tien|so no|\bno\b|tien|doanh thu|dthu|chi tieu|tong|so luong|so don|so kg|so ly|gia tri)"
)

_BOOLEAN = [
    r"\btang lien tuc\b",
    r"\bluon cao hon\b",
    r"\bcao hon thang truoc\b",
    r"\bphai khong\b",
    r"\bdung khong\b",
]
# a yes/no question: "có ... không?" at the end, and no count/measure word in between
_BOOLEAN_TAIL = re.compile(r"\bco\b[^?]{0,120}\b(khong|ko|hok|chua)\b\s*(a|ha|vay|the|nhi)?\s*$")
# a request for several columns per object: one row per object, name first
_TABLE_CUE = [
    r"\bkem (theo|voi)\b",
    r"\bkem (so|tien|tong|no|doanh thu|chi tieu|gia tri)\b",
    r"\bva so\b",
    r"\bva tong\b",
    r"\bmoi nguoi\b",
    r"\bmoi khach\b",
    r"\btung nguoi\b",
    r"\btung khach\b",
    r"\bmoi mat hang\b",
    r"\bmoi mon\b",
    r"\bcho bang\b",
    r"\bcho minh bang\b",
    r"\bcho toi bang\b",
]
_PERCENT = r"(\bphan tram\b|\bti le\b|\bty le\b|\bti trong\b|\bchiem\b)"
# a `%` that asks for a percentage, not the concentration in a product name ("Otrivin 0,1%")
_PERCENT_SIGN = re.compile(
    r"(bao nhieu|bao nhiu|bnhiu|bn|may|tang|giam|thay doi|chiem|ti le|ty le|phan tram"
    r"|ti trong)\b[^?]{0,25}%|%\s*(so voi|cua|tren)"
)
_DATE = (
    r"(\b(ngay|thang|nam) (nao|may)\b|\bvao (ngay|thang|nam) nao\b|\bkhi nao\b"
    r"|\b(han dung|het han)\b.*\b(ngay nao|khi nao|la ngay|vao ngay)\b)"
)
# "top N" with N >= 2; a bare number before an object noun counts too, but a year must not
# ("2026 mặt hàng ..." is one measure, not a list)
_TOP_N = re.compile(r"\btop\s*(\d{1,3})\b")
_N_OBJECT = re.compile(rf"(?<![\d/])\b([2-9]|[1-9]\d|100)\s+{_OBJECT}\b")
_LIST = [
    r"\bliet ke\b",
    r"\bke ten\b",
    r"\bdanh sach\b",
    r"\bnhung\b.*\bnao\b",
    r"\blan luot\b",
    r"\btheo thu tu\b",
    r"\bchia theo\b",
]
_ENUM = r"(thang|ngay|kenh|hinh thuc|loai|nhom|ben)"
_ENUM_FIRST = re.compile(
    rf"\bmoi {_ENUM}\b.*(\bbao nhieu\b|\bbao nhiu\b|\bbnhiu\b|\bbn\b|\blan luot\b)"
)
# adjacent only: "bao nhiêu mỗi tháng" is one value per month, "bao nhiêu, tính mọi loại" is one
# total (Vietnamese "mỗi" and "mọi" both fold to "moi")
_ENUM_LAST = re.compile(rf"(\bbao nhieu\b|\bbao nhiu\b|\bbnhiu\b|\bbn\b)[ ,]*\bmoi {_ENUM}\b")
_TWO_MEASURES = re.compile(
    r"\b(may|bao nhieu|bao nhiu|bnhiu)\b[^?]*\b(may|bao nhieu|bao nhiu|bnhiu)\b"
)
_STRING = (
    r"(\bla ai\b|\bai la\b|\bkhach nao\b|\bhang nao\b|\bsan pham nao\b|\bmat hang nao\b"
    r"|\bmon nao\b|\bnhan vien nao\b|\bthu nao\b|\bnguoi nao\b)"
)
# "ai" as the subject of a question, not "không ai mua ..." (nobody bought)
_WHO = re.compile(r"(?<!khong )\bai\b")
# an object question ("which customer/item/staff") that a count word must not override
_OBJECT_QUESTION = re.compile(r"\b(khach|hang|san pham|nhan vien|thu|nguoi) nao\b|\bla ai\b")
_NUMBER = (
    r"(\bbao nhieu\b|\bbao nhiu\b|\bbnhiu\b|\bmay\b|\btong\b|\btrung binh\b|\bdem\b"
    r"|\bso luong\b|\bgia tri\b|\bbn\b)"
)
_COUNT_MEASURE = re.compile(r"\b(bao nhieu|bao nhiu|bnhiu|bn)\b")
_OBJECT_WORD = re.compile(rf"\b{_OBJECT}\b")
_ENUMERATED = re.compile(
    r"\b(moi thang|moi ngay|moi kenh|moi hinh thuc|moi loai|moi nhom|moi ben|lan luot"
    r"|cac thang|cac ngay|cac kenh|[2-9] thang|[2-9] ngay)\b"
)

_DESCRIPTIONS = {
    "number": "one number: the value only, no unit, no thousands separator (money is whole VND)",
    "percent": "one number in percentage points (12.4, not 0.124 and not '12,4%')",
    "string": "one name, copied exactly as the shop's data writes it, with diacritics",
    "date": "one ISO date (YYYY-MM-DD), or YYYY-MM when the question asks about a month",
    "boolean": "true or false",
    "list": "a JSON array; one element is still an array",
    "table": '{"columns": [...], "rows": [[...], ...]}; one row per object, name first',
}


@dataclass(frozen=True)
class Shape:
    answer_type: str | None = None
    list_of: str | None = None  # "names" or "measures" when answer_type is list
    strong: bool = False
    reason: str = ""

    @property
    def known(self) -> bool:
        return self.answer_type is not None


def _matches(patterns: list[str] | str, text: str) -> bool:
    patterns = [patterns] if isinstance(patterns, str) else patterns
    return any(re.search(pattern, text) for pattern in patterns)


def infer_shape(question: str) -> Shape:
    """The answer shape the wording asks for, or `Shape()` when it does not say clearly."""
    text = fold(question)
    # `%` survives folding only when asked to: fold() drops punctuation
    percent = _matches(_PERCENT, text) or bool(_PERCENT_SIGN.search(fold(question, keep="%")))
    yes_no = _matches(_BOOLEAN, text) or (
        bool(_BOOLEAN_TAIL.search(text)) and not _matches(_NUMBER, text)
    )

    if yes_no:
        return Shape("boolean", strong=True, reason="yes/no wording")
    if percent:
        return Shape("percent", strong=True, reason="percent wording or % sign")
    if _matches(_DATE, text):
        return Shape("date", strong=True, reason="asks for a date")

    table_cue = _matches(_TABLE_CUE, text)
    if table_cue and _matches(_OBJECT, text) and _matches(_MEASURE, text):
        return Shape("table", strong=True, reason="several measures per named object")

    top = _TOP_N.search(text)
    top_n = int(top.group(1)) if top else 0
    list_cue = (
        _matches(_LIST, text)
        or top_n >= 2
        or bool(_N_OBJECT.search(text))
        or bool(_ENUM_FIRST.search(text))
        or bool(_ENUM_LAST.search(text))
        or bool(_TWO_MEASURES.search(text))
    )
    if list_cue:
        return Shape(
            "list",
            list_of=_list_of(text),
            strong=True,
            reason="asks for several values",
        )
    superlative = re.search(r"\b(nhieu|cao|lon|thap|ban chay|hot|loi) nhat\b", text)
    asks_who = _matches(_STRING, text) or bool(_WHO.search(text)) or bool(superlative)
    # "số khách mua ít nhất 4 đơn là bao nhiêu" is a count, not a question about a person
    if _matches(_NUMBER, text) and not _OBJECT_QUESTION.search(text):
        return Shape("number", strong=True, reason="asks for one measure")
    if top_n == 1 or asks_who:
        return Shape("string", strong=True, reason="asks for one object")
    return Shape()


def _list_of(text: str) -> str:
    """What the list holds: object names, or one measure per period/channel listed."""
    if _ENUMERATED.search(text) or len(_COUNT_MEASURE.findall(text)) >= 2:
        return "measures"
    return "names" if _OBJECT_WORD.search(text) else "measures"


def render_shape(shape: Shape) -> str:
    """The prompt block: the expected shape, or a note that the model must decide."""
    if not shape.known:
        return "(no explicit cue in the question: choose the type rulebook §9 requires and say why)"
    line = f"- Expected answer type: `{shape.answer_type}` — {_DESCRIPTIONS[shape.answer_type]}."
    if shape.answer_type == "list":
        what = "object names" if shape.list_of == "names" else "one measure per item"
        line += f" The list holds {what}, in the order the question names them."
    line += (
        "\n- Keep the query result in that shape: no label column for a list, one row per object"
        " for a table, exactly one row and one column for a scalar."
    )
    return line


def _numeric(frame: pd.DataFrame) -> list[int]:
    return [i for i, dtype in enumerate(frame.dtypes) if pd.api.types.is_numeric_dtype(dtype)]


def _table_to_list(frame: pd.DataFrame, kind: str | None) -> pd.DataFrame:
    """The one column a list question asks for: names, the single measure, or both measures."""
    if frame.shape[1] == 1:
        return frame
    columns = _numeric(frame)
    if kind == "names":
        return frame.iloc[:, [0]]
    if len(columns) == 1:
        return frame.iloc[:, [columns[0]]]
    if columns:
        values = frame.iloc[:, columns].to_numpy().ravel()
        return pd.DataFrame({"value": values})
    return frame.iloc[:, [0]]


def coerce(answer_type: str, frame: pd.DataFrame, shape: Shape) -> tuple[str, pd.DataFrame]:
    """(type, frame) after a conversion the rulebook leaves no choice about. Never raises."""
    if not shape.strong or not shape.known or shape.answer_type == answer_type:
        return answer_type, frame
    if answer_type == "table" and shape.answer_type == "list":
        return "list", _table_to_list(frame, shape.list_of)
    if (
        answer_type == "list"
        and shape.answer_type in {"number", "percent", "string", "date", "boolean"}
        and frame.shape == (1, 1)
    ):
        return shape.answer_type, frame
    return answer_type, frame
