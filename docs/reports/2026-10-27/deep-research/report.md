# Deep research, round 2: models, spreadsheets, abstention, question shapes

Date: 2026-10-27. Follows the [2026-10-26 report](../../2026-10-26/data-agent-research/report.md)
and docs/SUGGESTIONS.md. That earlier work already covers Google CA-API, Snowflake Cortex Analyst,
Databricks Genie, Fabric, Wren AI, Vanna, Arctic-Text2SQL-R1, XiYan, ReFoRCE, CHASE-SQL, N-rep,
CSC-SQL, TrustSQL and the selective-prediction study. This report adds only what is new. The
suggestions are numbered **S19 onward** so they can go straight into the backlog.

How the sources were read: papers marked *(read)* were read in their relevant sections. The others
were read from the abstract or search excerpts. Release dates come from the Hugging Face API
(`createdAt`). Vendor and leaderboard claims are as published by the vendor.

## 0. A measurement from train that changes priorities

On `data/train/questions.jsonl`, I folded accents and case and masked numbers and dates, then
compared each question with the questions of the *other* 29 businesses (rapidfuzz
`token_sort_ratio`, 300 random questions, seed 0):

| Measure | Value |
|---|---|
| Distinct masked questions | 2,326 of 3,000 |
| Questions with a ≥ 85 match in **another** business | **81%** (entity names were not masked, so the real overlap is higher) |
| Questions written without diacritics | 716 of 3,000 (24%) |
| Most common openings | "tháng # cửa hàng" (107), "doanh thu tháng #" (51), "trung bình mỗi đơn" (40), "tháng # ngày nào" (37), "cho tôi biết dthu" (31) |

The question generator reuses a small set of **question shapes** across businesses. This is the
precondition under which "structural" methods (templates and a deterministic compiler) beat
generating free SQL (§3). The open risk is coverage on the private test: public_test adds three shop
types (baby goods, motorbike repair, phone shop), and the private test may add more. A shape
library therefore has to be measured **leave-shop-type-out**, not only leave-business-out.

## 1. Target model: the ≤ 15B landscape has changed since PROJECT.md was written

Only models whose weights were public before 2026-10-01 are allowed. All dates below come from
Hugging Face `createdAt`.

| Model | Released | Params | Notes |
|---|---|---|---|
| `Qwen/Qwen3-14B` (current default) | 2025-04 | 14.8B | Dense; thinking can be switched off |
| **`Qwen/Qwen3.5-9B`** | 2026-02-27 | "9B" LM; the safetensors total is **~10B including the vision encoder** | Apache-2.0. Hybrid Gated DeltaNet + gated attention with MTP. Vendor numbers: MMLU-Pro 82.5, BFCL-V4 66.1, LiveCodeBench v6 65.6. vLLM recommends a **nightly build** and `--language-model-only` |
| `mistralai/Ministral-3-14B-Instruct-2512` / `-Reasoning-2512` | 2025-10-31 | 14B | Apache-2.0 |
| `google/gemma-4-12B-it` | 2026-05-23 | 12B | Check the licence terms |
| `Snowflake/Arctic-Text2SQL-R1-14B` | 2025-05 (paper) | 14.7B | BIRD 70.0 (vendor). The 14B repo and its licence still need checking on Hugging Face |
| Qwen3.6-27B / 35B-A3B, Qwen3.8-27B, Gemma-4-26B-A4B/31B | 2026-04 to 2026-08 | > 15B | **Not allowed** (the MoE counts all experts) |

Findings:
- **Qwen3.5-9B is the strongest new candidate and frees 5B of budget.** With ~10B used, a second
  0.5–1.5B model fits. Two uses for it: a CSC-style merge reviser (see the SLM-SQL row), or a
  separate verifier. Risks:
  1. vLLM support for the hybrid architecture is recent (nightly).
  2. Batch-invariant determinism on the RTX 5090 is unverified for *any* model, and the vLLM docs
     disagree on the minimum compute capability (8.0 vs 9.0).
  3. How the organisers count the unused vision encoder is not stated. Declare ~10B to be safe.
- **No head-to-head Qwen3.5-9B vs Qwen3-14B text-to-SQL result exists.** Community fine-tunes of
  Qwen3.5-9B report BIRD dev 59.9 (agentic) and Spider 74.5 (LoRA). These are not comparable to
  our setting, so only dev200 decides.
- *How Far Do On-Prem Open LLMs Get on Text-to-SQL?* (arXiv:2606.29733, *read*) uses
  Qwen2.5-Coder on BIRD:
  - 14B is the knee of the size curve.
  - **Execution-guided self-correction is the only consistent gain** (+1.5 points at 14B, +3.9 at
    7B).
  - Lexical schema linking does not help significantly (−2.15 at 14B, not significant).
  - 5-sample self-consistency adds about 0 accuracy at 5× the tokens.

  For us this means the k candidates buy **confidence, not accuracy**. Size k for calibration, and
  do not expect PA from extra candidates.
