# The challenge: DataMate (Zalo AI Challenge 2026)

An overview for anyone joining the project. It covers what the task is, what we get, what we
submit, how it is scored, and the limits on the solution. Details and our design are in
[PROJECT.md](PROJECT.md); the research plan is in [RESEARCH.md](RESEARCH.md).

Sources:
- the [challenge portal](https://challenge.zalo.ai/portal/datamate), whose description, timeline
  and submission quotas were read from the site's published page script;
- the data package itself: `questions.jsonl` and the split rulebook (`rulebook.md`). Rulebook §9 is
  the official answer format and scoring, and it is identical in train and public_test.

Things not confirmed from an official text are marked *unconfirmed*.

## 1. What it is about

> "Millions of Vietnamese shop owners, teachers, clinics and small offices keep their records in
> spreadsheets and simple databases — but few can write a query. DataMate challenges you to build
> an AI agent that answers everyday questions in Vietnamese directly on messy, real-world tabular
> data: multi-sheet Excel exports, inconsistent product names, colloquial phrasing, and business
> logic like cost of goods or overdue debt. Your agent must find the right answer on its own — and
> know when the data cannot answer at all. Correct answers score, wrong answers cost, silence is
> free: build a system that is right when it speaks." (portal, *DataMate — Talking To Your Data
> Through Agentic AI*)

In short, it is offline table question answering for small Vietnamese businesses. It is close to
text-to-SQL, but four things make it harder:
- The tables are messy. Headers are not on the first row, there are merged cells, many sheets per
  workbook, Vietnamese number formats such as `1.200.000`, dates without a year, and blank cells
  that mean "same as the row above".
