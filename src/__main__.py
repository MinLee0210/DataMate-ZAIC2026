"""Batch inference: python -m src --data /data --out /result [--workers N]

Writes one line per question to <out>/submission.jsonl, flushed as soon as it is decided, so a
timeout keeps every answer written so far. A per-question log goes to <out>/logs/questions.jsonl
(the competition asks for /result/logs/: id, final answer, elapsed time, and how the answer was
reached: thoughts, generated SQL and Python, execution results, errors). The same trace also
goes to $WORK_DIR/trace.jsonl for scripts/eval.py.

With --workers N (default WORKERS, 1) questions run on N threads. Every business is ingested
first, one at a time, so no two threads build the same cache. Each thread then has its own
QAService (LLM client, usage records, DuckDB connections). Lines are written in the order answers
are decided, so with N > 1 the file order differs from the questions file; scoring is by id.
"""

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.config import settings
from src.data.layout import (
    business_dir,
    calendar_file,
    load_questions,
    rulebook_file,
    split_dir,
)
from src.models import Answer, Question, SubmissionLine
from src.services.ingest import IngestService
from src.services.qa import QAService
from src.utils import get_logger

logger = get_logger("src.main")


def _append(handle, record: dict) -> None:
    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=settings.data_dir)
    parser.add_argument("--out", type=Path, default=settings.result_dir)
    parser.add_argument("--split", default=settings.split)
    parser.add_argument("--ids", type=Path, help="file with one question id per line (subset)")
    parser.add_argument("--resume", action="store_true", help="skip ids already in the output")
    parser.add_argument("--workers", type=int, default=settings.workers, help="question threads")
    args = parser.parse_args(argv)

    started = time.monotonic()
    root = split_dir(args.data, args.split)
    questions = load_questions(root)
    if args.ids:
        wanted = {line.strip() for line in args.ids.read_text().splitlines() if line.strip()}
        questions = [q for q in questions if q.id in wanted]

    args.out.mkdir(parents=True, exist_ok=True)
    settings.work_dir.mkdir(parents=True, exist_ok=True)
    submission = args.out / "submission.jsonl"
    done: set[str] = set()
    if args.resume and submission.is_file():
        done = {json.loads(line)["id"] for line in submission.read_text().splitlines() if line}
    elif submission.is_file():
        submission.unlink()
    todo = [q for q in questions if q.id not in done]

    calendar, rulebook = calendar_file(root), rulebook_file(root)
    if rulebook is None:
        logger.warning("no rulebook in %s; the agent runs without it", root)

    def package_dir(business_id: str) -> Path:
        return business_dir(root, business_id)

    def new_service() -> QAService:
        return QAService(
            IngestService(settings.work_dir, calendar=calendar), package_dir, rulebook=rulebook
        )

    # build every ingest cache before the threads start
    ingest = IngestService(settings.work_dir, calendar=calendar)
    for business_id in sorted({q.business_id for q in todo}):
        try:
            ingest.load(business_id, package_dir(business_id))
        except Exception:  # the question itself logs the failure and abstains
            logger.exception("ingest of %s failed", business_id)

    logger.info(
        "%d questions (%d to do), model %s at %s, k=%d tau=%.2f, %d workers",
        len(questions),
        len(todo),
        settings.llm_model,
        settings.llm_base_url,
        settings.k,
        settings.tau,
        args.workers,
    )
    local = threading.local()
    services: list[QAService] = []
    lock = threading.Lock()
    counter = {"n": 0}

    (args.out / "logs").mkdir(parents=True, exist_ok=True)
    with (
        submission.open("a", encoding="utf-8") as out,
        (settings.work_dir / "trace.jsonl").open("a", encoding="utf-8") as traces,
        (args.out / "logs" / "questions.jsonl").open("a", encoding="utf-8") as question_log,
    ):

        def run(question: Question) -> None:
            if not hasattr(local, "service"):
                local.service = new_service()
                with lock:
                    services.append(local.service)
            begun = time.monotonic()
            if begun - started > settings.time_budget_s:
                answer, trace = Answer(type="abstain"), {"id": question.id, "error": "time budget"}
            else:
                answer, trace = local.service.answer(question)
            trace["seconds"] = round(time.monotonic() - begun, 3)
            line = SubmissionLine(id=question.id, type=answer.type, answer=answer.value)
            with lock:
                _append(out, line.record())
                _append(traces, trace)
                _append(
                    question_log,
                    {
                        "id": question.id,
                        "answer": line.record(),
                        "seconds": trace["seconds"],
                        "question": question.question,
                        "as_of_date": str(question.as_of_date),
                        "trace": trace,
                    },
                )
                counter["n"] += 1
                if counter["n"] % 20 == 0:
                    logger.info(
                        "%d/%d answered, %.0fs",
                        counter["n"],
                        len(todo),
                        time.monotonic() - started,
                    )

        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for future in [pool.submit(run, q) for q in todo]:
                future.result()
    for service in services:
        service.close()
    logger.info("done in %.0fs -> %s", time.monotonic() - started, submission)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
