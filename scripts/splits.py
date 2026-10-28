"""Business-level hold-out of the train split, for honest evaluation once train data is used for
training (fine-tuning, synthetic examples, retrieved few-shot examples).

dev200 samples questions from every train business, so it measures known businesses. The private
test can bring new businesses and shop types; the hold-out mimics that: one business of each shop
type in train is never trained on, generated from or retrieved from.

    uv run python -m scripts.eval --subset holdout          # every hold-out question
    uv run python -m scripts.eval --subset holdout200       # fixed sample of 200 of them

Shop types were read from the businesses' products (2026-10-27). The pick inside each type is a
fixed random draw (seed 2026), so it does not depend on how well the pipeline does there.
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
SEED = 2026


def holdout_businesses() -> list[str]:
    rng = random.Random(SEED)
    return sorted(rng.choice(sorted(group)) for _, group in sorted(SHOP_TYPES.items()))


HOLDOUT = holdout_businesses()


def is_holdout(business_id: str) -> bool:
    return business_id in HOLDOUT
