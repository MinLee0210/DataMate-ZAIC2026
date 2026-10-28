# Which LLMs can run DataMate within the competition rules

Date: 2026-10-28. Scope: open models that could replace or be compared with the current target
(`Qwen/Qwen3-14B`, served as the official FP8 checkpoint). Method below; every figure comes from the
Hugging Face API or the model card on that date. Nothing here has been run on our data yet: this is
a shortlist for a dev200 / holdout200 bake-off (PLAN.md T13).

## 1. What a model must satisfy

Competition rules (portal, "Rule" tab, items 2, 3, 7):
- **≤ 15B parameters in total** across every model used at inference; a mixture-of-experts model
  counts **all** experts. A vision or audio encoder shipped in the checkpoint counts too.
- **Weights public before 2026-10-01**, under a licence that permits this use. Quantization allowed.
- Runs **offline** in our Docker image on **2× RTX 5090** (32 GB each) within 6 h, model loading
  included.

What our pipeline needs (dataAgent, NOTES.md 2026-10-27/28):
- **Vietnamese** questions, often colloquial and without accents.
- **SQL (DuckDB) and short pandas**, written from a schema card.
- **Strict JSON** replies, and a **thinking mode** that can be switched per call: thinking raised
  dev200 PA from 0.43 to 0.55 on deepseek-flash.
- **≥ 40k context**: public_test prompts reach about 28k tokens before thinking.
- Works at **temperature 0** (reproducibility rule 8), served by **vLLM 0.32**.

## 2. Method
1. Hugging Face API: the 500 most downloaded, liked and trending `text-generation` models; every
   model of 39 organisations (Qwen, Google, Microsoft, Meta, Mistral, NVIDIA, DeepSeek, IBM, AI2,
   LG, Zhipu, OpenBMB, Snowflake, Tencent, ServiceNow, Vietnamese and SEA groups, …), newest first;
   name searches for model families (Qwen3.5/3.6/3.8, Gemma 4, Ministral 3, Nemotron, Phi, gpt-oss,
   text-to-SQL models, Vietnamese models).
2. Kept: 1.5B-15.5B parameters (safetensors total of the original, not of a quantized copy, whose
   count is misleading), created before 2026-10-01, an instruct or reasoning variant.
3. Read the model card of the main candidates for thinking, context, languages and vLLM support.

Caveats: `createdAt` is the repository date, close to but not always the public release date; licence
fields marked `other` need the licence text read; parameter counts include encoders.

## 3. Shortlist

### Tier 1: general models with a thinking mode (closest to what works today)

| Model | Params | Date | Licence | Notes |
|---|---|---|---|---|
| `Qwen/Qwen3-14B` (current) | 14.8B | 2025-04-27 | Apache-2.0 | Baseline. Thinking switch per call; 40,960 context; official FP8. |
| **`Qwen/Qwen3.5-9B`** | 9.65B (incl. vision) | 2026-02-27 | Apache-2.0 | Next Qwen generation; card claims parity with Qwen3 in reasoning and coding; **201 languages**; thinking by default, switchable; 262k context; vLLM support stated. Most downloaded new model ≤ 15B (6.2 M). About 1.5× faster than 14B and leaves budget for a small helper model. |
| **`google/gemma-4-12B-it`** | 11.95B | 2026-05-23 | Apache-2.0 | Configurable thinking; 256k context; text, image, audio input; hybrid local/global attention (fast on long prompts). Gemma 4 licence is Apache-2.0 (Gemma 3 had its own). |
| `mistralai/Ministral-3-14B-Reasoning-2512` | 13.9B (13.5B LM) | 2025-10-31 | Apache-2.0 | Reasoning variant, 256k context, vLLM-first. Card recommends **temperature 1**: risky for reproducibility at temperature 0. Vietnamese not in its listed languages. |
| `ServiceNow-AI/Apriel-1.6-15b-Thinker` | 14.9B | 2025-11-28 | MIT | Strong reasoning per size, 30 % fewer reasoning tokens than 1.5. At the 15B limit: no room for anything else; confirm the exact count is ≤ 15.0B. |
| `microsoft/Phi-4-reasoning` | 14.7B | 2025-04-09 | MIT | Good at reasoning and code; English-centred, weak on Vietnamese. 32k context. |

### Tier 2: text-to-SQL specialists (strong SQL, no thinking, English-centred)

| Model | Params | Date | Licence | Notes |
|---|---|---|---|---|
| `seeklhy/OmniSQL-14B`, `-7B` | 14.8B / 7.6B | 2025-03-06 | Apache-2.0 | Trained on synthetic text-to-SQL at scale (Qwen2.5-Coder base). |
| `XGenerationLab/XiYanSQL-QwenCoder-14B-2504`, `-7B-2504` | 14.8B / 7.6B | 2025-04-28 | Apache-2.0 | Text-to-SQL fine-tunes of Qwen2.5-Coder. |
| `Snowflake/Arctic-Text2SQL-R1-7B` | 7.6B | 2025-05-22 | Apache-2.0 | RL-trained for execution accuracy; the 14B repo was not reachable (gated or removed). |
| `Qwen/Qwen2.5-Coder-14B-Instruct` | 14.8B | 2024-11-06 | Apache-2.0 | Base of most SQL specialists. |
| `internlm/JanusCoder-14B` | 14.8B | 2025-10-27 | Apache-2.0 | Code model on a Qwen3-14B base. |

