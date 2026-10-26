"""The per-question LangGraph: a fixed, bounded pipeline (not an open agent loop).

    prepare ─► generate ─► execute ─┬─► decide ─► END
                              ▲     │ failed candidates and repairs left
                              └─ repair ◄┘

LLM calls: generate (1 step, k prompt variants) + repair (<= max_repairs steps). With the default
max_repairs = 2 that is 3 LLM steps, under the limit of 4 per question.
"""

from collections.abc import Callable
from datetime import date
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.data.duckdb import DuckDBSource
from src.modules.agents.sql_agent import PlanParseError, SQLAgent, SQLPlan
from src.modules.context import link_entities, render_entity_matches
from src.modules.decide import UNANSWERABLE, Candidate, Decision, decide
from src.modules.format import format_result
from src.modules.timeparse import render_time_ranges, resolve
from src.services.ingest import BusinessContext
from src.utils import get_logger

logger = get_logger(__name__)


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
):
    """Compile the graph. `schema_text(business)` returns the rendered schema card (cached)."""

    def prepare(state: QAState) -> dict:
        business = state["business"]
        ranges = resolve(state["question"], state["as_of_date"])
        matches = link_entities(state["question"], business.entities)
        context = {
            "readme": business.card.readme[:3000] or "(no README)",
            "schema": schema_text(business),
            "semantic": ", ".join(business.semantic) or "(none)",
            "time": render_time_ranges(ranges, state["as_of_date"]),
            "entities": render_entity_matches(matches),
            "question": state["question"],
        }
        return {"context": context, "repairs": 0}

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
    graph.add_node("prepare", prepare)
    graph.add_node("generate", generate)
    graph.add_node("execute", execute)
    graph.add_node("repair", repair)
    graph.add_node("decide", decide_node)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "generate")
    graph.add_edge("generate", "execute")
    graph.add_conditional_edges("execute", needs_repair, ["repair", "decide"])
    graph.add_edge("repair", "execute")
    graph.add_edge("decide", END)
    return graph.compile()
