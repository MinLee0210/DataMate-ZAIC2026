"""Phase 0: a semantic taxonomy of the train questions, with current precision per family.

    uv run python -m scripts.taxonomy --data data \
        --scored docs/analysis/2026-11-11/phase0-taxonomy/dev500-scored.jsonl \
        --out docs/analysis/2026-11-11/phase0-taxonomy

The rules are rough keyword rules on folded text, ordered from the specific family to the general
one. The point is the coverage table: how much of the test a compiler family could own, and what
the current pipeline scores there — not an exact classifier.
"""

import argparse
import collections
import json
import re
from pathlib import Path

from src.utils.text import fold


def _rules() -> list[tuple[str, str]]:
    return [
        (
            "growth_percent",
            r"(%|phan tram).*(so voi|cung ky)|(tang|giam|thay doi|hon|kem).*(%|phan tram)",
        ),
        ("cancel_rate", r"(ti le|ty le|phan tram).*(huy|tra hang)|(huy|tra hang).*(ti le|ty le|%)"),
        ("difference_amount", r"(chenh lech|hon|kem|tang|giam).*(bao nhieu|bnhiu)"),
        ("share_by_group", r"(chiem|ti trong|dong gop).*(nhom|doanh thu)"),
        ("revenue_by_customer", r"(doanh thu|dthu|tien ban|thu ve).*(khach|nhom khach|than thiet)"),
        ("revenue_by_staff", r"(doanh thu|dthu|tien ban).*(nhan vien|nguoi ban|ma nv|nv[0-9])"),
        ("revenue_by_payment", r"(doanh thu|dthu|tien ban).*(tra bang|thanh toan)"),
        (
            "revenue_by_channel",
            r"(doanh thu|dthu|tien ban).*(kenh|ban qua|tai quay|zalo|dien thoai)",
        ),
        ("revenue_by_group", r"(doanh thu|dthu|tien ban).*nhom (hang|hang hoa|san pham|mat hang)"),
        ("revenue_by_item", r"(doanh thu|dthu|tien ban|thu ve).*(mat hang|san pham|mon |thuoc )"),
        ("revenue_plain", r"doanh thu|dthu|doanh so|tien ban|thu ve|thu duoc bao nhieu tien"),
        ("avg_order", r"(trung binh|binh quan|gia tri tb).*(don|bill|hoa don)"),
        ("avg_price", r"(trung binh|binh quan).*(gia|nhap)"),
        (
            "count_threshold_orders",
            r"(bao nhieu|bao nhiu|bnhiu|may|dem|so).*(don|bill).*(tu|dat|tro len|≥|>=)",
        ),
        ("count_cancelled", r"(bao nhieu|bao nhiu|bnhiu|may|dem|so).*(don|bill).*(huy)"),
        ("count_returned", r"(bao nhieu|bao nhiu|bnhiu|may|dem|so).*(don|bill).*(tra hang|hoan)"),
        ("count_orders", r"(bao nhieu|bao nhiu|bnhiu|may|dem|so).*(don|bill|hoa don)"),
        ("count_customers", r"(bao nhieu|bao nhiu|bnhiu|may|dem|so).*(khach)"),
        ("count_items", r"(bao nhieu|bao nhiu|bnhiu|may).*(mat hang|san pham|mon)"),
        (
            "count_qty",
            r"(bao nhieu|bao nhiu|bnhiu|may).*(kg|ly|cai|hop|chai|goi|vien|thung|mon|cuon|bao)",
        ),
        (
            "top_items",
            r"(top|nhieu nhat|cao nhat|ban chay|hot nhat|loi nhat|it nhat|thap nhat)"
            r".*(hang|mat hang|san pham|mon)",
        ),
        ("top_customers", r"(top|nhieu nhat|cao nhat|mua nhieu).*(khach)"),
        ("top_staff", r"(nhieu nhat|cao nhat|gioi nhat).*(nhan vien)"),
        ("best_day", r"(ngay nao|hom nao).*(cao nhat|dat nhat|nhieu nhat)"),
        ("worst_day", r"(ngay nao|hom nao).*(thap nhat|it nhat)"),
        ("debt_by_customer", r"(no|cong no).*(khach|top|liet ke|nhieu nhat)"),
        ("debt_paid", r"(thu no|tra no|thu hoi|khach tra|tra bot no)"),
        ("debt_total", r"(con no|cong no|tien no|so tien no|dang no)"),
        ("stock_value", r"(gia tri).*(ton kho|hang ton)|(ton kho).*(gia von|gia tri)"),
        ("stock_qty", r"(ton kho|ton cuoi|con lai|cuoi ngay|het hang)"),
        ("import_avg_price", r"(gia nhap).*(binh quan|trung binh)"),
        ("import_total", r"(nhap hang|tien nhap|phieu nhap|gia tri nhap)"),
        ("price_on_date", r"(gia ban|don gia|gia le).*(ngay|vao ngay)"),
        ("price_change_effect", r"(tang gia|giam gia|doi gia).*(ngay|hieu ung|khi)"),
        ("expiry_list", r"(het han|han dung|sap het han)"),
        ("list_items", r"(liet ke|danh sach).*(hang|mat hang|san pham|mon)"),
        ("list_customers", r"(liet ke|danh sach|top).*(khach)"),
        ("boolean", r"(co .*khong|tang lien tuc|luon cao hon|phai khong|dung khong)"),
    ]


