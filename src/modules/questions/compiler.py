"""Deterministic compilers for the highest-volume question families.

The model is good enough to find the table, and not good enough to apply the rulebook exactly:
on dev500, 21 of the 24 wrong revenue answers were within 5 % of gold, i.e. a definition or a
boundary, not a reasoning failure. A family the wording can be read by pattern is cheaper and
more accurate as SQL over the generated semantic views.

`compile_question` returns a ready-to-run SQL and an answer type, or None. It never guesses a
family from a resemblance: every rule requires its own cue and rejects the neighbouring family
(growth is not revenue, a threshold count is not a count, a payment channel is not the shop).
"""

import calendar
import re
from dataclasses import dataclass
from datetime import date

from src.modules.ingest.clean import parse_number
from src.utils.text import fold
from src.utils.timeparse import TimeRange

# a money question is about the shop's own revenue; the exclusions below are the neighbouring
# families (group, channel, customer, item, average, growth, threshold count) that have their own
# compiler or stay with the model
_REVENUE = re.compile(
    r"(doanh thu|dthu|doanh so|tien hang|tien ban|thu ve|thu duoc bao nhieu tien"
    r"|ban duoc bao nhieu tien|ban dc bao nhieu tien)"
)
_NOT_PLAIN = re.compile(
    r"(nhom|loai hang|kenh|quay|ca |nhan vien|nguoi ban|khach|mat hang|san pham|mon |"
    r"trung binh|binh quan|moi don|moi bill|%|phan tram|tang|giam|so voi|cung ky|"
    r"chenh lech|nhap|von|lai|phi|chiet khau|giam gia|\bno\b|hoat chat|nha cung cap|size|"
    r"bao nhieu don|bao nhiu don|may don|so don|ngay nao|thang nao|dot|"
    r"tra bang|tien tuoi|tien mat|chuyen khoan|vi dien tu|cod|zalo|dien thoai|the tin dung)"
)
_GROWTH = re.compile(
    r"(tang|giam|thay doi|hon|kem|cao hon|thap hon).*(bao nhieu|bnhiu|may)?\s*(%|phan tram)"
    r"|(tang|giam|thay doi).*(%|phan tram).*(so voi|cung ky|thang truoc|quy truoc|nam truoc)"
)
_NOT_GROWTH = re.compile(r"(lien tuc|luon cao hon)")
_DIFFERENCE = re.compile(r"(chenh lech|hon|kem|tang|giam).*(bao nhieu|bnhiu)")
_AVG = re.compile(r"(trung binh|binh quan|gia tri tb)")
_ORDER_WORD = re.compile(r"\b(don|bill|hoa don)\b")
_COUNT = re.compile(r"(so don|may don|bao nhieu don|bao nhiu don|bnhiu don|dem (so )?don|don hang)")
_THRESHOLD = re.compile(r"(tu|>=|≥|tro len|dat|tren|hon)\s*[0-9]")
_BEST_DAY = re.compile(r"(ngay nao|hom nao|ngay may).*(cao nhat|dat nhat|nhieu|lon nhat|thap nhat)")
_PAYMENT = re.compile(
    r"(tien mat|chuyen khoan|vi dien tu|vi dien thoai|cod|the tin dung|the ngan hang|"
    r"zalo|dien thoai|quay|tai cua hang|online|giao hang)"
)
_ITEM = re.compile(r"(mat hang|san pham|mon|hang hoa|thuoc)")
_STAFF = re.compile(r"(nhan vien|nguoi ban|ma nv|nv[0-9])")
_PERCENT = re.compile(r"(%|phan tram|ti le|ty le|ti trong|chiem)")
_GROUP = re.compile(r"nhom (hang hoa|hang|san pham|mat hang)?\s*([^,.;?]+)")
_DIMENSION = re.compile(
    r"(tra bang|thanh toan bang|ban qua|ban tai|kenh ban|qua zalo|tai quay|qua dien thoai)"
)
_DIMENSION_ALIASES = {
    "tien tuoi": ("payment_method", ("tien tuoi", "tien mat", "cash")),
    "tien mat": ("payment_method", ("tien mat", "cash")),
    "tm": ("payment_method", ("tien mat", "cash", "tm")),
    "chuyen khoan": ("payment_method", ("chuyen khoan", "transfer", "bank")),
    "ck": ("payment_method", ("chuyen khoan", "transfer", "ck")),
    "vi dien tu": ("payment_method", ("vi dien tu", "ewallet")),
    "vi dien thoai": ("payment_method", ("vi dien thoai", "ewallet")),
    "cod": ("payment_method", ("cod",)),
    "the tin dung": ("payment_method", ("the", "card")),
    "the ngan hang": ("payment_method", ("the", "card")),
    "zalo": ("channel", ("zalo",)),
    "dien thoai": ("channel", ("dien thoai", "phone")),
    "quay": ("channel", ("quay", "store")),
    "tai cua hang": ("channel", ("quay", "store", "cua hang")),
    "online": ("channel", ("online",)),
}
_CUSTOMER = re.compile(r"(khach|nhom khach|than thiet|si |le )")
_NUMBER = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+)")
_THRESHOLD_NUMBER = re.compile(r"(?:tu|>=|≥|tro len|dat|tren|hon)\s*([0-9][0-9.,]*)")


