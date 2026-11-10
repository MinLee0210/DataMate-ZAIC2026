# Small-model (<=15B) text-to-SQL: state of the art as of 2026-11-10

Method note: about 14 tool calls. Paper bodies were read through alphaXiv summaries or arXiv HTML. Raw PDFs did not parse. Many numbers below come from one table (Arctic paper Table 7). I did not reach the live BIRD or Spider 2.0 leaderboards, and I did not find direct sources for XiYan-SQL details, CHESS, Qwen3/3.5, Gemma 4 (small), Phi-4, Spider 2.0-snow/dbt for small models, or the messy-data gap for small models. These are listed under Gaps.

## 1. Current results, sizes, licences and dates (BIRD, Spider, Spider 2.0, EHRSQL)

### Takeaway
At 7B-14B the best published open recipe is OmniSQL-style SFT followed by execution-reward GRPO (Arctic-Text2SQL-R1). On BIRD dev it reaches about 69-71%, against 64% for OmniSQL SFT alone and 61.5% for Qwen2.5-Coder-14B-Instruct. Spider 2.0-SQLite stays at 12-17% for every small model. EHRSQL stays at 35-43%. Benchmark headroom at the top is closing and is partly limited by label noise.

### Cited Findings
- Arctic-Text2SQL-R1 main table (execution accuracy, greedy single sample, BIRD-dev / Spider-test / Spider2.0-SQLite / Spider-DK / EHRSQL / ScienceBenchmark / average) — [Arctic paper HTML, Table 7](https://arxiv.org/html/2505.20315v1):
  - Arctic-R1-7B: 68.9 / 88.8 / 15.6 / 81.5 / 36.7 / 51.8 / 57.2
  - Arctic-R1-14B: 70.1 / 89.4 / 16.3 / 79.4 / 40.7 / 58.2 / 59.0
  - Arctic-R1-32B: 70.5 / 88.7 / 16.3 / 80.6 / 40.1 / 60.9 / 59.5
  - OmniSQL-7B: 63.9 / 87.9 / 13.3 / 76.1 / 34.9 / 50.2 / 54.4
  - OmniSQL-14B: 64.2 / 88.3 / 12.6 / 72.9 / 39.9 / 56.9 / 55.8
  - OmniSQL-32B: 64.5 / 87.6 / 14.8 / 76.1 / 42.4 / 57.2 / 57.1
  - Qwen2.5-Coder-7B-Instruct: 50.9 / 82.2 / 4.4 / 67.5 / 24.3 / 45.2 / 45.8
  - Qwen2.5-Coder-14B-Instruct: 61.5 / 86.6 / 11.1 / 73.6 / 31.6 / 52.2 / 52.8
  - Qwen2.5-Coder-32B-Instruct: 64.5 / 87.5 / 10.4 / 78.3 / 36.4 / 54.8 / 55.3
  - DeepSeek-V3 (671B MoE): 63.2 / 85.5 / 14.8 / 72.9 / 43.2 / 56.2 / 55.6
  - GPT-4o: 61.9 / 83.2 / 17.0 / 72.9 / 44.9 / 55.5 / 55.9
  - XiYan-SQL-32B: BIRD-dev 67.0 (other columns not given)
- BIRD leaderboard figures quoted by Snowflake (blog dated 2025-05-29, comparisons as of 2025-05-20): Arctic-R1-32B 71.83, 14B 70.04, 7B 68.47. The blog does not say dev or test. The paper says the 14B model was the first open model past 70% and that the 32B beat XiYan-32B by 2.8 points — [Snowflake blog](https://www.snowflake.com/en/blog/engineering/arctic-text2sql-r1-sql-generation-benchmark/); [alphaXiv summary of Arctic paper](https://arxiv.org/abs/2505.20315). A later paper's leaderboard snapshot (2026-08-26) lists Arctic-R1 on dev at 72.20 (32B), 71.40 (14B), 70.70 (7B) — [ReToolSQL](https://arxiv.org/html/2608.27796v1). This is likely the few-shot or self-consistency submission, but the source does not say so.
- Arctic-Text2SQL-R1 was revised in January 2026 and accepted at Findings of ACL 2026. The paper is CC BY 4.0. The 7B weights are on Hugging Face as Snowflake/Arctic-Text2SQL-R1-7B — [arXiv abstract](https://arxiv.org/abs/2505.20315); [search listing of ACL anthology](https://aclanthology.org/2026.findings-acl.1345.pdf). The model licence is not verified.
- OmniSQL (Renmin Univ. and ByteDance) was submitted 2025-03-04 and revised 2025-07-13. It comes in 7B/14B/32B, fine-tuned from Qwen2.5-Coder-7B/14B/32B-Instruct. The OmniSQL-14B Hugging Face card says Apache-2.0. The GitHub README says SynSQL-2.5M is Apache-2.0 — [arXiv](https://arxiv.org/abs/2503.02240); [HF OmniSQL-14B](https://huggingface.co/seeklhy/OmniSQL-14B); [GitHub](https://github.com/RUCKBReasoning/OmniSQL). The HF card says the model supports SQLite only.
- OmniSQL reported numbers in its own paper: 7B gets 87.9 on Spider test (greedy), above DAIL-SQL+GPT-4 at 86.6. With maj@8, OmniSQL-32B gets 89.8 on Spider test and 67.0 on BIRD dev. On EHRSQL, OmniSQL-32B gets 46.8 with maj@8 against GPT-4o at 45.5. Note that the Arctic table reports EHRSQL 42.4 greedy for the same model, so these are different decoding settings — [OmniSQL alphaXiv summary](https://arxiv.org/abs/2503.02240).
- CSC-SQL (Wuhan Univ. of Technology and USTC, arXiv 2505.13271): BIRD private test EX of 71.72 for the 7B model (Qwen2.5-Coder-7B-Instruct base) and 73.67 for the 32B model (XiYanSQL-QwenCoder-32B-2412 base). The 32B gain over its base is +4.64 points. Code is at github.com/CycloneBoy/csc_sql, paper CC BY 4.0 — [arXiv](https://arxiv.org/abs/2505.13271); [alphaXiv summary](https://arxiv.org/abs/2505.13271).
- XiYan-SQL (ensemble pipeline, not a single small model): the abstract claims 75.63% on BIRD and 89.65% on Spider test, with the split not stated. Components are a schema filter, a multi-generator ensemble, and a selection model with candidate reorganisation. The page gave no parameter counts or ablations — [arXiv 2507.04701](https://arxiv.org/abs/2507.04701). XiYanSQL-QwenCoder was not found on the page.
- Newer 2026 results, all above 15B and so reference only: ReToolSQL (Gemma 4 31B, agentic RL) reports 74.32 dev EX (SFT then RL), 74.77 with self-consistency over 16, and 73.66 for RL only. Submitted 2026-08-28. The baseline is given as 71.19 in one table and 69.69 in another. No BIRD test number is reported. The paper's arXiv ID looks unusual and I could not cross-check it. The same paper lists a Gemma 4 E4B ablation, but no E4B number was extracted — [ReToolSQL](https://arxiv.org/html/2608.27796v1).
- Think2SQL (14B, Qwen2.5-Coder, RLVR): 0.602 weighted EX on BIRD dev — via [search result summary](https://arxiv.org/pdf/2504.15077). Reasoning-SQL 14B: about 72.3-72.8 on BIRD dev with a learned candidate selector — via [search result summary](https://arxiv.org/pdf/2503.23157). Both were reported by a search summariser and not checked in the papers.
- Spider 2.0 original paper: the strongest parser solved 5.7% of Spider 2.0-lite, against 91.2% on Spider 1.0 and 73.0% on BIRD — via search summary of [Spider 2.0](https://arxiv.org/html/2411.07763v2). Not checked in the source.

### Inferences
- Small-model Spider 2.0-SQLite scores (12.6-16.3) are close to GPT-4o (17.0) and DeepSeek-V3 (14.8). At this size, scale or specialisation barely moves multi-step enterprise-style tasks; the benchmark mostly measures something other than SQL generation.
- The BIRD "test" and "dev" labels are mixed across sources (68.47/70.04/71.83 from Snowflake vs 68.9/70.1/70.5 dev in the paper vs 70.7/71.4/72.2 in a 2026 leaderboard snapshot). Any number should be tagged by split and by single/multi-sample.

### Gaps
- BIRD test numbers for OmniSQL, and exact release dates and licences of the Arctic and XiYanSQL-QwenCoder weights, were not verified.
- No primary source for XiYanSQL-QwenCoder-7B/14B/32B numbers or licence, and none for CHESS (CHESS-IR+SS+CG numbers, 2024, and its small-model variants).
- No Spider 2.0-snow or dbt scores for any model of 15B or less.
- No live leaderboard check, so rankings may have moved after the snapshot dates above.

## 2. Training recipes and what gave the largest gains

### Takeaway
Three levers are measured: (a) large synthetic SFT with CoT (OmniSQL), (b) RL from a strong SQL SFT checkpoint with a simple execution reward and filtered data (Arctic), and (c) verified training labels (ReViSQL). Data quality and the starting checkpoint moved the numbers more than reward engineering.

### Cited Findings
- OmniSQL / SynSQL-2.5M: 2,544,390 (database, question, SQL, CoT) samples over 16,583 synthetic databases, built from about 19,935 web tables filtered from 1.3M. About 5M SQL queries were generated and cut to 2.5M. Pipeline: web-table-driven database generation and enhancement; complexity-aware SQL generation (4 levels); SQL-to-question back-translation in 9 language styles with a semantic-consistency selector; CoT synthesis with majority vote over execution results. Multiple open LLMs (Llama3.1, DeepSeek Coder, Qwen2.5, Qwen2.5-Coder) were used as generators. Human check on 1,000 samples: 96% databases realistic, 97% questions meaningful, 89% SQL appropriate, 86% fully correct — [OmniSQL summary](https://arxiv.org/abs/2503.02240).
- OmniSQL training: full-parameter SFT for 7B; LoRA for 14B and 32B reported in the summary. The input is `CREATE TABLE` text with column descriptions, representative values and question-relevant values. The output is CoT then SQL. Spider and BIRD train sets (with synthesised CoT) are mixed in. Ablations: SynSQL-2.5M adds an average of +8.4 points for the 7B model; removing CoT or removing SynSQL hurts on all sets; accuracy keeps rising with data scale — [OmniSQL summary](https://arxiv.org/abs/2503.02240).
- Arctic-Text2SQL-R1 recipe: GRPO, online RL, temperature 0.8, total batch 256 with 16 rollouts, update batch 128, KL beta 0.001, clip 0.2. Reward: 1 for execution match, 0.1 for executable but wrong, 0 otherwise. Learning rate, epochs and max length are not stated in the extracted text — [Arctic HTML](https://arxiv.org/html/2505.20315v1); [alphaXiv summary](https://arxiv.org/abs/2505.20315).
- Arctic training data (after filtering): BIRD-train 8,017 (from 9,428), Spider-train 6,972 (from 8,659), Spider-dev 985, Gretel-Synth-filtered 11,811. Filter rules: drop samples whose reference SQL returns empty results or runs over 5 seconds. Synthetic Gretel data got GPT-4o-written INSERT statements, then was kept only if at least one of 10 generations from a strong SFT model was correct — [Arctic HTML](https://arxiv.org/html/2505.20315v1); [alphaXiv summary](https://arxiv.org/abs/2505.20315).
- Arctic ablations (BIRD-dev / Spider-test, 14B on Qwen-coder base): BIRD+Spider only 64.9 / 86.8; adding unfiltered synthetic 64.6 / 86.4 (worse); adding model-filtered synthetic 66.5 / 88.3. 32B: Qwen2.5-Coder-32B base 64.4 / 87.3; QwQ-32B base 55.2 / 79.3; OmniSQL-32B base with online RL 67.9 / 88.2; switching to the modified OmniSQL prompt 70.5 / 88.7 (about +2.6 BIRD-dev). Online GRPO beat batch GRPO (66.6 vs 64.9 on BIRD-dev) and PPO (63.0 / 85.7 vs GRPO 64.9 / 87.7) — [Snowflake blog](https://www.snowflake.com/en/blog/engineering/arctic-text2sql-r1-sql-generation-benchmark/). The blog says finer-grained rewards encouraged shortcuts. The paper also reports failed LLM paraphrase and diversity augmentation.
- CSC-SQL recipe: GRPO via TRL, learning rate 3e-6, cosine schedule with warmup 0.1, 1 epoch, effective batch 12, input 8192 and output 1024 tokens. Reward R = R_EX + 0.1 R_Format. Both the generator and a separate merge-revision model are trained with RL. Revision-training data comes from 8 candidates per BIRD-train question from Qwen2.5-Coder-7B-Instruct. Sampling temperature 0.8 was best — [CSC-SQL summary](https://arxiv.org/abs/2505.13271).
- ReViSQL (UIUC): 2,500-instance BIRD-Platinum subset corrected by experts. Corrections touched 52.1% of SQL, 26.2% of questions and 18.2% of evidence entries; 61.1% of instances had at least one error. Training RLVR on the Platinum data gained +7.2 / +5.0 points on two clean benchmarks, while training on the 3.8x larger raw BIRD train lost 7.0 / 5.0 points. Reward shaping (VeriEQL equivalence check, 0.8 reward if refuted; penalty up to 0.2 for not using evidence) added +2.8 / +3.8 greedy. Result-only rewards had a 32.8% false-positive rate. Ignoring evidence caused 24.2% of failures under outcome-only RL and 4.3% after process rewards (small pilot samples of 33 and 23). Models trained were Qwen3-235B-A22B and Kimi-K2.6, so the recipe is a reference only. Settings: group 16, LoRA rank 32, lr 5e-5, up to 5 tool turns — [ReViSQL summary](https://arxiv.org/abs/2603.20004).
- ReToolSQL recipe (reference, 31B): SFT on rejection-sampled traces produced with a teacher that sees gold SQL, then GRPO with multi-turn SQL tool use, 16 rollouts, DAPO-style clipping (0.20 / 0.28), dynamic sampling, tool-token masking. Its reward has seven terms (max 3.8): execution 2.0, syntax 0.5, table-set linking 0.5, column Jaccard 0.5, format 0.2, non-empty 0.1, length penalty. Trained on 6,601 BIRD questions. This contrasts with Arctic's finding that simple rewards are better; the ReToolSQL weights are set heuristically with no ablation reported in the extract — [ReToolSQL](https://arxiv.org/html/2608.27796v1).

### Inferences
- Ranking of measured gains for a 7B-14B model: strong SQL SFT start plus prompt format plus filtered data (OmniSQL to Arctic: about +5-6 BIRD-dev points at 7B-14B) is larger than any inference trick (about +1 point, see section 5).
- Result-only execution rewards reward wrong-but-matching SQL, so noisy or ambiguous labels matter more than reward shape. The two sources disagree on reward complexity (Arctic: simple; ReToolSQL: seven terms), and neither runs the other's design as an ablation.

### Gaps
- Arctic learning rate, epochs and max length not extracted.
- No source found on the exact schema-linking components inside OmniSQL (it feeds the full schema plus value hints) beyond the input format above.
- XiYan-SQL and CHESS training recipes were not retrieved.

## 3. General reasoning models (8-15B) vs specialised text-to-SQL models

### Takeaway
I found no clean head-to-head of Qwen3, Qwen3.5, Gemma 4 small, or Phi-4 against OmniSQL or Arctic at equal size. What exists is indirect.

### Cited Findings
- On the same table, general Qwen2.5-Coder-14B-Instruct scores 61.5 on BIRD-dev against 64.2 (OmniSQL-14B) and 70.1 (Arctic-14B). The 7B gap is larger: 50.9 versus 63.9 and 68.9 — [Arctic HTML](https://arxiv.org/html/2505.20315v1).
- A 7B Arctic or OmniSQL model beats GPT-4o (61.9) and DeepSeek-V3 (63.2) on BIRD-dev — [Arctic HTML](https://arxiv.org/html/2505.20315v1).
- Starting RL from a reasoning general model was worse: QwQ-32B base gave 55.2 / 79.3 versus 64.4 / 87.3 for Qwen2.5-Coder-32B base under the same GRPO recipe — [Snowflake blog](https://www.snowflake.com/en/blog/engineering/arctic-text2sql-r1-sql-generation-benchmark/).
- A search summary reports SynSQL data used to train Qwen-3-8B reaching 68.84 on BIRD dev (from a SynSQL-Realistic-Eval paper, arXiv 2604.27261). I did not read the paper, so treat as unverified — [search result list](https://arxiv.org/pdf/2604.27261).
- Gemma 4 31B base is reported at 69.69-71.19 BIRD-dev EX before any text-to-SQL training. That is above all small specialised SFT models in the Arctic table, but it is 31B, over the budget — [ReToolSQL](https://arxiv.org/html/2608.27796v1).

### Inferences
- Specialised SQL SFT plus RL is worth roughly 10-18 BIRD-dev points over a non-SQL-tuned Qwen2.5-class model at 7B-14B. Newer general models (Qwen3, Gemma 4) may close part of that gap; no measurement was found. The team should measure its own target model, with and without an OmniSQL-style prompt.

### Gaps
- No source for Qwen3-8B/14B, Qwen3.5, Gemma 4 E4B/small, or Phi-4 BIRD, Spider or EHRSQL scores in thinking mode. No source on whether thinking mode helps or hurts on SQL for these models. Phi-4 not covered at all.

## 4. Benchmark accuracy vs unseen, messy, real-world databases

### Takeaway
Accuracy drops sharply from Spider 1.0 to BIRD to Spider 2.0 to enterprise data. Label noise in BIRD and Spider 2.0 puts a ceiling on what dev scores mean.

### Cited Findings
- Spider 2.0 paper: best parser at 5.7% on Spider 2.0-lite, versus 91.2% on Spider 1.0 and 73.0% on BIRD — via search summary of [Spider 2.0](https://arxiv.org/html/2411.07763v2) (not checked in the source).
- BEAVER (MIT enterprise data warehouse): the newer version reports the best agentic framework (GPT-5.2) at 10.8% EX, rising to 30.1% with oracle subtask hints. ReFoRCE with Claude-4.5-Sonnet gets 11.4% on BEAVER against 62.9% on Spider 2.0. The older version reported EX 64.4% lower than Spider and 27.6% lower than BIRD — via search summary of [BEAVER](https://arxiv.org/html/2409.02038v3). No small-model numbers were found.
- Annotation noise: in the BIRD-Platinum audit, 61.1% of evaluated BIRD-train instances had at least one error. On the cleaned benchmark, a top system reached 93.8% (greedy) and 69% of the remaining failures (44 of 64) were question ambiguity — [ReViSQL summary](https://arxiv.org/abs/2603.20004).
- Domain shift for small models: EHRSQL scores for 7B-14B models are 35-43 against 63-70 on BIRD-dev, and Spider2.0-SQLite scores are 12-16 — [Arctic HTML](https://arxiv.org/html/2505.20315v1).
- OmniSQL motivates synthetic data by arguing public datasets lack coverage so models fine-tuned on them generalise badly to unseen domains — [OmniSQL summary](https://arxiv.org/abs/2503.02240).

### Inferences
- A rough rule from the numbers: expect a small model's score on unseen messy business data to land near its EHRSQL or Spider2.0-SQLite level, not its BIRD level. This is an inference, not a measured figure.
- Because 69% of residual errors on the cleaned set are ambiguity, extra model or sampling effort has diminishing returns there; semantics (evidence, glossary, metric definitions) matter more than SQL syntax.

### Gaps
- No measurement of 7B-15B model accuracy on real private business databases was found (only BEAVER for large agents).
- BEAVER and Spider 2.0 figures came via search summaries and were not verified in the papers.
- Nothing found specific to Vietnamese or multilingual text-to-SQL, DuckDB dialect accuracy, or messy-spreadsheet inputs (headers, merged cells).

## 5. Inference-time techniques and measured gains for small models

### Takeaway
For SQL-tuned models, plain self-consistency and value retrieval add only about 0.4-1.0 BIRD-dev points. Execution-grouped voting with a trained revision step adds more (0.7-5.5 points over majority vote, growing with sample count), but only when the reviser is RL-trained.

### Cited Findings
- Arctic: 14B 70.1 greedy; +value retrieval 70.5; +maj@8 70.6; both 70.8. 32B 70.5; 70.9; 71.2; 71.5 (up to +1.0) — [Arctic HTML](https://arxiv.org/html/2505.20315v1).
- OmniSQL: BIRD dev 32B goes from 64.5 (greedy) to 67.0 (maj@8), +2.5 for an SFT-only model, and EHRSQL 42.4 to 46.8 — [Arctic HTML](https://arxiv.org/html/2505.20315v1) for greedy; [OmniSQL summary](https://arxiv.org/abs/2503.02240) for maj@8. Voting helps SFT-only models more than RL-trained ones. This is my reading of two different sources' numbers.
- CSC-SQL (execution-grouped top-2 candidates, then a merge-revision LLM, then a second vote): +0.72 to +5.54 BIRD-dev points over plain self-consistency across models and n. Gain grows with the number of initial samples n. Example: Qwen2.5-Coder-7B-Instruct without GRPO gains +1.28 at n=4 and +4.25 at n=64. Best top-group size is 2; a size of 1 gave little or negative gain. Revision samples m beyond 4-16 add little. A 7B model with n=64 beat 14B and 32B models using plain voting. The revision model hurt unless it was GRPO-trained. Cost: about +7% inference time for a 32B model with 16 candidates — [CSC-SQL summary](https://arxiv.org/abs/2505.13271). Temperature 0.8-1.0 gave better diversity than low values.
- ReToolSQL: self-consistency over 16 samples (temperature 1.2, largest execution-result cluster) added only +0.45-0.46 points for a model that already had multi-turn execution tools, while pass@16 was 77-82 — [ReToolSQL](https://arxiv.org/html/2608.27796v1). This gap between voting (about 74.8) and pass@16 (about 81.9) shows how much a better selector could still recover.
- Prompt format is itself a lever: the modified OmniSQL prompt added about 2.6 BIRD-dev points with the same weights and training — [Snowflake blog](https://www.snowflake.com/en/blog/engineering/arctic-text2sql-r1-sql-generation-benchmark/).
- Pipelines: XiYan-SQL (schema filter, multiple generators, selection model) reports 75.63% on BIRD (split not stated), above single-model results, but at the cost of many calls — [XiYan-SQL](https://arxiv.org/abs/2507.04701). ReViSQL argues that RL on clean data can replace schema linking, candidate selection and repair pipelines; it beat the strongest open pipeline (OpenSearch) by 8.4 and 5.6 points under greedy decoding with large models — [ReViSQL summary](https://arxiv.org/abs/2603.20004).
- Residual failure types for a top RL system: omitted schema-based filters, wrong value grounding, ignored external knowledge, join and aggregation mistakes — [ReViSQL summary](https://arxiv.org/abs/2603.20004).

### Inferences
- With k=1 and no voting, a small model leaves about 0.5-2.5 points on the table from voting alone. The larger recoverable gap is pass@k minus voting (about 7 points in ReToolSQL; CSC-SQL's figure of the same kind is shown graphically in the paper, not extracted). Execution-grouped top-2 reconciliation with an RL-trained reviser is the best-measured way to close part of it.
- An execution-only reward and a plain voting loop are both cheap to adopt; a trained reviser needs RL data and is the costlier option.

### Gaps
- No ablation found for schema linking (CHESS-style or XiYan schema filter) on a 7B-14B model; no isolated figure for repair loops on execution errors; no measurements of selector/ranker models at small scale beyond CSC-SQL.
- Interaction between thinking mode and voting for Qwen3-class models is unmeasured in the sources found.
