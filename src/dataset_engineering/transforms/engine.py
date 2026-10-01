from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TransformResult(BaseModel):
    records: list[dict[str, Any]]
    input_count: int
    output_count: int
    configuration: dict[str, Any]


def transform_records(
    records: list[dict[str, Any]],
    *,
    select: list[str] | None = None,
    filter_field: str | None = None,
    filter_equals: Any = None,
    normalize_fields: list[str] | None = None,
    map_fields: dict[str, Any] | None = None,
):
    out = [dict(r) for r in records]
    if filter_field is not None:
        out = [r for r in out if r.get(filter_field) == filter_equals]
    if normalize_fields:
        for r in out:
            for f in normalize_fields:
                if isinstance(r.get(f), str):
                    r[f] = " ".join(r[f].split())
    if map_fields:
        for r in out:
            for f, v in map_fields.items():
                if f in r:
                    r[f] = v(r[f]) if callable(v) else v
    if select is not None:
        out = [{f: r.get(f) for f in select if f in r} for r in out]
    return TransformResult(
        records=out,
        input_count=len(records),
        output_count=len(out),
        configuration={
            "order": ["filter", "normalize", "map", "select"],
            "select": select,
            "filter_field": filter_field,
        },
    )
