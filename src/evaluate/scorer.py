"""Penalized Accuracy scorer, per the official rules in the rulebook (§9, "Đáp án và chấm điểm").

    s_i = +1 correct, 0 abstain / missing / unreadable line, -1 wrong;  PA = mean(s_i)

Rules, as written in the rulebook:
- Each type has exactly one format, and a wrong format is wrong. The format is checked first,
  then the value.
  - number, percent: a JSON number (not a string, not a bool). Percent is in percentage points.
  - date: "YYYY-MM-DD", or "YYYY-MM" for monthly questions.
  - boolean: JSON true / false.
  - string: a JSON string.
  - list: a JSON array, ordered (one element is still an array).
  - table: {"columns": [...], "rows": [[...], ...]}.
- number, percent: exact match; only floating-point error is ignored.
- string: case, whitespace and punctuation are ignored; diacritics count. Any spelling found in
  the shop's files, or the code, is accepted (the gold `alias` field).
- list: same set, same order. Elements are compared as numbers or strings, with per-position
  aliases.
- table: one row per object; the first column is the object name. Columns are matched by name,
  else by position. Row order does not matter.
- unanswerable: correct only when the gold is unanswerable. `reason` is optional, but a line whose
  `reason` is not a string cannot be read and counts as blank (0).
- Answering an unanswerable question is wrong.

Not stated by the rules, so these are assumptions:
- A line that is not valid JSON, has no string `id`, or has an unknown `type` counts as blank.
- If an id appears more than once, the first readable line counts.
"""

import json
import math
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

ANSWER_TYPES = {
    "number",
    "percent",
    "string",
    "date",
    "boolean",
    "list",
    "table",
    "unanswerable",
    "abstain",
}
FLOAT_TOL = 1e-6  # "chỉ bỏ qua sai số dấu phẩy động"
_DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


@dataclass
class Scored:
    id: str
    score: int  # +1 / 0 / -1
    reason: str  # why: correct, abstain, missing, wrong_type, bad_format, wrong_value, ...


def normalize_string(text: Any) -> str:
    """NFC, lowercase, non-alphanumeric -> space, collapse spaces; diacritics are kept."""
    text = unicodedata.normalize("NFC", str(text)).lower()
    text = "".join(c if c.isalnum() else " " for c in text)
    return re.sub(r"\s+", " ", text).strip()


# ------------------------------------------------------------------ reading a submission


def parse_line(raw: str) -> dict | None:
    """One submission line -> {"id", "type", "answer"}, or None when the line cannot be read."""
    try:
        line = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(line, dict) or not isinstance(line.get("id"), str):
        return None
    if line.get("type") not in ANSWER_TYPES:
        return None
    if "reason" in line and not isinstance(line["reason"], str):
        return None
    return line


def read_submission(lines: Iterable[str]) -> dict[str, dict]:
    """Readable lines by id; the first readable line of an id wins."""
    preds: dict[str, dict] = {}
    for raw in lines:
        if not raw.strip():
            continue
        line = parse_line(raw)
        if line is not None and line["id"] not in preds:
            preds[line["id"]] = line
    return preds


# ------------------------------------------------------------------ format, then value


def _is_number(x: Any) -> bool:
    return isinstance(x, int | float) and not isinstance(x, bool) and math.isfinite(x)


def _is_table(x: Any) -> bool:
    return (
        isinstance(x, dict)
        and isinstance(x.get("columns"), list)
        and isinstance(x.get("rows"), list)
        and all(isinstance(r, list) for r in x["rows"])
    )


def check_format(answer_type: str, answer: Any) -> bool:
    """The answer has the one format the type allows (rulebook §9 table)."""
    if answer_type in ("number", "percent"):
        return _is_number(answer)
    if answer_type == "date":
        return isinstance(answer, str) and bool(_DATE.match(answer))
    if answer_type == "boolean":
        return isinstance(answer, bool)
    if answer_type == "string":
        return isinstance(answer, str)
    if answer_type == "list":
        return isinstance(answer, list)
    if answer_type == "table":
        return _is_table(answer)
    return answer_type == "unanswerable"


def _same_number(pred: Any, gold: Any) -> bool:
    return _is_number(pred) and _is_number(gold) and abs(pred - gold) <= FLOAT_TOL


def _same_cell(pred: Any, gold: Any, aliases: Iterable[Any] = ()) -> bool:
    """A list element or table cell: numbers by value, the rest as normalized strings."""
    if _is_number(gold):
        return _same_number(pred, gold)
    if isinstance(gold, bool) or isinstance(pred, bool):
        return pred is gold
    if not isinstance(pred, str):
        return False
    key = normalize_string(pred)
    return any(key == normalize_string(g) for g in [gold, *aliases] if g is not None)


