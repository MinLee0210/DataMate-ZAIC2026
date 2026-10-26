# Data agents, Google Conversational Analytics, and what DataMate takes from them

Date: 2026-10-26. Scope: architecture choices for DataMate (docs/PROJECT.md). Sources at the end;
claims about papers come from their abstracts and project pages, not a full read.

## 1. What a "data agent" is, and which level we build

The HKUST-led survey *A Survey of Data Agents: Emerging Paradigm or Overstated Hype?*
(arXiv:2510.23587) argues that "data agent" is used for very different systems. It proposes six
levels of autonomy modelled on SAE J3016 driving levels, from L0 (manual) to L5 (generative, fully
autonomous). It places the current frontier at the **L2 → L3** step, from procedural execution
(a pipeline designed by humans, with LLM calls at fixed points) to autonomous orchestration
(the agent plans its own workflow).

**DataMate is deliberately L2.** The competition gives a 14B model, ≤ 4 LLM steps per question,
6 hours and a metric where a wrong answer costs −1. An L3 agent that plans its own loop spends steps
and adds variance, and both cost PA here. Autonomy is useful offline, though: the synthetic-data
teacher (§4) is an L3-style deep agent that runs only in development.

Related surveys: *Table Question Answering in the Era of LLMs* (arXiv:2510.09671) unifies TQA tasks
and methods. A study of LLM table agents (arXiv:2507.10281) reports a gap between academic benchmarks
and real-world tables, larger for open-source models. That supports spending effort on deterministic
ingest of messy files (H1).

## 2. Google Conversational Analytics (CA) architecture

Components, from Google's documentation:

| CA concept | What it is | DataMate equivalent |
|---|---|---|
| Data agent | Authored context + data source connections + a reasoning engine with tools (SQL, Python, charts) | `services/qa` LangGraph pipeline |
| Structured context | Per table: `description`, `synonyms`, `tags`; per field: `name`, `description`, `synonyms`, `tags`, sample values | **Schema card**, auto-authored at ingest (`modules/context/schema_card.py`), rendered as YAML |
| System instructions (YAML) | `system_instruction`, `tables[].fields[].aggregations`, `relationships[]` (join type, columns), `glossaries[]` (term, description, synonyms), `additional_descriptions[]` | `sql_agent.md` + skills (`business-metrics` = glossary, `ranking-rules`, `time-expressions`) |
| Verified ("golden") queries | `example_queries[]`: a natural-language question + SQL, optional typed `parameters` | Synthetic (question, SQL) pairs from the teacher (`scripts/datagen/`), for few-shot retrieval |
| User functions (BigQuery UDFs) | Described routines the agent may call | **Semantic layer**: DuckDB views and macros from the rulebook (`assets/semantic/`) |
| Context versioning | `stagingContext` / `publishedContext` / `lastPublishedContext` | Git + `docs/EXPERIMENTS.md` |
| Output stream | text, data, chart, schema, citations, progress | One typed answer; the trace (SQL, votes) goes to `$WORK_DIR/trace.jsonl` |
| Stateful / stateless chat | Multi-turn history or independent calls | Stateless: one question per call |

Google recommends filling the structured fields first and using system instructions only for what
they cannot express (business logic, joins, glossary). Our order is the same: the schema card is
generated, and the skills carry only the rulebook knowledge.

What we drop from CA: clarifying questions, charts, long-form answers, multi-turn state and open
reasoning loops. What we keep: **authored context as the main lever** and **execution-grounded
answers**.

The key difference is that CA's context is written by hand for known tables, while the private test
has unseen businesses. So in DataMate every structured-context field is *auto-authored* by
deterministic code: header text kept as `header`, sample values, ranges, null ratios, and an entity
dictionary standing in for synonyms. Hand-written knowledge is limited to what is split-wide (the
rulebook).

## 3. Text-to-SQL: candidates, voting, selection

| Method | Idea | Use in DataMate |
|---|---|---|
| ReFoRCE (arXiv:2502.00675) | Parallel generation threads, self-refinement on errors, column exploration, majority vote | Repair loop on execution errors; vote over executed results |
| CHASE-SQL (ICLR 2025) | Diverse multi-path generation + a trained pairwise selector; single-candidate accuracy is far below the best-of-n upper bound, and the gap is larger than self-consistency recovers | Diversity from prompt variants; a selector is a later option |
| N-rep (arXiv:2505.14174) | Confidence-aware: self-consistency vote first, pairwise LLM comparison only when the vote is weak; order swapped against position bias | Plan for low-agreement questions (uses the 4th LLM step) |
| CSC-SQL (arXiv:2505.13271) | Group candidates by execution result, revise the top two groups, vote again | Same grouping; vote keys are normalized typed answers |

