# app/

Reserved for a simple demo UI, built once `src/` is done. It will call the API in `src/`:

- `GET /health`
- `POST /ask` with `{"id", "business_id", "question", "as_of_date"}`, which returns the answer and the
  trace (SQL candidates, votes, agreement), useful to show how an answer was reached.

Start the API with `make run` (`APP_HOST`, `APP_PORT` in `.env`). The UI is not part of the
competition image; the competition runs `python -m src` in batch.
