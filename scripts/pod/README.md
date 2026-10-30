# Running on a GPU pod (local vLLM)

Step 1 runs the target model on a rented GPU (A40 48 GB) to get the first legal public_test
submission and the real dev200 PA of Qwen3-14B. Step 2 repeats it on 2x RTX 5090, the
competition machine, for timing and the rerun check. No hosted API is used on test data.

## What the pod needs
- SSH access from the dev machine (host, port, user, key).
- CUDA 12.4+ (12.8+ on RTX 5090), Python 3.12, **40 GB of disk** (about 26 GB used, see below).
- Internet for the one-time downloads (uv, vLLM, the model weights).

## 1. Copy the repo and the data (from the dev machine)

```bash
POD=user@host   # plus -p PORT / -i KEY as needed
rsync -az --exclude /.venv --exclude /.venv-vllm --exclude /data --exclude /result --exclude /.env ./ $POD:~/DataMate-ZAIC2026/
rsync -az data/train data/public_test $POD:~/DataMate-ZAIC2026/data/
```

## 2. Set up (on the pod)

```bash
cd ~/DataMate-ZAIC2026
./scripts/pod/setup.sh          # uv, project env, vLLM in .venv-vllm, weights in /models/target, ingest
```

Disk used by the setup:

| Item | Size |
|---|---|
| `Qwen/Qwen3-14B-FP8` weights (official FP8 checkpoint) | 16.3 GB |
| vLLM env (`.venv-vllm`: vLLM, torch, CUDA libraries) | about 8 GB |
| project env, data (train + public_test), ingest caches | about 1 GB |
| vLLM / torch compile caches, logs, results | about 1 GB |
| **Total** | **about 26 GB**; ask for 40 GB to keep headroom |

The bf16 checkpoint (`MODEL_ID=Qwen/Qwen3-14B`, 29.6 GB) needs about 14 GB more. Docker builds for
the rerun check (step 2 of the plan, on 2x RTX 5090) need about 50 GB more: the CUDA base image
plus the weights baked into the image.

`.env` on the pod:

```
LLM_BASE_URL=http://127.0.0.1:8001/v1
LLM_API_KEY=EMPTY
LLM_MODEL=Qwen/Qwen3-14B
LLM_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": false}}
PIPELINE=malt
ANALYZE_EXTRA_BODY={"chat_template_kwargs": {"enable_thinking": true}}
ANALYZE_MAX_TOKENS=12288
DATA_DIR=./data
WORK_DIR=/tmp/datamate
```

## 3. Start vLLM (keep it running, e.g. in tmux)

```bash
export PATH=$PWD/.venv-vllm/bin:$PATH
TP=1 ./scripts/vllm.sh                                 # A40, one GPU, FP8 checkpoint
# TP=2 ./scripts/vllm.sh                                # 2x RTX 5090
curl -s http://127.0.0.1:8001/v1/models                 # ready when this answers
```

`MAX_MODEL_LEN` defaults to 49152 (YaRN above Qwen3's native 32768): public_test prompts reach about
28k tokens, plus up to `ANALYZE_MAX_TOKENS` of thinking.

## 4. Smoke test, then dev200 on the target model (train)

```bash
uv run python -m notebooks.llm_call --id q_001883280e83
make eval SUBSET=dev200 TOPIC=qwen3-ca-thinking WORKERS=8
```

Look at PA, the share of questions with errors (cut-off thinking, bad JSON) and seconds per
question before going on.

## 5. public_test (the submission)

```bash
START_VLLM=0 SPLIT=public_test DATA_DIR=./data RESULT_DIR=./result/public-qwen3 ./scripts/infer.sh
uv run python -m scripts.export --pred result/public-qwen3/submission.jsonl --topic public-test-qwen3
```

Upload `data/results/<date>/public-test-qwen3/submission.jsonl` (1000 lines). Run step 5 twice and
compare: the two files should agree on almost every line (rule 8: |PA difference| ≤ 0.03).

## Tuning knobs (env)

| Variable | Default | Use |
|---|---|---|
| `TP` | 2 | 1 on a single GPU |
| `QUANTIZATION` | (from the checkpoint) | `fp8` only with the bf16 checkpoint, to quantize when loading |
| `KV_CACHE_DTYPE` | auto | `fp8` for more parallel requests |
| `MAX_MODEL_LEN` | 49152 | longest prompt + `ANALYZE_MAX_TOKENS` |
| `MAX_NUM_SEQS` | 16 | parallel requests in vLLM; keep ≥ `WORKERS` × 1 |
| `WORKERS` | 8 (infer.sh) | questions in parallel |
| `ANALYZE_MAX_TOKENS` | 12288 | thinking budget per reasoning step |
