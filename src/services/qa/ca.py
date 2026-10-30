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

import difflib
import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import pandas as pd

from src.data.duckdb import DuckDBSource
from src.models import VALUE_TYPES, Answer, SchemaCard
from src.modules.agents.sql_agent import PlanParseError, SQLAgent
from src.modules.context.examples import ExampleStore, render_examples
from src.modules.context.sampling import sample_fields
from src.modules.decide import Candidate, vote_key
from src.modules.python_exec import run_python
from src.services.ingest import BusinessContext
from src.services.qa.graph import build_context
from src.utils import get_logger
from src.utils.assets import load_prompt_template
from src.utils.format import format_result, is_money_question, round_money
from src.utils.timeparse import LunarCalendar

logger = get_logger(__name__)

MAX_QUERIES = 3
MAX_LLM_CALLS = 4
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


def _same_value(cell: object, ref: str) -> bool:
    if str(cell).strip().lower() == ref.strip().lower():
        return True
    try:
        a, b = float(cell), float(ref)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return abs(a - b) <= 1e-6 * max(1.0, abs(a)) or round(a, 2) == round(b, 2)


def resolve_result(results: dict[str, DataResult], ref: object) -> DataResult | None:
    """The result a final answer points to. The model should give a result's name, but it also
    writes an index ("0"), the value itself ("42149500") or nothing. Tried in order: the name
    (case and quotes ignored), an index, a result holding that value (a single cell is cut out
    of a larger result), the only usable result."""
    usable = [r for r in results.values() if r.frame is not None and not r.error]
    text = "" if ref is None else str(ref).strip().strip("`'\"")
    by_name = {r.name.lower(): r for r in usable}
    if text.lower() in by_name:
        return by_name[text.lower()]
    if text.isdigit() and usable and int(text) <= len(usable):
        i = int(text)  # 0-based; a 1-based index of the last result is accepted too
        return usable[i] if i < len(usable) else usable[-1]
    if text:
        for r in reversed(usable):
            frame = r.frame
            assert frame is not None
            if frame.shape == (1, 1) and _same_value(frame.iat[0, 0], text):
                return r
        for r in reversed(usable):
            frame = r.frame
            assert frame is not None
            for row in frame.head(200).itertuples(index=False):
                for cell in row:
                    if _same_value(cell, text):
                        return DataResult(
                            r.name, r.question, r.language, r.code, pd.DataFrame([[cell]])
                        )
    return usable[0] if len(usable) == 1 else None


_MISSING_COLUMN = re.compile(r'(?:column named|Referenced column) "([^"]+)"')


def _column_hint(error: str, card: SchemaCard) -> str:
    """For a Binder error about a missing column: the tables that do have that column, or the
    closest real column names."""
    m = _MISSING_COLUMN.search(error)
    if m is None:
        return ""
    wanted = m.group(1).split(".")[-1].lower()
    owners = [t.name for t in card.tables if any(c.name.lower() == wanted for c in t.columns)]
    if owners:
        return f"\nColumn {wanted} exists in: {', '.join(owners)} (qualify it with that table)."
    names = {c.name for t in card.tables for c in t.columns}
    close = difflib.get_close_matches(wanted, names, n=4, cutoff=0.5)
    if close:
        return f"\nNo column {wanted}. Closest real columns: {', '.join(close)}."
    return f"\nNo column {wanted} in any table: do not invent columns."


def error_hint(code: str, card: SchemaCard | None, max_columns: int = 60, error: str = "") -> str:
    """Columns (and types) of the tables a failed query names, so the retry can use real names;
    for a missing column also the table that owns it or the closest real names.
    Deterministic, no LLM; empty when the query names no known table."""
    if card is None:
        return ""
    lowered = code.lower()
    lines = []
    for table in card.tables:
        if re.search(rf"\b{re.escape(table.name.lower())}\b", lowered):
            cols = ", ".join(f"{c.name} ({c.dtype})" for c in table.columns[:max_columns])
            lines.append(f"Columns of {table.name}: {cols}")
    if not lines:
        tables = ", ".join(t.name for t in card.tables)
        lines.append(f"Tables: {tables}")
    return "\nHint: " + "\n".join(lines) + _column_hint(error, card)


def infer_action(reply: dict) -> str:
    """The reply's action; when a model leaves `action` out (Gemma 4 does), it is read from the
    fields it did give: answer_type -> final, sql -> data_query, code -> analysis."""
    action = str(reply.get("action", "")).strip().lower()
    if action:
        return action
    if reply.get("answer_type"):
        return "final"
    if reply.get("sql"):
        return "data_query"
    if reply.get("code"):
        return "analysis"
    return ""