- The questions are colloquial and often without accents ("thang 7/2026 co bao nhiu don co dthu
  tu 55.000 dong tro len").
- The answer depends on the rulebook. "Revenue" excludes cancelled and returned orders, months are
  counted by order date, "Tết" is a lunar-calendar window, and so on.
- The metric punishes a wrong answer as much as it rewards a right one.

## 2. Inputs

Per split (`data/<split>/`):

| File | Content |
|---|---|
| `questions.jsonl` | `{"id", "business_id", "question", "as_of_date"}`. `as_of_date` is "today" for that question |
| `data/<business_id>/` | the shop's package: `README.md` plus one or more `.xlsx` / `.csv` / `.sqlite` files |
| `rulebook.md` | split-wide business rules (revenue, time, ranking, debt, stock, rules per shop type), answer format and scoring |
| `calendar.csv` | solar ↔ lunar calendar and holidays (for Tết and other lunar expressions) |
| `answers.jsonl` | **train only**: `{"id", "type", "answer", "alias"}` |

| Split | Questions | Businesses | Files | Shop types in the rulebook |
|---|---|---|---|---|
| train | 3,000 | 30 | 107 xlsx, 20 csv, 1 sqlite | café, pharmacy, building materials |
| public_test | 1,000 | 14 | 69 xlsx, 10 csv, 1 sqlite | the same three + **baby goods, motorbike repair, phone shop** |
| private_test | ? | ? | released 20/11 | expect unseen businesses and possibly unseen shop types |

The private test can bring businesses, and even shop types, that are not in train. The solution
must therefore generalize from the rulebook and the data. Per-business knowledge does not help, and
using it is forbidden (CLAUDE.md, rule 4).

Train answer types: number 1,884 (63%), percent 578 (19%), list 193, date 145, string 88,
unanswerable 70 (2.3%), boolean 23, table 19.

## 3. Output

One JSON line per question in `submission.jsonl`:

```json
{"id": "q_00558c1410ef", "type": "percent", "answer": 2.08}
```

Each type has exactly one accepted format (rulebook §9). **A wrong format is a wrong answer.**

| type | Format | Right | Wrong |
|---|---|---|---|
| number | JSON number, no unit, no thousands separator; money is whole VND | `4820000`, `18.6` | `"4,82 triệu"`, `"4.820.000"`, `"4820000"` |
| percent | JSON number in percentage points | `12.4` | `"12,4%"`, `0.124` |
| date | `"YYYY-MM-DD"`, or `"YYYY-MM"` for monthly questions | `"2026-08-15"`, `"2025-09"` | `"15/08/2026"` |
| boolean | `true` / `false` | `true` | `"có"`, `1` |
| string | the name as written in the data, with correct diacritics | `"Sting dâu 330ml"` | `"Sting dầu 330ml"`, `["Sting dâu 330ml"]` |
| list | JSON array, ordered; one element is still an array | `["Cà phê sữa"]`, `[3, 10]` | `"Cà phê sữa, Bạc xỉu"` |
| table | `{"columns": [...], "rows": [[...], ...]}`, numeric cells as JSON numbers | `{"columns": ["khach_hang", "so_tien_no"], "rows": [["Chị Lan", 3200000]]}` | a cell `"3.200.000đ"` |
| unanswerable | `{"type": "unanswerable", "reason": "..."}` (`reason` optional, must be a string) | | |
| abstain | `{"type": "abstain"}`, or no line at all | | |

## 4. How it is scored: Penalized Accuracy

```
PA = (1/N) Σ s_i      s_i = +1 correct,  0 abstain or missing,  −1 wrong
```

The format is checked first, then the value:
- **number / percent:** exact match; only floating-point error is ignored. Money is exact to the
  đồng and counts are exact to the unit. Percents and non-money averages are rounded to 2 dp,
  unless a rulebook rule says otherwise. An average of money is money, so it is rounded to the
  đồng.
- **string:** case, whitespace and punctuation are ignored, but diacritics count. Any spelling of
  the name that appears in the shop's files is accepted, and so is the code. A customer name
  copied with its phone number, as written in the file, is also accepted. (Train `alias` lists
  these spellings.)
- **list:** the same items in the same order. Top-k is in descending order of the question's
  criterion. A "list" question with a measure is sorted by that measure, descending; one sorted by
  expiry lists the earliest expiry first; a plain filter is sorted by code. Ties are broken by code
  ascending, or by name when there is no code.
- **table:** one row per object. The first column is the object's name, and the other columns are
  the measures in the order the question asks for them. Columns are matched by name, else by
  position. Row order does not matter.
- **unanswerable:** the released data cannot answer the question. Examples: the period lies
  entirely outside the shop's data, or the shop does not record that kind of information. "No
  data" is not the same as 0. If a period only partly overlaps the data, the answer is computed on
  the overlapping part. Answering an unanswerable question is wrong, and so is calling an
  answerable one unanswerable.
- A line whose `reason` is not a string is unreadable and counts as blank (0).
- *Unconfirmed:* how a repeated id, an unknown `type` or invalid JSON is treated. Our scorer treats
  the last two as blank and lets the first readable line of a repeated id count.

**What this implies.** The expected gain from answering is `2·P(correct) − 1`, so we should answer
only when P(correct) > 0.5. Calibrated abstention is worth as much as accuracy. For example, a
system that is right 60% of the time and always answers scores PA 0.20. If it skips its least
certain third, made up mostly of wrong answers, it can do much better.

**Ranking.** The leaderboard is sorted by PA. Ties are broken first by **total inference time in
the organisers' rerun**, then by the earlier submission. The public leaderboard is provisional; the
final ranking uses the private test.

## 5. Limits on the solution

From [PROJECT.md §3](PROJECT.md) and the hard rules in CLAUDE.md:

| Item | Limit |
|---|---|
| Models at inference | ≤ 15B parameters in total (MoE counts all experts); weights public before 2026-10-01; licence allows use; all declared |
| Hardware | 2× RTX 5090 (32 GB each), 512 GB RAM, CUDA ≥ 12.8 |
| Time | the whole private test in ≤ 6 h, model loading included |
| Network | none: the Docker image runs with networking disabled |
| Reproducibility | the organisers rerun the image. \|PA_upload − PA_rerun\| ≤ 0.03, and logs must explain any difference |
| Data | train, self-generated and public data only; never public_test or private_test answers |

## 6. Timeline and submissions

| Date (GMT+7) | Event |
|---|---|
| 26/10 | Start: development kit, train and public test data, evaluation software |
| 26/10 → | Public test submissions to the provisional leaderboard (quota shown on the portal: 5) |
| 16/11 23:59 | **Submit the solution**: training code, testing code, models, Docker image (quota: 2; the last one counts) |
| 20/11 09:00 | Private test released |
| 23/11 23:59 | **Submit the final result** on the private test (quota: 2) |
| 02/12 | Finalists announced (top 2 teams per track) |
| 12/12 | Final standing |

*Unconfirmed:* whether the public quota of 5 is per day or in total.

## 7. Where this lives in the repo

| Topic | Location |
|---|---|
| Official scorer (rulebook §9) | `src/evaluate/scorer.py`. Checked: all train gold answers, and their alias forms, score PA 1.0 |
| Extra metrics, not scored (time, tokens, TTFT, LLM steps, coverage, oracle@k, calibration AUROC) | `src/evaluate/metrics.py`, from `$WORK_DIR/trace.jsonl` |
| Eval runner and report | `scripts/eval.py` → `docs/analysis/<date>/<topic>/summary.md` + `metrics.json` |
| Answer formatting | `src/utils/format.py` |
| Abstain / unanswerable policy | `src/modules/decide/` |
| Improvement backlog | [SUGGESTIONS.md](SUGGESTIONS.md) |
