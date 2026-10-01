# Security

## v1.0 API controls

- Request bodies are bounded by `MAX_REQUEST_BODY_BYTES` (10 MiB by default).
- Dataset version creation is bounded to 100,000 records per request.
- Sampling and split parameters are range constrained.
- Dataset names are restricted to safe identifier characters.
- The API does not accept arbitrary filesystem paths.
- Dataset versions are immutable; new content creates a new version.
- Audit metadata must contain identifiers and operational facts, not raw dataset records or secrets.
- Request IDs are returned as `X-Request-ID` for traceability.
- CORS is explicitly configured through `CORS_ORIGINS` and is not wildcarded by default.
- Authentication is intentionally deferred, but the FastAPI dependency boundary leaves a clean insertion point for it.

## Production notes

Run behind TLS and an authenticated reverse proxy, use a non-default PostgreSQL password, restrict CORS to trusted origins, and apply resource limits appropriate to the deployment.