- **Thinking mode.** Thinking is disabled now. AutoThinkSQL (arXiv:2607.22622) and HES-SQL
  (arXiv:2510.08896) both argue for *adaptive* reasoning: think only on hard questions. Neither
  paper was read in full.

## 2. Fine-tuning: the train gold answers are a free verifiable reward

The literature has converged on SFT on synthetic or verified data, followed by GRPO with an
execution reward:

| Work | Recipe | Result |
|---|---|---|
| Arctic-Text2SQL-R1 | GRPO with simple execution-correctness rewards on Qwen2.5-Coder | 14B: BIRD 70.0 |
| SLM-SQL (arXiv:2507.22478, *read*) | SFT on SynSQL-Think-916K → GRPO on BIRD train (reward = EX + 0.1·format) → CSC inference with a **0.5B merge reviser** | 1.5B: BIRD dev 67.1. Without SFT: −8.9; without RL: −4.2; without CSC: −5.1 |
| ReViSQL (arXiv:2603.20004, abstract) | RLVR on **cleaned** labels (61% of the 2.5k BIRD samples corrected) | Clean labels gave 11–16 points over noisy BIRD train. Label quality matters more than scaffolding |

Our advantage is that `data/train/answers.jsonl` holds 3,000 typed gold answers, and
`src/evaluate/scorer.py` is the official scorer. An answer-level reward needs **no gold SQL**: run
the model's SQL, format the result, and score it (+1 / −1 / 0 for abstain). That is RL directly on
PA.

## 3. Structural vs statistical abstention

*Never the Number* (Apple, arXiv:2608.13926, *read*) separates two families:
- **Statistical abstention:** generate an answer, then estimate whether to trust it. This is our
  current `decide/`.
- **Structural abstention:** a deterministic kernel matches the question to a bounded set of
  answerable *question shapes* and compiles it. The LLM may choose *which question* is answered,
  never *which value* is returned.

The paper sets three preconditions: the answer is consumed as fact, questions are structurally
repetitive, and errors cost more than refusals. All three hold here (§0, PA). It recommends the
composition: kernel when grounding succeeds, generative fallback with statistical abstention
otherwise, **routed on grounding success, not on a confidence score**.

Related evidence:
- **OceanBase DataPilot** (vendor blog, Jan 2026) claims first place on **DABstep**, a benchmark of
  data files plus a rules manual, i.e. our setting. It got there with *versioned SOPs and code
  templates*, not a bigger model. This is a vendor claim; the page returned 429 and was not read.
- **PremiseSQL** (arXiv:2610.22158) benchmarks *premise critique*: questions whose presupposition
  is false. Our rulebook's main unanswerable case, "the period lies entirely outside the data", is a
  premise that can be checked deterministically against the date ranges in the schema card.

## 4. Calibration: lessons on measuring confidence

- *Certified Against Which Oracle?* (arXiv:2609.25938, *read*):
  - A conformal abstention threshold set at α = 0.10 carried **17–20%** real risk under expert
    labels.
  - An execution-consistency score always looks better when judged by the oracle that also built
    its clusters (16 of 16 cases).

  What this means for us:
  1. Our oracle is the official scorer on gold answers, which is good: our vote keys must not
     define correctness differently from the scorer.
  2. Choose `tau` with business-grouped (or shop-type-grouped) CV and report confidence intervals.
     A point estimate on dev200 will understate risk on unseen businesses.
- With k = 3 at temperature 0, agreement takes only three values {1/3, 2/3, 1}. The PA-optimal
  threshold needs a finer score. This strengthens S14: agreement plus entity distance, template
  hit, empty result, repair count and type plausibility.
- AbstentionBench (arXiv:2506.09038) found that reasoning models abstain *worse*. If thinking is
  turned on (§1), check #wrong, not only #correct.

## 5. Messy spreadsheets

| Work | Finding | Relevance |
|---|---|---|
| **SheetBrain** (Microsoft, arXiv:2510.19247, *read*) | Understand → execute → validate. Ablations: dropping the understanding module costs 3.3 points, dropping validation about the same, and **replacing the code sandbox with in-context data drops 79.1 → 65.1**. HTML/Markdown serialization **with cell positions** and merged-cell annotations helps. A common agent failure is trusting a `df.head()` preview and taking the wrong header row | Confirms execution over in-context data. Suggests showing a positioned raw-layout preview when header detection is uncertain |
| **Understanding Errors over Imperfect Tables / GBDI** (arXiv:2610.04687, *read*) | Telling the model *where* errors are barely helps. Giving it **repaired tables** raises code-agent accuracy by 39–59 points. Formatting-specific rules gave the largest single gain | Repair at ingest, deterministically. Do not ask the model to "watch out for" messy cells |
| ST-Raptor, SQuARE, SheetCompass, TabScope (2025–26) | Hierarchical headers, multi-row headers and scope selection for semi-structured tables | Ideas for `ingest/clean.py` if error analysis shows header or merged-cell failures |
| SpreadsheetLLM / SheetCompressor (2024) | Anchor-based compression for table detection | Low priority: our files are small |

