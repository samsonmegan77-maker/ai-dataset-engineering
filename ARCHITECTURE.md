# Architecture

## v0.7.0 boundary

The project is deliberately split into three layers:

1. **Interfaces** — Typer CLI and FastAPI HTTP API.
2. **Application/domain services** — validation, quality, processing, evaluation, fingerprints, sampling, and transformations.
3. **Persistence** — repository interfaces with SQLite as the default and a PostgreSQL adapter boundary.

Neither interface owns business rules. Both call the same application services.

```text
CLI ───────┐
           ├── Application Services ── Domain Engines
API ───────┘                 │
                             ▼
                       Repository API
                         │        │
                      SQLite   PostgreSQL
```

### Versioning

Dataset content is represented by immutable `DatasetVersion` records. A new upload or transformation result creates a new version rather than overwriting an existing version. Each version stores a deterministic SHA-256 fingerprint and record count. Records are stored separately from metadata.

### Processing runs

A `ProcessingRun` records operation, input/output version references, fingerprints, configuration, seed, timing, status, and a reproducibility manifest. Large dataset contents are not copied into run metadata.

### Audit

Audit events are append-only records containing action, resource identity, run identity, and non-sensitive metadata. Record contents and secrets are excluded.

### Storage

SQLite is the default local deployment. The repository boundary is designed so a PostgreSQL implementation can be selected with `DATABASE_URL` without changing domain services.

## API workflow

`POST /datasets` → `POST /datasets/{id}/versions` → validate → quality → transform/deduplicate/sample/split → evaluate.

The current version is used by dataset-level processing endpoints. Version history remains queryable at `GET /datasets/{id}/versions`.
