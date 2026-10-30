"""Combine several runs of the same split into one submission by vote (pod models only).

    uv run python -m scripts.ensemble --traces a/trace.jsonl b/trace.jsonl --out dir --min-votes 6

Every k>1 trace contributes one vote per sample, every k=1 trace one vote; a failed sample is an
abstain vote. The top answer is written when it has at least --min-votes votes (and at least
--min-share of all votes); `unanswerable` only when all votes say so. Everything else abstains.
Without --out it prints the number answered for a grid of thresholds.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from src.data.layout import load_questions, split_dir
from src.models import Answer, SubmissionLine
from src.modules.decide import Candidate, vote_key


def votes_of(trace: dict) -> list[tuple[str, Answer | None]]:
    """(key, answer) per vote of one question in one run; None answer = abstain."""
    samples = trace.get("samples")
    tops = [s.get("top") for s in samples] if samples is not None else [trace.get("top")]
    # a k>1 sample trace stores its answer under "top" only when it answered
    out = []
    for top in tops:
        if not top or top.get("type") in (None, "abstain"):
            out.append(("", None))
            continue
        answer = Answer(**top)
        key = (
            "unanswerable"
            if answer.type == "unanswerable"
            else vote_key(Candidate(answer.type, answer.value))
        )
        out.append((key, answer))
    return out


def decide(votes: list[tuple[str, Answer | None]], min_votes: int, min_share: float) -> Answer:
    counts = Counter(k for k, _ in votes if k)
    if not counts:
        return Answer(type="abstain")
    key, n = counts.most_common(1)[0]
    if key == "unanswerable":
        return Answer(type="unanswerable") if n == len(votes) else Answer(type="abstain")
    if n < min_votes or n / len(votes) < min_share:
        return Answer(type="abstain")
    return next(a for k, a in votes if k == key)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--traces", nargs="+", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--split", default="public_test")
    parser.add_argument("--min-votes", type=int, default=0)
    parser.add_argument("--min-share", type=float, default=0.0)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--borderline-out",
        type=Path,
        help="write the ids whose top answer has between --lo and --hi votes (one id per line)",
    )
    parser.add_argument("--lo", type=int, default=3)
    parser.add_argument("--hi", type=int, default=6)
    args = parser.parse_args()

    questions = load_questions(split_dir(args.data, args.split))
    per_q: dict[str, list] = {q.id: [] for q in questions}
    for path in args.traces:
        seen = set()
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            trace = json.loads(line)
            if trace["id"] in per_q and trace["id"] not in seen:
                seen.add(trace["id"])
                per_q[trace["id"]] += votes_of(trace)
        for qid in per_q:  # a run that has no trace for a question votes abstain for its samples
            if qid not in seen:
                per_q[qid].append(("", None))
    if args.borderline_out is not None:
        ids = []
        for qid, votes in per_q.items():
            counts = Counter(k for k, _ in votes if k and k != "unanswerable")
            top = counts.most_common(1)[0][1] if counts else 0
            if args.lo <= top <= args.hi:
                ids.append(qid)
        args.borderline_out.write_text("\n".join(ids) + "\n")
        span = f"[{args.lo}, {args.hi}]"
        print(f"{len(ids)} borderline ids (top votes in {span}) -> {args.borderline_out}")
        return 0
    if args.out is None:
        total = max(len(v) for v in per_q.values())
        print(f"votes per question: up to {total}")
        for m in range(max(1, total // 2), total + 1):
            n = sum(
                decide(v, m, 0.0).type not in ("abstain", "unanswerable") for v in per_q.values()
            )
            print(f"min-votes {m}: {n} answered")
        return 0
    args.out.mkdir(parents=True, exist_ok=True)
    answered = 0
    with (args.out / "submission.jsonl").open("w", encoding="utf-8") as f:
        for q in questions:
            a = decide(per_q[q.id], args.min_votes, args.min_share)
            answered += a.type not in ("abstain", "unanswerable")
            record = SubmissionLine(id=q.id, type=a.type, answer=a.value).record()
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"{answered} answered of {len(questions)} -> {args.out / 'submission.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
