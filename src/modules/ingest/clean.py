import re
import unicodedata
from datetime import date, timedelta

import pandas as pd

HEADER_SCAN_ROWS = 20
# a column is converted when at least this share of its non-null values parse
PARSE_THRESHOLD = 0.95

_VI_THOUSANDS = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$")  # 1.234.567,5
_EN_THOUSANDS = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")  # 1,234,567.5
_DECIMAL_COMMA = re.compile(r"^-?\d+,\d+$")  # 12,5
_PLAIN = re.compile(r"^-?\d+(\.\d+)?$")
_CURRENCY = re.compile(r"(vnđ|vnd|đồng|đ|\$|usd)", re.IGNORECASE)
_VND = re.compile(r"(vnđ|vnd|đồng|đ)", re.IGNORECASE)
_DOT_THOUSANDS = re.compile(r"^-?\d{1,3}(\.\d{3})+$")  # 50.000: thousands when the value is VND
# shorthand money: 25k, 1.5tr, 2 triệu, 30 nghìn
_SCALE = re.compile(r"^(-?\d+(?:[.,]\d+)?)(k|nghìn|ngàn|nghin|ngan|tr|triệu|trieu)$", re.IGNORECASE)
_SCALES = {"k": 1e3, "nghìn": 1e3, "ngàn": 1e3, "nghin": 1e3, "ngan": 1e3}
_DATE_LIKE = re.compile(r"^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}( \d{1,2}:\d{2}(:\d{2})?)?$")
_ISO_DATE = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}")


