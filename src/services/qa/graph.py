"""The per-question LangGraph: a fixed, bounded pipeline (not an open agent loop).

    prepare ─► analyze ─► generate ─► execute ─┬─► decide ─► END
                                         ▲     │ failed candidates and repairs left
                                         └─ repair ◄┘

LLM calls: analyze (1 step, optional: a business analysis every candidate reads) + generate
(1 step, k prompt variants) + repair (<= max_repairs steps). Repairs run only while some candidate
has failed.

Each node adds its wall time to `timings` (seconds per node name, summed over repeats).
"""

import time
from collections.abc import Callable
from datetime import date
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from src.data.duckdb import DuckDBSource
from src.modules.agents.sql_agent import PlanParseError, SQLAgent, SQLPlan
from src.modules.context import link_entities, render_entity_matches
from src.modules.decide import UNANSWERABLE, Candidate, Decision, decide
from src.services.ingest import BusinessContext
from src.utils import get_logger
from src.utils.format import format_result
from src.utils.timeparse import LunarCalendar, render_time_ranges, resolve

logger = get_logger(__name__)


def _sum_timings(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    merged = dict(left or {})
    for name, seconds in (right or {}).items():
        merged[name] = merged.get(name, 0.0) + seconds
    return merged


def _timed(name: str, node: Callable[[dict], dict]) -> Callable[[dict], dict]:
    def run(state: dict) -> dict:
        started = time.perf_counter()
        update = node(state)
        return {**update, "timings": {name: time.perf_counter() - started}}

    return run


class QAState(TypedDict, total=False):
    question: str
    as_of_date: date
    business: BusinessContext
    source: DuckDBSource
    context: dict[str, str]  # rendered prompt sections
    plans: list[SQLPlan | None]
    candidates: list[Candidate]
    repairs: int
    decision: Decision
    timings: Annotated[dict[str, float], _sum_timings]


def build_context(
    question: str,
    as_of_date: date,
    business: BusinessContext,
    schema_text: Callable[[BusinessContext], str],
    lunar: LunarCalendar | None = None,
) -> dict[str, str]:
    """Prompt sections for one question: README, schema card, semantic views, resolved time,
    entity links. Deterministic, no LLM; shared by the vote and the MALT pipelines."""
    ranges = resolve(question, as_of_date, lunar)
    matches = link_entities(question, business.entities)
    return {
        "readme": business.card.readme[:3000] or "(no README)",
        "schema": schema_text(business),
        "semantic": ", ".join(business.semantic) or "(none)",
        "time": render_time_ranges(ranges, as_of_date),
        "entities": render_entity_matches(matches),
        "question": question,
        "analysis": "(none)",
    }


def build_qa_graph(
    agent: SQLAgent,
    *,
    k: int,
    tau: float,
    max_repairs: int,
    seed: int,
    schema_text: Callable[[BusinessContext], str],
    sql_timeout_s: float,
    max_rows: int,
    lunar: LunarCalendar | None = None,
    analyze: bool = False,
    analyze_body: dict | None = None,
    analyze_max_tokens: int | None = None,
):
    """Compile the graph. `schema_text(business)` returns the rendered schema card (cached)."""

    def prepare(state: QAState) -> dict:
        context = build_context(
            state["question"], state["as_of_date"], state["business"], schema_text, lunar
        )
        return {"context": context, "repairs": 0}

    def analyze_node(state: QAState) -> dict:
        analysis = agent.analyze(
            state["context"], seed=seed - 1, extra_body=analyze_body, max_tokens=analyze_max_tokens
        )
        return {"context": {**state["context"], "analysis": analysis or "(none)"}}

    def generate(state: QAState) -> dict:
        plans: list[SQLPlan | None] = []
        candidates: list[Candidate] = []
        for i in range(k):
            try:
                plans.append(agent.generate(state["context"], variant=i, seed=seed + i))
                candidates.append(Candidate(answer_type="pending"))
            except PlanParseError as e:
                plans.append(None)
                candidates.append(Candidate(answer_type="pending", error=f"bad reply: {e}"))
        return {"plans": plans, "candidates": candidates}

    def execute(state: QAState) -> dict:
        candidates = list(state["candidates"])
        for i, plan in enumerate(state["plans"]):
            if plan is None or candidates[i].answer_type != "pending":
                continue
            if plan.answer_type == UNANSWERABLE:
                candidates[i] = Candidate(answer_type=UNANSWERABLE)
                continue
            try:
                frame = state["source"].query(plan.sql, timeout_s=sql_timeout_s, max_rows=max_rows)
                value = format_result(plan.answer_type, frame)
                candidates[i] = Candidate(plan.answer_type, value, plan.sql)
            except Exception as e:  # SQL, safety or format errors are repairable
                candidates[i] = Candidate("pending", sql=plan.sql, error=f"{type(e).__name__}: {e}")
        return {"candidates": candidates}

    def repair(state: QAState) -> dict:
        plans = list(state["plans"])
        candidates = list(state["candidates"])
        step = state["repairs"] + 1
        for i, candidate in enumerate(candidates):
            if candidate.ok:
                continue
            previous = plans[i] or SQLPlan(answer_type="unknown")
            try:
                plans[i] = agent.repair(
                    state["context"], previous, candidate.error or "", seed=seed + 100 * step + i
                )
                candidates[i] = Candidate(answer_type="pending")
            except PlanParseError as e:
                candidates[i] = Candidate("pending", sql=previous.sql, error=f"bad reply: {e}")
        return {"plans": plans, "candidates": candidates, "repairs": step}

    def needs_repair(state: QAState) -> str:
        failed = any(not c.ok for c in state["candidates"])
        return "repair" if failed and state["repairs"] < max_repairs else "decide"

    def decide_node(state: QAState) -> dict:
        return {"decision": decide(state["candidates"], tau)}

    graph = StateGraph(QAState)
    graph.add_node("prepare", _timed("prepare", prepare))
    graph.add_node("analyze", _timed("analyze", analyze_node))
    graph.add_node("generate", _timed("generate", generate))
    graph.add_node("execute", _timed("execute", execute))
    graph.add_node("repair", _timed("repair", repair))
    graph.add_node("decide", _timed("decide", decide_node))
    graph.add_edge(START, "prepare")
    if analyze:
        graph.add_edge("prepare", "analyze")
        graph.add_edge("analyze", "generate")
    else:
        graph.add_edge("prepare", "generate")
    graph.add_edge("generate", "execute")
    graph.add_conditional_edges("execute", needs_repair, ["repair", "decide"])
    graph.add_edge("repair", "execute")
    graph.add_edge("decide", END)
    return graph.compile()
