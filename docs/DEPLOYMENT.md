# Deployment Guide

Set environment variables from `.env.example`, then run `PYTHONPATH=src:apps/api uvicorn dataset_api.main:app --host 127.0.0.1 --port 8000`.

Docker: `docker compose up api`. The browser talks to FastAPI; storage remains behind the application boundary.

Production deployments should configure `DATABASE_URL`, `CORS_ORIGINS`, `MAX_UPLOAD_BYTES`, logging, TLS, and authentication at the deployment boundary.
