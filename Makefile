.PHONY: install install-datagen run ingest eval eval-full vllm infer test lint fmt docker-build docker-push rerun-check

SPLIT ?= train
SUBSET ?= dev200
TOPIC ?= eval
IMAGE ?= datamate
TAG ?= latest

install:
	uv sync

install-datagen:
	uv sync --extra datagen

run:
	APP_RELOAD=true ./scripts/entrypoints.sh

ingest:
	uv run python -m scripts.ingest --split $(SPLIT)

eval:
	uv run python -m scripts.eval --split train --subset $(SUBSET) --topic $(TOPIC)

eval-full:
	uv run python -m scripts.eval --split train --subset all --topic $(TOPIC)-full

vllm:
	./scripts/vllm.sh

infer:
	./scripts/infer.sh

test:
	uv run pytest

lint:
	uv run ruff check .

fmt:
	uv run ruff format . && uv run ruff check --fix .

docker-build:
	IMAGE=$(IMAGE) TAG=$(TAG) ./scripts/docker-build.sh

docker-push:
	./scripts/docker-push.sh

rerun-check:
	IMAGE=$(IMAGE) TAG=$(TAG) ./scripts/rerun-check.sh
