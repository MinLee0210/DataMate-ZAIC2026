import json
import re
from dataclasses import dataclass

from src.models import VALUE_TYPES
from src.modules.agents.base import BaseAgent
from src.modules.agents.prompts import load_prompt_template, render
from src.modules.llm import LLM

DEFAULT_SKILLS = [
    "answer-types",
    "time-expressions",
    "ranking-rules",
    "business-metrics",
    "unanswerable",
]
_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class PlanParseError(ValueError):
    pass


@dataclass
class SQLPlan:
    answer_type: str  # one of VALUE_TYPES, or "unanswerable"
    sql: str = ""
    reason: str = ""


def parse_plan(text: str) -> SQLPlan:
    """Parse the model's JSON reply. Raises PlanParseError when it is not a valid plan."""
    text = _THINK.sub("", text)
    match = _JSON_BLOCK.search(text)
    if not match:
        raise PlanParseError("no JSON object in reply")
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError as e:
        raise PlanParseError(f"invalid JSON: {e}") from e
    answer_type = str(data.get("answer_type", "")).strip().lower()
    sql = str(data.get("sql") or "").strip().rstrip(";")
    if answer_type == "unanswerable":
        return SQLPlan("unanswerable", reason=str(data.get("reason", "")))
    if answer_type not in VALUE_TYPES:
        raise PlanParseError(f"unknown answer_type {answer_type!r}")
    if not sql:
        raise PlanParseError("empty sql")
    return SQLPlan(answer_type, sql, str(data.get("reason", "")))


class SQLAgent(BaseAgent):
    """Writes one DuckDB query (plus its answer type) for a question over a business's tables.

    Diversity across the k candidates comes from prompt variants (`sql_variants.md`), not from
    sampling: temperature stays 0 so every candidate is reproducible.
    """

    prompt_template = "sql_agent"
    skills = tuple(DEFAULT_SKILLS)

    def __init__(self, llm: LLM | None = None, skills: list[str] | None = None):
        super().__init__(skills)
        self.llm = llm or LLM()
        self.user_template = load_prompt_template("sql_question")
        self.repair_template = load_prompt_template("repair")
        self.variants = [v.strip() for v in load_prompt_template("sql_variants").split("\n---\n")]

    def generate(self, context: dict[str, str], variant: int, seed: int) -> SQLPlan:
        prompt = render(
            self.user_template, variant=self.variants[variant % len(self.variants)], **context
        )
        reply = self.llm.complete(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            seed=seed,
        )
        return parse_plan(reply)

    def repair(self, context: dict[str, str], plan: SQLPlan, error: str, seed: int) -> SQLPlan:
        prompt = render(
            self.repair_template,
            answer_type=plan.answer_type,
            sql=plan.sql,
            error=error[:1500],
            **context,
        )
        reply = self.llm.complete(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
            seed=seed,
        )
        return parse_plan(reply)

    def execute(self, context: dict[str, str], variant: int = 0, seed: int = 0) -> SQLPlan:
        return self.generate(context, variant, seed)
