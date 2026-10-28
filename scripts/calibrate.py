"""Choose the dataAgent confidence threshold (MIN_CONFIDENCE) by cross-fitting over the
family-grouped development folds, so the reported PA is not scored on the data it was tuned on.

    uv run python -m scripts.calibrate --date 2026-10-28 --topic qwen35-9b-v2-dev200
    uv run python -m scripts.calibrate --date 2026-10-28 --topic run-fold0 run-fold1 run-fold2

For each fold k: pick the threshold that maximises PA on the other folds' questions of this run,
apply it to fold k. The cross-fitted PA sums those out-of-fold results. The final threshold is
then fitted on all development questions of the run; check it once on the hold-out.
Hold-out questions in the run are reported apart and never used for fitting.
"""

import argparse
import json
from pathlib import Path

from scripts.splits import HOLDOUT, dev_folds
from src.config import settings
from src.data.layout import load_gold, split_dir
from src.evaluate import tau_curve

ROOT = Path(__file__).resolve().parents[1]
TAUS = [round(0.05 * i, 2) for i in range(21)]


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def best_tau(traces: dict, golds: dict) -> tuple[float, float]:
    """(threshold, PA) with the highest PA; ties go to the lower threshold."""
    curve = tau_curve(traces, golds, TAUS)
    tau, pa = max(curve, key=lambda tp: (tp[1], -tp[0]))
    return tau, pa


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date", required=True)
    parser.add_argument("--topic", required=True, nargs="+", help="one or more eval topics")
    args = parser.parse_args(argv)

    traces = {
        t["id"]: t
        for topic in args.topic
        for t in _jsonl(ROOT / f"data/results/{args.date}/{topic}/raw/trace.jsonl")
    }
    golds_all, questions = load_gold(split_dir(settings.data_dir, "train"))
    business = {i: q["business_id"] for i, q in questions.items()}
    dev = [i for i in traces if business[i] not in HOLDOUT]
    held = [i for i in traces if business[i] in HOLDOUT]
    counts: dict[str, int] = {}
    for i in golds_all:
        if business[i] not in HOLDOUT:
            counts[business[i]] = counts.get(business[i], 0) + 1
    fold_of = dev_folds(counts)

    total, n = 0.0, 0
    name = " + ".join(args.topic)
    print(f"{name}: {len(dev)} development and {len(held)} hold-out questions with traces")
    for k in sorted({fold_of[business[i]] for i in dev}):
        inner = [i for i in dev if fold_of[business[i]] != k]
        outer = [i for i in dev if fold_of[business[i]] == k]
        tau, inner_pa = best_tau({i: traces[i] for i in inner}, {i: golds_all[i] for i in inner})
        outer_pa = dict(tau_curve({i: traces[i] for i in outer}, {i: golds_all[i] for i in outer},
                                  [tau]))[tau]  # fmt: skip
        print(f"  fold {k}: tau {tau} (inner PA {inner_pa}) -> outer PA {outer_pa} on {len(outer)}")
        total += outer_pa * len(outer)
        n += len(outer)
    ungated = dict(tau_curve({i: traces[i] for i in dev}, {i: golds_all[i] for i in dev}, [0.0]))
    final_tau, final_pa = best_tau({i: traces[i] for i in dev}, {i: golds_all[i] for i in dev})
    print(f"development: no gate PA {ungated[0.0]}, cross-fitted PA {round(total / max(n, 1), 4)}")
    print(f"final MIN_CONFIDENCE {final_tau} (in-sample PA {final_pa}, optimistic)")
    if held:
        h = tau_curve({i: traces[i] for i in held}, {i: golds_all[i] for i in held},
                      [0.0, final_tau])  # fmt: skip
        print(f"hold-out (check only, log it in docs/holdout_exposure.md): {dict(h)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