## 6. Vietnamese

- No new Vietnamese text-to-SQL benchmark exists. ViText2SQL (2020, translated Spider) is still
  the reference. ViR² (2026) only improves few-shot example selection on it, and it was evaluated
  on formal Vietnamese, not our colloquial style.
- 24% of train questions have no diacritics, and string answers *must* carry the data's
  diacritics. So:
  1. Never copy an entity string from the question into an answer. Always return the value from
     the DB.
  2. Link entities on folded text (`utils/text.fold` already does this).
  3. Build an **abbreviation lexicon mined from train questions** ("dthu", "sp", "dc", "đh", "ko",
     "sl", "kh", …) as a split-wide skill or a deterministic pre-normalizer. ViSoLex (2025) covers
     teencode normalization but is not needed if the lexicon covers the train vocabulary.
- I found no Vietnamese POS vendor (KiotViet, Sapo, MISA) with a documented conversational
  data-QA product. Their AI marketing is about reports and dashboards. There is no product to copy
  here.

## 7. New suggestions (S19+)

| ID | Suggestion | Evidence | Effort | Measure |
|---|---|---|---|---|
| **S19** | **Question-shape library (structural kernel).** Cluster train questions by masked shape. For each frequent shape, write one parameterized query over *semantic roles* (S6 views), not over business columns. At inference: normalize, then match a shape and fill its slots deterministically. If every slot resolves, compile and answer with no free SQL; otherwise fall back to the LLM path. Route on grounding success | §0 (81% shape overlap), §3 Apple + DataPilot; strengthens S8/S9 | M–L | Leave-**shop-type**-out coverage; PA on matched vs unmatched questions; #wrong |
| **S20** | **Model bake-off v2:** add `Qwen3.5-9B` (≈ 10B), `Ministral-3-14B-Instruct-2512`, `gemma-4-12B-it`, `Arctic-Text2SQL-R1-14B` next to Qwen3-14B. Declare each in MODELS.md first. Run the GPU smoke test (T7) on Qwen3.5-9B early, because its vLLM support needs nightly | §1 | M | dev200 PA, s/question, rerun diff |
| **S21** | **Second small model when the target is ≤ 10B:** a 0.5–1.5B CSC merge reviser, used only when the vote splits | SLM-SQL (CSC −5.1 when removed) | M (needs training) | PA in the low-agreement band |
| **S22** | **Fine-tune on PA:** LoRA SFT on teacher examples verified against train gold, then (if time allows) GRPO with reward = official scorer. Hold out by business, and train once per CV fold for honest tau. Merged weights keep the same parameter count | §2 | L | Leave-business-out PA; #wrong must not rise |
| **S23** | **Premise checks before the LLM:** deterministic unanswerable decisions for decidable cases, e.g. the asked period lies fully outside the data's date range, or a concept has no column or glossary hit. Partial overlap → answer on the overlap (rulebook) | PremiseSQL; structural abstention; rulebook §7 | S | Unanswerable precision and recall; false unanswerable count |
| **S24** | **Repair at ingest, do not annotate:** checks for mixed number formats per column, "same as above" blanks, duplicate header rows, subtotal rows inside data and outliers in money columns, each fixed in `clean.py` and logged in the schema card. When header detection is unsure, add a positioned raw preview (A1 cells, merged ranges) to the context | GBDI (+39–59 points from repaired tables), SheetBrain | M | Errors attributed to ingest in T5 |
| **S25** | **Abbreviation lexicon** mined from train questions (folded tokens that are not in the data vocabulary), as a deterministic pre-normalizer plus a skill table | §6 | S | Entity and metric errors on no-diacritic questions |
| **S26** | **Adaptive thinking:** answer without thinking first; turn thinking on only for questions below `tau` (it replaces repair rounds as the extra step). Respect ≤ 4 LLM steps; MAX_REPAIRS = 5 currently breaks that rule | AutoThinkSQL, HES-SQL; AbstentionBench caution | S | PA, #wrong, s/question in the low-agreement band |
| **S27** | **Calibration hygiene:** choose `tau` by business-grouped CV with bootstrap CIs; report risk at the chosen tau; keep vote keys identical to scorer normalization | arXiv:2609.25938 | S | CI width; upload-vs-rerun gap on public |
| S28 | Fewer candidates: since self-consistency adds about 0 accuracy, test k = 2 + confidence features against k = 3, to save time (the tie-break) | arXiv:2606.29733 | S | PA vs s/question |

