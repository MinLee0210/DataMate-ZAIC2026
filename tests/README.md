# tests/

Run with `make test` (pytest). The suite needs no network and no GPU: the LLM is a `FakeLLM`
(`conftest.py`) that replies from a script, and `toy_split` writes a small messy business package
(`scripts/devfree/toy.py`: CSV with title rows and Vietnamese numbers, XLSX with merged cells and two
sheets, SQLite).

| File | Covers |
|---|---|
| `test_timeparse.py` | Vietnamese time expressions → date ranges (required) |
| `test_format.py` | typed answers and rounding (required) |
| `test_decide.py` | voting, abstain, unanswerable, tie-breaks (required) |
| `test_scorer.py` | PA scorer, dev subset, tau curve (required) |
| `test_ingest.py` | header detection, number locale, merged cells, cache |
| `test_qa.py` | SQL guard, plan parsing, the LangGraph pipeline end to end, batch output, FINAL_MODE |
| `test_agents.py` | prompt templates and skills |
| `test_datagen.py` | teacher tools and the train-only guard (skipped without the datagen extra) |