@dataclass(frozen=True)
class Compile:
    family: str
    sql: str
    answer_type: str
    note: str = ""


def _dates(item: TimeRange) -> str:
    return f"DATE '{item.start.isoformat()}' AND DATE '{item.end.isoformat()}'"


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + month - 1 + delta
    return index // 12, index % 12 + 1


def _previous_month(current: TimeRange, as_of: date | None) -> TimeRange:
    """The month before `current`, capped to the same day count when `current` is partial."""
    year, month = _shift_month(current.start.year, current.start.month, -1)
    last = calendar.monthrange(year, month)[1]
    partial = current.start.day == 1 and as_of is not None and current.end == as_of
    end_day = min(as_of.day, last) if partial and as_of is not None else last
    return TimeRange(current.phrase, date(year, month, 1), date(year, month, end_day), "month")


def _last_year(current: TimeRange) -> TimeRange:
    def shift(day: date) -> date:
        try:
            return date(day.year - 1, day.month, day.day)
        except ValueError:  # 29 February
            return date(day.year - 1, day.month, 28)

    return TimeRange(current.phrase, shift(current.start), shift(current.end), current.granularity)


def _period_pair(
    ranges: list[TimeRange], text: str, as_of: date | None
) -> tuple[TimeRange, TimeRange] | None:
    """(current, base) for a comparison question, including the relative base cases."""
    first = ranges[0]
    second = ranges[1] if len(ranges) > 1 else None
    current, other = first, second
    if second is not None and re.search(r"(truoc|roi|qua|cung ky|nam ngoai)", fold(first.phrase)):
        current, other = second, first
    if "tet" in text and other is not None:
        base = other
    elif re.search(r"thang (truoc|lien truoc|trc)", text) and current.granularity == "month":
        base = _previous_month(current, as_of)
    elif re.search(r"(cung ky )?nam (truoc|ngoai|roi|qua)", text):
        base = _last_year(current)
    elif other is not None:
        base = other
    else:
        return None
    return current, base


def _money_sum(ranges: list[TimeRange]) -> str:
    item = ranges[0]
    return (
        f"SELECT SUM(line_total) AS answer FROM v_sales"
        f" WHERE is_valid AND sale_date BETWEEN {_dates(item)}"
    )


def _dimension(text: str) -> tuple[str, tuple[str, ...]] | None:
    """(column, accepted spellings) for a payment method or sales channel in the wording."""
    match = _DIMENSION.search(text)
    if not match:
        return None
    tail = text[match.end() :]
    tail = re.split(r"\b(thang|la|bao nhieu|bnhiu|moi|va|hoac|cua|trong|hom nay|tuan|quy)\b", tail)[
        0
    ]
    mention = tail.strip(" ,.;")
    if not mention or " va " in mention or "moi loai" in text:
        return None
    for key, value in _DIMENSION_ALIASES.items():
        if key in mention:
            return value
    return None


def _group(text: str) -> str | None:
    """The group name after "nhóm", or None when the sentence names a time or a measure next."""
    match = _GROUP.search(text)
    if not match:
        return None
    tail = match.group(2)
    tail = re.split(r"\b(thang|trong|la|bao nhieu|bnhiu|chie|dong gop|cua|thuoc|nam|quy)\b", tail)[
        0
    ]
    mention = tail.strip(" ,.;")
    return mention or None


def _threshold_value(question: str) -> float | None:
    """The number after the threshold word, not the month at the start of the question."""
    folded = fold(question, keep=".≥")
    match = _THRESHOLD_NUMBER.search(folded)
    if not match:
        return None
    raw = match.group(1).rstrip(".,")
    # money written with dot groups is VND; parse_number alone would read 55.000 as a decimal
    value = (
        float(raw.replace(".", ""))
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", raw)
        else parse_number(raw)
    )
    return value


