from collections.abc import Callable
from pathlib import Path

from src.config import settings
from src.data.duckdb import DuckDBSource
from src.models import Answer, Question
from src.modules.agents.sql_agent import SQLAgent
from src.modules.context import render_schema_card
from src.services.ingest import BusinessContext, IngestService
from src.services.qa.graph import build_qa_graph
from src.utils import get_logger

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
    ) -> None:
        self.ingest = ingest
        self.package_dir = package_dir
        self.agent = agent or SQLAgent()
        self._sources: dict[str, DuckDBSource] = {}
        self._schemas: dict[str, str] = {}
        self.graph = build_qa_graph(
            self.agent,
            k=settings.k,
            tau=settings.tau,
            max_repairs=settings.max_repairs,
            seed=settings.seed,
            schema_text=self._schema_text,
            sql_timeout_s=settings.sql_timeout_s,
            max_rows=settings.max_result_rows,
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
        try:
            business = self.ingest.load(
                question.business_id, self.package_dir(question.business_id)
            )
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
            return Answer(type="abstain"), trace
        decision = state["decision"]
        trace.update(
            agreement=decision.agreement,
            top=decision.top.model_dump() if decision.top else None,
            votes=decision.votes,
            repairs=state["repairs"],
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
