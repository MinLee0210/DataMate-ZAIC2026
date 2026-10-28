# Models

Every model used at inference is declared here before it is used (CLAUDE.md, rule 5).
Budget: ≤ 15B parameters in total across all inference models (MoE counts all experts), weights
public before 2026-10-01, licence allows use.

## Inference (counts toward the budget)

| Role | Model | Params (total) | Released | Licence | Status |
|---|---|---|---|---|---|
| SQL agent (target) | `Qwen/Qwen3-14B` | 14.8B | 2025-04 | Apache-2.0 | candidate, default in `src/config.py` |
| evaluation candidate | `Qwen/Qwen3.5-9B` | 9.65B (incl. vision encoder) | 2026-02-27 | Apache-2.0 | dev200 bake-off 2026-10-28; bf16 weights, fp8 at load; vLLM `Qwen3_5ForConditionalGeneration`, `enable_thinking` |
| evaluation candidate | `google/gemma-4-12B-it` | 11.96B (incl. audio encoder) | 2026-05-23 | Apache-2.0 | dev200 bake-off 2026-10-28; bf16 weights, fp8 at load; vLLM `Gemma4UnifiedForConditionalGeneration`, `enable_thinking` |
| evaluation candidate (coder) | `Qwen/Qwen2.5-Coder-14B-Instruct` | 14.7B | 2024-11-06 | Apache-2.0 | dev200 run 2026-10-28 (after public 0.26 drop of Qwen3.5-9B); bf16 weights, fp8 at load; no thinking; 32,768 context |
| same model, official FP8 weights | `Qwen/Qwen3-14B-FP8` | 14.8B (same model) | 2025-04-28 | Apache-2.0 | served on the pod and planned for 2x RTX 5090: 16.3 GB instead of 29.6 GB |

**Budget used: 14.8B / 15B.** Nothing else fits next to a 14B model: a verifier or an embedding
model would require switching the target to an ~8B model (see docs/PROJECT.md §6).

Next to evaluate (agreed 2026-10-28; declared in the table above, first run 2026-10-28):
`Qwen/Qwen3.5-9B` (9.65B incl. vision encoder, 2026-02-27, Apache-2.0) and
`google/gemma-4-12B-it` (11.95B, 2026-05-23, Apache-2.0). Survey and other options:
[reports/2026-10-28/llm-candidates](reports/2026-10-28/llm-candidates/report.md).

Alternatives to compare on dev200 with the same pipeline before locking the target:
`Qwen/Qwen2.5-Coder-14B-Instruct` (14.7B), `seeklhy/OmniSQL-14B` (~14.8B, text-to-SQL tuned). Verify
the parameter count and release date from the model card before adding a row above.

Serving: vLLM, settings pinned in `scripts/vllm.sh`: the official FP8 checkpoint (`TP=1` on one
48 GB GPU, `TP=2` on 2× RTX 5090; any quantization is allowed by rule 2), prefix caching, `max-model-len` 49152 with static YaRN
(factor 1.5 over the native 32768). Thinking is off for plain calls and on for dataAgent's
reasoning steps (`ANALYZE_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": true}}`).

## Development only (not at inference, no budget)

| Role | Where | Model |
|---|---|---|
| Hosted model (dev_free, train only) | `src/` through `LLM_BASE_URL` | DeepSeek `deepseek-flash`; OpenRouter `qwen/qwen3-14b` |
| Teacher for synthetic train data | `scripts/datagen/` only | `DATAGEN_MODEL` (default `openai/gpt-5.5`) |

The teacher runs on train businesses only, never on public_test or private_test.
