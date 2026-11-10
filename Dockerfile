# syntax=docker/dockerfile:1
# Competition image: local vLLM + DataMate batch inference, runs with --network none.
# DRAFT: not built yet. VLLM_IMAGE has no default on purpose: Qwen3.5 needs vLLM >= 0.17 (the old
# default, v0.11.0, cannot load it) and RTX 5090 (sm_120) needs a build with its kernels. Use the
# vLLM version that already served the model on the 2x RTX 5090 pod, pinned by digest:
#   VLLM_IMAGE=vllm/vllm-openai@sha256:... make docker-build && make rerun-check
ARG VLLM_IMAGE
FROM ${VLLM_IMAGE}

COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app

# app dependencies in their own venv (vLLM stays in the base image's Python); rebuilt only when
# pyproject.toml / uv.lock change
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-dev --no-install-project --python python3

# model weights, downloaded beforehand into ./models/target (declared in docs/MODELS.md)
COPY models/target /models/target

# code last: editing src/ does not invalidate the layers above
COPY src ./src
COPY scripts/infer.sh scripts/vllm.sh scripts/final.env ./scripts/

ENV DATA_DIR=/data RESULT_DIR=/result WORK_DIR=/tmp/datamate MODEL_PATH=/models/target \
    PYTHONUNBUFFERED=1
ENTRYPOINT ["./scripts/infer.sh"]
