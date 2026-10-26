"""Text normalization shared by entity linking and time parsing."""

import re
import unicodedata


def fold(text: str, keep: str = "") -> str:
    """Lowercase, drop diacritics, collapse non-alphanumerics: 'Cà phê sữa' -> 'ca phe sua'.

    Characters in `keep` (e.g. '/-' for dates) are not collapsed.
    """
    text = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn").lower()
    return re.sub(rf"[^a-z0-9{re.escape(keep)}]+", " ", text).strip()
