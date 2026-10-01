from __future__ import annotations

from dataset_engineering import __version__
from dataset_engineering.deduplication import deduplicate_records
from dataset_engineering.evaluation import evaluate_quality
from dataset_engineering.persistence.models import (
    DatasetRecord,
    DatasetVersionRecord,
    ProcessingRunRecord,
)
from dataset_engineering.provenance import operation_fingerprint
from dataset_engineering.sample import dataset_fingerprint, sample_records, split_records
from dataset_engineering.transforms import transform_records


class ApplicationService:
    def __init__(self, repo):
        self.repo = repo

    def create_dataset(self, name, description=""):
        return self.repo.create_dataset(DatasetRecord(name=name, description=description))

    def create_version(self, dataset_id, records, schema=None, source_metadata=None):
        d = self.repo.get_dataset(dataset_id)
        if not d:
            raise KeyError("Dataset not found")
        versions = self.repo.list_versions(dataset_id)
        v = self.repo.create_version(
            DatasetVersionRecord(
                dataset_id=dataset_id,
                version=(versions[-1].version + 1 if versions else 1),
                fingerprint=dataset_fingerprint(records),
                record_count=len(records),
                schema=schema or {},
                source_metadata=source_metadata or {},
            )
        )
        self.repo.store_records(v.id, records)
        return v

    def quality(self, records, fields, name, thresholds=None):
        return evaluate_quality(records, fields, name, thresholds or {})

    def validate(self, version_id, records, schema):
        from dataset_engineering.validation.engine import validate_records

        return validate_records(records, schema, version_id)

    def dedup(self, records, fields=None, normalize=False):
        return deduplicate_records(records, fields=fields, normalize=normalize)

    def transform(self, records, **kw):
        return transform_records(records, **kw)

    def sample(self, records, **kw):
        return sample_records(records, **kw)

    def split(self, records, **kw):
        return split_records(records, **kw)

    def run(self, operation, version_id, fn, config=None, seed=None):
        v = self.repo.get_version(version_id)
        result = fn()
        run = ProcessingRunRecord(
            operation=operation,
            input_version_id=version_id,
            input_fingerprint=v.fingerprint if v else None,
            config=config or {},
            seed=seed,
            manifest={
                "engine_version": __version__,
                "algorithm_version": "1",
                "operation_fingerprint": operation_fingerprint(
                    v.fingerprint if v else "", operation, config or {}, seed
                ),
            },
        )
        if hasattr(result, "records"):
            out = self.create_version(
                v.dataset_id,
                result.records,
                v.schema,
                {"derived_from_version": str(v.id), "operation": operation},
            )
            run.output_version_id = out.id
            run.output_fingerprint = out.fingerprint
            run.output_count = len(result.records)
        self.repo.create_run(run)
        return run, result

    def replay(self, run_id):
        r = self.repo.get_run(run_id)
        if not r:
            raise KeyError("Processing run not found")
        expected = operation_fingerprint(
            r.input_fingerprint,
            r.operation,
            r.config,
            r.seed,
            r.manifest.get("engine_version", __version__),
        )
        ok = expected == r.manifest.get("operation_fingerprint")
        if r.output_version_id and r.output_fingerprint:
            ok = (
                ok
                and dataset_fingerprint(self.repo.get_records(r.output_version_id))
                == r.output_fingerprint
            )
        return {
            "run_id": str(run_id),
            "status": "REPRODUCIBLE" if ok else "MISMATCH",
            "expected_operation_fingerprint": expected,
            "recorded_operation_fingerprint": r.manifest.get("operation_fingerprint"),
        }
