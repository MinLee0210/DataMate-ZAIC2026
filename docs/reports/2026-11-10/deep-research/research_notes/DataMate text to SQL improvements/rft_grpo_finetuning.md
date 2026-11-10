# RFT, self-distillation and execution-reward RL for 7-14B text-to-SQL / data-analysis agents (as of 2026-11-10)

Research depth note: about 12 search/fetch calls. Several items come from search-engine summaries and not from the primary page; those are flagged "(secondary)". Nothing here was found for the Vietnamese or messy-spreadsheet setting specifically.

## 1. Rejection-sampling FT / STaR / ReST-EM / self-distillation: gains, data size, generalisation

### Takeaway
The general RFT literature (ReST-EM) shows that filtering a model's own samples by a binary correctness check beats fine-tuning on human data alone and transfers to held-out tasks, but the first iteration gives most of the gain and small problem sets overfit. I found no paper that cleanly measures execution-filtered self-distillation SFT on unseen databases at the 3k-example scale, so that part is an evidence gap.

### Cited Findings
- ReST-EM (generate samples, filter with binary feedback, fine-tune, repeat) on MATH and APPS with PaLM-2 scales favourably with model size and significantly surpasses fine-tuning only on human data. Training sets: MATH 7,500 problems, APPS-Introductory 2,342 problems; transfer checked on GSM8K and HumanEval — [arXiv 2312.06585](https://arxiv.org/abs/2312.06585), retrieved 2026-11-10 (via search summary).
- Lecture-slide summary of the same paper (secondary, verify in the paper): on APPS the first iteration gives the largest boost and further iterations can hurt because there are few training problems; method needs a reliable correctness check and can overfit with a small problem set — [Toronto course slides](https://www.cs.toronto.edu/~cmaddis/courses/csc2541_w25/presentations/bansal_%20muraleedharan_restem.pdf).
- ACE-SQL (arXiv 2606.05906, mid-2026) cold-starts Qwen3-8B by self-distillation SFT: the model's own generator samples are kept only if their execution result matches gold, then a joint RL stage starts from that checkpoint. Unseen-database results were not in the snippets I saw — [ACE-SQL](https://arxiv.org/pdf/2606.05906) (secondary summary).
- ExeSQL (EMNLP 2025 Findings) uses execution-based rejection sampling with best-of-N for dialect text-to-SQL, followed by offline preference learning — [arXiv 2505.17231](https://arxiv.org/pdf/2505.17231).
- ReToolSQL: SFT on rejection-sampled traces from a privileged teacher then agentic RL; only a news summary was found, unseen-database performance described as unknown — [summary](https://aiunderstanding.org/news/retoolsql-trains-a-31b-model-to-verify-and-repair-sql-through-tool-use) (unverified, no primary paper read).
- Reasoning-SQL: SFT on the 14B model lowers Spider-DK and Spider-Syn below the base model for 7B, while the RL model improves on base (14B Spider-Syn: RL 72.63, SFT 61.02, base 72.14; Spider-DK: RL 73.03, SFT 69.15, base 71.4) — [arXiv 2503.23157](https://arxiv.org/html/2503.23157). This is direct evidence that plain SFT on a fixed train split can hurt out-of-distribution schemas.

### Inferences
- With about 3,000 labelled pairs, expect the first RFT round to carry most of the benefit; a second round on the same questions is likely to add little (extrapolated from ReST-EM APPS note).
- Because SFT-only models degraded on shifted benchmarks in Reasoning-SQL, use a held-out set of whole train businesses (split by business, not by question) to detect schema overfitting.

### Gaps
- No quantitative RFT-for-text-to-SQL result at the 300-3,000 example scale on unseen databases found.
- No evidence found for self-distillation on data-analysis agents (multi-step pandas/SQL tool use) with Vietnamese questions.

## 2. LoRA/QLoRA vs full fine-tuning, hyperparameters, time and memory

### Takeaway
At small data scale LoRA is the sensible choice: it forgets less, and for instruction fine-tuning high-rank LoRA can match full fine-tuning. Unsloth says 9B bf16 LoRA needs about 22 GB, so one 32 GB RTX 5090 fits a 9B; a 14B bf16 LoRA is tight on 32 GB and was not documented in what I found.

### Cited Findings
- LoRA vs full FT on Llama-2-7B (code and math): full FT generally learns more; in instruction fine-tuning high ranks can match full FT; for code full FT forgets substantially more than any LoRA config; code CPT at 20B tokens: full FT 0.545 vs LoRA r=256 0.617 on the forgetting metric as quoted — [arXiv 2405.09673](https://arxiv.org/pdf/2405.09673). Note these are 7B Llama-2 results from 2024, not Qwen.
- Unsloth Qwen3.5 bf16 LoRA VRAM: 0.8B 3 GB, 2B 5 GB, 4B 10 GB, 9B 22 GB, 27B 56 GB, 35B-A3B 74 GB; full fine-tuning about 4x more VRAM — [Unsloth Qwen3.5 fine-tune docs](https://unsloth.ai/docs/models/qwen3.5/fine-tune), retrieved 2026-11-10.
- Unsloth says 4-bit QLoRA is not recommended for any Qwen3.5 model (dense or MoE), use bf16 LoRA — same source.
- Unsloth example SFT config (27B): r=16, alpha=16, dropout 0, targets q/k/v/o/gate/up/down, batch 1 x grad-accum 4, warmup 10, max_steps 100 (demo), adamw_8bit, max_seq_length 2048, gradient checkpointing "unsloth", seed 3407 — same source. Demo values, not tuned.
- Reasoning-SQL SFT baseline: lr 1e-5 cosine, batch 32, 3 epochs, 8 H100 — [arXiv 2503.23157](https://arxiv.org/html/2503.23157).
- Qwen3.5 sizes: 397B-A17B launched 2026-02-16; 122B-A10B, 35B-A3B, 27B mid sizes; 9B, 4B, 2B, 0.8B late Feb 2026 — [Qwen3.5 GitHub README via search](https://backiee.wasmer.app/https_github_com/QwenLM/Qwen3_5) and a third-party guide ([nxcode](https://www.nxcode.io/resources/news/qwen-3-5-developer-guide-api-visual-agents-2026)). No Qwen3.5 14B was found, so under a 15B cap the Qwen3.5 candidate is the 9B (27B exceeds the cap); Qwen3-14B is the other option.

### Inferences
- Two 5090s (2 x 32 GB): a 9B bf16 LoRA at 22 GB per Unsloth fits on one card with headroom for longer SFT sequences; run two experiments in parallel, one per GPU. 14B bf16 LoRA (weights about 28 GB) will not fit on one 32 GB card with activations; it needs sharding across both cards or 8-bit base weights (my estimate, not sourced).
- 3,000 examples x about 1-2k tokens x 2-3 epochs is a small job (order of an hour on a 9B LoRA; my estimate, no source timed this).

### Gaps
- No measured wall-clock for Qwen3.5-9B / Qwen3-14B LoRA on RTX 5090 found.
- No Qwen-family LoRA-vs-full ablation at 3k-sample scale found.

## 3. GRPO / RLVR with execution rewards for SQL

### Takeaway
Published GRPO gains are real but come with large data and compute (thousands of questions, 8-64 H100s). Small, short runs on one consumer GPU have a documented null result. A few-GPU-hour GRPO run is technically feasible but is unlikely to give a measurable gain with outcome-only reward on about 3k questions.

### Cited Findings
- Arctic-Text2SQL-R1: GRPO with a simple reward (1 for execution match, 0.1 for valid executable SQL, 0 otherwise). Starting from OmniSQL checkpoints: BIRD-dev 7B 63.9 to 68.9, 14B 64.2 to 70.1, 32B 64.5 to 70.5; Spider-test 87.9 to 88.8 (7B). Training data: BIRD-train 8,017, Spider-train 6,972, Gretel-Synth-filtered 11,811 after filtering. 8 nodes of H100-80GB (64 GPUs); a few hours for 7B, up to 2.5 days for 32B. Batch 256, 16 rollouts, temp 0.8, KL beta 0.001, clip 0.2. Step count and lr not reported. Training on BIRD alone averaged 1.4 points lower than adding Spider and synthetic data. Starting from Qwen2.5-Coder-32B-Instruct gave 64.9 BIRD-dev vs 70.5 from OmniSQL start — [arXiv 2505.20315](https://arxiv.org/html/2505.20315v2).
- Majority voting (8 samples) or value retrieval added up to about 1 point on top of the RL model (32B 70.5 to 71.5 combined) — same source.
- Reasoning-SQL: Qwen2.5-Coder 3B/7B/14B, about 8,026 filtered BIRD train questions, GRPO lr 1e-6, batch 32, 3 epochs, 6 completions per prompt, 8 H100; composite reward (execution weight 3, LLM judge 2, syntax, schema Jaccard, bigram Jaccard, format weight 1). 7B: base 58.73 to RL 64.01 EX (SFT 61.53); 14B: SFT 63.75, RL 65.31; 14B Spider 81.43 RL vs 75.04 SFT vs 79.40 base — [arXiv 2503.23157](https://arxiv.org/html/2503.23157).
- SQL-R1 paper: 7B model, 88.6 Spider and 66.6 BIRD EX, reward includes execution, length, syntax, format — [arXiv 2504.08600](https://arxiv.org/abs/2504.08600) (via search summary and Arctic's comparison table). A separate Hugging Face repo summary says a Qwen3-4B-Base LoRA SFT+GRPO run used 300 optimisation steps, 4 candidates, 12,885 RL records with only a 2.32-point Spider gain over SFT and no BIRD gain — [HF j2521402/SQL-R1](https://huggingface.co/j2521402/SQL-R1) (secondary, unclear whether it is the paper's authors; treat as unverified).
- CSC-SQL: GRPO on both generation and revision models; about 69.2 BIRD-dev with a 7B Qwen2.5-Coder, 71.7 with a 70B — [arXiv 2505.13271](https://arxiv.org/pdf/2505.13271) (via search summary).
- Think2SQL: reward-density and advantage-scaling study; Arctic compares its reward with Think2SQL's precision/recall/cardinality reward — [arXiv 2504.15077](https://arxiv.org/html/2504.15077v3).
- Negative result: Qwen2.5-Coder-1.5B SFT LoRA then TRL GRPO (8 generations, no reference model, lr 1e-6, 400 steps, 2h42m on one 24-32 GB GPU), 494 questions selected with pass-rate between 0.2 and 0.8. BIRD slice 36.9 to 36.2, Spider slice 82.0 to 83.0, within roughly +-4% noise. First attempt on Spider-train had about 70% of groups with zero reward variance. Author attributes published gains to process rewards (unverified opinion) — [HF slmsql-grpo-v2](https://huggingface.co/Anurich/slmsql-grpo-v2). Single practitioner, 1.5B model, small eval slices.
- A 2026 paper argues strict execution matching is sparse and a partial-credit reward gives about 5% over binary GRPO on BIRD — [arXiv 2603.16161](https://arxiv.org/pdf/2603.16161) (secondary summary; not read).
- Reported single-GPU GRPO feasibility: a Qwen2.5-7B LoRA GRPO run in under 2 h on one GPU; a 7B QLoRA GRPO on a 16 GB laptop GPU took 16 h with 2 generations — [search results](https://tech-insider.org/?p=44511), [HF blog](https://huggingface.co/spaces/junaid0600/sql-db-engineer-agent/blob/main/blog_post.md) (unvetted blog-level sources).

### Inferences
- Reward-variance filtering (keep questions with 0.2 to 0.8 pass rate under the current model) is a prerequisite; with 3k questions only a fraction will qualify, which limits RL data to maybe several hundred (estimate from the negative result's 494 of 1,367 = 36%).
- Cheaper alternative with the same signal: RFT / best-of-k distillation (section 1), which needs only sampling plus SFT.

### Gaps
- No published GRPO result at about 3k questions with a 9-14B model on 1-2 consumer GPUs.
- Arctic step count and lr not reported; SQL-R1 hardware not verified.

## 4. Fine-tuning hybrid thinking models (Qwen3 / Qwen3.5): pitfalls and keeping reasoning

### Takeaway
The main documented risks are chat-template mismatch and losing the reasoning format when training on answer-only data. Unsloth's guidance is to keep at least 75% reasoning examples if you want to preserve reasoning, and to reuse the exact training chat template at inference.

### Cited Findings
- Unsloth: to preserve reasoning, mix reasoning-style examples with direct answers keeping at least 75% reasoning examples, or train fully on reasoning-style output — [Unsloth Qwen3.5 docs](https://unsloth.ai/docs/models/qwen3.5/fine-tune).
- Unsloth: if an exported model performs worse in another runtime, the most common cause is a wrong chat template or EOS token; use the same template as training — same source.
- Qwen3 report: non-thinking samples retain an empty thinking block to keep format consistent; thinking is the default — [arXiv 2505.09388](https://arxiv.org/pdf/2505.09388).
- Qwen3.5 serving: the enable_thinking toggle must be passed inside chat_template_kwargs to take effect (GitHub issue report) — [pi-agent issue 2020](https://github.com/earendil-works/pi/issues/2020) (single issue report).
- Qwen3-Thinking-2507-type checkpoints always generate reasoning regardless of the flag — [vLLM forum](https://discuss.vllm.ai/t/thinking-token-limit-setting/2400/12) (forum reply).
- Reasoning-SQL 2025: dropping reasoning output in GRPO gave about 2% gain in the text, i.e. reasoning is not always beneficial for SQL — [arXiv 2503.23157](https://arxiv.org/html/2503.23157) (paper text and tables disagree in places).
- Arctic: starting from QwQ-32B (a reasoning model) gave 55.2 BIRD-dev vs 64.9 from Qwen2.5-Coder-32B-Instruct under the same GRPO recipe — [arXiv 2505.20315](https://arxiv.org/html/2505.20315v2).

### Inferences
- Self-generated traces keep the model's own `<think>` style, so RFT on its own thinking-mode outputs (filtered by execution correctness) avoids the format shift that teacher-written or answer-only data would cause. Store the full assistant turn including the think block, and train with the same template and enable_thinking value used at inference.
- Verify with a no-fine-tune baseline that the template used for data rendering reproduces the base model's outputs before training.

### Gaps
- No source found quantifying "thinking collapse" after LoRA SFT on Qwen3.5 specifically; the 75% rule is vendor guidance without a published ablation.

## 5. Tooling support (Unsloth, TRL, LLaMA-Factory, Axolotl, verl, vLLM, fp8)

### Takeaway
Unsloth, verl and vLLM all have Qwen3.5 support in some form, but versions are moving and conflicting: the Unsloth page says vLLM 0.16.0 did not support Qwen3.5, while other sources show vLLM serving Qwen3.5 with the qwen3 reasoning parser. Pin and test versions before committing.

### Cited Findings
- Unsloth: Qwen3.5 needs transformers v5; GRPO/GSPO works with fast_inference=False; merged 16-bit export for vLLM via save_pretrained_merged merged_16bit; GGUF export; the page said vLLM 0.16.0 does not support Qwen3.5 and advised waiting or using nightly — [Unsloth docs](https://unsloth.ai/docs/models/qwen3.5/fine-tune). This may be stale as the Qwen3.5 README gives a vllm serve command with `--reasoning-parser qwen3` ([README mirror](https://backiee.wasmer.app/https_github_com/QwenLM/Qwen3_5)); contradiction not resolved.
- verl v0.8.0 notes list Qwen3.5 FSDP GRPO training support and Qwen3.5 sequence parallelism; v0.7.1 had Qwen3.5 via mbridge; an issue thread reports a vLLM-init conflict with transformers versions and a maintainer suggested SGLang — [verl v0.8.0 release](https://newreleases.io/project/github/verl-project/verl/release/v0.8.0), [verl PR 5381](https://github-users.yhajoa.workers.dev/verl-project/verl/pull/5381).
- SkyRL note: Qwen3.5 needs vllm 0.17.0, torch 2.10.0, transformers >= 5.3.0 — [SkyRL PR](https://gh.r-mj.com/FrontierCS/SkyRL/pull/1/files) (different project).
- vLLM serves LoRA adapters via `--lora-modules name=path` and supports runtime loading with VLLM_ALLOW_RUNTIME_LORA_UPDATING — [vLLM LoRA docs](https://docs.vllm.ai/en/stable/features/lora/); Qwen3.5-4B example: [Tinker docs](https://tinker-docs.thinkingmachines.ai/tutorials/deployment/lora-adapter/). One Qwen3-VL adapter failed to load in vLLM while the merged model worked — [Unsloth issue 3560 mirror](https://www.goodfirstissue.org/unslothai/unsloth/issues/3560).

### Inferences
- Safest path for determinism and for the offline-inference rule: merge the LoRA into bf16 weights, then serve the merged checkpoint (avoids adapter-loading bugs).

### Gaps
- Not found: TRL, LLaMA-Factory and Axolotl Qwen3.5 support status; fp8 quantisation-after-merge accuracy for Qwen3.5 or its vLLM/5090 (Blackwell) support; 5090-specific training issues.

## 6. Risks: overfitting to train shops, determinism after merge, licence and parameter cap

### Takeaway
Overfitting to train schemas is the main quality risk; licence is fine (Apache 2.0) but check the 15B cap, which excludes Qwen3.5-27B and larger.

### Cited Findings
- Qwen3.5 open-weight models are Apache 2.0 per the official README (retrieved via search; check each HF repo's LICENSE) — [Qwen3.5 README mirror](https://backiee.wasmer.app/https_github_com/QwenLM/Qwen3_5).
- Qwen3.5 release dates: 2026-02-16 onward, so all sizes are public before 2026-10-01 — same source and [nxcode guide](https://www.nxcode.io/resources/news/qwen-3-5-developer-guide-api-visual-agents-2026).
- SFT on a fixed train split lowered out-of-distribution scores (Spider-DK/Syn) in Reasoning-SQL; training on BIRD alone generalised worse than BIRD+Spider+synthetic in Arctic (average 54.3 vs 55.7 for OmniSQL-7B) — sources in sections 1 and 3.
- Small eval slices are noisy: about +-4% on 149-200 questions — [HF slmsql-grpo-v2](https://huggingface.co/Anurich/slmsql-grpo-v2).
- Qwen3.5-27B bf16 LoRA needs 56 GB, and its parameters exceed 15B — [Unsloth docs](https://unsloth.ai/docs/models/qwen3.5/fine-tune).

### Inferences
- Determinism after merge: no source found; plan to verify by running the merged model twice with fixed seed and temperature 0 under the final vLLM settings, and compare to the unmerged run (merge numerics in bf16 can shift greedy outputs).
- Use business-level held-out validation, and compare against the untouched base model on that split; accept a tuned model only if it beats base by more than the noise band.

### Gaps
- Nothing found on determinism of merged LoRA weights in vLLM.
- The model-parameter counting for Qwen3.5 (vision tower included in 9B?) was not checked; confirm against docs/MODELS.md rules.

## 7. Synthetic question/SQL generation with a teacher and execution verification

### Takeaway
Large synthetic SQL corpora clearly help (OmniSQL), but I found no published yield rate for execution-based verification, and the project rules limit teacher use to scripts/datagen and the dev phase.

### Cited Findings
- SynSQL-2.5M: 2,544,390 samples over 16,583 synthetic databases, each with database, question, SQL and chain-of-thought; SQLite only — [OmniSQL-7B model card](https://huggingface.co/seeklhy/OmniSQL-7B), [arXiv 2503.02240](https://arxiv.org/pdf/2503.02240).
- OmniSQL-7B: average 61.2% over nine datasets vs 52.8% for Qwen2.5-Coder-7B-Instruct (+8.4), Spider test 87.9% greedy, 88.9% with majority voting — same sources.
- Arctic filtered training data by dropping empty-result references and queries over 5 seconds (about 1,400 BIRD and 1,700 Spider removed) and by using a pass-rate filter style elsewhere; Gretel-Synth-Filtered contributed 11,811 examples — [arXiv 2505.20315](https://arxiv.org/html/2505.20315v2).
- Reasoning-SQL removed 1,402 of 9,428 BIRD train questions flagged as incorrect by LLM judges (8,026 remain) — [arXiv 2503.23157](https://arxiv.org/html/2503.23157).
- Pass-rate filtering example: of 1,367 held-out questions sampled 8 times, 494 uncertain, 502 always-fail, 184 always-pass — [HF slmsql-grpo-v2](https://huggingface.co/Anurich/slmsql-grpo-v2).

### Inferences
- About 15% of BIRD train labels were judged wrong or unusable; expect label noise in the 3k pairs too, so execution-verified RFT samples (agreeing with the label) double as a label-cleaning step.

### Gaps
- No reported teacher-generated yield (fraction surviving execution check) found; no evidence on synthetic data for Vietnamese questions.

## Overall decision-relevant summary (inference)
- Cheap, likely worthwhile: RFT (sample k per train question with the target model, keep execution-correct traces, optionally prefer shorter or majority-agreeing ones), LoRA r=16-64 bf16 on Qwen3.5-9B on one 5090, 1-2 epochs, hours not days; validate on held-out businesses.
- Uncertain: GRPO. Published successes use 8-64 H100 and 15-20k questions; the one small-scale replication found a null result. If tried, start from the RFT checkpoint, filter to questions with 0.2-0.8 pass rate, use partial-credit reward.
- Unverified before committing: Qwen3.5 version stack (transformers 5, vLLM version, verl), fp8 after merge, determinism of merged weights.
