from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

AnswerType = Literal[
    "number", "percent", "string", "date", "boolean", "list", "table", "unanswerable", "abstain"
]
# types a SQL candidate can produce; unanswerable/abstain come from the decision step
VALUE_TYPES: tuple[str, ...] = ("number", "percent", "string", "date", "boolean", "list", "table")


class Question(BaseModel):
    id: str
    business_id: str
    question: str
    as_of_date: date
    # optional labels present in train only
    category: str | None = None


class Answer(BaseModel):
    type: AnswerType
    # number | str | bool | list | list[list] | None (unanswerable, abstain)
    value: Any = None


UNANSWERABLE_REASON = "Dữ liệu không có thông tin cần thiết để trả lời câu hỏi"


class SubmissionLine(BaseModel):
    id: str
    type: AnswerType
    answer: Any = None

    def record(self) -> dict:
        """The JSONL record in the portal's format (Submission example, rulebook §9).

        Value types: {"id", "type", "answer"}. unanswerable: {"id", "type", "reason"} with a
        Vietnamese reason. abstain: {"id", "type"}. Neither of the last two has an "answer" key.
        """
        if self.type == "unanswerable":
            return {"id": self.id, "type": self.type, "reason": UNANSWERABLE_REASON}
        if self.type == "abstain":
            return {"id": self.id, "type": self.type}
        return {"id": self.id, "type": self.type, "answer": self.answer}


class ColumnCard(BaseModel):
    name: str  # SQL identifier in DuckDB
    original: str  # header as written in the source file
    dtype: str
    null_ratio: float = 0.0
    distinct: int = 0
    top_values: list[str] = Field(default_factory=list)
    min: str | None = None
    max: str | None = None


class TableCard(BaseModel):
    name: str
    source: str  # file (and sheet) it came from
    rows: int
    columns: list[ColumnCard]


class SchemaCard(BaseModel):
    business_id: str
    readme: str = ""
    tables: list[TableCard] = Field(default_factory=list)
    # first and last dates any transaction-like date column covers (ISO); None when no column
    # looks like a transaction date. Used by the deterministic unanswerable premise check.
    data_start: str | None = None
    data_end: str | None = None
