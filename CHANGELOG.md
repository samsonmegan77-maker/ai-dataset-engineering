# Changelog

## 1.0.0 - 2026-10-01

### Added
- Production release verification matrix with explicit PASS / NOT RUN states.
- End-to-end dataset workflow and failure-path integration tests.
- Explicit SQLite migration runner and release documentation.
- Replay verification now checks the recorded output fingerprint against persisted output data.
- Engine and algorithm versions are captured in processing manifests.
- Release and deployment documentation.
- Bounded API pagination for collection endpoints and standardized request-validation errors.
- Explicit persistence rollback regression coverage.
- Release manifest no longer embeds a circular self-hash; the final archive checksum is recorded externally.

### Changed
- API dataset run history now covers all dataset versions rather than only the current version.
- Evaluation endpoint now applies supplied quality thresholds.
- Frontend release metadata updated to 1.0.0.

## 0.8.0 — Web Interface + Full Workflow UX

- Added React + TypeScript + Vite web workspace.
- Added responsive dataset list, import/preview flow, version history, quality/validation views, processing actions, run history, and report downloads.
- Added API upload preview/import endpoints for CSV, JSON and JSONL with bounded uploads.
- Added dataset processing-run listing and report export endpoints.
- Added web architecture ADR and workflow documentation.
- Preserved the API/application/repository separation established in v0.7.
- Python regression suite: 65 passed, 1 skipped; 81.06% coverage.

## 0.5.0 - 2026-10-01

- Added deterministic quality metrics and composable evaluation with thresholds.
- Added `dataset quality` and `dataset evaluate` CLI commands.

## 0.3.0 - Development

- Added iterator-based resilient CSV and JSONL ingestion.
- Added malformed-record isolation so later records can continue processing.
- Expanded field schemas with numeric bounds, string lengths, regex patterns, enums, nullability, defaults, nested objects, and arrays.
- Added structured validation values, issue counts, and fields-checked statistics.
- Added property-based ingestion tests using Hypothesis.
- Added synthetic fixture categories for valid, invalid, malformed, edge-case, large, and privacy-oriented data.
- Added deterministic completeness quality metrics.
- Updated the CLI validation workflow to process streaming iterators.

## 0.2.0 - Development

- Hardened CSV, JSON, and JSONL ingestion error handling.
- Added duplicate CSV-header and missing-column detection.
- Added JSON and Markdown report renderers.
- Added CLI report-format selection and output support.
- Expanded schema and validation tests.
- Added CLI integration tests.
- Added regression tests for empty and malformed inputs.
- Added package version metadata.

## 0.1.0 - Development baseline

- Added typed dataset domain models.
- Added CSV, JSON, and JSONL readers.
- Added schema validation.
- Added validation reporting.
- Added initial CLI workflow.
- Added pytest-based unit tests and coverage configuration.

## 0.4.0 - 2026-10-01

### Added
- Deterministic exact and key-based deduplication with optional string normalization.
- Duplicate-group and duplicate-record statistics.
- Declarative transformation engine for filtering, normalization, field selection, and value mapping.
- Transformation reproducibility metadata including ordered operations and input/output counts.
- `dataset deduplicate` and `dataset transform` CLI commands with JSON output.
- Deduplication and transformation ADRs plus a transformation example.
- Explicit in-process deduplication → transformation pipeline and integration coverage.

## 0.6.0

- Added deterministic sampling by size or fraction.
- Added train/validation/test splitting with seeded shuffling and overlap-safe partitioning.
- Added canonical SHA-256 dataset fingerprints.
- Added ProcessingRun metadata and reproducibility manifests to sampling/splitting results.
- Added `dataset sample`, `dataset split`, and `dataset fingerprint` CLI commands.
- Added deterministic regression tests for seeds, partitions, fingerprints, tiny datasets, and invalid configurations.
- Hypothesis remains declared as a development dependency, but could not be installed in the offline verification environment.

## 0.7.0 — Persistence + API

- Added repository abstraction and SQLite persistence.
- Added immutable dataset versioning and persisted SHA-256 fingerprints.
- Added persistent processing runs and reproducibility manifests.
- Added FastAPI service with dataset, validation, quality, processing, evaluation, health, and readiness endpoints.
- Added bounded request models, request IDs, configurable CORS, and request-size limits.
- Added append-only audit events and persisted report/evaluation artifacts.
- Added optional PostgreSQL adapter boundary and Docker Compose profile.
- Added API integration tests while retaining the v0.2–v0.6 regression suite.

## 0.9.0 — Production Engineering + Provenance

- Added explicit provenance and deterministic operation fingerprints.
- Added engine version capture to processing manifests.
- Added replay verification through CLI and API.
- Added tamper-evident audit sequence, previous hash, and event hash.
- Added environment-aware runtime settings and bounded API configuration.
- Added `/api/v1` API namespace while retaining compatibility routes.
- Added provenance and audit API endpoints.
- Added licensing-readiness rights and dependency documentation.
- Added provenance and licensing ADRs.
