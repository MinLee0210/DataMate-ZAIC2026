# System design review: template → DataMate

Date: 2026-10-26. Method: the system-design framework (requirements → high-level design → deep
dive → scale and reliability → trade-offs), applied to the code as forked from
`ai-app-project-template`, against docs/PROJECT.md and CLAUDE.md.

## 1. Requirements

**Functional.** For each question (business package, colloquial Vietnamese text, `as_of_date`),
write one JSONL line `{id, type, answer}` with a typed answer, `unanswerable`, or `abstain`.

**Non-functional.**

| Requirement | Source | Consequence for the design |
|---|---|---|
| PA: +1 / 0 / −1 | PROJECT §2 | Calibrated abstention is a first-class component (`decide/`) |
| Offline, local vLLM only | CLAUDE rule 1 | `config.py` refuses a non-local URL when `FINAL_MODE=1` |
| ≤ 15B params in total | rule 5 | One 14B model; no embedding model, no verifier model |
| ≤ 6 h including model load | PROJECT §3 | Time budget in `__main__` (default 4.5 h, then abstain) |
| Rerun within 0.03 PA | rule 8 | Temperature 0, fixed seeds, fixed vLLM settings, deterministic tie-breaks |
| Incremental output | rule 7 | Append, flush and fsync each line |
| ≤ 4 LLM steps per question | CLAUDE workflow | Bounded LangGraph: 1 generate + ≤ 2 repair |
| `/data` read-only | rule 6 | Ingest cache in `$WORK_DIR`; DuckDB opened read-only for queries |

**Constraints.** Two weeks to final submission, one codebase for both phases, unseen businesses in
the private test, dataset layout not yet known.

## 2. Evaluation of the template as found

| Area | Template | Fit |
|---|---|---|
| Layering (routes → services → modules/data/utils) | Clean, documented | **Keep** |
| Prompts and skills as files, loaded by `BaseAgent` | Yes, with path-traversal checks | **Keep**; the skill format already matches deepagents / Agent Skills |
| Lazy LLM client, tests with a fake LLM | Yes | **Keep** |
| Request-driven FastAPI `/chat` | Main entrypoint | **Wrong shape**: the competition is a batch job. Kept `/health`; `/ask` for debugging only |
| Postgres + Milvus datasources | Optional | **Remove**: not used; no embedding model in the budget |
| LLM call | No seed, no temperature, no base URL | **Gap**: no determinism or local endpoint |
| Answers | Free text | **Gap**: no typed answers, scorer or decision policy |
| Config | API key + model | **Gap**: no offline guard, paths or policy knobs |
| Dockerfile | API image | **Gap**: needs vLLM, model weights, batch entrypoint |

Verdict: the structure is sound and was kept. The runtime model (request/response chat) and the
datasources were replaced.

## 3. High-level design (as built)

```
                     ┌──────────────── INGEST (once per business, cached by content hash) ──────┐
 business pkg ──────►│ readers: CSV (encoding/sep sniff) · XLSX (all sheets, merged cells)      │
 (/data, read-only)  │          · SQLite (stdlib, works offline)                                │
                     │ clean: header-row detection · snake_case ids (+ original header kept)   │
                     │        · vi/en number locale per column · day-first dates               │
                     │ → DuckDB file ─► semantic layer (rulebook views, skipped if unsupported) │
                     │             └──► schema card (YAML) + entity dict  → $WORK_DIR/ingest/   │
                     └──────────────────────────────────────────────────────────────────────────┘
 question ─► LangGraph:  prepare ──► generate ──► execute ──┬──► decide ──► submission.jsonl
             (no LLM:     (1 LLM step,  (DuckDB, read- │          (vote on typed   (append+fsync)
              time ranges,  k prompt     only, sqlglot   │           results, tau)
              entity links) variants)    guard, timeout) └─► repair (≤ 2 LLM steps) ─┘
```

Module map: `modules/ingest`, `modules/context`, `modules/timeparse`, `modules/semantic`,
`modules/agents/sql_agent.py`, `modules/format`, `modules/decide`, `data/duckdb.py`,
`data/layout.py` (the only module that knows the dataset layout), `services/ingest`,
`services/qa/graph.py`.

## 4. Deep dive: key decisions

**Bounded LangGraph at inference, deepagents only in datagen.** An open deep-agent loop
(todos, filesystem, subagents) has an unbounded step count and more run-to-run variance. Both
break hard rules (4 steps, 0.03 PA). The graph makes the step count a property of the code. deepagents
is used where autonomy pays off and APIs are allowed: the teacher in `scripts/datagen/`.

