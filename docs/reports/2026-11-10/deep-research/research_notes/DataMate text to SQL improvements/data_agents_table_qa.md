# Data-analysis agents and table QA over messy tabular data (state as of 2026-11-10)

Method note: about 12 tool calls (web search plus page fetches). Several primary pages (HF leaderboard, Spider 2.0 site, dbt post, SemEval overview tables, paper PDFs) could not be opened; those numbers come from search-result snippets or aggregators and are flagged UNVERIFIED. Nothing here comes from private project details.

## 1. Top solutions and scores per benchmark; model sizes of best small-model entries

### Takeaway
DABstep hard-task accuracy moved from 14.55% (o4-mini, launch) to about 41-45% for agent frameworks in H2 2025; an 8B open model reportedly reached 32.8% hard. On DataBench (SemEval-2025 Task 8) top systems were about 95% on the test set, while open-source-only pipelines landed around 65-80%. I could not retrieve 2026 leaderboard snapshots or a 2026 business-data QA benchmark with confidence.

### Cited Findings
- DABstep launch: best agent o4-mini (reasoning prompt) reached 14.55% on Hard tasks and 76.39% on Easy; 378 Hard tasks = 84% of the benchmark — [DABstep paper](https://arxiv.org/pdf/2506.23719) (search snippet summaries, 2025-06).
- Amity AI Labs claimed #1 with 80.56% easy / 41.01% hard as of 2025-07-11 (company press release, not independently verified) — [Amity press release](https://www.amitysolutions.com/press-release/amity-ai-labs-1-global-ranking-for-multi-step-data-analysis).
- Google DS-STAR: DABStep 41.0% (best baseline) -> 45.2%; KramaBench 39.8% -> 44.7%; DA-Code 37.0% -> 38.5%; ranked first on public DABStep leaderboard as of 2025-09-18; baselines AutoGen and DA-Agent; base LLMs Gemini-2.5-Pro and GPT-5 (Gemini better on hard, GPT-5 on easy) — [Google Research blog](https://research.google/blog/ds-star-a-state-of-the-art-versatile-data-science-agent/).
- DeepAnalyze-8B (open, 8B, released 2025-10-19): DABStep about 70.8% easy / 32.8% hard per an aggregator (UNVERIFIED against paper); paper claims it beats workflow agents built on proprietary LLMs — [DeepAnalyze arXiv](https://arxiv.org/pdf/2510.16872); [SOTA2 aggregator](https://www.sota2.com/research/sota/data-analysis-on-dabstep-2025-hard-level).
- Actioneer vendor blog claims 93.78% overall / 94.44% hard on DABstep (marketing, UNVERIFIED, implausibly above other reports) — [Actioneer](https://actioneer-1.ghost.io/dabstep-benchmark-ai-agents-financial-data-accuracy/).
- SemEval-2025 Task 8 (DataBench, DataBench Lite): over 100 teams, 35 system papers; overview says top systems use large LLMs but prompting strategy mattered — [Task overview](https://aclanthology.org/2025.semeval-1.324/).
- Aggregator leaderboard: UNTeleAI 95.02%, UNSRPOL AIS 89.66%, UNHITSZ-HLT 86.97% on DataBench (secondary, open/closed not labelled; another source cites best 95.20) — [benchmarklist](https://benchmarklist.com/benchmarks/databench/).
- Aestar (SQL pipeline: example selection, SQL generation, answer extraction, verification, iterative refinement; GPT-4o, GPT-4o-mini, DeepSeek v2 16B): 70.5% DataBench, 71.6% Lite vs baselines 26%/27% — [Aestar](https://preview.aclanthology.org/setup/2025.semeval-1.292). Per-component ablation not on abstract page.
- IUST_Champs: 70.49% test with open-source LLMs generating Python; YNU-HPCC built on TableGPT2: 65.64% DataBench / 66.62% Lite — via [search summary of ACL Anthology papers](https://aclanthology.org/2025.semeval-1.297) (UNVERIFIED snippets).
- Team Anotheroption (open-source-only track): text-to-SQL + text-to-code, self-correction, RAG, end-to-end module, ablated per component; 80% on eval phase, top-13 of 38 in open-source section; models cited include Llama 3, Codestral, Qwen2, MiniMax-01 — [arXiv 2506.09657](https://arxiv.org/abs/2506.09657).
- Spider 2.0: AgentSM (claude-4-sonnet) 62.0 on Spider 2.0-Lite with gold tables (paper, 2026-01; note the "gold tables" setting) — [AgentSM](https://arxiv.org/pdf/2601.15709). Spider 2.0-DBT: Databao Agent 58.82, SignalPilot 51.56 (digest, 2026-05) — [digest](https://buttondown.com/theaggregate/archive/ai-benchmark-digest-2026-05-03/). Aggregator lists Spider-Agent-Extended+GPT-5 at 40.40 (metric unclear, UNVERIFIED) — [benchmarklist](https://benchmarklist.com/benchmarks/spider_2_0/). ReFoRCE earlier SOTA 35.83 Snow / 36.56 Lite (2025).
- Benchmarks for table understanding: TableBench (AAAI 2025, 18 fields), MMTU (NeurIPS 2025, 28K questions, 25 tasks), TableEval (real-world multilingual, multi-structure), MiMoTable (COLING 2025 spreadsheets) — [MMTU](https://papers.nips.cc/paper_files/paper/2025/hash/63b3985ad1dade84a34d581590e5f608-Abstract-Datasets_and_Benchmarks_Track.html); [TableEval](https://arxiv.org/html/2506.03949v3); [MiMoTable](https://arxiv.org/pdf/2412.11711).

### Inferences
- A sub-15B open model is competitive on DABstep easy tasks (about 70%) but trails frontier agent stacks on hard tasks (32.8% vs 41-45%).
- DataBench is largely solved by strong closed-model pipelines (about 95%); open-model-only pipelines are in the 65-80% range, which is the realistic band for a small-model setup.

### Gaps
- Current (2026) DABstep, Spider 2.0 and DA-Code leaderboards, TableBench and WikiTQ/TabFact SOTA: not retrieved.
- Exact model sizes of the DataBench winners and open-source-track top scores: overview tables not readable.
- No 2026 business-data QA benchmark confirmed (only a 2026 synthetic private-equity multi-sheet dataset, [arXiv 2603.07316](https://arxiv.org/pdf/2603.07316), contents not reviewed).

## 2. Winning architectures and measured component gains

### Takeaway
Winners are code-generation agents (pandas or SQL) with a plan-execute-verify-refine loop and explicit data profiling. The one clearly measured ablation I found: removing DS-STAR's data-file analyzer drops DABstep hard accuracy to 26.98% (from 45.2% headline).

### Cited Findings
- DS-STAR loop: file analysis -> Planner -> Coder -> LLM Verifier -> Router (add step or fix step), up to 10 rounds; hard tasks averaged 5.6 rounds vs 3.0 for easy; over half of easy tasks solved in round 1 — [Google Research](https://research.google/blog/ds-star-a-state-of-the-art-versatile-data-science-agent/).
- DS-STAR ablation: no data-file analyzer -> 26.98% on hard DABstep; no router (only append steps) hurt both easy and hard — same source.
- Aestar pipeline stages (example selection, SQL, extraction, verification, iterative refinement) took accuracy from 26% baseline to 70.5% — [Aestar](https://preview.aclanthology.org/setup/2025.semeval-1.292).
- Anotheroption combined text-to-SQL, text-to-code, self-correction, RAG and structured checklists against multi-hop errors; claims open-source models become comparable to proprietary ones — [arXiv 2506.09657](https://arxiv.org/abs/2506.09657).
- DeepAnalyze trains an 8B model with agentic RL-style curriculum for data science (training approach not verified here) — [arXiv 2510.16872](https://arxiv.org/pdf/2510.16872).
- Snowflake Cortex Analyst describes an agentic multi-step system with semantic search over literals and verified queries as accuracy drivers — [Snowflake engineering blog](https://www.snowflake.com/en/blog/engineering/snowflake-cortex-analyst-behind-the-scenes/).

### Inferences
- Data profiling and a verifier/router loop are the best-evidenced components; retry loops cost rounds (hard tasks about 2x), which matters under a 4-LLM-step budget.

### Gaps
- Per-component gains for ensembling, value sampling and answer-type formatting: not found with numbers (Aestar and Anotheroption ablations exist in the full papers, not read).

## 3. Messy spreadsheets: header detection, merged cells, locale, subtotals

### Takeaway
There is little controlled evidence isolating cleaning steps. Related work targets encoding (SpreadsheetLLM) or manipulation (TableLLM, MMTU), not locale numbers or subtotals.

### Cited Findings
- SpreadsheetLLM: structural-anchor compression, about 25x compression, 78.9% F1 on table detection (+12.3% over prior best); Chain of Spreadsheet gave +22% over GPT-4 baseline on QA (secondary summaries) — [arXiv 2407.09025](https://arxiv.org/html/2407.09025v2); [summary](https://huggingface.co/papers/2407.09025.md).
- TableLLM targets office-style spreadsheet operations via generated Python (insert, delete, update, query, merge, chart) — [TableLLM](https://arxiv.org/html/2403.19318v1).
- MiMoTable, TableEval and MMTU include real-world structured/multilingual tables — links in section 1.
- A practical tool heuristic: header = row with most text cells in first 20 rows (min 3); does not rebuild stacked headers or merged header cells (product doc, not a study) — [instafill](https://instafill.ai/agent-tools/read-spreadsheet-records).

### Inferences
- Header detection and unit/locale normalization are best done deterministically before the LLM; no published source gives measured gains.

### Gaps
- Nothing found on SpreadsheetBench, Table-GPT, TabAgent, Chain-of-Table, Data Interpreter scores (not searched), nor on subtotal-row removal, text-encoded numbers or locale-specific dates and numbers as controlled variables.

## 4. Product architectures and semantic layers

### Takeaway
Vendors consistently report that curated semantic models/business definitions raise accuracy, but figures are vendor-reported and on internal sets.

### Cited Findings
- Snowflake (2024-08-29): 90%+ SQL accuracy on an internal 150-question set; single-prompt GPT-4o 51%; "nearly 2x" and about 14% over another solution; four difficulty pillars: question, schema, SQL complexity and business-semantics alignment — [Snowflake blog](https://www.snowflake.com/en/engineering-blog/cortex-analyst-text-to-sql-accuracy-bi). No quantified with/without semantic model number there.
- Snowflake "agentic semantic model improvement" reports about 20% accuracy gain vs no proper semantic model across four datasets built from BIRD pairs (search snippet, UNVERIFIED) — [Snowflake](https://www.snowflake.com/en/engineering-blog/agentic-semantic-model-text-to-sql). Atlan cites 57% -> 78% (UNVERIFIED) — [Atlan](https://atlan.com/know/snowflake/cortex-analyst-vs-text-to-sql/).
- dbt Labs 2026 benchmark (ACME Insurance, 11 questions x 20 runs): Claude Sonnet 4.6 90.0% -> 98.2% with Semantic Layer; GPT-5.3-Codex 84.1% -> 100%; raw text-to-SQL on unmodeled schema 32.7% (2023) -> 64.5% (2026); out-of-scope questions get no answer (third-party summaries, dbt post not opened) — [dbt post](https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026); [Atlan](https://atlan.com/know/ai-agent/data-for-ai/text-to-sql-for-enterprise/); [Bodo reproduction](https://www.bodo.ai/blog/how-pydough-reached-100-accuracy-on-dbts-semantic-layer-benchmark).
- Databricks Genie: general text instructions, example SQL and certified/parameterized answers feed context; benchmarks are evaluation-only and never used as context; community report: out-of-box 6/20 correct, biggest gain from preparing the data — [Databricks docs](https://docs.databricks.com/gcp/genie); [Databricks blog](https://www.databricks.com/blog/building-confidence-your-genie-space-benchmarks-and-ask-review); [community post](https://community.databricks.com/t5/genie-hub/operationalizing-a-live-genie-space-benchmarking-governance-amp/td-p/167186).

### Inferences
- A deterministic metric layer trades coverage for accuracy (0% on out-of-scope questions), so a fallback to free SQL plus abstain logic is needed.

### Gaps
- Google Conversational Analytics and Julius: not researched.

## 5. Failure categories on business-rule-heavy questions and mitigations

### Takeaway
Reported failures are about unstated business semantics and time handling, not syntax.

### Cited Findings
- Snowflake examples: wrong date reference (assumed Christmas 2022 rather than latest), LAG over non-consecutive dates, window applied after date filter, missed client-specific metric definition (forecast accuracy), omitted requested column — [Snowflake blog](https://www.snowflake.com/en/engineering-blog/cortex-analyst-text-to-sql-accuracy-bi). Mitigations named: semantic model measures/filters, verified queries, literal search.
- Databricks mitigation loop: run benchmark, add instructions for failing metrics (e.g. "best sales rep"), rerun — [Databricks blog](https://www.databricks.com/blog/building-confidence-your-genie-space-benchmarks-and-ask-review).
- DS-STAR: multi-file hard tasks need more rounds; profiling of files is the main mitigation — [Google Research](https://research.google/blog/ds-star-a-state-of-the-art-versatile-data-science-agent/).

### Inferences
- Encoding definitions (revenue, valid orders) as views/macros plus time-parsing in code addresses the observed categories directly.

### Gaps
- No systematic taxonomy with percentages from DABstep/DataBench error analyses retrieved.