def family(question: str, answer_type: str) -> str:
    if answer_type == "unanswerable":
        return "unanswerable"
    text = fold(question)
    for name, pattern in _rules():
        if re.search(pattern, text):
            return name
    if answer_type == "date":
        return "date_other"
    if answer_type == "string":
        return "string_other"
    if answer_type == "table":
        return "table_other"
    if answer_type == "list":
        return "list_other"
    return "other"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--scored", type=Path, required=True, help="dev500 scored.jsonl")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    train = [json.loads(line) for line in (args.data / "train" / "questions.jsonl").open()]
    gold = {
        row["id"]: row
        for row in (json.loads(line) for line in (args.data / "train" / "answers.jsonl").open())
    }
    scored = {
        row["id"]: row for row in (json.loads(line) for line in args.scored.open() if line.strip())
    }
    counts: collections.Counter = collections.Counter()
    dev: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for question in train:
        name = family(question["question"], gold[question["id"]]["type"])
        counts[name] += 1
        if question["id"] in scored:
            score = scored[question["id"]]["score"]
            dev[name]["n"] += 1
            dev[name]["correct" if score == 1 else "wrong" if score == -1 else "abstain"] += 1

    total = len(train)
    rows = []
    for name, n in counts.most_common():
        d = dev[name]
        answered = d["correct"] + d["wrong"]
        precision = d["correct"] / answered if answered else 0.0
        rows.append(
            (
                name,
                n,
                100 * n / total,
                d["n"],
                d["correct"],
                d["wrong"],
                d["abstain"],
                precision,
            )
        )

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "families.csv").open("w") as handle:
        handle.write("family,train_n,train_share,dev_n,correct,wrong,abstain,precision\n")
        for row in rows:
            handle.write(",".join(str(value) for value in row) + "\n")

    lines = [
        "# Phase 0: question families and their current precision",
        "",
        f"Train questions: {total}. Dev500: {sum(d['n'] for d in dev.values())}.",
        "",
        "| family | train n | share | dev n | correct | wrong | abstain | precision |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, n, share, dn, correct, wrong, abstain, precision in rows:
        lines.append(
            f"| {name} | {n} | {share:.1f} % | {dn} | {correct} | {wrong} | {abstain}"
            f" | {precision:.2f}"
        )
    cumulative = 0.0
    covers = {}
    for name, _n, share, *_ in rows:
        cumulative += share
        for threshold in (50, 70, 80, 90, 95):
            if cumulative >= threshold and threshold not in covers:
                covers[threshold] = name
    lines += [
        "",
        "## Coverage",
        "",
    ]
    for threshold in (50, 70, 80, 90, 95):
        lines.append(
            f"- {threshold} % of train is covered by the top families up to"
            f" `{covers.get(threshold, '—')}`."
        )
    lines += [
        "",
        "## Reading",
        "",
        "`precision` is the current k=1 pipeline on the 500 dev questions in that family.",
        "A family worth compiling has a large dev n and precision well below 1.0; the ceiling of",
        "compiling it is its dev share, not its precision.",
        "",
    ]
    (args.out / "report.md").write_text("\n".join(lines))
    print("\n".join(lines[:12]))
    print(f"\nwrote {args.out / 'report.md'} and families.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
