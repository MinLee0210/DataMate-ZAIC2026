"""Intent mix of the questions, and precision per intent from scored runs. No LLM, no GPU.

    uv run python -m scripts.diagnose_intents --data data \
        --scored docs/analysis/2026-10-30/d1k-old-h0/scored.jsonl \
                 docs/analysis/2026-10-30/d1k-old-h1/scored.jsonl

Prints the share of each intent in train and public_test (is there a shift in the kind of
question?) and, with --scored, how many answers were right / wrong / abstained per intent and the
relative error of the wrong number answers. Intents come from keyword rules on the folded
question: rough, meant to point at where to look, not to classify exactly.
"""

import argparse
import collections
import json
import re
import statistics
from pathlib import Path

from src.utils.text import fold

RULES = [
    ("cancel_rate", r"ti le.*huy|huy.*phan tram|phan tram.*huy"),
    ("cancel_count", r"(so|dem|bao nhieu|may).*(don|bill).*(huy|tra)|huy may|bi huy|don huy"),
    ("avg_order", r"trung binh.*(don|bill|phieu)|(don|bill).*trung binh|gia tri tb"),
    ("best_day", r"ngay nao.*(cao|nhieu|dat|thap|it)|(cao|nhieu) nhat.*ngay"),
    ("growth_compare", r"so voi|tang|giam|thay doi|cung ky"),
    ("debt", r"\bno\b|cong no|thu no|con no"),
    ("customer", r"khach"),
    ("top_item", r"(ban chay|nhieu nhat|cao nhat|top \d+|thap nhat|it nhat)"),
    ("stock_cost", r"ton kho|nhap hang|gia von|loi nhuan|lai |von "),
    ("revenue", r"doanh thu|dthu|doanh so|ban duoc.*tien|tien ban|thu ve"),
    ("count_qty", r"bao nhieu (ly|cai|hop|cay|chai|goi|kg|vien|thung|mon)|so luong"),
]


def intent(question: str) -> str:
    text = fold(question)
    for name, pattern in RULES:
        if re.search(pattern, text):
            return name
    return "other"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--scored", nargs="*", type=Path, default=[], help="scored.jsonl files")
    args = parser.parse_args()

    train = {q["id"]: q for q in read_jsonl(args.data / "train" / "questions.jsonl")}
    gold = {a["id"]: a for a in read_jsonl(args.data / "train" / "answers.jsonl")}
    public = read_jsonl(args.data / "public_test" / "questions.jsonl")

    t = collections.Counter(intent(q["question"]) for q in train.values())
    p = collections.Counter(intent(q["question"]) for q in public)
    print("intent            train %  public %")
    for name in sorted(set(t) | set(p), key=lambda k: -t[k]):
        print(f"{name:16s}{100 * t[name] / len(train):8.1f}{100 * p[name] / len(public):10.1f}")
    if not args.scored:
        return 0

    scored = {r["id"]: r for path in args.scored for r in read_jsonl(path)}
    agg: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0, 0])
    for qid, row in scored.items():
        slot = {1: 0, -1: 1}.get(row["score"], 2)
        agg[intent(train[qid]["question"])][slot] += 1
    print("\nintent            n  right wrong abst precision    PA")
    for name, (right, wrong, abst) in sorted(agg.items(), key=lambda kv: -sum(kv[1])):
        n = right + wrong + abst
        precision = right / (right + wrong) if right + wrong else 0.0
        pa = (right - wrong) / n
        print(f"{name:16s}{n:4d}{right:7d}{wrong:6d}{abst:5d}{precision:10.2f}{pa:7.2f}")

    errors = []
    for qid, row in scored.items():
        if row["score"] != -1 or intent(train[qid]["question"]) != "revenue":
            continue
        answer, pred = gold[qid]["answer"], (row.get("pred") or {}).get("answer")
        if isinstance(answer, int | float) and isinstance(pred, int | float) and answer:
            errors.append(abs(pred - answer) / abs(answer))
    if errors:
        print(
            f"\nwrong revenue numbers: {len(errors)}, median relative error "
            f"{statistics.median(errors):.3f}"
        )
        for limit in (0.01, 0.05, 0.2, 1.0):
            print(f"  within {limit:>4.0%}: {sum(e <= limit for e in errors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