These are tuned for one SQL statement from a clean schema. DataMate's hard parts are business rules,
Vietnamese and messy data, so they are a reference rather than the expected winner. They also do
not follow our JSON-plus-thinking protocol out of the box.

### Tier 3: smaller or faster options

| Model | Params | Date | Licence | Notes |
|---|---|---|---|---|
| `Qwen/Qwen3-8B` | 8.2B | 2025-04-27 | Apache-2.0 | Same family as the target, about 1.7× faster. |
| `Qwen/Qwen3.5-4B` | 4.7B | 2026-02-27 | Apache-2.0 | Tiny; useful as a verifier next to a 9B model. |
| `Qwen/Qwen3-4B-Thinking-2507` | 4.0B | 2025-08-05 | Apache-2.0 | Reasoning-only 4B. |
| `google/gemma-4-E4B-it` | 8.0B (4.5B effective) | 2026-03-02 | Apache-2.0 | On-device size, configurable thinking. |
| `mistralai/Ministral-3-8B-Instruct-2512` | 8.9B | 2025-10-31 | Apache-2.0 | |
| `ibm-granite/granite-4.2-8b` | 8.8B | 2026-08-07 | Apache-2.0 | Enterprise / tool use. |
| `nvidia/NVIDIA-Nemotron-Nano-9B-v2`, `-12B-v2` | 8.9B / 12.3B | 2025-08 | NVIDIA open model licence (read) | Hybrid Mamba; reasoning on/off. |
| `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B` | 8.2B | 2025-05-29 | MIT | Distilled reasoning; long thinking. |
| `ornith-ai/Ornith-1.5-9B` | 9.7B | 2026-08-18 | MIT | Agentic and coding benchmarks; base model not stated (same size as Qwen3.5-9B): check before use. |
| `allenai/Olmo-3-7B-Think` | 7.3B | 2025-11-18 | Apache-2.0 | Fully open; English-centred. |

## 4. Excluded

| Model | Why |
|---|---|
| `openai/gpt-oss-20b` | 20.9B total |
| `google/gemma-4-26B-A4B-it`, `gemma-4-31B-it` | MoE counts all experts: 25.8B; 31.3B |
| `Qwen/Qwen3.5-27B`, `Qwen3.6-27B`, `Qwen3.8-27B`, `Qwen3.5/3.6-35B-A3B` | 27.8B-36B |
| `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, `Nemotron-3.5-Lightning-30B-A3B` | 31.6B |
| `zai-org/GLM-4.7-Flash` | 31.2B |
| `ornith-ai/Ornith-1.5-35B-A3B`, `Qwen/Qwen3.8-Flash-Next` | 36B; 180B |
| `CohereLabs/tiny-aya-*` | CC-BY-NC licence; only 3.3B |
| Vietnamese-specific models (`SeaLLMs/SeaLLM-7B-v2.5`, `Vikhrmodels/Vistral-24B`) | Old (2024) or 24B; general multilingual models now cover Vietnamese better |
| Models released after 2026-10-01 (e.g. `Ornith-1.5-122B`, 2026-10-16) | Date rule |

## 5. Recommendation

1. **Keep `Qwen3-14B-FP8` as the target** until its dev200 and public scores with today's fixes are
   in (run in progress on 2× RTX 5090).
2. **Bake-off, same pipeline, dev200 and holdout200**, in this order:
   1. `Qwen/Qwen3.5-9B`: newest, multilingual, thinking, faster; frees about 5B of the budget.
   2. `google/gemma-4-12B-it`: different family, Apache-2.0, thinking, fast attention.
   3. `mistralai/Ministral-3-14B-Reasoning-2512`: check how it behaves at temperature 0.
   4. One SQL specialist (`OmniSQL-14B` or `XiYanSQL-QwenCoder-14B-2504`) without thinking, as a
      reference for how much SQL skill alone gives.
3. Before running any of them (CLAUDE.md rule 5): read the licence file, confirm the release date
   and parameter count from `config.json`, check vLLM 0.32 support and the chat template's thinking
   switch, and add a row to `docs/MODELS.md`.
4. Cost: each dev200 on 2× RTX 5090 takes about 20-25 minutes, about 1 USD at 2.39 USD per hour,
   plus a 16-30 GB download and about 4 minutes of vLLM start-up per model.

## Sources
- Hugging Face Hub API (`/api/models`, sorted by downloads, likes, trending, creation date), 2026-10-28.
- Model cards: [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B),
  [gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it),
  [Ministral-3-14B-Reasoning-2512](https://huggingface.co/mistralai/Ministral-3-14B-Reasoning-2512),
  [Apriel-1.6-15b-Thinker](https://huggingface.co/ServiceNow-AI/Apriel-1.6-15b-Thinker),
  [Ornith-1.5-9B](https://huggingface.co/ornith-ai/Ornith-1.5-9B),
  [OmniSQL-14B](https://huggingface.co/seeklhy/OmniSQL-14B),
  [XiYanSQL-QwenCoder-14B-2504](https://huggingface.co/XGenerationLab/XiYanSQL-QwenCoder-14B-2504),
  [Arctic-Text2SQL-R1-7B](https://huggingface.co/Snowflake/Arctic-Text2SQL-R1-7B),
  [Phi-4-reasoning](https://huggingface.co/microsoft/Phi-4-reasoning),
  [gpt-oss-20b](https://huggingface.co/openai/gpt-oss-20b).
- Competition rules: challenge.zalo.ai/portal/datamate, "Rule" tab (read 2026-10-27).
