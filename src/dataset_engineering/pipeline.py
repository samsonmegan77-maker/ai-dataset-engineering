"""Composable in-process processing pipeline for dataset records."""
from __future__ import annotations
from collections.abc import Iterable
from typing import Any
from dataset_engineering.deduplication import deduplicate_records
from dataset_engineering.transforms import TransformationResult, transform_records
from dataset_engineering.sample import sample_records

def process_records(records: Iterable[dict[str, Any]], *, deduplicate_fields: list[str] | None = None, normalize_duplicates: bool = False, transform_select: list[str] | None = None, transform_filter_field: str | None = None, transform_filter_equals: Any = None, transform_normalize_fields: list[str] | None = None, sample_size: int | None = None, sample_fraction: float | None = None, seed: int = 0) -> tuple[list[dict[str, Any]], dict[str, Any], TransformationResult]:
    materialized = list(records)
    dedup_report = deduplicate_records(materialized, fields=deduplicate_fields, normalize=normalize_duplicates)
    duplicate_indexes = {index for group in dedup_report.duplicate_groups for index in group.record_indexes[1:]}
    unique_records = [record for index, record in enumerate(materialized) if index not in duplicate_indexes]
    transformed = transform_records(unique_records, select=transform_select, filter_field=transform_filter_field, filter_equals=transform_filter_equals, normalize_fields=transform_normalize_fields)
    if sample_size is not None or sample_fraction is not None:
        sampled = sample_records(transformed.records, size=sample_size, fraction=sample_fraction, seed=seed)
        metadata = dedup_report.model_dump(mode="json"); metadata["sampling"] = sampled.model_dump(mode="json")
        return sampled.records, metadata, transformed
    return transformed.records, dedup_report.model_dump(mode="json"), transformed
