import re
import unicodedata

import pandas as pd

HEADER_SCAN_ROWS = 20
# a column is converted when at least this share of its non-null values parse
PARSE_THRESHOLD = 0.95

_VI_THOUSANDS = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$")  # 1.234.567,5
_EN_THOUSANDS = re.compile(r"^-?\d{1,3}(,\d{3})+(\.\d+)?$")  # 1,234,567.5
_DECIMAL_COMMA = re.compile(r"^-?\d+,\d+$")  # 12,5
_PLAIN = re.compile(r"^-?\d+(\.\d+)?$")
_CURRENCY = re.compile(r"(vnđ|vnd|đồng|đ|\$|usd)", re.IGNORECASE)
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
    text = _CURRENCY.sub("", str(value)).strip().replace(" ", "").replace(" ", "")
    percent = text.endswith("%")
    text = text.rstrip("%")
    if locale == "vi" and _VI_THOUSANDS.match(text):
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


def infer_column(series: pd.Series) -> pd.Series:
    """Convert a text column to numbers or dates when nearly all of its values parse."""
    non_null = series.dropna()
    if non_null.empty or not (series.dtype == object or pd.api.types.is_string_dtype(series)):
        return series
    locale = number_locale(non_null)
    numbers = non_null.map(lambda v: parse_number(v, locale))
    if numbers.notna().mean() >= PARSE_THRESHOLD:
        return series.map(lambda v: parse_number(v, locale)).astype("float64")
    as_text = non_null.astype(str).str.strip()
    if as_text.str.match(_DATE_LIKE).mean() >= PARSE_THRESHOLD:
        parsed = _parse_dates(series.dropna())
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