def to_identifier(name: str) -> str:
    """'Doanh thu (VNĐ)' -> 'doanh_thu_vnd'. ASCII snake_case, safe to use unquoted in SQL."""
    text = unicodedata.normalize("NFD", str(name).replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if not text:
        return "col"
    return f"c_{text}" if text[0].isdigit() else text


def unique_identifiers(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for name in names:
        ident = to_identifier(name)
        if ident in seen:
            seen[ident] += 1
            ident = f"{ident}_{seen[ident]}"
        else:
            seen[ident] = 0
        out.append(ident)
    return out


def detect_header_row(raw: pd.DataFrame) -> int:
    """Index of the first row that looks like a header: the row with the most distinct cells,
    mostly text.

    Titles and notes above a table usually fill one or two cells, so they lose to the real header.
    """
    best, best_score = 0, -1.0
    for i in range(min(HEADER_SCAN_ROWS, len(raw))):
        cells = [c for c in raw.iloc[i].tolist() if pd.notna(c) and str(c).strip()]
        if not cells:
            continue
        text = sum(1 for c in cells if isinstance(c, str) and not _PLAIN.match(c.strip()))
        # distinct values: a merged title repeated across the row counts once
        score = len({str(c).strip() for c in cells}) + text / len(cells)
        if score > best_score + 1e-9:
            best, best_score = i, score
    return best


def frame_from_raw(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Use the detected header row, drop empty rows and columns.

    Returns the frame (identifier columns) and the original header text of each column.
    """
    raw = raw.dropna(how="all").dropna(axis=1, how="all").reset_index(drop=True)
    if raw.empty:
        return pd.DataFrame(), []
    h = detect_header_row(raw)
    originals = [
        str(v).strip() if pd.notna(v) and str(v).strip() else f"column_{j + 1}"
        for j, v in enumerate(raw.iloc[h].tolist())
    ]
    body = raw.iloc[h + 1 :].dropna(how="all").reset_index(drop=True)
    body.columns = unique_identifiers(originals)
    return body, originals


_ID_LIKE = re.compile(r"(^|_)(ma|so|id|code|no|stt)(_|$)")


def _mostly_numeric(values: pd.Series) -> bool:
    values = values.dropna()
    if values.empty:
        return False
    return values.map(lambda v: parse_number(v) is not None).mean() >= PARSE_THRESHOLD


def fill_grouped_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Fill the blank parent cells of a grouped export (one order header, several line rows).

    Some exports write the order's code, date, status and customer on the first line of an
    order only; the next lines of that order leave them blank. The columns blank on exactly the
    same rows form the parent group. It is filled down only when it holds an id-like column
    and a date column, so a field that is legitimately empty (a walk-in customer with no code)
    is left alone.
    """
    if len(frame) < 2:
        return frame
    blank = frame.isna() | frame.astype(str).apply(lambda c: c.str.strip().isin(["", "nan"]))
    masks: dict[tuple, list[str]] = {}
    for col in frame.columns:
        mask = blank[col]
        if 0.05 <= mask.mean() <= 0.95 and not mask.iloc[0]:
            masks.setdefault(tuple(mask.tolist()), []).append(col)
    for mask, cols in masks.items():
        if len(cols) < 2 or not any(_ID_LIKE.search(c) for c in cols):
            continue
        dated = [
            c
            for c in cols
            if frame[c][~pd.Series(mask, index=frame.index)]
            .astype(str)
            .str.strip()
            .str.match(_DATE_LIKE)
            .mean()
            >= PARSE_THRESHOLD
            or pd.api.types.is_datetime64_any_dtype(frame[c])
        ]
        if not dated:
            continue
        # money and quantities stay on the first line only: filling an order total down to every
        # line makes a sum over lines count it once per line
        cols = [
            c for c in cols if not _mostly_numeric(frame[c][~pd.Series(mask, index=frame.index)])
        ]
        frame = frame.copy()
        frame[cols] = frame[cols].mask(blank[cols]).ffill()
    return frame


_ORDER_CODE = re.compile(
    r"(^|_)(ma|so|id)_.*(don|phieu|hoa_don|hd|ct|order)(_|$)|^(so_ct|so_phieu)$"
)


def drop_duplicate_order_lines(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop rows identical in every cell, in a table with an order code column.

    Rulebook §8: two lines of the same order that are equal in every cell are an export error
    and count once. In a table without an order code, equal rows are two records and stay.
    """
    if not any(_ORDER_CODE.search(str(c)) for c in frame.columns):
        return frame
    return frame.drop_duplicates(ignore_index=True)


def number_locale(values: pd.Series) -> str | None:
    """'vi' (1.234.567,5) or 'en' (1,234,567.5) when the column's unambiguous values agree.

    '350.000' alone is ambiguous; it is read as thousands only in a column that is otherwise
    written the Vietnamese way.
    """
    text = values.dropna().astype(str).map(lambda v: _CURRENCY.sub("", v).strip().replace(" ", ""))
    vi = text.str.match(r"^-?\d{1,3}(\.\d{3}){2,}(,\d+)?$|^-?\d{1,3}(\.\d{3})+,\d+$|^-?\d+,\d+$")
    en = text.str.match(r"^-?\d{1,3}(,\d{3}){2,}(\.\d+)?$|^-?\d{1,3}(,\d{3})+\.\d+$")
    if vi.sum() > en.sum():
        return "vi"
    if en.sum() > vi.sum():
        return "en"
    return None


def parse_number(value: object, locale: str | None = None) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    raw = str(value)
    text = _CURRENCY.sub("", raw).strip().replace(" ", "").replace(" ", "")
    percent = text.endswith("%")
    text = text.rstrip("%")
    scaled = _SCALE.match(text)
    if scaled:
        unit = scaled.group(2).lower()
        return float(scaled.group(1).replace(",", ".")) * _SCALES.get(unit, 1e6)
    if _VND.search(raw) and _DOT_THOUSANDS.match(text):
        # VND has no decimals, so 50.000đ is fifty thousand
        number = float(text.replace(".", ""))
    elif locale == "vi" and _VI_THOUSANDS.match(text):
        number = float(text.replace(".", "").replace(",", "."))
    elif _PLAIN.match(text):
        number = float(text)
    elif _VI_THOUSANDS.match(text):
        number = float(text.replace(".", "").replace(",", "."))
    elif _EN_THOUSANDS.match(text):
        number = float(text.replace(",", ""))
    elif _DECIMAL_COMMA.match(text):
        number = float(text.replace(",", "."))
    else:
        return None
    return number / 100 if percent else number


def _parse_dates(values: pd.Series) -> pd.Series:
    text = values.astype(str).str.strip()
    # ISO dates are year first; everything else is read the Vietnamese way (day first)
    iso = text.str.match(_ISO_DATE)
    out = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns]")
    if iso.any():
        out[iso] = pd.to_datetime(text[iso], errors="coerce", format="mixed")
    if (~iso).any():
        out[~iso] = pd.to_datetime(text[~iso], errors="coerce", dayfirst=True, format="mixed")
    return out


# 30 thg 5 2026, ngày 30 tháng 5 năm 2026, 30 tháng 5, 2026 (year optional)
_VN_DATE = re.compile(
    r"^(?:ngày\s*)?(\d{1,2})\s*(?:thg|tháng|th)\s*(\d{1,2})(?:\s*,?\s*(?:năm\s*)?(\d{4}))?$",
    re.IGNORECASE,
)
_SERIAL = re.compile(r"^\d{5}(\.0+)?$")  # Excel day number, 1954..2119 for 20000..80000
_NO_YEAR = re.compile(r"^(\d{1,2})[/.-](\d{1,2})$")
_EXCEL_EPOCH = date(1899, 12, 30)


def normalize_date_text(value: object) -> str:
    """One date cell as text `parse_dates` reads: Vietnamese month words and Excel day numbers
    become day/month/year or ISO. Anything else is returned stripped."""
    text = str(value).strip()
    m = _VN_DATE.match(text)
    if m:
        day, month, year = m.groups()
        return f"{day}/{month}/{year}" if year else f"{day}/{month}"
    if _SERIAL.match(text):
        n = int(float(text))
        if 20000 <= n <= 80000:
            return (_EXCEL_EPOCH + timedelta(days=n)).isoformat()
    return text


def add_sheet_year(frame: pd.DataFrame, year: int | None) -> pd.DataFrame:
    """Rulebook §8: a date written without a year has the year of its sheet.

    Only in a column where at least a fifth of the cells are full dates, so a fraction like 1/2
    in another column is left alone."""
    if year is None:
        return frame
    out = frame.copy()
    for col in out.columns:
        values = out[col].dropna()
        if values.empty or not (values.dtype == object or pd.api.types.is_string_dtype(values)):
            continue
        text = values.map(normalize_date_text)
        if text.str.match(_DATE_LIKE).mean() < 0.2 or not text.str.match(_NO_YEAR).any():
            continue
        out.loc[values.index, col] = text.map(lambda t: f"{t}/{year}" if _NO_YEAR.match(t) else t)
    return out


_SUBTOTAL = re.compile(
    r"^(tổng|cộng|tong|cong)(\s+(cộng|cong))?(\s+(ngày|ngay|tháng|thang|năm|nam|tuần|tuan)\b.*)?$|"
    r"^(total|subtotal|grand total)\b",
    re.IGNORECASE,
)


def drop_subtotal_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop subtotal and total rows mixed into the data ("Tổng ngày 30/05", "Cộng ngày …",
    "TỔNG THÁNG", "Cộng"), so sums do not count them twice.

    "Tong Ngoc Chi" (a name) does not match: a bare tổng / cộng must stand alone or be followed
    by a period word. Run before `fill_grouped_rows`, or the subtotal would get an order code."""
    text = frame.astype(str).apply(lambda c: c.str.strip())
    hit = text.apply(lambda c: c.str.match(_SUBTOTAL)).any(axis=1)
    return frame[~hit].reset_index(drop=True) if hit.any() else frame


def drop_repeated_headers(frame: pd.DataFrame, originals: list[str]) -> pd.DataFrame:
    """Drop rows that repeat the header (exports that print it again on every page or block)."""
    if frame.empty or not originals:
        return frame
    headers = [str(h).strip().lower() for h in originals]
    text = frame.astype(str).apply(lambda c: c.str.strip().str.lower())
    same = sum(text.iloc[:, j] == headers[j] for j in range(min(len(headers), frame.shape[1])))
    repeated = same >= max(2, (frame.shape[1] + 1) // 2)
    return frame[~repeated].reset_index(drop=True) if repeated.any() else frame


def infer_column(series: pd.Series) -> pd.Series:
    """Convert a text column to numbers or dates when nearly all of its values parse."""
    non_null = series.dropna()
    if non_null.empty or not (series.dtype == object or pd.api.types.is_string_dtype(series)):
        return series
    locale = number_locale(non_null)
    numbers = non_null.map(lambda v: parse_number(v, locale))
    if numbers.notna().mean() >= PARSE_THRESHOLD:
        return series.map(lambda v: parse_number(v, locale)).astype("float64")
    as_text = non_null.map(normalize_date_text)
    if as_text.str.match(_DATE_LIKE).mean() >= PARSE_THRESHOLD:
        parsed = _parse_dates(as_text)
        if parsed.notna().mean() >= PARSE_THRESHOLD:
            out = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
            out[parsed.index] = parsed
            return out
    return series.map(lambda v: str(v).strip() if pd.notna(v) else None)


def infer_types(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for col in out.columns:
        out[col] = infer_column(out[col])
        if out[col].dtype == "float64" and (out[col].dropna() % 1 == 0).all():
            out[col] = out[col].astype("Int64")
    return out
