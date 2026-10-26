"""Where a split's files live. This is the only module that knows the dataset layout.

Official layout (train, public_test):

    <data_dir>/<split>/                     or <data_dir>/ itself when it holds questions directly
    ├── questions.jsonl                     {"id", "business_id", "question", "as_of_date"}
    ├── answers.jsonl                       train only: {"id", "type", "answer", "alias"}
    ├── rulebook.md                         split-wide business rules
    ├── calendar.csv                        date, weekday, lunar_day/month/year, lunar_leap, holiday
    └── data/<business_id>/                 README.md + one or more .csv / .xlsx / .sqlite

`businesses/` and `packages/` are also accepted for the business folders.
"""

import json
from pathlib import Path

import pandas as pd

from src.models import Question

QUESTION_FILES = ("questions.jsonl", "questions.json", "questions.csv")
BUSINESS_DIRS = ("businesses", "data", "packages")


def split_dir(data_dir: Path, split: str) -> Path:
    candidate = data_dir / split
    return candidate if candidate.is_dir() else data_dir


def _read_records(path: Path) -> list[dict]:
    if path.suffix == ".csv":
        return pd.read_csv(path, dtype=str).to_dict(orient="records")
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return json.loads(path.read_text())


def questions_file(root: Path) -> Path:
    for name in QUESTION_FILES:
        if (root / name).is_file():
            return root / name
    raise FileNotFoundError(f"no questions file ({', '.join(QUESTION_FILES)}) in {root}")


def load_questions(root: Path) -> list[Question]:
    return [Question.model_validate(r) for r in _read_records(questions_file(root))]


def business_dir(root: Path, business_id: str) -> Path:
    for name in BUSINESS_DIRS:
        path = root / name / business_id
        if path.is_dir():
            return path
    path = root / business_id
    if path.is_dir():
        return path
    raise FileNotFoundError(f"no data package for business {business_id!r} under {root}")


def list_businesses(root: Path) -> list[Path]:
    for name in BUSINESS_DIRS:
        if (root / name).is_dir():
            return sorted(p for p in (root / name).iterdir() if p.is_dir())
    return []


def calendar_file(root: Path) -> Path | None:
    for path in sorted(root.glob("calendar.*")) + sorted(root.glob("*lunar*")):
        if path.suffix.lower() in {".csv", ".xlsx"}:
            return path
    return None


def rulebook_file(root: Path) -> Path | None:
    for path in sorted(root.glob("rulebook*")):
        return path
    return None


def load_gold(root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """Train labels: {id: {"type", "answer", "alias"}} and the raw question records.

    Labels are read from `answers.jsonl` when present, else from `type` / `answer` fields in the
    questions file. Only train (and self-generated) splits have them. `alias` holds the other
    accepted spellings (codes): a list for strings, one list per position for lists, one list per
    row for tables.
    """
    questions = {q.id: q.model_dump(mode="json") for q in load_questions(root)}
    answers = root / "answers.jsonl"
    records = _read_records(answers if answers.is_file() else questions_file(root))
    gold = {
        str(r["id"]): {"type": r["type"], "answer": r.get("answer"), "alias": r.get("alias") or []}
        for r in records
        if r.get("type")
    }
    if not gold:
        raise ValueError(f"no labels in {root}; gold answers exist only for train")
    return gold, questions