Implications:
1. **Vote on executed, typed, normalized results, not on SQL text.** Different SQL with the same
   answer should agree. `decide/vote.py` keys on (type, normalized value).
2. **Agreement is a confidence score.** PA rewards abstaining when P(correct) ≤ 0.5. We calibrate
   `tau` on dev from the trace (`scripts/eval.py` writes the PA-vs-tau curve) instead of trusting the
   model's own confidence.
3. **Diversity without sampling.** The hard rule is temperature 0, so the k candidates come from k
   prompt variants (`sql_variants.md`) with fixed seeds. The trade-off: less diversity than sampling,
   in exchange for reproducible runs.

## 4. LangGraph and deepagents

- **LangGraph** (1.2.x): explicit `StateGraph` with nodes, conditional edges and a recursion limit.
  It fits a bounded pipeline: the number of LLM calls per question is known in advance.
- **deepagents** (0.7.x, pre-1.0, minor versions may break the API): `create_deep_agent(model, tools,
  system_prompt, subagents, skills, memory, backend, permissions, ...)` returns a compiled LangGraph
  agent with planning (`write_todos`), a virtual filesystem (State / Filesystem / Store / Composite
  backends), subagents (`task`), progressive-disclosure skills (`SKILL.md` with `name` /
  `description` frontmatter) and summarization.

How DataMate uses them:

| Where | Framework | Why |
|---|---|---|
| `src/services/qa/graph.py` (inference) | LangGraph `StateGraph` | Bounded: 1 generate step + ≤ 2 repair steps; deterministic; meets the 4-step rule |
| `scripts/datagen/teacher.py` (dev only) | deepagents | Open exploration is useful here: the teacher plans a question mix, probes the data with `run_sql`, and submits verified examples; API models are allowed in this folder |

Both read the **same** `src/assets/skills/*/SKILL.md`. Our skills already use the deepagents /
Agent Skills format, so the teacher and the inference agent follow the same rulebook. The teacher
sees the skills through a read-only `FilesystemBackend` (a write `deny` permission).

## 5. Takeaways for the roadmap

1. Ingest quality and the auto-authored context come first (H1); measure them per error class.
2. Calibrate abstention before tuning prompts: PA moves more from fewer wrong answers than from more
   right ones.
3. Add teacher-made verified queries as retrieved few-shot examples (CA's golden queries), chosen by
   rapidfuzz/BM25 similarity, with no embedding model.
4. Use the 4th LLM step on a pairwise selector or verifier only for low-agreement questions (N-rep).
5. Infer table relationships (join keys from names and value overlap) as CA-style `relationships`.

## Sources
- [A Survey of Data Agents: Emerging Paradigm or Overstated Hype? (arXiv:2510.23587)](https://arxiv.org/abs/2510.23587)
- [Table Question Answering in the Era of Large Language Models (arXiv:2510.09671)](https://arxiv.org/abs/2510.09671v1)
- [LLM-based table agents, benchmark vs real-world gap (arXiv:2507.10281)](https://papers.cool/arxiv/2507.10281)
- [Exploring the Landscape of Text-to-SQL with LLMs (arXiv:2505.23838)](https://arxiv.org/html/2505.23838v1)
- [ReFoRCE (arXiv:2502.00675)](https://arxiv.org/pdf/2502.00675)
- [CHASE-SQL (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/file/974ff7b5bf08dbf9400b5d599a39c77f-Paper-Conference.pdf)
- [Cheaper, Better, Faster, Stronger: N-rep (arXiv:2505.14174)](https://arxiv.org/html/2505.14174v1)
- [CSC-SQL (arXiv:2505.13271)](https://arxiv.org/html/2505.13271v1)
- [Conversational Analytics API: architecture and key concepts](https://docs.cloud.google.com/gemini/docs/conversational-analytics-api/key-concepts)
- [Conversational Analytics API: data agent system instructions](https://docs.cloud.google.com/gemini/data-agents/conversational-analytics-api/data-agent-system-instructions)
- [Conversational Analytics API: authored context for BigQuery](https://docs.cloud.google.com/gemini/data-agents/conversational-analytics-api/data-agent-authored-context-bq)
- [BigQuery conversational analytics overview (verified queries)](https://docs.cloud.google.com/bigquery/docs/conversational-analytics)
- [Looker conversational analytics data agents](https://docs.cloud.google.com/looker/docs/2606/conversational-analytics-looker-data-agents)
- [deepagents customization guide](https://docs.langchain.com/oss/python/deepagents/customization)
- [deepagents `create_deep_agent` reference](https://reference.langchain.com/python/deepagents/graph/create_deep_agent)
- [deepagents README](https://cdn.jsdelivr.net/gh/langchain-ai/deepagents@main/README.md)
