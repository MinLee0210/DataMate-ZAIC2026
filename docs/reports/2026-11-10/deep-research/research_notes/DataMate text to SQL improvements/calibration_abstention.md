# Calibration, selective prediction and abstention for code/SQL-executing LLM agents (as of 2026-11-10)

Method note: about 11 tool calls (alphaXiv discovery plus arXiv abstract fetches, all read 2026-11-10). Most numbers come from abstracts only; full-text tables were not read except TrustSQL. Items marked UNVERIFIED are not backed by a fetched source.

## 1. What estimates P(correct) for text-to-SQL / code answers, with AUROC and risk-coverage numbers

### Takeaway
A July 2026 selective-prediction study finds that reasoning-based verification (LLM judges, ensembled across providers) beats black-box consistency and log-prob signals (AUROC about 0.82 vs 0.61-0.68). Self-consistency alone gives no valid low-risk subset in that study. Trajectory-feature classifiers (Sentinel) show a concrete gain under a penalised metric.

### Cited Findings
- On text-to-SQL (correct = same execution result as the reference), an LLM judge gets AUROC 0.72 (GPT-4o-mini) and 0.78 (Claude); a two-provider ensemble gets 0.82 with ECE 0.03. — [What Predicts Correctness in Text-to-SQL? (arXiv 2607.06799, 2026-07-07)](https://arxiv.org/abs/2607.06799)
- Same study: black-box signals (string, structural and execution self-consistency, schema relevance, executability) plateau at 0.61-0.68; string self-consistency is the best at 0.675; white-box log-prob 0.67. — [arXiv 2607.06799](https://arxiv.org/abs/2607.06799)
- Same study: fine-tuned verifiers reach about 0.77-0.79 in-distribution but about 0.66 on unseen schemas. The ensemble answers 27% of questions at 24% selective risk; self-consistency offers no valid low-risk subset. — [arXiv 2607.06799](https://arxiv.org/abs/2607.06799)
- Sentinel (classifier over reasoning, generated code and DB outputs; decides at pre-run, mid-trajectory and delivery; thresholds by Chow's rule) on EHRSQL: reliability score +0.08 to +0.24 at low error cost (refuse-all = +0.03); delivered-answer accuracy 54% to 69% as coverage falls 84% to 55%; at high error cost the unmonitored agent scores -3.02, Sentinel +0.03. No AUROC or feature list on the abstract page. — [arXiv 2610.04156 (2026-10-02)](https://arxiv.org/abs/2610.04156)
- Execution-consistency scores are biased by the oracle used to label correctness: with a stricter test-suite oracle, held-out risk is 2.73-10.23 points above the certificate's own-label risk; expert labels show 17.2-20.0 points risk at a nominal 0.10 level; every consistency score ranks better under the oracle that built its clusters (16/16). Recommendation: evaluate a consistency score under an oracle that did not build it. — [arXiv 2609.25938 (2026-09-22)](https://arxiv.org/abs/2609.25938)
- Reasoning mode concentrates errors: wrong answers of two independent samples coincide more often with reasoning on (10/10 dataset-scale comparisons); answer log-prob predicted correctness without reasoning but predicted errors with reasoning; none of 280 method-dataset-model combos beat plain majority vote after correction; a six-signal learned combination gave no out-of-domain gain. — [arXiv 2609.32035 (2026-09-25; single author, 0 votes, treat cautiously)](https://arxiv.org/abs/2609.32035)
- TrustSQL penalised metric RS(c): +1 correct (or correct abstention), 0 abstain on feasible, -c for wrong SQL or any SQL on an infeasible question. Best pipeline under c=10 was generator + error-detector (CLSP→SQLPrompt→ErrorP) at 46.7 on EHRSQL, 51.4 ATIS, 45.8 Advising; at c=N nobody beat abstain-all on ATIS/Advising/EHRSQL. Abstain-all scores 50% there because half of questions are infeasible. — [TrustSQL (arXiv 2403.15879)](https://arxiv.org/html/2403.15879v6)
- Related 2026 papers surfaced but not read in detail: TraceSQL reference-free verification ([2608.17795](https://www.alphaxiv.org/abs/2608.17795)); Confidence Reasoning Graphs for agents ([2610.07948](https://www.alphaxiv.org/abs/2610.07948)); agent confidence from internal representations ([2609.09448](https://www.alphaxiv.org/abs/2609.09448)); PremiseSQL abstention benchmark ([2610.22158](https://www.alphaxiv.org/abs/2610.22158)).

### Inferences
- At the DataMate rule (+1/0/-1, break-even P=0.5), the 0.82-AUROC ensemble judge setting is the best-supported signal, but it used API judges; with one local <=15B model, judge quality will likely be lower (not tested in the sources).
- Agreement among k samples is a weak sole signal for SQL (AUROC about 0.68), and reasoning models make it weaker; combine it with other features rather than rely on it.
- Evaluate any consistency-based confidence against labels it did not help produce (e.g. a separate scorer or independent computation path).

### Gaps
- No AUROC for execution-result clustering / semantic entropy specifically on code/SQL agents was verified beyond the 2607.06799 aggregate.
- Sentinel's feature set and AUROC not retrieved (abstract page only).
- EHRSQL 2024 top-team scores and methods not retrieved (the overview abstract has none); only PromptMind (2nd place, LLM ensemble, no scores on abstract page) is noted: [arXiv 2405.08839](https://arxiv.org/abs/2405.08839).

## 2. Verbalised confidence of small reasoning models and fixes

### Takeaway
Verbalised confidence from RL-trained reasoning models is systematically overconfident. A linear probe on the hidden state is far better calibrated, and unsupervised/cheap recalibration exists, but these need weights access (fine for local vLLM/HF) and calibration data.

### Cited Findings
- Verbalised confidence of reasoning models is overconfident; it tracks willingness to commit rather than correctness; post-hoc rescaling rarely transfers. A linear probe on the hidden state between CoT and answer gives ECE 5-38x lower than verbalised on four factual-QA benchmarks and two model families; Probe-SD fine-tuning on Qwen3-14B cuts in-domain ECE 0.178 to 0.024, out-of-domain 0.542 to 0.113. The probe nearly matches majority vote for answer selection but is better for confidence than for choosing answers. — [arXiv 2609.33290 (2026-09-27)](https://arxiv.org/abs/2609.33290)
- BASC: calibrates reasoning-LLM confidence without correctness labels using agreement between an anchor and one probe response; needs as few as 2 responses per unlabeled calibration query and 1 per query at deployment; isotonic recalibration gives a distribution-free guarantee w.r.t. latent self-consistency; 5 tasks, 9 reasoning models (no metrics on abstract page). — [arXiv 2604.19444 (2026-04-21)](https://arxiv.org/abs/2604.19444)
- Further 2026 calibration work surfaced (not read): [2609.32470](https://www.alphaxiv.org/abs/2609.32470) pitfalls of verbalized confidence priors in RL; [2609.34857](https://www.alphaxiv.org/abs/2609.34857) differentiable readouts; [2610.02695](https://www.alphaxiv.org/abs/2610.02695) test-time calibration; [2605.14098](https://www.alphaxiv.org/abs/2605.14098) conformal aggregation for CoT.

### Inferences
- Do not use the model's stated confidence as P(correct) directly; at minimum fit isotonic/Platt on held-out grouped data and verify ECE near 0.5, where the decision lies.
- A hidden-state probe or logistic regression on trace features is plausible within 15B local; transfer to unseen databases is the risk (the SQL verifier numbers above fall from 0.78 to 0.66 on unseen schemas).

### Gaps
- No Platt/isotonic/conformal numbers specific to code or SQL agents were found for small (<=15B) models.

## 3. Which cheap features are most predictive

### Takeaway
Not established by a direct source. The only fetched evidence: sample agreement (string 0.675 AUROC), executability and schema relevance sit in the 0.61-0.68 band individually; judge verification is stronger. Sentinel used trajectory and output features but the list was not retrieved.

### Cited Findings
- Individual black-box signals (execution consistency, executability, schema relevance) each in 0.61-0.68 AUROC. — [arXiv 2607.06799](https://arxiv.org/abs/2607.06799)
- Trajectory-derived classifier over reasoning, code and DB outputs improves reliability score under penalties. — [arXiv 2610.04156](https://arxiv.org/abs/2610.04156)
- Answer log-prob flips sign (predicts errors) when reasoning mode is on. — [arXiv 2609.32035](https://arxiv.org/abs/2609.32035)

### Inferences
- Features named in the assignment (SQL error count/retries, empty/NULL results, literal-not-in-data warnings, answer type, cardinality, entity-match distance, independent-path agreement) are plausible but I found no source quantifying them. Treat as hypotheses to test with a grouped-CV logistic regression on your own dev runs.
- Avoid raw log-prob features with reasoning models (sign instability).

### Gaps
- No paper found ranking those specific cheap features; this is the largest evidence gap.

## 4. Threshold choice, grouped CV, distribution shift, leaderboard overfitting

### Takeaway
Evidence is indirect: calibration labels can be biased by the oracle, verifiers lose accuracy on unseen schemas, and learned signal combinations did not transfer out of domain. This supports grouped-by-database CV and conservative thresholds.

### Cited Findings
- Fine-tuned verifier AUROC drops about 0.77-0.79 to about 0.66 on unseen schemas. — [arXiv 2607.06799](https://arxiv.org/abs/2607.06799)
- Certificates calibrated on one label oracle understate held-out risk by 2.73-10.23 points. — [arXiv 2609.25938](https://arxiv.org/abs/2609.25938)
- Six-signal learned combination gave no out-of-domain gain. — [arXiv 2609.32035](https://arxiv.org/abs/2609.32035)
- Sentinel picks thresholds by Chow's rule optimised against the penalised score; optimal behaviour changes strongly with error cost (abstain nearly everything at high cost). — [arXiv 2610.04156](https://arxiv.org/abs/2610.04156)

### Inferences
- With +1/0/-1 the Chow threshold is P>0.5, but because estimates are overconfident on unseen databases, a margin above 0.5 (tune by grouped CV, report the PA-vs-tau curve and choose a plateau, not the peak) is prudent. Unverified by a direct source.
- A small leaderboard gives noisy PA; pick the threshold on dev CV and avoid re-tuning on leaderboard feedback.

### Gaps
- No paper on leaderboard-threshold overfitting found.

## 5. Majority-vote efficiency

### Takeaway
Adaptive stopping can cut samples several-fold with negligible loss; but diversity gains are limited for reasoning models and weighted voting rarely changes the majority outcome.

### Cited Findings
- Adaptive-Consistency: up to 7.9x fewer samples with under 0.1% average accuracy drop, 17 datasets (reasoning and code), 3 LLMs. — [arXiv 2305.11860](https://arxiv.org/abs/2305.11860)
- Weighted voting agreed with majority vote on 98.5% of problem-method pairs; reasoning cut distinct answers to 0.43-0.65x. — [arXiv 2609.32035](https://arxiv.org/abs/2609.32035)
- Confidence-weighted voting works with a well-calibrated confidence (Probe-SD); probe selection nearly matches majority vote. — [arXiv 2609.33290](https://arxiv.org/abs/2609.33290)
- Newer adaptive/ranking self-consistency papers surfaced, not read: [2609.38931](https://www.alphaxiv.org/abs/2609.38931), [2608.24590](https://www.alphaxiv.org/abs/2608.24590), [2606.05054](https://www.alphaxiv.org/abs/2606.05054), [2605.07654](https://www.alphaxiv.org/abs/2605.07654).

### Inferences
- Sequential stopping (stop when first 2-3 samples agree on the executed result) is a time-budget saver; the unanimous-early-stop sample set also yields a free high-confidence tier.

### Gaps
- Prompt-variant vs temperature diversity: no verified source. Optimal k for SQL: none found.

## 6. Penalised-accuracy competitions

### Takeaway
TrustSQL and EHRSQL 2024 are the closest analogues; the strongest pipelines paired a generator with a separate error/abstention detector, and under severe penalties abstaining everything was hard to beat.

### Cited Findings
- TrustSQL result pattern above (generator + ErrorP detector best at c=10; no method beats abstain-all at c=N). — [arXiv 2403.15879](https://arxiv.org/html/2403.15879v6)
- EHRSQL 2024 shared task: eight teams completed out of 100+ applicants. — [arXiv 2405.06673](https://arxiv.org/abs/2405.06673)
- Entries: LG AI/KAIST self-training with pseudo-labeled unanswerable questions ([2405.11162](https://www.alphaxiv.org/abs/2405.11162)); ProbGate probabilistic threshold filtering plus error handling ([2404.16659](https://www.alphaxiv.org/abs/2404.16659)); PromptMind LLM ensemble, 2nd place ([2405.08839](https://arxiv.org/abs/2405.08839)). Winner/scores not verified.

### Inferences
- A two-stage design (answer, then a separate verifier/abstainer) with an error-detector is the best-supported pattern.

### Gaps
- Final EHRSQL 2024 leaderboard and exact winner method not retrieved; SemEval/NeurIPS abstention-aware competitions beyond these not searched.

## Cross-cutting caveats
- Several 2026 papers are very recent, low vote counts, unreviewed preprints; numbers come from abstracts via a summarising fetch tool, so quote with care.
