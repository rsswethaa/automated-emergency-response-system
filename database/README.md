# Database package

The prototype uses SQLite so the project is easy to clone, inspect and run without external infrastructure.

## Canonical files
- `../schema.sql` defines tables, integrity constraints, foreign keys and indexes.
- `../seed.sql` loads deterministic demonstration incidents and alert records.
- `sample_queries.sql` contains useful inspection/reporting queries.

The application creates `emergency.db` automatically on first request if the `incidents` table does not yet exist. The generated database file is intentionally ignored by Git because it is local runtime state.

## Data lifecycle
1. A simulated incident is validated in `app.py`.
2. Severity is classified by `detector.py`.
3. The incident is inserted into `incidents`.
4. A simulated notification is inserted into `alerts` in the same request flow.
5. A responder can mark an incident `RESOLVED`.

See `docs/DATABASE.md` for the ER model, field dictionary, constraints and design rationale.
