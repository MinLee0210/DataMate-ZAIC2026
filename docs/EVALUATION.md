# Evaluation: Penalized Accuracy

The official matching rules for DataMate, and how this repo implements them
(`src/evaluate/scorer.py`). The overview of the challenge is in [CHALLENGE.md](CHALLENGE.md);
the full text is rulebook §9, "Đáp án và chấm điểm", identical in train and public_test.

## 1. Score

```
PA = (1/N) Σ s_i      s_i = +1 correct,  0 abstain / missing / unreadable,  −1 wrong
```

- The **format** is checked first, then the value. A wrong format is a wrong answer.
- Expected gain from answering is `2·P(correct) − 1`: answer only when P(correct) > 0.5.
- Ranking: PA, then total inference time in the organisers' rerun, then the earlier submission.

## 2. Matching rules per type

| Type | Answer content | Example | Matching rule |
|---|---|---|---|
| `number` | A numeric value (VND amounts, counts, quantities) | `48250000` | Exact match. Reference values are integers (VND, counts, quantities) or rounded to 2 decimals. |
| `percent` | A percentage value, in percent | `-12.45` | Exact match after rounding to 2 decimal places; the sign must be correct. |
| `string` | A name (product, customer, branch, weekday, ...) | `"Sting dâu 330ml"` | Answer and each accepted form of the reference are normalized, then compared for exact equality (see §3). Accepted forms: every spelling of the name in that business's data, plus its code. |
| `date` | A date in ISO format | `"2026-08-15"`, `"2025-09"` | Exact match. `yyyy-mm-dd`; questions about a month: `yyyy-mm`. |
| `boolean` | `true` / `false` | `true` | Exact match. |
| `list` | An ordered list of names or numbers | `["Cà phê sữa", "Bạc xỉu", "Trà đào"]` | Always ordered, matched position by position. The order is the one the question asks for, else the rulebook default (ranking rules). Elements use the `string` or `number` rule. |
| `table` | A small table: column names and rows | `{"columns": [...], "rows": [[...], ...]}` | Columns matched by normalized name, else by position. Rows matched as a set. Name cells use the `string` rule, numeric cells the `number` rule. |
| `unanswerable` | The data does not contain what is needed | — | Correct if and only if the reference is unanswerable. |
| `abstain` | The agent chooses not to answer | — | Scored as abstain (0) regardless of the reference. |

Line shape: `{"id", "type", "answer"}`. `unanswerable` carries an optional string `reason` instead
of `answer`; a non-string `reason` makes the line unreadable (0). `abstain` is `{"id", "type"}` or
no line at all.

## 3. String normalization

Applied to the answer and to every accepted form of the reference:

1. Unicode NFC.
2. Lowercase.
3. Every character that is not a letter, a digit or whitespace becomes a **space** (it is not
   deleted: `a-b` becomes `a b`, which differs from `ab`).
4. Leading and trailing whitespace removed, runs of whitespace collapsed to one space.

Diacritics are **not** removed. `sting dâu 330ml` and `sp0042` both match the example reference.
The answer should therefore use the name as written in the shop's files, with its diacritics.

## 4. Ranking questions

Where the question names no order, the rulebook default applies: descending by the question's
criterion, ties by code ascending (by name when there is no code). A plain filter list is sorted by
code; "by expiry" lists the earliest expiry first. Our rules: `src/assets/skills/ranking-rules/`.

## 5. Implementation in this repo

| Rule | Where |
|---|---|
| Scorer (format, then value; aliases per position) | `src/evaluate/scorer.py` |
| String normalization | `normalize_string` |
| Typed answer formatting and 2 dp rounding | `src/utils/format.py` |
| Money rounded to whole VND, half up | `round_money`, `is_money_question` |
| Check against gold | all 3,000 train answers and their aliases score PA 1.0 |
| Tests | `tests/test_scorer.py`, `tests/test_format.py` |

Known small differences from the official rules (not stated by the rulebook, or a stricter local
reading):

- Numbers are compared with a `1e-6` tolerance and a percent is **not** rounded to 2 dp before the
  comparison. `format.py` always rounds before submitting, so real answers are unaffected.
- A table whose columns match by name only in part is mapped column by column (name, else
  position); a collision counts as a mismatch.
- Not stated officially, assumed: invalid JSON, a missing `id` or an unknown `type` counts as
  blank; for a repeated `id` the first readable line counts.
