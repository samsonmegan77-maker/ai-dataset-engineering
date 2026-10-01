from __future__ import annotations

import json
import sqlite3
from datetime import UTC
from pathlib import Path
from threading import RLock
from uuid import UUID

from dataset_engineering.persistence.models import (
    AuditEventRecord,
    DatasetRecord,
    DatasetVersionRecord,
    ProcessingRunRecord,
)
from dataset_engineering.provenance import event_hash


class SQLiteRepository:
    """Thread-safe SQLite repository with immutable dataset versions and audit events."""

    def __init__(self, path: str | Path = "dataset_engineering.db") -> None:
        self.path = str(path)
        self._lock = RLock()
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(
                """CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, description TEXT NOT NULL, created_at TEXT NOT NULL, current_version INTEGER); CREATE TABLE IF NOT EXISTS dataset_versions (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES datasets(id), version INTEGER NOT NULL, fingerprint TEXT NOT NULL, record_count INTEGER NOT NULL, schema_json TEXT NOT NULL, created_at TEXT NOT NULL, source_metadata_json TEXT NOT NULL, UNIQUE(dataset_id, version), UNIQUE(dataset_id, fingerprint)); CREATE TABLE IF NOT EXISTS version_records (version_id TEXT NOT NULL REFERENCES dataset_versions(id), record_index INTEGER NOT NULL, record_json TEXT NOT NULL, PRIMARY KEY(version_id, record_index)); CREATE TABLE IF NOT EXISTS processing_runs (id TEXT PRIMARY KEY, operation TEXT NOT NULL, input_version_id TEXT, output_version_id TEXT, input_fingerprint TEXT, output_fingerprint TEXT, config_json TEXT NOT NULL, seed INTEGER, started_at TEXT NOT NULL, completed_at TEXT, output_count INTEGER, status TEXT NOT NULL, manifest_json TEXT NOT NULL); CREATE TABLE IF NOT EXISTS processing_artifacts (id TEXT PRIMARY KEY, artifact_type TEXT NOT NULL, resource_id TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, run_id TEXT, metadata_json TEXT NOT NULL, sequence INTEGER NOT NULL UNIQUE, previous_hash TEXT, event_hash TEXT NOT NULL UNIQUE); CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL); CREATE INDEX IF NOT EXISTS idx_versions_dataset ON dataset_versions(dataset_id, version); CREATE INDEX IF NOT EXISTS idx_runs_input ON processing_runs(input_version_id); CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource_type, resource_id);"""
            )
            columns = {
                row[1] for row in self.conn.execute("PRAGMA table_info(audit_events)").fetchall()
            }
            if "sequence" not in columns:
                self.conn.execute(
                    "ALTER TABLE audit_events ADD COLUMN sequence INTEGER NOT NULL DEFAULT 0"
                )
            if "previous_hash" not in columns:
                self.conn.execute("ALTER TABLE audit_events ADD COLUMN previous_hash TEXT")
            if "event_hash" not in columns:
                self.conn.execute(
                    "ALTER TABLE audit_events ADD COLUMN event_hash TEXT NOT NULL DEFAULT ''"
                )
            count = self.conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]
            if (
                count
                and (self.conn.execute("SELECT MAX(sequence) FROM audit_events").fetchone()[0] or 0)
                == 0
            ):
                rows = self.conn.execute("SELECT * FROM audit_events ORDER BY rowid").fetchall()
                previous = None
                for sequence, row in enumerate(rows, 1):
                    digest = event_hash(
                        sequence,
                        row["timestamp"],
                        row["action"],
                        row["resource_type"],
                        row["resource_id"],
                        row["run_id"],
                        json.loads(row["metadata_json"]),
                        previous,
                    )
                    self.conn.execute(
                        "UPDATE audit_events SET sequence=?, previous_hash=?, event_hash=? WHERE id=?",
                        (sequence, previous, digest, row["id"]),
                    )
                    previous = digest
            self.conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_sequence ON audit_events(sequence)"
            )
            from dataset_engineering.persistence.migrations import apply_sqlite_migrations

            apply_sqlite_migrations(self.conn)

    @staticmethod
    def _dt(value: str):
        from datetime import datetime

        return datetime.fromisoformat(value)

    def create_dataset(self, dataset: DatasetRecord) -> DatasetRecord:
        with self._lock, self.conn:
            self.conn.execute(
                "INSERT INTO datasets VALUES (?,?,?,?,?)",
                (
                    str(dataset.id),
                    dataset.name,
                    dataset.description,
                    dataset.created_at.isoformat(),
                    dataset.current_version,
                ),
            )
        return dataset

    def list_datasets(self) -> list[DatasetRecord]:
        rows = self.conn.execute("SELECT * FROM datasets ORDER BY created_at, id").fetchall()
        return [
            DatasetRecord(
                id=UUID(r["id"]),
                name=r["name"],
                description=r["description"],
                created_at=self._dt(r["created_at"]),
                current_version=r["current_version"],
            )
            for r in rows
        ]

    def get_dataset(self, dataset_id: UUID) -> DatasetRecord | None:
        r = self.conn.execute("SELECT * FROM datasets WHERE id=?", (str(dataset_id),)).fetchone()
        return (
            None
            if r is None
            else DatasetRecord(
                id=UUID(r["id"]),
                name=r["name"],
                description=r["description"],
                created_at=self._dt(r["created_at"]),
                current_version=r["current_version"],
            )
        )

    def create_version(self, version: DatasetVersionRecord) -> DatasetVersionRecord:
        with self._lock, self.conn:
            self.conn.execute(
                "INSERT INTO dataset_versions VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(version.id),
                    str(version.dataset_id),
                    version.version,
                    version.fingerprint,
                    version.record_count,
                    json.dumps(version.schema, sort_keys=True),
                    version.created_at.isoformat(),
                    json.dumps(version.source_metadata, sort_keys=True),
                ),
            )
            self.conn.execute(
                "UPDATE datasets SET current_version=? WHERE id=? AND (current_version IS NULL OR current_version < ?)",
                (version.version, str(version.dataset_id), version.version),
            )
        return version

    def list_versions(self, dataset_id: UUID) -> list[DatasetVersionRecord]:
        rows = self.conn.execute(
            "SELECT * FROM dataset_versions WHERE dataset_id=? ORDER BY version", (str(dataset_id),)
        ).fetchall()
        return [self._version(r) for r in rows]

    def get_version(self, version_id: UUID) -> DatasetVersionRecord | None:
        r = self.conn.execute(
            "SELECT * FROM dataset_versions WHERE id=?", (str(version_id),)
        ).fetchone()
        return None if r is None else self._version(r)

    def _version(self, r: sqlite3.Row) -> DatasetVersionRecord:
        return DatasetVersionRecord(
            id=UUID(r["id"]),
            dataset_id=UUID(r["dataset_id"]),
            version=r["version"],
            fingerprint=r["fingerprint"],
            record_count=r["record_count"],
            schema=json.loads(r["schema_json"]),
            created_at=self._dt(r["created_at"]),
            source_metadata=json.loads(r["source_metadata_json"]),
        )

    def store_records(self, version_id: UUID, records: list[dict]) -> None:
        with self._lock, self.conn:
            self.conn.executemany(
                "INSERT INTO version_records(version_id, record_index, record_json) VALUES (?,?,?)",
                [
                    (str(version_id), i, json.dumps(r, sort_keys=True, ensure_ascii=False))
                    for i, r in enumerate(records)
                ],
            )

    def get_records(self, version_id: UUID) -> list[dict]:
        rows = self.conn.execute(
            "SELECT record_json FROM version_records WHERE version_id=? ORDER BY record_index",
            (str(version_id),),
        ).fetchall()
        return [json.loads(r[0]) for r in rows]

    def create_run(self, run: ProcessingRunRecord) -> ProcessingRunRecord:
        with self._lock, self.conn:
            self.conn.execute(
                "INSERT INTO processing_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(run.id),
                    run.operation,
                    str(run.input_version_id) if run.input_version_id else None,
                    str(run.output_version_id) if run.output_version_id else None,
                    run.input_fingerprint,
                    run.output_fingerprint,
                    json.dumps(run.config, sort_keys=True),
                    run.seed,
                    run.started_at.isoformat(),
                    run.completed_at.isoformat() if run.completed_at else None,
                    run.output_count,
                    run.status,
                    json.dumps(run.manifest, sort_keys=True),
                ),
            )
        return run

    def list_runs(self, version_id: UUID | None = None) -> list[ProcessingRunRecord]:
        rows = (
            self.conn.execute("SELECT * FROM processing_runs ORDER BY started_at DESC").fetchall()
            if version_id is None
            else self.conn.execute(
                "SELECT * FROM processing_runs WHERE input_version_id=? ORDER BY started_at DESC",
                (str(version_id),),
            ).fetchall()
        )
        return [self._run(r) for r in rows]

    def _run(self, r: sqlite3.Row) -> ProcessingRunRecord:
        return ProcessingRunRecord(
            id=UUID(r["id"]),
            operation=r["operation"],
            input_version_id=UUID(r["input_version_id"]) if r["input_version_id"] else None,
            output_version_id=UUID(r["output_version_id"]) if r["output_version_id"] else None,
            input_fingerprint=r["input_fingerprint"],
            output_fingerprint=r["output_fingerprint"],
            config=json.loads(r["config_json"]),
            seed=r["seed"],
            started_at=self._dt(r["started_at"]),
            completed_at=self._dt(r["completed_at"]) if r["completed_at"] else None,
            output_count=r["output_count"],
            status=r["status"],
            manifest=json.loads(r["manifest_json"]),
        )

    def get_run(self, run_id: UUID) -> ProcessingRunRecord | None:
        r = self.conn.execute("SELECT * FROM processing_runs WHERE id=?", (str(run_id),)).fetchone()
        if r is None:
            return None
        return self._run(r)

    def update_run(self, run: ProcessingRunRecord) -> ProcessingRunRecord:
        with self._lock, self.conn:
            self.conn.execute(
                "UPDATE processing_runs SET output_version_id=?, output_fingerprint=?, completed_at=?, output_count=?, status=?, manifest_json=? WHERE id=?",
                (
                    str(run.output_version_id) if run.output_version_id else None,
                    run.output_fingerprint,
                    run.completed_at.isoformat() if run.completed_at else None,
                    run.output_count,
                    run.status,
                    json.dumps(run.manifest, sort_keys=True),
                    str(run.id),
                ),
            )
        return run

    def create_artifact(self, artifact_type: str, resource_id: UUID, payload: dict) -> None:
        import uuid
        from datetime import datetime

        with self._lock, self.conn:
            self.conn.execute(
                "INSERT INTO processing_artifacts VALUES (?,?,?,?,?)",
                (
                    str(uuid.uuid4()),
                    artifact_type,
                    str(resource_id),
                    json.dumps(payload, sort_keys=True, default=str),
                    datetime.now(UTC).isoformat(),
                ),
            )

    def create_audit(self, event: AuditEventRecord) -> AuditEventRecord:
        with self._lock, self.conn:
            row = self.conn.execute(
                "SELECT sequence, event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
            sequence = int(row["sequence"]) + 1 if row else 1
            previous = row["event_hash"] if row else None
            digest = event_hash(
                sequence,
                event.timestamp.isoformat(),
                event.action,
                event.resource_type,
                str(event.resource_id),
                str(event.run_id) if event.run_id else None,
                event.metadata,
                previous,
            )
            self.conn.execute(
                "INSERT INTO audit_events VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    str(event.id),
                    event.timestamp.isoformat(),
                    event.action,
                    event.resource_type,
                    str(event.resource_id),
                    str(event.run_id) if event.run_id else None,
                    json.dumps(event.metadata, sort_keys=True, default=str),
                    sequence,
                    previous,
                    digest,
                ),
            )
        return event.model_copy(
            update={"sequence": sequence, "previous_hash": previous, "event_hash": digest}
        )

    def list_audit(
        self, resource_type: str | None = None, resource_id: UUID | None = None
    ) -> list[AuditEventRecord]:
        sql = "SELECT * FROM audit_events WHERE 1=1"
        params: list[str] = []
        if resource_type:
            sql += " AND resource_type=?"
            params.append(resource_type)
        if resource_id:
            sql += " AND resource_id=?"
            params.append(str(resource_id))
        rows = self.conn.execute(sql + " ORDER BY sequence", params).fetchall()
        return [
            AuditEventRecord(
                id=UUID(r["id"]),
                timestamp=self._dt(r["timestamp"]),
                action=r["action"],
                resource_type=r["resource_type"],
                resource_id=UUID(r["resource_id"]),
                run_id=UUID(r["run_id"]) if r["run_id"] else None,
                metadata=json.loads(r["metadata_json"]),
                sequence=r["sequence"],
                previous_hash=r["previous_hash"],
                event_hash=r["event_hash"],
            )
            for r in rows
        ]

    def list_artifacts(self, resource_id: UUID) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM processing_artifacts WHERE resource_id=? ORDER BY created_at",
            (str(resource_id),),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "artifact_type": r["artifact_type"],
                "resource_id": r["resource_id"],
                "payload": json.loads(r["payload_json"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def close(self) -> None:
        self.conn.close()
