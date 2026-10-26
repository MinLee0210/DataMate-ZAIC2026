# semantic/

Split-wide semantic layer, written once from the rulebook: one `*.sql` file per concept, holding
`CREATE OR REPLACE VIEW` / `CREATE OR REPLACE MACRO` statements separated by `;`.

`src/modules/semantic/views.py` runs every statement against each business's DuckDB at ingest time.
A statement that refers to a table or column the business does not have is skipped, so keep each
statement small and self-contained.

Rules:
- Generic across businesses: never name a specific `business_id`.
- Name objects after the rulebook concept (`valid_orders`, `revenue`, `cogs`, `overdue_debt`).
- Add the concept to `skills/business-metrics/SKILL.md` so the SQL agent knows it exists.

Empty until the rulebook has been read.
