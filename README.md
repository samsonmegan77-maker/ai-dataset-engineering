# AI Dataset Engineering

**Current release: v1.0.0**

A standalone toolkit for preparing, validating, profiling, and auditing datasets used in AI/ML development.

## Status

Version 1.0.0 adds explicit provenance, deterministic replay verification, tamper-evident audit events, production configuration, API versioning, bounded API collection endpoints, SQLite migrations, rollback regression coverage, release verification, and licensing-readiness documentation on top of the v0.8 web workflow.

## Quick start

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest --cov
```

Validate the example dataset:

```bash
dataset validate examples/sample.jsonl --schema examples/schema.json
```

## Design principles

- library-first and CLI-first
- deterministic processing
- explicit typed domain models
- no external AI API required
- reproducible results
- synthetic fixtures for tests and examples
- privacy-conscious data handling

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [SECURITY.md](SECURITY.md).

## License

See [LICENSE](LICENSE). Licensing is intentionally explicit and should be reviewed before any public release or third-party licensing discussion.

## Validation behaviour

JSONL and CSV are processed as iterators. In resilient mode, a malformed record is isolated and reported while later records continue to be processed. Validation supports numeric bounds, string length, regex patterns, enums, nullability, nested objects, and array item definitions.

Validation reports include total/valid/invalid records, validity rate, fields checked, per-rule issue counts, and record-level diagnostics.

## Quality

The quality engine provides deterministic completeness, uniqueness, numeric statistics, categorical distributions, consistency, diversity, and duplicate-rate metrics. The evaluation layer keeps metrics transparent and supports optional minimum/maximum thresholds with PASS/WARN/FAIL statuses.

## Deduplication and transformations

v0.4.0 adds deterministic deduplication and a fixed-order transformation engine. Deduplication can compare complete records or explicit key fields, with optional string normalization. Transformations support filtering, normalization, value mapping, and field selection. Each transformation result records its input/output counts and configuration.

## Reproducible sampling and splitting

```bash
dataset fingerprint data.jsonl
dataset sample data.jsonl --size 1000 --seed 42
dataset split data.jsonl --train 0.8 --validation 0.1 --test 0.1 --seed 42
```

Sampling and splitting record deterministic algorithm identifiers, seeds, counts, and SHA-256 fingerprints.

## Persistence and API

SQLite is the default local store. The repository abstraction leaves a PostgreSQL adapter boundary for deployments that need it. FastAPI exposes dataset, validation, quality, processing, evaluation, provenance, audit, replay, and health workflows.

## Web workspace

The web client lives in `apps/web` and communicates only with FastAPI.

```bash
cd apps/web
npm install
npm run dev
```

Set `VITE_API_BASE_URL` when the API is not running at `http://localhost:8000`.

## Release documentation

- [Release verification](docs/RELEASE.md)
- [Deployment guide](docs/DEPLOYMENT.md)
- [Provenance guide](docs/PROVENANCE.md)