def compile_question(
    question: str,
    ranges: list[TimeRange],
    has_sales: bool,
    has_orders: bool,
    as_of: date | None = None,
) -> Compile | None:
    """A deterministic SQL for a high-volume family, or None (the model keeps the question)."""
    if not has_sales or not ranges:
        return None
    text = fold(question)
    growth = _GROWTH.search(text) or (
        "%" in question and re.search(r"(tang|giam|thay doi|hon|kem|cao hon|thap hon)", text)
    )
    if growth and not _NOT_GROWTH.search(text):
        pair = _period_pair(ranges, text, as_of)
        if pair is None:
            return None
        current, base = pair
        sql = (
            "SELECT 100.0 * (a.v - b.v) / NULLIF(b.v, 0) AS answer FROM"
            f" (SELECT SUM(line_total) AS v FROM v_sales WHERE is_valid"
            f" AND sale_date BETWEEN {_dates(current)}) a,"
            f" (SELECT SUM(line_total) AS v FROM v_sales WHERE is_valid"
            f" AND sale_date BETWEEN {_dates(base)}) b"
        )
        return Compile("growth_plain", sql, "percent")

    if (
        _DIFFERENCE.search(text)
        and not _NOT_GROWTH.search(text)
        and ("%" not in question and not _PERCENT.search(text))
        and _REVENUE.search(text)
    ):
        pair = _period_pair(ranges, text, as_of)
        if pair is not None:
            current, base = pair
            sql = (
                "SELECT (a.v - b.v) AS answer FROM"
                f" (SELECT SUM(line_total) AS v FROM v_sales WHERE is_valid"
                f" AND sale_date BETWEEN {_dates(current)}) a,"
                f" (SELECT SUM(line_total) AS v FROM v_sales WHERE is_valid"
                f" AND sale_date BETWEEN {_dates(base)}) b"
            )
            return Compile("difference_amount", sql, "number")

    group = (
        _group(text)
        if _REVENUE.search(text) and len(ranges) == 1 and not _CUSTOMER.search(text)
        else None
    )
    if group is not None:
        item = ranges[0]
        exists = (
            "EXISTS (SELECT 1 FROM v_products p WHERE"
            " (p.item_code = s.item_code OR fold(p.item_name) = fold(s.item_name))"
            f" AND fold(p.category) LIKE '%{group}%')"
        )
        if "%" in question or _PERCENT.search(text):
            sql = (
                "SELECT 100.0 * SUM(CASE WHEN " + exists + " THEN s.line_total ELSE 0 END)"
                " / NULLIF(SUM(s.line_total), 0) AS answer"
                " FROM v_sales s WHERE s.is_valid"
                f" AND s.sale_date BETWEEN {_dates(item)}"
            )
            return Compile("share_by_group", sql, "percent")
        sql = (
            "SELECT SUM(s.line_total) AS answer FROM v_sales s"
            f" WHERE s.is_valid AND s.sale_date BETWEEN {_dates(item)} AND {exists}"
        )
        return Compile("revenue_by_group", sql, "number")

    dimension = _dimension(text) if _REVENUE.search(text) and len(ranges) == 1 else None
    if dimension is not None:
        column, spellings = dimension
        condition = " OR ".join(f"fold({column}) LIKE '%{value}%'" for value in spellings)
        item = ranges[0]
        sql = (
            "SELECT SUM(line_total) AS answer FROM v_sales"
            f" WHERE is_valid AND sale_date BETWEEN {_dates(item)} AND ({condition})"
        )
        return Compile(f"revenue_by_{column}", sql, "number")

    if _BEST_DAY.search(text) and not _NOT_PLAIN.search(text.replace("ngay nao", "")):
        item = ranges[0]
        sql = (
            "SELECT sale_date AS answer FROM v_sales"
            f" WHERE is_valid AND sale_date BETWEEN {_dates(item)}"
            " GROUP BY 1 HAVING SUM(line_total) IS NOT NULL"
            " ORDER BY SUM(line_total) DESC, sale_date ASC LIMIT 1"
        )
        return Compile("best_day", sql, "date")

    if _AVG.search(text) and _ORDER_WORD.search(text) and has_orders and len(ranges) == 1:
        item = ranges[0]
        sql = (
            "SELECT SUM(line_total) / NULLIF(COUNT(DISTINCT order_code), 0) AS answer"
            " FROM v_sales"
            f" WHERE is_valid AND sale_date BETWEEN {_dates(item)}"
        )
        return Compile("avg_order", sql, "number")

    if (
        _COUNT.search(text)
        and _ORDER_WORD.search(text)
        and has_orders
        and len(ranges) == 1
        and not _CUSTOMER.search(text)
        and not re.search(r"ca (sang|chieu)", text)
        and "%" not in question
        and "phan tram" not in text
    ):
        item = ranges[0]
        value = _threshold_value(question)
        threshold_cue = bool(_THRESHOLD.search(text)) or "≥" in question or ">=" in question
        valid = "is_valid AND "
        condition = ""
        family = "count_orders"
        if re.search(r"(^| )huy", text):
            valid = ""
            condition = " AND is_cancelled(status)"
            family = "count_cancelled"
        elif re.search(r"(tra hang|hoan hang|doi tra|tra lai)", text):
            valid = ""
            condition = " AND is_returned(status)"
            family = "count_returned"
        elif value is not None and threshold_cue:
            condition = f" AND order_total >= {value}"
            family = "count_orders_threshold"
        sql = (
            "SELECT COUNT(DISTINCT order_code) AS answer FROM v_orders"
            f" WHERE {valid}order_date BETWEEN {_dates(item)}{condition}"
        )
        return Compile(family, sql, "number")

    if "tien ban" in text and not re.search(r"cua (hang|shop|quan)|toan bo|tong", text):
        return None  # "tiền bán <món>" is one item's revenue, not the shop's
    if (
        _REVENUE.search(text)
        and len(ranges) == 1
        and not _NOT_PLAIN.search(text)
        and "%" not in question
    ):
        return Compile("revenue_plain", _money_sum(ranges), "number")

    return None
