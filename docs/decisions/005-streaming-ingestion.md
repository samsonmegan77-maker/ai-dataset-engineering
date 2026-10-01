# ADR 005: Streaming ingestion

CSV and JSONL readers expose iterators and can isolate record-level errors. JSON arrays remain whole-document input because the standard JSON parser requires a complete document.
