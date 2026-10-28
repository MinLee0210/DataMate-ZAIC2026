"""Evaluation splits of the train data: a hold-out of whole schema families, family-grouped folds
for cross-fitted calibration, and sector subsets for leave-one-sector-out checks.

    uv run python -m scripts.eval --subset holdout            # every hold-out question (v2)
    uv run python -m scripts.eval --subset holdout200         # fixed sample of 200 of them
    uv run python -m scripts.eval --subset development200     # sample of non-hold-out questions
    uv run python -m scripts.eval --subset fold2              # one family-grouped dev fold
    uv run python -m scripts.eval --subset sector:pharmacy    # one sector, dev businesses only

Why families: several businesses share one export template (the same sales-table headers), so a
hold-out business whose template sits in development measures a seen format, not a new shop.
Families were built 2026-10-28 from the ingested headers: two businesses share a family when any
of their transaction tables (6+ columns, 1,000+ rows) have header sets with Jaccard >= 0.8.
Another team's audit found the same family biz_102/103/104/121/122.

Hold-out v1 (2026-10-28 morning: biz_102, 106, 114, 120, 125, 130) leaked: four of its six
businesses had family members in development. It was scored once (exposure log:
docs/holdout_exposure.md) and replaced by v2.

dev200 (scripts/eval.py) is a random sample over all 30 businesses, kept for comparison with
earlier runs; it includes hold-out businesses and overstates scores on new shops.
"""

import random

SHOP_TYPES: dict[str, list[str]] = {
    "grocery": ["biz_102", "biz_103", "biz_108", "biz_109"],
    "cafe": ["biz_104", "biz_105", "biz_106", "biz_111", "biz_112"],
    "building_materials": ["biz_114", "biz_115", "biz_116", "biz_117", "biz_118"],
    "pharmacy": ["biz_119", "biz_120", "biz_121", "biz_122", "biz_123", "biz_124"],
    "restaurant": ["biz_126", "biz_127", "biz_128", "biz_129", "biz_130"],
    # one sales book each, 40 questions each
    "small": ["biz_101", "biz_107", "biz_110", "biz_113", "biz_125"],
}
SECTOR = {b: s for s, bs in SHOP_TYPES.items() for b in bs}

# schema families (shared export templates); singletons are their own family
FAMILIES: list[list[str]] = [
    ["biz_102", "biz_103", "biz_104", "biz_121", "biz_122"],
    ["biz_106", "biz_108", "biz_109", "biz_119", "biz_120", "biz_128"],
    ["biz_112", "biz_115", "biz_116", "biz_118", "biz_130"],
    *[[b] for b in ("biz_101", "biz_105", "biz_107", "biz_110", "biz_111", "biz_113", "biz_114",
                    "biz_117", "biz_123", "biz_124", "biz_125", "biz_126", "biz_127", "biz_129")],
]  # fmt: skip
FAMILY = {b: i for i, family in enumerate(FAMILIES) for b in family}

# hold-out v2: whole families, all five sectors plus a small sales book (about 866 questions)
HOLDOUT = sorted(["biz_102", "biz_103", "biz_104", "biz_121", "biz_122", "biz_117", "biz_129",
                  "biz_125"])  # fmt: skip
HOLDOUT_V1 = ["biz_102", "biz_106", "biz_114", "biz_120", "biz_125", "biz_130"]
SEED = 2026
N_FOLDS = 4


def is_holdout(business_id: str) -> bool:
    return business_id in HOLDOUT


def same_family(a: str, b: str) -> bool:
    return a in FAMILY and FAMILY.get(a) == FAMILY.get(b)


def dev_folds(question_counts: dict[str, int]) -> dict[str, int]:
    """Family-grouped folds over the development businesses, balanced by question count
    (largest family first into the lightest fold). Returns business -> fold."""
    dev_families = [f for f in FAMILIES if not any(b in HOLDOUT for b in f)]
    sizes = sorted(dev_families, key=lambda f: (-sum(question_counts.get(b, 0) for b in f), f))
    load = [0] * N_FOLDS
    fold_of: dict[str, int] = {}
    for family in sizes:
        k = min(range(N_FOLDS), key=lambda i: (load[i], i))
        load[k] += sum(question_counts.get(b, 0) for b in family)
        for b in family:
            fold_of[b] = k
    return fold_of


def subset_ids(
    ids: list[str], subset: str, business_of: dict[str, str], seed: int = SEED
) -> list[str] | None:
    """Question ids of a split subset, or None when `subset` is not a split name."""

    def sample(pool: list[str], n: int) -> list[str]:
        return sorted(random.Random(seed).sample(sorted(pool), min(n, len(pool))))

    held = [i for i in ids if business_of.get(i) in HOLDOUT]
    dev = [i for i in ids if business_of.get(i) and business_of[i] not in HOLDOUT]
    if subset == "holdout":
        return sorted(held)
    if subset.startswith("holdout") and subset[7:].isdigit():
        return sample(held, int(subset[7:]))
    if subset == "development":
        return sorted(dev)
    if subset.startswith("development") and subset[11:].isdigit():
        return sample(dev, int(subset[11:]))
    if subset.startswith("fold") and subset[4:].isdigit():
        counts: dict[str, int] = {}
        for i in dev:
            counts[business_of[i]] = counts.get(business_of[i], 0) + 1
        folds = dev_folds(counts)
        return sorted(i for i in dev if folds.get(business_of[i]) == int(subset[4:]))
    if subset.startswith("sector:"):
        return sorted(i for i in dev if SECTOR.get(business_of[i]) == subset[7:])
    return None
