# Knowledge store tools

SQLite schema: [`knowledge/database/schema.sql`](../../knowledge/database/schema.sql).
DB path default: `knowledge/database/dishonored-research.sqlite` (gitignored).

```text
python tools/knowledge/sync_from_experiments.py
```

Imports experiment frontmatter, seeds known Blink activation edges (E1–E10), key function attributions, and open/rejected hypotheses. Safe to re-run.