def _position_aliases(alias: Any, n: int) -> list[list[Any]]:
    """Gold `alias` for lists and tables: one list of accepted spellings per position / row."""
    out: list[list[Any]] = [[] for _ in range(n)]
    if isinstance(alias, list) and len(alias) == n:
        for i, a in enumerate(alias):
            out[i] = a if isinstance(a, list) else [a]
    return out


def _column_map(pred_cols: list[Any], gold_cols: list[Any]) -> list[int] | None:
    """For each gold column, the pred column index: by name, else by position."""
    if len(pred_cols) != len(gold_cols):
        return None
    names = [normalize_string(c) for c in pred_cols]
    mapping = []
    for j, col in enumerate(gold_cols):
        key = normalize_string(col)
        mapping.append(names.index(key) if key in names else j)
    return mapping if len(set(mapping)) == len(mapping) else None


def _same_table(pred: dict, gold: dict, alias: Any) -> bool:
    gold_rows, pred_rows = gold["rows"], pred["rows"]
    if len(gold_rows) != len(pred_rows):
        return False
    mapping = _column_map(pred["columns"], gold["columns"])
    if mapping is None:
        return False
    name_aliases = _position_aliases(alias, len(gold_rows))
    unused = list(range(len(pred_rows)))
    for g_row, names in zip(gold_rows, name_aliases, strict=True):
        hit = None
        for k in unused:
            p_row = pred_rows[k]
            if len(p_row) != len(g_row):
                continue
            if all(
                _same_cell(p_row[mapping[j]], g, names if j == 0 else ())
                for j, g in enumerate(g_row)
            ):
                hit = k
                break
        if hit is None:
            return False
        unused.remove(hit)
    return True


def match_value(answer_type: str, pred: Any, gold: Any, alias: Any = None) -> bool:
    """Value comparison, after `check_format` passed."""
    if answer_type in ("number", "percent"):
        return _same_number(pred, gold)
    if answer_type in ("date", "boolean"):
        return pred == gold and type(pred) is type(gold)
    if answer_type == "string":
        aliases = alias if isinstance(alias, list) else []
        return _same_cell(pred, gold, aliases)
    if answer_type == "list":
        if not isinstance(gold, list) or len(pred) != len(gold):
            return False
        per_pos = _position_aliases(alias, len(gold))
        return all(_same_cell(p, g, a) for p, g, a in zip(pred, gold, per_pos, strict=True))
    if answer_type == "table":
        return _is_table(gold) and _same_table(pred, gold, alias)
    return False


def score_line(pred: dict | None, gold: dict) -> int:
    return judge(pred, gold)[0]


def judge(pred: dict | None, gold: dict) -> tuple[int, str]:
    """(score, reason) for one question. `gold` is {"type", "answer", "alias"?}."""
    if pred is None:
        return 0, "missing"
    if pred.get("type") == "abstain":
        return 0, "abstain"
    if gold["type"] == "unanswerable" or pred["type"] == "unanswerable":
        return (1, "correct") if pred["type"] == gold["type"] else (-1, "wrong_type")
    if pred["type"] != gold["type"]:
        return -1, "wrong_type"
    answer = pred.get("answer")
    if not check_format(pred["type"], answer):
        return -1, "bad_format"
    if match_value(gold["type"], answer, gold.get("answer"), gold.get("alias")):
        return 1, "correct"
    return -1, "wrong_value"


def score_submission(preds: dict[str, dict], golds: dict[str, dict]) -> list[Scored]:
    """Score every gold question; ids missing from `preds` score 0. Extra ids are ignored."""
    return [Scored(qid, *judge(preds.get(qid), gold)) for qid, gold in golds.items()]


def summarize(scores: list[int]) -> dict:
    n = len(scores)
    return {
        "n": n,
        "pa": round(sum(scores) / n, 4) if n else 0.0,
        "correct": scores.count(1),
        "wrong": scores.count(-1),
        "abstain": scores.count(0),
    }


def tau_curve(
    traces: dict[str, dict], golds: dict[str, dict], grid: Iterable[float]
) -> list[tuple[float, float]]:
    """PA if we had answered the vote winner only when agreement >= tau."""
    curve = []
    for tau in grid:
        scores = []
        for qid, gold in golds.items():
            t = traces.get(qid) or {}
            top = t.get("top")
            if top is None or t.get("agreement", 0.0) < tau:
                scores.append(0)
            else:
                scores.append(score_line({"type": top["type"], "answer": top.get("value")}, gold))
        curve.append((tau, round(sum(scores) / len(scores), 4) if scores else 0.0))
    return curve
