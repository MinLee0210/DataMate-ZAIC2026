"""Batch inference: python -m src --data /data --out /result

Writes one line per question to <out>/submission.jsonl, flushed as soon as it is decided, so a
timeout keeps every answer written so far. A per-question trace goes to $WORK_DIR/trace.jsonl.
"""

import argparse
import json
import os
import time
from pathlib import Path

from src.config import settings
from src.data.layout import business_dir, calendar_file, load_questions, split_dir
from src.models import Answer, SubmissionLine
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

    service = QAService(
        IngestService(settings.work_dir, calendar=calendar_file(root)),
        package_dir=lambda business_id: business_dir(root, business_id),
    )
    logger.info(
        "%d questions, model %s at %s, k=%d tau=%.2f",
        len(questions),
        settings.llm_model,
        settings.llm_base_url,
        settings.k,
        settings.tau,
    )
    with (
        submission.open("a", encoding="utf-8") as out,
        (settings.work_dir / "trace.jsonl").open("a", encoding="utf-8") as traces,
    ):
        for n, question in enumerate(questions, 1):
            if question.id in done:
                continue
            elapsed = time.monotonic() - started
            if elapsed > settings.time_budget_s:
                answer, trace = Answer(type="abstain"), {"id": question.id, "error": "time budget"}
            else:
                answer, trace = service.answer(question)
            trace["seconds"] = round(time.monotonic() - started - elapsed, 3)
            line = SubmissionLine(id=question.id, type=answer.type, answer=answer.value)
            _append(out, line.model_dump())
            _append(traces, trace)
            if n % 20 == 0:
                logger.info("%d/%d answered, %.0fs", n, len(questions), time.monotonic() - started)
    service.close()
    logger.info("done in %.0fs -> %s", time.monotonic() - started, submission)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
