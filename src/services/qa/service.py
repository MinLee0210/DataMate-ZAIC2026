import time
from collections.abc import Callable
from pathlib import Path

from src.config import settings
from src.data.duckdb import DuckDBSource
from src.models import Answer, Question
from src.modules.agents.sql_agent import SQLAgent
from src.modules.context import render_schema_card
from src.modules.context.examples import ExampleStore
from src.services.ingest import BusinessContext, IngestService
from src.services.qa.graph import build_qa_graph
from src.services.qa.malt import MaltPipeline
from src.utils import get_logger
from src.utils.timeparse import LunarCalendar

logger = get_logger(__name__)

# prepare, generate, execute, (repair, execute) x max_repairs, decide: well under this
RECURSION_LIMIT = 25


class QAService:
    """One question end to end: ingest (cached) -> LangGraph pipeline -> typed answer."""

    def __init__(
        self,
        ingest: IngestService,
        package_dir: Callable[[str], Path],
        agent: SQLAgent | None = None,
        rulebook: Path | None = None,
    ) -> None:
        """`rulebook` is the split's rulebook.md; it goes into the agent's system prompt."""
        self.ingest = ingest
        self.package_dir = package_dir
        self.agent = agent or SQLAgent(rulebook=rulebook.read_text() if rulebook else "")
        self._sources: dict[str, DuckDBSource] = {}
        self._schemas: dict[str, str] = {}
        lunar = LunarCalendar.from_csv(ingest.calendar) if ingest.calendar else None
        self.graph = build_qa_graph(
            self.agent,
            k=settings.k,
            tau=settings.tau,
            max_repairs=settings.max_repairs,
            seed=settings.seed,
            schema_text=self._schema_text,
            sql_timeout_s=settings.sql_timeout_s,
            max_rows=settings.max_result_rows,
            lunar=lunar,
            analyze=settings.analyze,
            analyze_body=settings.analyze_body,
            analyze_max_tokens=settings.analyze_max_tokens,
        )

        self.malt = (
            MaltPipeline(
                self.agent,
                seed=settings.seed,
                schema_text=self._schema_text,
                sql_timeout_s=settings.sql_timeout_s,
                max_rows=settings.max_result_rows,
                lunar=lunar,
                extra_body=settings.analyze_body,
                max_tokens=settings.analyze_max_tokens,
                min_confidence=settings.min_confidence,
                examples=ExampleStore.load() if settings.few_shot_k > 0 else None,
                few_shot_k=settings.few_shot_k,
                samples=settings.malt_samples,
                min_agreement=settings.malt_min_agreement,
                early_stop=settings.malt_early_stop,
                variant_offset=settings.malt_variant_offset,
            )
            if settings.pipeline == "malt"
            else None
        )

    def _schema_text(self, business: BusinessContext) -> str:
        if business.business_id not in self._schemas:
            self._schemas[business.business_id] = render_schema_card(business.card)
        return self._schemas[business.business_id]

    def _source(self, business: BusinessContext) -> DuckDBSource:
        if business.business_id not in self._sources:
            source = DuckDBSource(business.db_path)
            source.connect()
            self._sources[business.business_id] = source
        return self._sources[business.business_id]

    def answer(self, question: Question) -> tuple[Answer, dict]:
        """The decided answer, plus a trace for calibration and error analysis.

        Any failure is logged and becomes `abstain` (0 points) rather than a wrong answer.
        """
        trace: dict = {"id": question.id, "business_id": question.business_id}
        self.agent.llm.pop_usage()  # drop records left by an earlier failed question
        try:
            started = time.perf_counter()
            business = self.ingest.load(
                question.business_id, self.package_dir(question.business_id)
            )
            trace["ingest_s"] = round(time.perf_counter() - started, 4)
            if self.malt is not None:
                answer, malt_trace = self.malt.run(
                    question.question, question.as_of_date, business, self._source(business)
                )
                trace.update(malt_trace, llm=[u.to_dict() for u in self.agent.llm.pop_usage()])
                return answer, trace
            state = self.graph.invoke(
                {
                    "question": question.question,
                    "as_of_date": question.as_of_date,
                    "business": business,
                    "source": self._source(business),
                },
                {"recursion_limit": RECURSION_LIMIT},
            )
        except Exception as e:
            logger.exception("question %s failed, abstaining", question.id)
            trace["error"] = f"{type(e).__name__}: {e}"
            trace["llm"] = [u.to_dict() for u in self.agent.llm.pop_usage()]
            return Answer(type="abstain"), trace
        decision = state["decision"]
        trace.update(
            llm=[u.to_dict() for u in self.agent.llm.pop_usage()],
            timings={name: round(s, 4) for name, s in state.get("timings", {}).items()},
            agreement=decision.agreement,
            top=decision.top.model_dump() if decision.top else None,
            votes=decision.votes,
            repairs=state["repairs"],
            analysis=state["context"].get("analysis"),
            candidates=[
                {"type": c.answer_type, "value": c.value, "sql": c.sql, "error": c.error}
                for c in state["candidates"]
            ],
        )
        return decision.answer, trace

    def close(self) -> None:
        for source in self._sources.values():
            source.close()
        self._sources.clear()
