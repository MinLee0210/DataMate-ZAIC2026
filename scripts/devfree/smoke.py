"""dev_free smoke run: the real LLM endpoint (.env) on the synthetic toy business.

    uv run python -m scripts.devfree.smoke

Checks connectivity, the JSON reply format and the whole graph before spending on a dev200 eval.
"""

import json
import tempfile
from pathlib import Path

from scripts.devfree.toy import write_toy_split
from src.config import settings
from src.data.layout import business_dir, load_questions
from src.services.ingest import IngestService
from src.services.qa import QAService


def main() -> int:
    root = write_toy_split(Path(tempfile.mkdtemp(prefix="datamate-smoke-")) / "train")
    print(f"model {settings.llm_model} at {settings.llm_base_url}")
    service = QAService(
        IngestService(root.parent / "work"), package_dir=lambda b: business_dir(root, b)
    )
    gold = {
        r["id"]: r for r in map(json.loads, (root / "questions.jsonl").read_text().splitlines())
    }
    ok = 0
    for question in load_questions(root):
        answer, trace = service.answer(question)
        expected = gold[question.id]
        hit = answer.type == expected["type"] and answer.value == expected["answer"]
        ok += hit
        print(
            f"\n{question.question!r}: {answer.type} {answer.value!r} "
            f"(expected {expected['answer']!r}) {'OK' if hit else 'MISS'}"
        )
        for c in trace.get("candidates", []):
            print(f"  - {c['type']} {c['value']!r} {c['error'] or ''}\n    {c['sql']}")
        if "error" in trace:
            print(f"  error: {trace['error']}")
    service.close()
    print(f"\n{ok}/2 correct")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
