"""The CA pipeline: the reasoning loop of Google's Conversational Analytics API (CA-API), bounded.

    SCHEMA    schema card, semantic views, resolved time, entity links          (no LLM)
    THOUGHT   reason over the schema: need, term -> field mapping, fields to check (LLM 1)
    PROGRESS  sample real values of those fields                                 (no LLM)
    THOUGHT   plan named data queries {name, question, sql}                       (LLM 2)
    DATA      run them -> named results, or recoverable errors                    (DuckDB)
    THOUGHT   reason over the results -> final | analysis | data_query | abstain  (LLM 3)
    ANALYSIS  pandas over the named results, or DATA: one more query              (sandbox / DuckDB)
    THOUGHT   reason over the new result -> final | abstain                       (LLM 4)
    FINAL     the chosen result, formatted in code as the typed answer            (no LLM)

At most 4 LLM steps per question. CA-API has no abstain; here the last THOUGHT may abstain,
because a wrong answer costs a point. Every step is kept in the trace as a CA-shaped message
(`thought`, `progress`, `data`, `analysis`, `error`, `final`).
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.data.duckdb import DuckDBSource
from src.models import VALUE_TYPES, Answer
from src.modules.agents.sql_agent import SQLAgent
from src.modules.context.sampling import sample_fields
from src.modules.python_exec import run_python
from src.services.ingest import BusinessContext
from src.services.qa.graph import build_context
from src.utils import get_logger
from src.utils.assets import load_prompt_template
from src.utils.format import format_result
from src.utils.timeparse import LunarCalendar

logger = get_logger(__name__)

MAX_QUERIES = 3
PREVIEW_ROWS = 20
PREVIEW_CHARS = 2500


@dataclass
class DataResult:
    """A named result, as CA-API's DataResult; `language` is `sql` (DATA) or `python` (ANALYSIS)."""

    name: str
    question: str
    language: str
    code: str
    frame: pd.DataFrame | None = None
    error: str | None = None

    def render(self) -> str:
        head = f"### {self.name} ({self.language})\nQuestion: {self.question}\n"
        head += f"```{self.language}\n{self.code}\n```\n"
        if self.error:
            return head + f"Error: {self.error[:800]}"
        assert self.frame is not None
        preview = self.frame.head(PREVIEW_ROWS).to_csv(index=False)[:PREVIEW_CHARS]
        return head + f"{len(self.frame)} rows. First rows (CSV):\n{preview}"

    def message(self) -> dict:
        rows = None if self.frame is None else len(self.frame)
        return {
            "type": "data" if self.language == "sql" else "analysis",
            "name": self.name,
            "question": self.question,
            "code": self.code,
            "rows": rows,
            "error": self.error,
        }


