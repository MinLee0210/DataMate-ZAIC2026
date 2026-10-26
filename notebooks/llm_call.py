"""Call the LLM from .env (LLM_BASE_URL, LLM_MODEL, ...), raw or through the QA pipeline.

    uv run python -m notebooks.llm_call --prompt "Thủ đô Việt Nam là gì?"
    uv run python -m notebooks.llm_call --id q_001883280e83          # one train question
    uv run python -m notebooks.llm_call --business biz_125 --n 3     # first 3 of a business

Questions come from train only: never send public_test or private_test to a hosted API.
In a notebook: `from notebooks.llm_call import ask, run_question`.
"""

import argparse
import json

from src.config import settings
from src.data.layout import business_dir, calendar_file, load_gold, load_questions, split_dir
from src.models import Question
from src.modules.llm import LLM
from src.services.ingest import IngestService
from src.services.qa import QAService

SPLIT = "train"


def ask(prompt: str, system: str | None = None, seed: int | None = None) -> str:
    """One raw chat completion with the pinned settings (temperature, seed, extra_body)."""
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": prompt})
    return LLM().complete(messages, seed=seed)


def qa_service() -> QAService:
    root = split_dir(settings.data_dir, SPLIT)
    return QAService(
        IngestService(settings.work_dir, calendar=calendar_file(root)),
        package_dir=lambda business_id: business_dir(root, business_id),
    )


def run_question(service: QAService, question: Question, gold: dict | None = None) -> dict:
    """Answer one question through the LangGraph pipeline; print candidates and the gold label."""
    answer, trace = service.answer(question)
    print(f"\n[{question.id}] {question.business_id} as_of={question.as_of_date}")
    print(f"  Q: {question.question}")
    print(f"  -> {answer.type} {answer.value!r}  (agreement {trace.get('agreement')})")
    if gold is not None:
        print(f"  gold: {gold['type']} {gold['answer']!r}")
    for c in trace.get("candidates", []):
        print(f"  - {c['type']} {c['value']!r} {c['error'] or ''}\n    {c['sql']}")
    if "error" in trace:
        print(f"  error: {trace['error']}")
    return {"answer": answer.model_dump(), "trace": trace}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prompt", help="send one raw prompt and print the reply")
    parser.add_argument("--system", help="optional system message for --prompt")
    parser.add_argument("--id", action="append", default=[], help="train question id (repeatable)")
    parser.add_argument("--business", help="take questions of this train business")
    parser.add_argument("--n", type=int, default=1, help="how many questions with --business")
    args = parser.parse_args(argv)

    print(f"model {settings.llm_model} at {settings.llm_base_url}")
    if args.prompt:
        print(ask(args.prompt, system=args.system))
        return 0

    root = split_dir(settings.data_dir, SPLIT)
    questions = load_questions(root)
    if args.id:
        questions = [q for q in questions if q.id in set(args.id)]
    elif args.business:
        questions = [q for q in questions if q.business_id == args.business][: args.n]
    else:
        parser.error("give --prompt, --id or --business")
    gold, _ = load_gold(root)

    service = qa_service()
    try:
        results = [run_question(service, q, gold.get(q.id)) for q in questions]
    finally:
        service.close()
    answers = json.dumps([r["answer"] for r in results], ensure_ascii=False)
    print(f"\n{len(results)} question(s); answers: {answers}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