Suggested order, merged with the existing backlog: S1 → S6 + S5 → **baseline (T5)** → S23, S25
(small, deterministic) → **S19** (biggest structural lever) → S14 + S27 → S20 → S24 (driven by T5
error classes) → S26, S28 → S22, S21 (only if time is left before 16/11).

## Sources

Models and serving
- [Hugging Face API, Qwen models by date](https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1&limit=60)
- [Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B)
- [Ministral-3-14B models (HF API)](https://huggingface.co/api/models?search=Ministral-3-14B&author=mistralai)
- [Gemma 4 models (HF API)](https://huggingface.co/api/models?search=gemma-4&author=google&limit=30)
- [Arctic-Text2SQL-R1 (arXiv:2505.20315)](https://arxiv.org/abs/2505.20315)
- [How Far Do On-Prem Open LLMs Get on Text-to-SQL? (arXiv:2606.29733)](https://arxiv.org/html/2606.29733)
- [vLLM batch invariance](https://docs.vllm.ai/en/latest/features/batch_invariance/)
- [Qwen3.5-9B agentic GRPO fine-tune (community)](https://huggingface.co/VikramPal/Qwen3.5-9B-Agentic-GRPO)
- [Modal: best open models for SQL agents 2026](https://modal.com/resources/best-open-source-models-sql-generating-ai-agents)

Training
- [SLM-SQL (arXiv:2507.22478)](https://arxiv.org/abs/2507.22478)
- [ReViSQL: RL on verified data (arXiv:2603.20004)](https://arxiv.org/abs/2603.20004)
- [Learning When to Reason for Text-to-SQL (arXiv:2607.22622)](https://arxiv.org/pdf/2607.22622)
- [HES-SQL (arXiv:2510.08896)](https://arxiv.org/html/2510.08896v1)

Abstention and calibration
- [Never the Number: Structural Abstention (arXiv:2608.13926)](https://www.alphaxiv.org/abs/2608.13926)
- [Certified Against Which Oracle? (arXiv:2609.25938)](https://www.alphaxiv.org/abs/2609.25938)
- [PremiseSQL (arXiv:2610.22158)](https://www.alphaxiv.org/abs/2610.22158)
- [LatentRefusal (arXiv:2601.10398)](https://www.alphaxiv.org/abs/2601.10398)
- [Reliable Text-to-SQL with Adaptive Abstention (arXiv:2501.10858)](https://www.alphaxiv.org/abs/2501.10858)
- [AbstentionBench (arXiv:2506.09038)](https://www.alphaxiv.org/abs/2506.09038)

Data agents and spreadsheets
- [DABstep (arXiv:2506.23719)](https://www.arxiv.org/abs/2506.23719) and [blog](https://huggingface.co/blog/dabstep)
- [OceanBase: solving DABstep hard mode with versioned assets](https://en.oceanbase.com/blog/24781555459)
- [Amity AI Labs DABstep press release](https://www.amitysolutions.com/press-release/amity-ai-labs-1-global-ranking-for-multi-step-data-analysis)
- [SheetBrain (arXiv:2510.19247)](https://www.alphaxiv.org/abs/2510.19247)
- [Understanding Errors over Imperfect Tables / GBDI (arXiv:2610.04687)](https://www.alphaxiv.org/abs/2610.04687)
- [ST-Raptor (arXiv:2508.18190)](https://www.alphaxiv.org/abs/2508.18190)
- [SQuARE (arXiv:2512.04292)](https://www.alphaxiv.org/abs/2512.04292)
- [TabScope (arXiv:2609.03395)](https://www.alphaxiv.org/abs/2609.03395)
- [SpreadsheetLLM (arXiv:2407.09025)](https://huggingface.co/papers/2407.09025.md)

Vietnamese
- [ViText2SQL (arXiv:2010.01891)](https://arxiv.org/pdf/2010.01891)
- [ViR² example selection for Vietnamese text-to-SQL](https://vietnamscience.vjst.vn/index.php/vjste/article/view/1364)
- [VietNormalizer (arXiv:2603.04145)](https://arxiv.org/pdf/2603.04145)
- [MISA AI article (vendor)](https://www.misaeshop.vn/?p=36067)
- [Sapo AI survey (vendor)](https://www.sapo.vn/bao-chi-noi-ve-sapo/Sapo-Khao-sat-15-000-nha-ban-hang-Thue-hoa-don-dien-tu-da-kenh-va-AI-dinh-hinh-t-a2788.html)
