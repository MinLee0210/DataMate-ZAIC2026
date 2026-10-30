from pathlib import Path

from src.data.layout import load_gold, split_dir
from src.evaluate import read_submission, score_submission, summarize

golds, _ = load_gold(split_dir(Path("data"), "train"))


def pred(p):
    return read_submission(Path(p).read_text().splitlines())


en = pred("/tmp/dm-en/eval/lang-en-dev200/submission.jsonl")
vi = pred("/tmp/dm-vi/eval/lang-vi-dev200/submission.jsonl")
ids = [i for i in vi if i in golds]
g = {i: golds[i] for i in ids}
for n, p in (("en", en), ("vi", vi)):
    s = score_submission({i: p.get(i) for i in ids if i in p}, g)
    print(n, len(ids), summarize([x.score for x in s]))
