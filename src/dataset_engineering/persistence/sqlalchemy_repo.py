"""PostgreSQL repository adapter implementing the same boundary as SQLite."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import create_engine, text

from dataset_engineering.persistence.models import (
    AuditEventRecord,
    DatasetRecord,
    DatasetVersionRecord,
    ProcessingRunRecord,
)
from dataset_engineering.provenance import event_hash


class SQLAlchemyRepository:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, future=True, pool_pre_ping=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS datasets "
                    "(id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, "
                    "description TEXT NOT NULL, created_at TEXT NOT NULL, "
                    "current_version INTEGER)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS dataset_versions "
                    "(id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, "
                    "version INTEGER NOT NULL, fingerprint TEXT NOT NULL, "
                    "record_count INTEGER NOT NULL, schema_json TEXT NOT NULL, "
                    "created_at TEXT NOT NULL, source_metadata_json TEXT NOT NULL, "
                    "UNIQUE(dataset_id, version), UNIQUE(dataset_id, fingerprint))"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS version_records "
                    "(version_id TEXT NOT NULL, record_index INTEGER NOT NULL, "
                    "record_json TEXT NOT NULL, "
                    "PRIMARY KEY(version_id, record_index))"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS processing_runs "
                    "(id TEXT PRIMARY KEY, operation TEXT NOT NULL, "
                    "input_version_id TEXT, output_version_id TEXT, "
                    "input_fingerprint TEXT, output_fingerprint TEXT, "
                    "config_json TEXT NOT NULL, seed INTEGER, "
                    "started_at TEXT NOT NULL, completed_at TEXT, "
                    "output_count INTEGER, status TEXT NOT NULL, "
                    "manifest_json TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS processing_artifacts "
                    "(id TEXT PRIMARY KEY, artifact_type TEXT NOT NULL, "
                    "resource_id TEXT NOT NULL, payload_json TEXT NOT NULL, "
                    "created_at TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS audit_events "
                    "(id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL, "
                    "resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, "
                    "run_id TEXT, metadata_json TEXT NOT NULL, sequence BIGINT UNIQUE NOT NULL, "
                    "previous_hash TEXT, event_hash TEXT UNIQUE NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS schema_migrations "
                    "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_versions_dataset "
                    "ON dataset_versions(dataset_id, version)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_runs_input ON processing_runs(input_version_id)"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_audit_resource "
                    "ON audit_events(resource_type, resource_id)"
                )
            )

    def create_dataset(self, dataset: DatasetRecord) -> DatasetRecord:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO datasets "
                    "VALUES (:id,:name,:description,:created_at,:current_version)"
                ),
                {
                    "id": str(dataset.id),
                    "name": dataset.name,
                    "description": dataset.description,
                    "created_at": dataset.created_at.isoformat(),
                    "current_version": dataset.current_version,
                },
            )
        return dataset

    def _dataset(self, row: object) -> DatasetRecord:
        return DatasetRecord(
            id=UUID(row[0]),
            name=row[1],
            description=row[2],
            created_at=datetime.fromisoformat(row[3]),
            current_version=row[4],
        )

    def list_datasets(self) -> list[DatasetRecord]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id,name,description,created_at,current_version "
                    "FROM datasets ORDER BY created_at,id"
                )
            ).fetchall()
        return [self._dataset(row) for row in rows]

    def get_dataset(self, dataset_id: UUID) -> DatasetRecord | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT id,name,description,created_at,current_version "
                    "FROM datasets WHERE id=:id"
                ),
                {"id": str(dataset_id)},
            ).first()
        return None if row is None else self._dataset(row)

    def create_version(self, version: DatasetVersionRecord) -> DatasetVersionRecord:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO dataset_versions "
                    "VALUES (:id,:dataset_id,:version,:fingerprint,:record_count,"
                    ":schema_json,:created_at,:source_metadata_json)"
                ),
                {
                    "id": str(version.id),
                    "dataset_id": str(version.dataset_id),
                    "version": version.version,
                    "fingerprint": version.fingerprint,
                    "record_count": version.record_count,
                    "schema_json": json.dumps(version.schema, sort_keys=True),
                    "created_at": version.created_at.isoformat(),
                    "source_metadata_json": json.dumps(version.source_metadata, sort_keys=True),
                },
            )
            connection.execute(
                text(
                    "UPDATE datasets SET current_version=:version "
                    "WHERE id=:id AND "
                    "(current_version IS NULL OR current_version < :version)"
                ),
                {"version": version.version, "id": str(version.dataset_id)},
            )
        return version

    def _version(self, row: object) -> DatasetVersionRecord:
        return DatasetVersionRecord(
            id=UUID(row[0]),
            dataset_id=UUID(row[1]),
            version=row[2],
            fingerprint=row[3],
            record_count=row[4],
            schema=json.loads(row[5]),
            created_at=datetime.fromisoformat(row[6]),
            source_metadata=json.loads(row[7]),
        )

    def list_versions(self, dataset_id: UUID) -> list[DatasetVersionRecord]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id,dataset_id,version,fingerprint,record_count,schema_json,"
                    "created_at,source_metadata_json FROM dataset_versions "
                    "WHERE dataset_id=:id ORDER BY version"
                ),
                {"id": str(dataset_id)},
            ).fetchall()
        return [self._version(row) for row in rows]

    def get_version(self, version_id: UUID) -> DatasetVersionRecord | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text(
                    "SELECT id,dataset_id,version,fingerprint,record_count,schema_json,"
                    "created_at,source_metadata_json FROM dataset_versions WHERE id=:id"
                ),
                {"id": str(version_id)},
            ).first()
        return None if row is None else self._version(row)

    def store_records(self, version_id: UUID, records: list[dict[str, object]]) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO version_records "
                    "(version_id,record_index,record_json) "
                    "VALUES (:version_id,:record_index,:record_json)"
                ),
                [
                    {
                        "version_id": str(version_id),
                        "record_index": index,
                        "record_json": json.dumps(record, sort_keys=True, ensure_ascii=False),
                    }
                    for index, record in enumerate(records)
                ],
            )

    def get_records(self, version_id: UUID) -> list[dict[str, object]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT record_json FROM version_records "
                    "WHERE version_id=:id ORDER BY record_index"
                ),
                {"id": str(version_id)},
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _run(self, row: object) -> ProcessingRunRecord:
        return ProcessingRunRecord(
            id=UUID(row[0]),
            operation=row[1],
            input_version_id=UUID(row[2]) if row[2] else None,
            output_version_id=UUID(row[3]) if row[3] else None,
            input_fingerprint=row[4],
            output_fingerprint=row[5],
            config=json.loads(row[6]),
            seed=row[7],
            started_at=datetime.fromisoformat(row[8]),
            completed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            output_count=row[10],
            status=row[11],
            manifest=json.loads(row[12]),
        )

    def create_run(self, run: ProcessingRunRecord) -> ProcessingRunRecord:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO processing_runs VALUES "
                    "(:id,:operation,:input_version_id,:output_version_id,"
                    ":input_fingerprint,:output_fingerprint,:config_json,:seed,"
                    ":started_at,:completed_at,:output_count,:status,:manifest_json)"
                ),
                {
                    "id": str(run.id),
                    "operation": run.operation,
                    "input_version_id": (
                        str(run.input_version_id) if run.input_version_id else None
                    ),
                    "output_version_id": (
                        str(run.output_version_id) if run.output_version_id else None
                    ),
                    "input_fingerprint": run.input_fingerprint,
                    "output_fingerprint": run.output_fingerprint,
                    "config_json": json.dumps(run.config, sort_keys=True),
                    "seed": run.seed,
                    "started_at": run.started_at.isoformat(),
                    "completed_at": (run.completed_at.isoformat() if run.completed_at else None),
                    "output_count": run.output_count,
                    "status": run.status,
                    "manifest_json": json.dumps(run.manifest, sort_keys=True),
                },
            )
        return run

    def get_run(self, run_id: UUID) -> ProcessingRunRecord | None:
        with self.engine.connect() as connection:
            row = connection.execute(
                text("SELECT * FROM processing_runs WHERE id=:id"),
                {"id": str(run_id)},
            ).first()
        return None if row is None else self._run(row)

    def list_runs(self, version_id: UUID | None = None) -> list[ProcessingRunRecord]:
        sql = "SELECT * FROM processing_runs"
        params: dict[str, object] = {}
        if version_id:
            sql += " WHERE input_version_id=:id"
            params["id"] = str(version_id)
        sql += " ORDER BY started_at DESC"
        with self.engine.connect() as connection:
            rows = connection.execute(text(sql), params).fetchall()
        return [self._run(row) for row in rows]

    def update_run(self, run: ProcessingRunRecord) -> ProcessingRunRecord:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE processing_runs SET output_version_id=:output_version_id,"
                    "output_fingerprint=:output_fingerprint,completed_at=:completed_at,"
                    "output_count=:output_count,status=:status,manifest_json=:manifest_json "
                    "WHERE id=:id"
                ),
                {
                    "output_version_id": (
                        str(run.output_version_id) if run.output_version_id else None
                    ),
                    "output_fingerprint": run.output_fingerprint,
                    "completed_at": (run.completed_at.isoformat() if run.completed_at else None),
                    "output_count": run.output_count,
                    "status": run.status,
                    "manifest_json": json.dumps(run.manifest, sort_keys=True),
                    "id": str(run.id),
                },
            )
        return run

    def create_artifact(
        self, artifact_type: str, resource_id: UUID, payload: dict[str, object]
    ) -> None:
        with self.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO processing_artifacts "
                    "(id,artifact_type,resource_id,payload_json,created_at) "
                    "VALUES (:id,:type,:resource,:payload,:created)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "type": artifact_type,
                    "resource": str(resource_id),
                    "payload": json.dumps(payload, sort_keys=True, default=str),
                    "created": datetime.now(UTC).isoformat(),
                },
            )

    def create_audit(self, event: AuditEventRecord) -> AuditEventRecord:
        with self.engine.begin() as connection:
            row = connection.execute(
                text("SELECT sequence,event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1")
            ).first()
            sequence = (int(row[0]) + 1) if row else 1
            previous = row[1] if row else None
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
            connection.execute(
                text(
                    "INSERT INTO audit_events VALUES "
                    "(:id,:timestamp,:action,:resource_type,:resource_id,:run_id,"
                    ":metadata_json,:sequence,:previous_hash,:event_hash)"
                ),
                {
                    "id": str(event.id),
                    "timestamp": event.timestamp.isoformat(),
                    "action": event.action,
                    "resource_type": event.resource_type,
                    "resource_id": str(event.resource_id),
                    "run_id": str(event.run_id) if event.run_id else None,
                    "metadata_json": json.dumps(event.metadata, sort_keys=True, default=str),
                    "sequence": sequence,
                    "previous_hash": previous,
                    "event_hash": digest,
                },
            )
        return event.model_copy(
            update={
                "sequence": sequence,
                "previous_hash": previous,
                "event_hash": digest,
            }
        )

    def list_audit(
        self, resource_type: str | None = None, resource_id: UUID | None = None
    ) -> list[AuditEventRecord]:
        sql = "SELECT * FROM audit_events WHERE 1=1"
        params: dict[str, object] = {}
        if resource_type:
            sql += " AND resource_type=:type"
            params["type"] = resource_type
        if resource_id:
            sql += " AND resource_id=:resource"
            params["resource"] = str(resource_id)
        sql += " ORDER BY sequence"
        with self.engine.connect() as connection:
            rows = connection.execute(text(sql), params).fetchall()
        return [
            AuditEventRecord(
                id=UUID(row[0]),
                timestamp=datetime.fromisoformat(row[1]),
                action=row[2],
                resource_type=row[3],
                resource_id=UUID(row[4]),
                run_id=UUID(row[5]) if row[5] else None,
                metadata=json.loads(row[6]),
                sequence=row[7],
                previous_hash=row[8],
                event_hash=row[9],
            )
            for row in rows
        ]

    def list_artifacts(self, resource_id: UUID) -> list[dict[str, object]]:
        with self.engine.connect() as connection:
            rows = connection.execute(
                text(
                    "SELECT id,artifact_type,resource_id,payload_json,created_at "
                    "FROM processing_artifacts WHERE resource_id=:id ORDER BY created_at"
                ),
                {"id": str(resource_id)},
            ).fetchall()
        return [
            {
                "id": row[0],
                "artifact_type": row[1],
                "resource_id": row[2],
                "payload": json.loads(row[3]),
                "created_at": row[4],
            }
            for row in rows
        ]

    def close(self) -> None:
        self.engine.dispose()