**Diversity at temperature 0.** Self-consistency normally samples at T > 0. Rule 8 fixes T = 0, so
the k candidates differ by prompt variant (direct / CTE-structured / filters-first), each with its
own fixed seed. Failed candidates count against agreement, so a question where 2 of 3 queries crash
is not answered on one vote.

**Vote keys are typed, normalized results.** `(type, value)`, with strings lowercased and NFC,
and int and float merged, so equivalent SQL agrees. Ties go to the first variant (deterministic).

**Safety of generated SQL.** sqlglot allows exactly one SELECT/UNION statement; DuckDB is opened
read-only with `enable_external_access=false`; each query gets its own cursor with an interrupt
timer and a row cap.

**Deterministic pre-processing (H3).** Time expressions are resolved in Python (week = Monday–Sunday,
"tháng M" = latest month M not after `as_of_date`, chat abbreviations). Entities are matched by
rapidfuzz on folded text with a phonetic map (`ph→f`, `k→c`, `z→d`), so "cà fê sữa" links to
"Cà phê sữa".

**Number locale per column.** "350.000" is ambiguous. The column decides: if its unambiguous values
are Vietnamese-formatted (`1.200.000`), "350.000" is read as 350000.

**Errors become abstain.** Any exception in a question is logged and becomes `abstain` (0), never a
crash and never a guess.

## 5. Scale and reliability

- **Throughput.** N is unknown. If N = 2,000, the 4.5 h budget gives about 8 s per question. Three
  sequential ~300-token generations from a 14B model on TP=2 take a few seconds, and repairs add
  more. If N is much larger: send the k candidates concurrently (vLLM batches them). That needs a
  determinism check first, because batch composition can change logits; test vLLM's batch-invariance
  option on the target GPU.
- **Prompt size.** The schema card can grow with wide multi-sheet workbooks; `max-model-len` is
  16k. Revisit: prune the card to tables and columns linked to the question when it exceeds a token
  budget.
- **Reliability.** Incremental fsync'd output, `--resume`, a per-question try/except, a time budget,
  an ingest cache keyed by content (a rerun recomputes nothing and gives identical tables).
- **Observability.** `$WORK_DIR/trace.jsonl` holds candidates, SQL, errors, votes, agreement and
  seconds for every question; the scorer reads it for the tau curve.

## 6. Trade-offs

| Decision | Chosen | Alternative | Why / cost |
|---|---|---|---|
| Orchestration | Fixed LangGraph | deepagents loop | Bounded and reproducible; gives up adaptive exploration |
| Candidate diversity | Prompt variants, T = 0 | Sampling, T > 0 | Required by rule 8; less diverse, so agreement is optimistic, which tau calibration absorbs |
| Execution | DuckDB SQL | pandas / Python sandbox | Safe, fast, checkable; some questions may need Python (later, ≤ 1 step) |
| Confidence | Vote agreement | Verifier model / logprobs | No budget for a second model; agreement is cheap and execution-grounded |
| Context | Auto-authored YAML | Hand-written per business | Private businesses are unseen; only split-wide knowledge is hand-written |
| Entities | rapidfuzz + phonetic map | Embeddings | No embedding model in the budget; deterministic |
| SQLite ingest | stdlib sqlite3 | DuckDB sqlite extension | The extension downloads at first use, which fails offline |

## 7. Open items, and what to revisit as the system grows

1. **Dataset layout.** `src/data/layout.py` assumes `questions.jsonl` + `businesses/<id>/`. Fix it on
   the first look at the data. Also the answer JSON shapes (percent units, boolean, table), the
   abstain/unanswerable `answer` value, and the week start.
2. **Rulebook.** Fill `skills/business-metrics` and `assets/semantic/*.sql`.
3. **Calendar.** The lunar calendar is ingested as table `lunar_calendar` when the split has
   `calendar.*`; lunar phrases are not parsed in Python yet.
4. **Few-shot verified queries** from the teacher (CA golden queries), retrieved by similarity.
5. **4th LLM step**: a pairwise selector or verifier on low-agreement questions only (N-rep).
6. **Relationships**: infer join keys and add them to the schema card.
7. **Docker**: pin the vLLM image for Blackwell, bake the weights, `make rerun-check` on the GPU.