def _confidence(value: object) -> float | None:
    """The final step's confidence in [0, 1]; 0-100 is read as a percent; None when missing."""
    try:
        x = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if x > 1.0:
        x /= 100.0
    return min(max(x, 0.0), 1.0)


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
        min_confidence: float = 0.0,
        examples: ExampleStore | None = None,
        few_shot_k: int = 0,
        samples: int = 1,
        min_agreement: float = 0.0,
        early_stop: bool = False,
    ) -> None:
        self.agent = agent
        self.seed = seed
        self.schema_text = schema_text
        self.sql_timeout_s = sql_timeout_s
        self.max_rows = max_rows
        self.lunar = lunar
        self.extra_body = extra_body
        self.max_tokens = max_tokens
        self.min_confidence = min_confidence
        self.examples = examples
        self.few_shot_k = few_shot_k
        self.samples = max(1, samples)
        self.min_agreement = min_agreement
        self.early_stop = early_stop
        self.variants = [v.strip() for v in load_prompt_template("ca_variants").split("\n---\n")]
        self._sample = 0
        self._llm_calls = 0

    def _think(self, template: str, values: dict[str, str], step: int) -> dict:
        if self._llm_calls >= MAX_LLM_CALLS:
            raise RuntimeError("CA reasoning call budget exhausted")
        self._llm_calls += 1
        return self.agent.think(
            template,
            values,
            seed=self.seed + step + 1000 * self._sample,
            extra_body=self.extra_body,
            max_tokens=self.max_tokens,
        )

    def _think_or_retry(self, template: str, values: dict[str, str], step: int) -> dict:
        """One reasoning step; a non-JSON reply is asked again once, with the error."""
        try:
            return self._think(template, values, step)
        except PlanParseError as e:
            note = f"\n\n(Your previous reply could not be read: {e}. Reply with one JSON object.)"
            return self._think(template, {**values, "question": values["question"] + note}, step)

    def _run(
        self,
        source: DuckDBSource,
        results: dict[str, DataResult],
        name: str,
        question: str,
        language: str,
        code: str,
        card: SchemaCard | None = None,
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
            result.error = f"{type(e).__name__}: {e}" + error_hint(result.code, card, error=str(e))
        results[name] = result
        return result

    def run(
        self, question: str, as_of: date, business: BusinessContext, source: DuckDBSource
    ) -> tuple[Answer, dict]:
        """One answer; with samples > 1, self-consistency: the loop runs once per approach
        (`ca_variants.md`) and the answer is the majority. `agreement` = majority share, which
        the eval's PA-vs-tau curve and `scripts/calibrate.py` use; MIN_AGREEMENT gates it."""
        if self.samples == 1:
            self._sample = 0
            return self._run_once(question, as_of, business, source, self.variants[0])
        runs = []
        votes: dict[str, list[Answer]] = {}
        for i in range(self.samples):
            self._sample = i
            approach = self.variants[i % len(self.variants)]
            try:
                answer, t = self._run_once(question, as_of, business, source, approach)
            except Exception as e:  # one failed sample must not discard the others' votes
                logger.exception("sample %d failed", i)
                answer = Answer(type="abstain")
                t = {
                    "messages": [{"type": "error", "step": 0, "text": f"{type(e).__name__}: {e}"}],
                    "llm_steps": self._llm_calls,
                    "timings": {},
                }
            runs.append((answer, t))
            if answer.type != "abstain":
                key = vote_key(Candidate(answer.type, answer.value))
                votes.setdefault(key, []).append(answer)
            if self.early_stop and self._decided(votes, self.samples - i - 1):
                break
        top = max(votes.values(), key=len)[0] if votes else None  # first-seen wins ties
        # a lower bound when the loop stopped early: the samples not run are counted as dissent
        agreement = round(max(map(len, votes.values())) / self.samples, 4) if votes else 0.0
        final = (
            top if top is not None and agreement >= self.min_agreement else Answer(type="abstain")
        )
        timings: dict[str, float] = {}
        for _, t in runs:
            for k, v in t["timings"].items():
                timings[k] = round(timings.get(k, 0.0) + v, 4)
        trace = {
            "pipeline": "ca",
            "samples": [t for _, t in runs],
            "votes": {k: len(v) for k, v in votes.items()},
            "messages": runs[0][1]["messages"],
            "llm_steps": sum(t["llm_steps"] for _, t in runs),
            "timings": timings,
            "top": top.model_dump() if top is not None else None,
            "agreement": agreement,
        }
        return final, trace

    def _decided(self, votes: dict[str, list[Answer]], remaining: int) -> bool:
        """True when the samples still to run cannot change the outcome: the leading answer
        cannot be overtaken and already meets MIN_AGREEMENT, so the answer is the same as with
        all samples (only the reported agreement is lower)."""
        if remaining <= 0 or not votes:
            return False
        counts = sorted((len(v) for v in votes.values()), reverse=True)
        second = counts[1] if len(counts) > 1 else 0
        return counts[0] > second + remaining and counts[0] / self.samples >= self.min_agreement

    def _run_once(
        self,
        question: str,
        as_of: date,
        business: BusinessContext,
        source: DuckDBSource,
        approach: str,
    ) -> tuple[Answer, dict]:
        self._llm_calls = 0
        timings: dict[str, float] = {}
        messages: list[dict] = []

        def timed(name: str, started: float) -> None:
            timings[name] = timings.get(name, 0.0) + time.perf_counter() - started

        started = time.perf_counter()
        ctx = build_context(question, as_of, business, self.schema_text, self.lunar)
        ctx["approach"] = approach
        timed("schema", started)

        # THOUGHT 1: reason over the schema
        started = time.perf_counter()
        step1 = self._think_or_retry("ca_schema_thought", ctx, step=1)
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
        shots = (
            self.examples.search(question, business.business_id, self.few_shot_k)
            if self.examples is not None
            else []
        )
        messages.append({"type": "examples", "ids": [e.id for e in shots]})
        step2 = self._think_or_retry(
            "ca_data_queries",
            {**ctx, "thought": thought, "samples": samples, "examples": render_examples(shots)},
            2,
        )
        thought2 = str(step2.get("thought", "")).strip()
        messages.append({"type": "thought", "step": 2, "text": thought2})
        timed("thought_queries", started)
        started = time.perf_counter()
        results: dict[str, DataResult] = {}
        for query in (step2.get("data_queries") or [])[:MAX_QUERIES]:
            if isinstance(query, dict) and query.get("sql"):
                self._run(
                    source, results, query.get("name", ""), query.get("question", ""), "sql",
                    query["sql"], business.card,
                )  # fmt: skip
        messages += [r.message() for r in results.values()]
        timed("data", started)
        thoughts = "\n\n".join(t for t in (thought, thought2) if t)
        notes: list[str] = []

        # THOUGHT 3 (and 4, and 5 only after a failed extra query): reason over the results
        answer, reason = Answer(type="abstain"), "no final answer"
        confidence: float | None = None
        extra_failed = False
        for step in (3, 4, 5):
            if self._llm_calls >= MAX_LLM_CALLS:
                reason = "CA reasoning call budget exhausted"
                break
            last = step == 5 or (step == 4 and not extra_failed)
            started = time.perf_counter()
            data = "\n\n".join([r.render() for r in results.values()] + notes) or "(no results)"
            actions = load_prompt_template("ca_actions_final" if last else "ca_actions_more")
            names = ", ".join(f"`{r.name}`" for r in results.values() if not r.error) or "(none)"
            try:
                reply = self._think(
                    "ca_results_thought",
                    {**ctx, "thought": thoughts, "data": data, "actions": actions, "names": names},
                    step,
                )
            except PlanParseError as e:  # recoverable once: the next step sees the error
                timed("thought_results", started)
                notes.append(
                    f"### Error in your last reply\n{e}. Reply with one valid JSON object."
                )
                messages.append({"type": "error", "step": step, "text": str(e)})
                if last:
                    reason = f"bad reply: {e}"
                    break
                extra_failed = True  # a bad reply also earns the extra step
                continue
            timed("thought_results", started)
            action = infer_action(reply)
            text = str(reply.get("thought", "")).strip()
            thoughts += "\n\n" + text
            message = {"type": "thought", "step": step, "text": text, "action": action}
            if action == "final":
                message.update(
                    answer_type=reply.get("answer_type"), data_result=reply.get("data_result")
                )
            messages.append(message)

            if action == "final":
                answer_type = str(reply.get("answer_type", "")).strip().lower()
                confidence = _confidence(reply.get("confidence"))
                if answer_type == "unanswerable":
                    answer, reason = Answer(type="unanswerable"), str(reply.get("reason", ""))
                    if not str(reply.get("evidence", "")).strip():
                        confidence = 0.0  # unanswerable needs the missing column or period
                    break
                result = resolve_result(results, reply.get("data_result"))
                problem = None
                if answer_type not in VALUE_TYPES:
                    problem = f"unknown answer_type {answer_type!r}"
                elif result is None or result.frame is None:
                    problem = f"no usable result named {reply.get('data_result')!r}"
                else:
                    try:
                        value = format_result(answer_type, result.frame)
                        if answer_type == "number" and is_money_question(question):
                            value = round_money(value)  # rulebook §9: money is whole VND
                        answer = Answer(type=answer_type, value=value)
                        reason = f"from {result.name}"
                        break
                    except Exception as e:
                        problem = f"{type(e).__name__}: {e}"
                notes.append(f"### Error in the final answer\n{problem}")
                messages.append({"type": "error", "step": step, "text": problem})
                if last:
                    break
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
                    business.card,
                )
                extra_failed = result.error is not None
                messages.append(result.message())
                timed("analysis" if language == "python" else "data", started)
                continue
            reason = str(reply.get("reason", "")) or f"action {action!r}"
            break

        top = answer if answer.type != "abstain" else None
        score = 1.0 if confidence is None else confidence
        if top is not None and score < self.min_confidence:
            answer, reason = Answer(type="abstain"), f"confidence {score} < {self.min_confidence}"
        messages.append(
            {"type": "final", "answer": answer.model_dump(), "reason": reason}
        )  # fmt: skip
        trace = {
            "pipeline": "ca",
            "messages": json.loads(json.dumps(messages, ensure_ascii=False, default=str)),
            "llm_steps": self._llm_calls,
            "timings": {k: round(v, 4) for k, v in timings.items()},
            # for the PA-vs-tau curve: the answer before the confidence gate, and its confidence
            "top": top.model_dump() if top is not None else None,
            "agreement": score if top is not None else 0.0,
            "confidence": confidence,
        }
        return answer, trace
