# Models

Every model used at inference is declared here before it is used (CLAUDE.md, rule 5).
Budget: ≤ 15B parameters in total across all inference models (MoE counts all experts), weights
public before 2026-10-01, licence allows use.

## Inference (counts toward the budget)

| Role | Model | Params (total) | Released | Licence | Status |
|---|---|---|---|---|---|
| SQL agent (target) | `Qwen/Qwen3-14B` | 14.8B | 2025-04 | Apache-2.0 | candidate, default in `src/config.py` |

**Budget used: 14.8B / 15B.** Nothing else fits next to a 14B model: a verifier or an embedding
model would require switching the target to an ~8B model (see docs/PROJECT.md §6).

Alternatives to compare on dev200 with the same pipeline before locking the target:
`Qwen/Qwen2.5-Coder-14B-Instruct` (14.7B), `seeklhy/OmniSQL-14B` (~14.8B, text-to-SQL tuned). Verify
the parameter count and release date from the model card before adding a row above.

Serving: vLLM, bf16, tensor parallel 2 on 2× RTX 5090, thinking disabled
(`chat_template_kwargs.enable_thinking=false`), settings pinned in `scripts/vllm.sh`.

## Development only (not at inference, no budget)

| Role | Where | Model |
|---|---|---|
| Hosted copy of the target (dev_free) | `src/` through `LLM_BASE_URL` | OpenRouter `qwen/qwen3-14b` |
| Teacher for synthetic train data | `scripts/datagen/` only | `DATAGEN_MODEL` (default `openai/gpt-5.5`) |

The teacher runs on train businesses only, never on public_test or private_test.
