# assets/

Static files used by the agents. No prompt text lives in Python code.

```
assets/
├── prompt_templates/
│   ├── sql_agent.md       system prompt of SQLAgent (followed by its skills)
│   ├── sql_question.md    user prompt: README, schema, semantic views, time, entities, variant, question
│   ├── sql_variants.md    the k approach hints, separated by a line `---` (diversity at temperature 0)
│   ├── repair.md          user prompt after a failed query
│   └── default.md         BaseAgent default
├── skills/<name>/SKILL.md YAML frontmatter (name, description) + instructions
└── semantic/*.sql         rulebook views and macros, applied to every business at ingest
```

Placeholders in templates are `{{name}}`; single braces are left alone because SQL and JSON use them.

Skills: `answer-types`, `time-expressions`, `ranking-rules`, `business-metrics`, `unanswerable`.
They must be generic across businesses. `BaseAgent` appends the skill bodies (frontmatter removed)
to its prompt template. The same folders are read by the deepagents teacher in `scripts/datagen/`;
the format is the Agent Skills format that deepagents uses. An unknown skill or template name
raises `KeyError` when the agent is built.
