# notebooks/

Exploration only (data inspection, error analysis). Never imported by `src/`. Results that matter go
to `docs/analysis/<date>/<topic>/`.

This is also the place for experiments: quick scripts and notebooks that try an idea before it moves
into `src/`. A claimed improvement still needs `make eval SUBSET=dev200`.

- `llm_call.py`: call the LLM from `.env`, raw or through the QA pipeline, on train questions only.

  ```bash
  uv run python -m notebooks.llm_call --prompt "Thủ đô Việt Nam là gì?"
  uv run python -m notebooks.llm_call --id q_001883280e83
  uv run python -m notebooks.llm_call --business biz_125 --n 3
  ```
