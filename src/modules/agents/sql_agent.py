import json
import re
from dataclasses import dataclass

from src.models import VALUE_TYPES
from src.modules.agents.base import BaseAgent
from src.modules.llm import LLM
from src.utils.assets import load_prompt_template, render

DEFAULT_SKILLS = [
    "answer-types",
    "time-expressions",
    "ranking-rules",
    "business-metrics",
    "unanswerable",
    "messy-data",
]
_DECODER = json.JSONDecoder()
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


class PlanParseError(ValueError):
    pass


def first_json_object(text: str) -> dict:
    """The first JSON object in a reply, ignoring text before or after it (and other objects).

    Raises PlanParseError when no object decodes."""
    text = _THINK.sub("", text)
    start = text.find("{")
    if start < 0:
        raise PlanParseError("no JSON object in reply")
    error = None
    while start >= 0:
        try:
            data, _ = _DECODER.raw_decode(text, start)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError as e:
            error = error or e
        start = text.find("{", start + 1)
    raise PlanParseError(f"invalid JSON: {error}")


@dataclass
class SQLPlan:
    answer_type: str  # one of VALUE_TYPES, or "unanswerable"
    sql: str = ""
    reason: str = ""


def parse_plan(text: str) -> SQLPlan:
    """Parse the model's JSON reply. Raises PlanParseError when it is not a valid plan."""
    data = first_json_object(text)
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

    def __init__(self, llm: LLM | None = None, skills: list[str] | None = None, rulebook: str = ""):
        super().__init__(skills)
        self.llm = llm or LLM()
        # split-wide rules, at the end of the system prompt so the shared prefix stays cacheable
        self.rulebook = (
            render(load_prompt_template("rulebook"), rulebook=rulebook.strip()) if rulebook else ""
        )
        self.user_template = load_prompt_template("sql_question")
        self.repair_template = load_prompt_template("repair")
        self.analyze_template = load_prompt_template("analyze")
        self.variants = [v.strip() for v in load_prompt_template("sql_variants").split("\n---\n")]

    @property
    def system_prompt(self) -> str:
        return "\n\n".join(p for p in (super().system_prompt, self.rulebook) if p)

    def analyze(
        self,
        context: dict[str, str],
        seed: int,
        extra_body: dict | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Business analysis of the question (intent, rulebook rules, measure, filters, ...).

        Free text, passed to every SQL candidate. Thinking, when on, is dropped from the text.
        """
        reply = self.llm.complete(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": render(self.analyze_template, **context)},
            ],
            seed=seed,
            extra_body=extra_body,
            max_tokens=max_tokens,
        )
        return _THINK.sub("", reply).strip()

    def think(
        self,
        template: str,
        values: dict[str, str],
        seed: int,
        extra_body: dict | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """One reasoning step of the CA pipeline: render `template`, return the JSON reply.

        Raises PlanParseError when the reply holds no JSON object.
        """
        reply = self.llm.complete(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": render(load_prompt_template(template), **values)},
            ],
            seed=seed,
            extra_body=extra_body,
            max_tokens=max_tokens,
        )
        return first_json_object(reply)

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