class CAPipeline:
    def __init__(
        self,
        agent: SQLAgent,
        *,
        seed: int,
        schema_text: Callable[[BusinessContext], str],
        sql_timeout_s: float,
        max_rows: int,
        lunar: LunarCalendar | None = None,
        extra_body: dict | None = None,
        max_tokens: int | None = None,
    ) -> None:
        self.agent = agent
        self.seed = seed
        self.schema_text = schema_text
        self.sql_timeout_s = sql_timeout_s
        self.max_rows = max_rows
        self.lunar = lunar
        self.extra_body = extra_body
        self.max_tokens = max_tokens

    def _think(self, template: str, values: dict[str, str], step: int) -> dict:
        return self.agent.think(
            template,
            values,
            seed=self.seed + step,
            extra_body=self.extra_body,
            max_tokens=self.max_tokens,
        )

    def _run(
        self,
        source: DuckDBSource,
        results: dict[str, DataResult],
        name: str,
        question: str,
        language: str,
        code: str,
    ) -> DataResult:
        name = (str(name).strip() or f"result_{len(results) + 1}").replace(" ", "_")
        while name in results:
            name += "_2"
        result = DataResult(name, str(question), language, str(code).strip().rstrip(";"))
        try:
            if language == "sql":
                result.frame = source.query(result.code, self.sql_timeout_s, self.max_rows)
            else:
                frames = {k: r.frame for k, r in results.items() if r.frame is not None}
                result.frame = run_python(
                    result.code,
                    lambda sql: source.query(sql, self.sql_timeout_s, self.max_rows),
                    frames,
                    timeout_s=self.sql_timeout_s,
                )
        except Exception as e:  # recoverable: shown to the next THOUGHT
            result.error = f"{type(e).__name__}: {e}"
        results[name] = result
        return result

    def run(
        self, question: str, as_of: date, business: BusinessContext, source: DuckDBSource
    ) -> tuple[Answer, dict]:
        timings: dict[str, float] = {}
        messages: list[dict] = []

        def timed(name: str, started: float) -> None:
            timings[name] = timings.get(name, 0.0) + time.perf_counter() - started

        started = time.perf_counter()
        ctx = build_context(question, as_of, business, self.schema_text, self.lunar)
        timed("schema", started)

        # THOUGHT 1: reason over the schema
        started = time.perf_counter()
        step1 = self._think("ca_schema_thought", ctx, step=1)
        thought = str(step1.get("thought", "")).strip()
        messages.append({"type": "thought", "step": 1, "text": thought})
        timed("thought_schema", started)

        # PROGRESS: sample the fields it asked for
        started = time.perf_counter()
        fields = [str(f) for f in step1.get("sample_fields") or []]
        samples = sample_fields(source, business.card, fields, as_of)
        messages.append({"type": "progress", "fields": fields, "text": samples})
        timed("progress", started)

        # THOUGHT 2 + DATA: named data queries
        started = time.perf_counter()
        step2 = self._think("ca_data_queries", {**ctx, "thought": thought, "samples": samples}, 2)
        thought2 = str(step2.get("thought", "")).strip()
        messages.append({"type": "thought", "step": 2, "text": thought2})
        timed("thought_queries", started)
        started = time.perf_counter()
        results: dict[str, DataResult] = {}
        for query in (step2.get("data_queries") or [])[:MAX_QUERIES]:
            if isinstance(query, dict) and query.get("sql"):
                self._run(
                    source, results, query.get("name", ""), query.get("question", ""), "sql",
                    query["sql"],
                )  # fmt: skip
        messages += [r.message() for r in results.values()]
        timed("data", started)
        thoughts = "\n\n".join(t for t in (thought, thought2) if t)
        notes: list[str] = []

        # THOUGHT 3 (and 4): reason over the results
        answer, reason = Answer(type="abstain"), "no final answer"
        for step in (3, 4):
            last = step == 4
            started = time.perf_counter()
            data = "\n\n".join([r.render() for r in results.values()] + notes) or "(no results)"
            actions = load_prompt_template("ca_actions_final" if last else "ca_actions_more")
            reply = self._think(
                "ca_results_thought",
                {**ctx, "thought": thoughts, "data": data, "actions": actions},
                step,
            )
            timed("thought_results", started)
            action = str(reply.get("action", "")).strip().lower()
            text = str(reply.get("thought", "")).strip()
            thoughts += "\n\n" + text
            messages.append({"type": "thought", "step": step, "text": text, "action": action})

            if action == "final":
                answer_type = str(reply.get("answer_type", "")).strip().lower()
                if answer_type == "unanswerable":
                    answer, reason = Answer(type="unanswerable"), str(reply.get("reason", ""))
                    break
                result = results.get(str(reply.get("data_result", "")))
                problem = None
                if answer_type not in VALUE_TYPES:
                    problem = f"unknown answer_type {answer_type!r}"
                elif result is None or result.frame is None:
                    problem = f"no usable result named {reply.get('data_result')!r}"
                else:
                    try:
                        answer = Answer(
                            type=answer_type, value=format_result(answer_type, result.frame)
                        )
                        reason = f"from {result.name}"
                        break
                    except Exception as e:
                        problem = f"{type(e).__name__}: {e}"
                notes.append(f"### Error in the final answer\n{problem}")
                messages.append({"type": "error", "step": step, "text": problem})
                continue
            if action in ("analysis", "data_query") and not last:
                started = time.perf_counter()
                language = "python" if action == "analysis" else "sql"
                result = self._run(
                    source,
                    results,
                    reply.get("name", "analysis" if language == "python" else ""),
                    reply.get("question", ""),
                    language,
                    reply.get("code" if language == "python" else "sql", ""),
                )
                messages.append(result.message())
                timed("analysis" if language == "python" else "data", started)
                continue
            reason = str(reply.get("reason", "")) or f"action {action!r}"
            break

        messages.append(
            {"type": "final", "answer": answer.model_dump(), "reason": reason}
        )  # fmt: skip
        trace = {
            "pipeline": "ca",
            "messages": json.loads(json.dumps(messages, ensure_ascii=False, default=str)),
            "llm_steps": sum(1 for m in messages if m["type"] == "thought"),
            "timings": {k: round(v, 4) for k, v in timings.items()},
            "top": answer.model_dump() if answer.type != "abstain" else None,
            "agreement": 1.0 if answer.type != "abstain" else 0.0,
        }
        return answer, trace
