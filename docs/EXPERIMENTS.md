# Experiments

Runbook for gated experiments. Link results under `docs/analysis/<yyyy-mm-dd>/<topic>/`
rather than copying numbers by hand.

| Date | Topic | Command | Results |
|---|---|---|---|
| 2026-10-27 | baseline-qwen3-14b (Qwen/Qwen3-14B:deepinfra via HF) | `python -m scripts.eval --split train --subset dev200 --topic baseline` | PA -0.01 (40/42/118), 24.8183 s/q, 81812.705 prompt tok/q, [summary](analysis/2026-10-27/baseline-qwen3-14b/summary.md) |
| 2026-10-27 | baseline (deepseek-flash) | `python -m scripts.eval --split train --subset dev200 --topic baseline` | PA 0.09 (92/74/34), 5.4516 s/q, 41113.39 prompt tok/q, [summary](analysis/2026-10-27/baseline/summary.md) |
| 2026-10-27 | rulebook (deepseek-flash) | `python -m scripts.eval --split train --subset dev200 --topic rulebook --workers 8` | PA 0.35 (117/47/36), 5.8322 s/q, 61112.25 prompt tok/q, [summary](analysis/2026-10-27/rulebook/summary.md) |
| 2026-10-27 | analyze (deepseek-flash) | `python -m scripts.eval --split train --subset dev200 --topic analyze --workers 8` | PA 0.335 (129/62/9), 8.9385 s/q, 82664.185 prompt tok/q, [summary](analysis/2026-10-27/analyze/summary.md) |
| 2026-10-27 | analyze-thinking (deepseek-flash) | `python -m scripts.eval --split train --subset dev200 --topic analyze-thinking --workers 8` | PA 0.52 (143/39/18), 15.3052 s/q, 83237.3 prompt tok/q, [summary](analysis/2026-10-27/analyze-thinking/summary.md) |
| 2026-10-27 | ca (deepseek-flash) | `python -m scripts.eval --split train --subset dev200 --topic ca --workers 8` | PA 0.43 (140/54/6), 7.377 s/q, 58289.515 prompt tok/q, [summary](analysis/2026-10-27/ca/summary.md) |
| 2026-10-27 | ca-thinking (deepseek-flash) | `python -m scripts.eval --split train --subset dev200 --topic ca-thinking --workers 8` | PA 0.55 (122/12/66), 23.0906 s/q, 58066.145 prompt tok/q, [summary](analysis/2026-10-27/ca-thinking/summary.md) |
