# Offline, reproducible vLLM serving of a Qwen3.5-9B-class model on 2x RTX 5090 (as of 2026-11-10)

Note: dates are retrieval date 2026-11-10 unless a page gave its own. Many pages are "stable" docs that change over time. Items marked UNVERIFIED are not confirmed by a primary source.

## 1. vLLM versions, images, Blackwell sm_120, flags for Qwen3.5

### Takeaway
Qwen3.5-9B is supported by vLLM 0.17.0 or later with `--reasoning-parser qwen3`; `--language-model-only` frees memory for text-only use. Official images moved to CUDA 13 by about v0.20, and sm_120 (RTX 5090) support in official images is documented only by older or community reports, so it must be tested on the actual pod.

### Cited Findings
- Qwen3.5-9B card: model type `qwen3_5`, "Causal Language Model with Vision Encoder", 9B (safetensors shows ~10B, BF16), 32 layers, 262,144 native context. Card gives no architecture class name. — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B)
- Card serve command: `vllm serve Qwen/Qwen3.5-9B --port 8000 --tensor-parallel-size 1 --max-model-len 262144 --reasoning-parser qwen3`; text-only: add `--language-model-only`; MTP: `--speculative-config '{"method":"qwen3_next_mtp","num_speculative_tokens":2}'`; tools: `--enable-auto-tool-choice --tool-call-parser qwen3_coder`. Card says to use nightly vLLM and transformers main (no version numbers). — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B)
- vLLM recipe for Qwen3.5-9B: minimum vLLM 0.17.0; single-GPU BF16 `vllm serve Qwen/Qwen3.5-9B --max-model-len 262144 --reasoning-parser qwen3`; MTP via `{"method":"mtp","num_speculative_tokens":1}` (differs from card's `qwen3_next_mtp`/2); sized for a 24 GB GPU; if CUDA-graph or Mamba cache size errors occur lower `--max-cudagraph-capture-size`; disable thinking server-side with `--default-chat-template-kwargs '{"enable_thinking": false}'`. Recipe header says "8x H200" yet shows TP=1 (inconsistency). — [vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.5-9B)
- The `qwen3` reasoning parser covers Qwen3 and Qwen3.5. From Qwen3.5 the chat template puts the opening think token in the prompt, so output contains only the closing token. Tool-call tag inside thinking is treated as an implicit end of reasoning. — [vLLM qwen3 parser API doc](https://docs.vllm.ai/en/v0.20.1/api/vllm/reasoning/qwen3_reasoning_parser/)
- Qwen3.5 is a hybrid (gated delta net + attention) model: vLLM sets attention block size (528 tokens for Qwen3.5-4B on 0.19.1) to match the Mamba page size; prefix caching works on full blocks only, so short prompts get nothing (our 25k prompts are far above this). — [vLLM issue #40696](https://github.com/vllm-project/vllm/issues/40696)
- Prefix caching for the Mamba/GDN layers is "experimental" (`--mamba-cache-mode align`); default max-num-seqs 1024 can exceed the ~296 Mamba cache blocks on one GPU, giving "max_num_seqs exceeds available Mamba cache blocks"; fix: lower `--max-num-seqs`. — [vLLM Qwen3.5-122B recipe](https://recipes.vllm.ai/Qwen/Qwen3.5-122B-A10B?variant=default); [LMCache recipe](https://docs.lmcache.ai/recipes/qwen3_5.html) (secondary, via search snippet)
- Transformers bug: gated-delta-net used cached recurrent state only when seq_len==1, so multi-token continuations (e.g. chunked prefill) could restart linear layers from zero; same reported for qwen3_next. This is transformers, not confirmed in vLLM. — [transformers commit f53ca05](https://app.semanticdiff.com/gh/huggingface/transformers/commit/f53ca05d02d24372c3de27e2c59d5cf857050efb) (secondary, via search snippet)
- Docker images: default vllm-openai CUDA moved to 13.0 around v0.20.0; v0.32.0 (Oct 18, 2026) was the last with a `-cu129` tag; v0.33.0+ are CUDA 13.0 only; CUDA 13 needs driver >= 580.65.06. — [Qovery CUDA 13 migration checklist](https://www.qovery.com/blog/vllm-cuda-13-migration-checklist-kubernetes-gpu-nodes) (third-party; verify on Docker Hub); [newreleases v0.20.0](https://newreleases.io/project/pypi/vllm/release/0.20.0)
- RTX 5090 history: v0.9.0 official image lacked sm_120 kernels ([vLLM forum](https://discuss.vllm.ai/t/docker-image-vllm-vllm-openai-v0-9-0-doesnt-work-on-5090/761)); 2025 guide needed torch cu128 + source build ([vLLM forum](https://discuss.vllm.ai/t/vllm-on-rtx5090-working-gpu-setup-with-torch-2-9-0-cu128/1492)); segfault/deadlock on 5090 with 0.11.2 ([vLLM forum](https://discuss.vllm.ai/t/bug-segfault-in-pythonsymnodeimpl-and-deadlock-on-rtx-5090-blackwell-with-vllm-0-11-2/2688)). These are older than the current line.
- A March 2026 community guide runs Qwen3.5-27B NVFP4 on one 5090 with vLLM 0.17.1 plus an SM120 TMA patch (PR #36325). Single-user report. — [friendli.ai guide](https://friendli.ai/models/mconcat/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-NVFP4)
- NVFP4 MoE on SM120 has CUTLASS grouped-GEMM problems; not relevant to a dense 9B BF16/FP8 model. — [vLLM forum SM120 report](https://discuss.vllm.ai/t/sm120-rtx-pro-6000-nvfp4-moe-performance-report-qwen3-5-397b/2536)
- Issue #37714: Qwen3.5 27B+ failing with missing libcudart.so.12 (CUDA mismatch example). — [vLLM #37714](https://github.com/vllm-project/vllm/issues/37714) (content not opened)

### Inferences
- Use an official `vllm/vllm-openai:v0.3x-cu130` tag (or a pinned recent one) with driver >= 580.65; pin by digest. A 5090 pod must have a driver that supports CUDA 13 or you must use a `-cu129` tag (v0.32.0 or earlier).
- Dense 9B BF16 is ~18-19 GB, leaving ~10 GB/GPU for KV on a 32 GB card; FP8 weights (or FP8 KV) would help but add a numerics variable; none of this was benchmarked in sources.
- Start with `--language-model-only`, `--reasoning-parser qwen3`, and lowered `--max-num-seqs`.

### Gaps
- No primary source confirming the exact first vLLM release for Qwen3.5 beyond the recipe's 0.17.0 minimum, nor the exact Docker tags that run on sm_120 today; check Docker Hub and the release notes.
- fp8 quantisation / KV-cache fp8 behaviour for Qwen3.5 hybrid layers on sm_120: not found.
- Whether chunked prefill is safe for Qwen3.5 in vLLM: not found (only the transformers bug).

## 2. Determinism

### Takeaway
vLLM does not guarantee reproducibility by default; for online serving the only supported lever is batch invariance (`VLLM_BATCH_INVARIANT=1`, beta), and Qwen3.5's hybrid architecture and sm_120 are not listed as validated. Guarantees hold only on same hardware and vLLM version.

### Cited Findings
- "vLLM does not guarantee reproducible results by default"; offline: `VLLM_ENABLE_V1_MULTIPROCESSING=0` makes scheduling deterministic; online: only batch invariance. Reproducible only on same hardware and vLLM version. Seed defaults to 0 per worker in V1. — [vLLM reproducibility docs](https://docs.vllm.ai/en/stable/usage/reproducibility/)
- Batch invariance: `VLLM_BATCH_INVARIANT=1`; output independent of batch size and request order; uses deterministic kernels, disables some optimizations, disables FlashInfer, AITER, QuickReduce under TP; beta; tracking issue #27433; cost: slower than default (no numbers given). — [vLLM batch invariance docs](https://docs.vllm.ai/en/stable/features/batch_invariance/) (page footer Oct 19, 2026)
- Hardware: stable docs say compute capability >= 8.0; older docs (v0.11.1 to v0.20.2) said >= 9.0 (Hopper/Blackwell datacenter). sm_120 is not mentioned. — [stable](https://docs.vllm.ai/en/stable/features/batch_invariance/); [v0.20.1](https://docs.vllm.ai/en/v0.20.1/features/batch_invariance/)
- Validated models: DeepSeek, Qwen3 (dense, VL, MoE), Qwen2.5, Llama 3, GPT-OSS, Mistral, GLM-4 and others; "other models may work but are unvalidated" (Qwen3.5 / GDN not listed). — [stable](https://docs.vllm.ai/en/stable/features/batch_invariance/)
- TP caveat: all-reduce sizes not a multiple of 16 bytes can switch between NCCL and custom all-reduce depending on batch size, breaking invariance (hidden size not divisible by 8 for fp16/bf16). — [stable](https://docs.vllm.ai/en/stable/features/batch_invariance/)

### Inferences
- Safest determinism design: TP=1 replicas (no all-reduce), fixed `--max-num-seqs`, `VLLM_BATCH_INVARIANT=1` if it starts on Qwen3.5/sm_120 (test: same prompts at batch 1 vs full load, byte-compare), fallback to `--enforce-eager` and fixed concurrency. Qwen3.5-9B hidden size 4096 is divisible by 8, so the TP caveat would not trigger, but TP=1 avoids it anyway.
- Prefix caching, chunked prefill and fp8 are plausible sources of numeric differences; with batch invariance on, the docs imply they should be neutralised but this is not stated per feature (UNVERIFIED). Speculative decoding (MTP) adds risk; avoid.
- Sampling at temperature>0 with fixed seed: per-request `seed` is supported by vLLM, but output still depends on logits being identical (UNVERIFIED for our setup).

### Gaps
- No throughput-cost number for batch invariance; no report of it on RTX 5090 or Qwen3.5 found.
- No official statement on prefix caching / chunked prefill interaction with invariance.

## 3. Throughput planning: DP x2 (TP=1) vs TP=2

### Takeaway
For a 9B model that fits on one 32 GB card, two independent TP=1 replicas are the standard choice (no inter-GPU all-reduce, better determinism); but each replica has its own prefix cache, so a router that keeps shared-prefix requests together matters. No Qwen3.5-on-5090 benchmark numbers were found.

### Cited Findings
- `--data-parallel-size N` replicates weights; `--max-num-seqs` applies per rank; internal LB routes by running/waiting queue; `--api-server-count` for scaling frontends. — [vLLM data-parallel docs](https://docs.vllm.ai/en/stable/serving/data_parallel_deployment/)
- External load balancing: each rank a separate server; "non-MoE models can simply run as independent instances". — same page
- "Each DP engine has an independent KV cache"; current internal balancer is not KV-cache aware. — same page
- RTX 5090 has no NVLink (general hardware fact, UNVERIFIED here, not searched); TP=2 would use PCIe all-reduce.
- Forum/issue reports of TP OOM or illegal memory access on sm_120. — [search summary of vLLM forum/issues](https://discuss.vllm.ai/c/hardware-support/5) (not individually verified)

### Inferences
- Run two `vllm serve` processes (one per GPU, `CUDA_VISIBLE_DEVICES`), shard the question set deterministically (e.g. by business) so each business's shared prefix lands on one replica; this also makes the output split reproducible. Static sharding beats the internal LB for both prefix cache and determinism.
- With ~25k-token prompts and BF16 weights ~18 GB, KV memory is the limit: per-replica concurrency will be small (order of a few to a dozen sequences); measure rather than assume. Prefix cache pays off only if the shared prefix stays resident in the hybrid cache.

### Gaps
- No tokens/s figures for Qwen3.5-9B on 5090, no max-num-seqs guidance, no measured prefix-cache gain on hybrid models. Must benchmark.

## 4. Sampling, looping, thinking budget

### Takeaway
Official thinking-mode setting is temperature 1.0 with presence_penalty 1.5, not greedy; greedy in thinking mode is reported to loop. vLLM has a native `thinking_token_budget` to force-close reasoning.

### Cited Findings
- Thinking general: T=1.0, top_p=0.95, top_k=20, min_p=0, presence_penalty=1.5, repetition_penalty=1.0. Thinking precise coding: T=0.6, top_p=0.95, top_k=20, presence_penalty=0. Non-thinking: T=0.7, top_p=0.8, top_k=20, presence_penalty=1.5. Thinking is on by default; disable via `chat_template_kwargs: {enable_thinking: false}`; `/think` `/nothink` not supported. — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B)
- Presence penalty 0-2 reduces endless repetition; higher values may cause language mixing and slight performance drop. — [HF Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B)
- vLLM `thinking_token_budget` request parameter plus `--reasoning-config '{"reasoning_start_str":..., "reasoning_end_str":...}'` forces the end string when the budget is hit; `reasoning_end_str` can include a transition phrase; no version given; docs example uses qwen3 parser. — [vLLM reasoning outputs docs](https://docs.vllm.ai/en/stable/features/reasoning_outputs/)
- Reports of loops: once repetition starts, P(</think>) falls; community says budgets of 8k-32k plus presence penalty 1.0-1.5; one user says repetition_penalty 1.1 helped; Qwen3 thinking truncation up to 27.5% on hard problems (community patch). Low-quality sources. — [arXiv 2605.31268](https://arxiv.org/pdf/2605.31268); [community vLLM default-thinking-budget](https://net.nhd.workers.dev/palmfuture/vllm-default-thinking-budget); [Reddit snapshot](https://reddit.sentinel-team.org/posts/1rg0487/snapshots/2026-02-27T15%3A04%3A59.533315Z) (UNVERIFIED)

### Inferences
- A deterministic plan: temperature 0 (violates card advice, expect more loops) with `thinking_token_budget` (e.g. ~6-8k) and a fallback second pass with enable_thinking=false for truncated cases. Alternatively fixed-seed sampling with card settings; reproducibility then depends on identical logits.
- Presence penalty interacts with SQL: penalising repeated tokens may hurt repeated identifiers in code/SQL; suggest applying it only to the thinking phase is not supported by vLLM (UNVERIFIED), so test.

### Gaps
- No A/B evidence of greedy vs sampled on Qwen3.5-9B for SQL; no official Qwen statement on greedy decoding failure (the card says nothing about greedy in the fetched summary).

## 5. Packaging for offline run

### Takeaway
Bake weights and caches into the image, set offline env vars, and test with `--network none`; official guidance on JIT/FlashInfer caches was not found.

### Cited Findings
- `HF_HUB_OFFLINE=1` stops vLLM reaching the internet; local path can be passed as the model. — [vLLM forum airgapped thread](https://discuss.vllm.ai/t/setting-up-vllm-in-an-airgapped-environment/916)
- A user still saw connection attempts despite HF_HUB_OFFLINE=1 (same thread, later replies).
- HF_HUB_OFFLINE governs only huggingface_hub; `VLLM_NO_USAGE_STATS=1` closes telemetry; copy HF_HUB_CACHE/HF_XET_CACHE/HF_ASSETS_CACHE; test with `docker run --network none` and `--load-format dummy`. — [particula.tech air-gapped guide](https://particula.tech/blog/vllm-air-gapped-offline-deployment) (third-party blog)
- torch.compile cache dir `~/.cache/vllm/torch_compile_cache` can be copied to skip compilation. — [vLLM torch.compile design doc](https://docs.vllm.ai/en/v0.8.5/design/v1/torch_compile.html); one user found none in a container.

### Inferences
- Pass the model by local path (`/models/Qwen3.5-9B`) plus `--served-model-name`; also set `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1`; warm the compile and CUDA-graph caches during build or first run on the same GPU type; ensure Triton/FlashInfer JIT (needs nvcc) either is prebuilt or avoided (batch invariance disables FlashInfer).
- Rule 1 of the project: set `LLM_BASE_URL` to localhost only.

### Gaps
- FlashInfer JIT cache location and prebuilt-kernel options: not found. Image size limits: not found (competition rule must be read from the organizer's docs). tokenizers/tiktoken downloads for Qwen3.5: not checked.
