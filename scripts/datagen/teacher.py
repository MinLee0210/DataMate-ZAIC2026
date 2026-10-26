"""Synthesize (question, SQL, answer) examples from TRAIN businesses with a deepagents teacher.

    uv sync --extra datagen
    OPENROUTER_API_KEY=... uv run python -m scripts.datagen.teacher --split train --per-business 30

The teacher is a strong hosted model (API allowed here only, never imported by src/). It explores
one business through read-only tools, writes Vietnamese questions in the competition's colloquial
style, and submits each with a DuckDB query. Answers are computed here by executing the query and
formatting it with src/modules/format, never taken from the model's text.

Hard rules: train split only (never public_test or private_test), and nothing keyed on a business.
"""

import argparse
import json
from datetime import date
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemPermission
from langchain_openai import ChatOpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config import settings
from src.data.duckdb import DuckDBSource
from src.data.layout import calendar_file, list_businesses, split_dir
from src.models import VALUE_TYPES
from src.modules.context import render_schema_card
from src.modules.format import format_result
from src.services.ingest import IngestService
from src.utils import get_logger

logger = get_logger("datagen.teacher")

ROOT = Path(__file__).resolve().parents[2]
PROMPT = Path(__file__).with_name("prompts") / "teacher.md"
ALLOWED_SPLITS = {"train"}


class DatagenSettings(BaseSettings):
    """Teacher endpoint, read from the environment or .env. Never used by src/."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    datagen_model: str = "openai/gpt-5.5"
    datagen_base_url: str = "https://openrouter.ai/api/v1"


# the virtual filesystem is src/assets: the teacher may read the skills, never change them
READ_ONLY = [FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")]


def build_tools(source: DuckDBSource, business_id: str, examples: list[dict], schema: str):
    def describe_business() -> str:
        """Return the business's tables, columns, types, sample values and date ranges (YAML)."""
        return schema

    def run_sql(sql: str) -> str:
        """Run a read-only DuckDB SELECT and return up to 20 rows as CSV, or the error."""
        try:
            return source.query(sql, max_rows=20).to_csv(index=False)
        except Exception as e:
            return f"ERROR {type(e).__name__}: {e}"

    def submit_example(
        question: str, as_of_date: str, answer_type: str, sql: str, category: str
    ) -> str:
        """Submit one example. The answer is computed by executing `sql`.

        Args:
            question: colloquial Vietnamese question, as a shop owner would type it.
            as_of_date: yyyy-mm-dd, the "today" of the question, inside the data's date range.
            answer_type: number | percent | string | date | boolean | list | table | unanswerable.
            sql: DuckDB query whose result is the answer ("" for unanswerable).
            category: short label, e.g. ranking, aggregate, time-compare, lookup, unanswerable.
        """
        try:
            date.fromisoformat(as_of_date)
            if answer_type == "unanswerable":
                answer = None
            elif answer_type in VALUE_TYPES:
                answer = format_result(answer_type, source.query(sql))
            else:
                return f"REJECTED: unknown answer_type {answer_type!r}"
        except Exception as e:
            return f"REJECTED {type(e).__name__}: {e}. Fix the query and submit again."
        examples.append(
            {
                "id": f"syn-{business_id}-{len(examples):04d}",
                "business_id": business_id,
                "question": question,
                "as_of_date": as_of_date,
                "type": answer_type,
                "answer": answer,
                "sql": sql,
                "category": category,
            }
        )
        return f"OK #{len(examples)}: answer = {json.dumps(answer, ensure_ascii=False)[:200]}"

    return [describe_business, run_sql, submit_example]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="deepagents teacher for synthetic QA data")
    parser.add_argument("--split", default="train")
    parser.add_argument("--per-business", type=int, default=30)
    parser.add_argument("--limit-businesses", type=int, default=0)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "synth" / "teacher.jsonl")
    args = parser.parse_args(argv)
    config = DatagenSettings()
    if args.split not in ALLOWED_SPLITS:
        raise SystemExit(f"refusing split {args.split!r}: datagen runs on train businesses only")

    if not config.openrouter_api_key:
        raise SystemExit("set OPENROUTER_API_KEY in .env")
    model = ChatOpenAI(
        model=config.datagen_model,
        base_url=config.datagen_base_url,
        api_key=config.openrouter_api_key,
        temperature=0.7,
    )
    root = split_dir(settings.data_dir, args.split)
    ingest = IngestService(settings.work_dir, calendar=calendar_file(root))
    businesses = list_businesses(root)
    if args.limit_businesses:
        businesses = businesses[: args.limit_businesses]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # the teacher reads the same skills as the SQL agent, through a read-only virtual filesystem
    backend = FilesystemBackend(root_dir=ROOT / "src" / "assets", virtual_mode=True)
    system_prompt = PROMPT.read_text()

    with args.out.open("a", encoding="utf-8") as out:
        for package in businesses:
            business = ingest.load(package.name, package)
            source = DuckDBSource(business.db_path)
            source.connect()
            examples: list[dict] = []
            agent = create_deep_agent(
                model=model,
                tools=build_tools(
                    source, business.business_id, examples, render_schema_card(business.card)
                ),
                system_prompt=system_prompt,
                skills=["/skills/"],
                backend=backend,
                permissions=READ_ONLY,
            )
            task = (
                f"Business `{business.business_id}`. README:\n{business.card.readme[:3000]}\n\n"
                f"Submit {args.per_business} diverse, verified examples."
            )
            try:
                agent.invoke(
                    {"messages": [{"role": "user", "content": task}]},
                    {"recursion_limit": 40 + 6 * args.per_business},
                )
            except Exception:
                logger.exception(
                    "teacher failed on %s, keeping %d examples", package.name, len(examples)
                )
            finally:
                source.close()
            for example in examples:
                out.write(json.dumps(example, ensure_ascii=False) + "\n")
            out.flush()
            logger.info("%s: %d examples", package.name, len(examples))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
