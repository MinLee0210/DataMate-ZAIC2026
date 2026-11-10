# Vietnamese text-to-SQL / table QA and public material on Zalo AI Challenge 2026 DataMate (as of 2026-11-10)

## (a) Vietnamese text-to-SQL and table QA datasets, models and results

### Takeaway
Public Vietnamese text-to-SQL work is thin: ViText2SQL (2020, Spider translation), two community HF translations (ViSpider, ViBIRD) and one 2025 few-shot prompting paper. I found no public benchmark of Qwen/Gemma/Llama/Vistral/SeaLLM/Sailor on Vietnamese SQL, none on English-vs-Vietnamese prompting for SQL, and none on accent-stripped input for text-to-SQL.

### Cited Findings
- ViText2SQL (EMNLP Findings 2020) is the first public large-scale Vietnamese text-to-SQL dataset, a manual translation of Spider (questions, schema, SQL values). Word segmentation helped both baselines (EditSQL, IRNet) and PhoBERT beat XLM-R. Licence: research/education only, no redistribution of original or modified data. — [arXiv 2010.01891](https://arxiv.org/pdf/2010.01891); [dataset repo mirror](https://gh.mise.run.place/VinAIResearch/ViText2SQL)
- ViSpider (about 11,840 items; translations from humans, GPT few-shot and a fine-tuned Qwen2.5-7B translator, `hoadm/qwen25-spider-translator-vi`) and ViBIRD (10,962 train+dev items, question and evidence translated) exist as community HF datasets by user hoadm. Licences not checked. — [ViSpider](https://huggingface.co/datasets/hoadm/vispider/blob/main/README.md); [ViBIRD](https://huggingface.co/datasets/hoadm/vibird/blob/main/README.md)
- ViR2 (VJSTE, 2025/26): unsupervised two-stage few-shot example selection (semantic retrieval, then beam-guided POS-based re-ranking). On ViText2SQL it reports 23.33% EM and 87.83% component F1, up to 5 EM points above Random, Skill-KNN, ASTRES, DICL. The page does not name the LLMs and reports no prompt-language comparison. — [VJSTE](https://vietnamscience.vjst.vn/index.php/vjste/article/view/1364); [PDF](https://vietnamscience.vjst.vn/index.php/vjste/article/download/1364/603/2926)
- Diacritics: one classical source states 95% of Vietnamese words carry diacritics and 80% of those are ambiguous without them; restoration systems reach about 96-97% accuracy (2017, MT-based). Only classical restoration work was found, nothing LLM or SQL specific. — [arXiv 1709.07104](https://arxiv.org/pdf/1709.07104)

### Inferences
- Exact-match numbers on translated Spider are not comparable to DataMate (messy spreadsheets, execution-match scoring); they mainly say Vietnamese SQL generation was hard for 2020-era and few-shot setups.
- The design choice (English prompts/skills with Vietnamese data, accent folding for matching) has no published support or refutation I could find; it must be settled by the team's own dev evals.

### Gaps
- No public numbers for Qwen3/3.5, Gemma, Llama, Vistral, SeaLLM, VinaLLaMA, PhoGPT, Viet-Mistral, Sailor on Vietnamese text-to-SQL or table QA (searches returned nothing).
- No Vietnamese table-QA dataset beyond the Spider/BIRD translations found.
- No evidence on English vs Vietnamese prompting, chat spelling/teencode, phonetic entity matching, number/date formats, or lunar calendar handling in the literature.

## (b) Zalo AI Challenge 2026 DataMate: official info, repos, approaches

### Takeaway
Rules and timeline are confirmed only through press/aggregator pages and a team repo; I could not read the official challenge site. Public GitHub repos from other teams exist, mostly early-stage designs; the only concrete leaderboard number found is a baseline of 0.019. Common design: LLM plans or writes SQL/Python, deterministic code computes, abstain when evidence is weak.

### Cited Findings
- Tracks: LifeMate (spoken Vietnamese to tool calls) and DataMate (Vietnamese questions over provided data such as sales tables, inventory, unstandardised records; agent must find the data, compute correctly, and refuse when data cannot support a conclusion). — [QUASA, 2026-11-06, citing VnExpress and Zalo](https://quasa.io/vi/media/zalo-ai-challenge-hut-1600-doi-han-nop-giai-phap-con-den-16-11)
- Timeline (Vietnam time): start 26/10/2026; 1,600+ teams by 2/11; Public Test submission (training code, test code, model) before 23:59 16/11; team changes locked 17/11; private test set released 20/11, public ranking provisional until verified; final submission before 23:59 23/11; two finalists per track expected 2/12; final ranking 12/12. Prizes: 12,000 USD total, per track 3,500 (1st) and 2,500 (2nd). Max 5 per team. — [QUASA](https://quasa.io/vi/media/zalo-ai-challenge-hut-1600-doi-han-nop-giai-phap-con-den-16-11)
- Over 1,000 teams after 72 hours (page returned 403, only search snippet seen; unverified). — [vietnam.vn](https://www.vietnam.vn/en/zalo-ai-challenge-2026-vuot-moc-1000-doi-thi-sau-72-gio-khoi-tranh)
- Repo `dakiemdarktharr/NoSleepClub_zalohacks_datamate` (licence file present, type not shown; 0 stars): research/roadmap/offline eval harness. One shared backbone for planner, code generator and critic; tables kept out of context, answers computed by SQL/Python over full data; typed contracts for Vietnamese business terms, grain, units, time; separate missing data from true zero; GEPA-style prompt search and ACE-style lessons before a freeze. No model chosen yet. Reports official public score 0.01900 for baseline v1 (41 answers, 959 abstentions, 02/11/2026). States constraints: offline, models total at most 15B, weights public before 01/10/2026, at most 6 h for full private run. — [GitHub](https://github.com/dakiemdarktharr/NoSleepClub_zalohacks_datamate)
- Repo `Long-uit/datamate` (no licence stated): planned neuro-symbolic agent, six modules: ingestion with forward-fill and dedup into SQLite; date resolution via `as_of_date` and `calendar.csv`; BM25 plus fuzzy entity matching; feasibility gate; code synthesis with Qwen2.5-Coder-14B-Instruct on vLLM, T=0; sandbox with at most 2 repair rounds; normaliser (NFC, lowercase, diacritics kept) and calibrated abstention. Design only, no scores. — [GitHub](https://github.com/Long-uit/datamate)
- Metric as described by teams: Penalized Accuracy, +1 correct, 0 abstain, -1 wrong. — [Long-uit/datamate](https://github.com/Long-uit/datamate), [NoSleepClub repo](https://github.com/dakiemdarktharr/NoSleepClub_zalohacks_datamate)
- Other repos listed by search but not read (verify before use): [pvananh2805/DataMate-Zalo_AI](https://github.com/pvananh2805/DataMate-Zalo_AI) (404 on fetch), [Vincent-1512/ZALO_AI_CHALLENGE_2026](https://github.com/Vincent-1512/ZALO_AI_CHALLENGE_2026), [dinhkhoi124/DateMate](https://github.com/dinhkhoi124/DateMate), [phamchivy/Zalo-AI-Challenge-2026](https://github.com/phamchivy/Zalo-AI-Challenge-2026), [thanhtrung665/zalo-ai-challenge-2026](https://github.com/thanhtrung665/zalo-ai-challenge-2026). Search summary (unverified) says several use "LLM translates, code computes", JSON query-plan executors, teencode normalisation, time resolution and voting. Event news: [techsignin](https://www.techsignin.com/261026-zalo-ai-challenge-2026/).
- Past editions, process lessons (2022): winners mostly had prior Kaggle/Zindi-type experience; teams split tasks by strength; one team (Cool Water) said it deliberately overfit the public leaderboard to mislead rivals and won on the private test as a comeback; final ranking also involved an advisory board review at presentation. — [Znews](https://znews.vn/quan-quan-zalo-ai-challenge-2022-thang-nho-kinh-nghiem-va-chien-thuat-post1388291.html)
- 2025 edition: about 1,060 teams; winners CtelAI (CMC Telecom, RoadBuddy) and a UIT/HCMUS team (AeroEyes). News only, no method write-ups or private-vs-public numbers. — [VietnamNet](https://vietnamnet.vn/en/cmc-telecom-s-young-talent-triumphs-at-zalo-ai-challenge-2025-2475280.html), [UIT](https://en.uit.edu.vn/article/uit-students-crowned-champions-zalo-ai-challenge-2025)

### Inferences
- Public repos corroborate the architecture class used by most teams (plan/SQL by LLM, deterministic compute, abstention); no public evidence of a team with a high score yet. A baseline of 0.019 shows heavy abstention scores near zero, so the public leaderboard is likely low overall (inference from one data point).
- Private set is released 20/11 and public ranking is "provisional until verified", so some public-to-private shift is expected; the 2022 anecdote shows it has happened before, but it is a single self-reported claim.

### Gaps
- Official challenge site (rules, data format, exact scorer, leaderboard) not accessed; leaderboard standings not found.
- No Facebook, Reddit, Zalo community, Kaggle or Hugging Face discussions found; no blog write-ups of DataMate approaches.
- No systematic data on public-vs-private shifts in Zalo/AIVN challenges beyond the 2022 anecdote.
- Licences of the repos above are not confirmed (none stated or not shown).
