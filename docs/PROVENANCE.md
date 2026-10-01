# Provenance and reproducibility

Immutable dataset versions use SHA-256 fingerprints. Processing runs record input identity, operation, configuration, seed, engine version and an operation fingerprint. Replay verifies that recorded identity remains internally consistent.

Audit metadata should contain operational identifiers only; raw dataset records and secrets do not belong in the audit trail.
