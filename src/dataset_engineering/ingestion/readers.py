from __future__ import annotations

import csv
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any


class IngestionError(ValueError):
    pass


Handler = Callable[[int, str, str], None]


def _open(path):
    try:
        return path.open("r", encoding="utf-8", newline="")
    except OSError as e:
        raise IngestionError(f"Unable to read dataset: {path}") from e


def read_csv(path: Path, on_error: Handler | None = None) -> Iterator[dict[str, Any]]:
    with _open(path) as h:
        reader = csv.DictReader(h)
        if not reader.fieldnames:
            raise IngestionError("CSV file has no header row")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise IngestionError("CSV header contains duplicate field names")
        for i, row in enumerate(reader):
            if None in row or any(v is None for v in row.values()):
                if on_error:
                    on_error(i, "columns", "CSV record has invalid columns")
                    continue
                raise IngestionError(f"CSV record {i} has invalid columns")
            yield dict(row)


def read_json(path: Path, on_error: Handler | None = None) -> Iterator[dict[str, Any]]:
    try:
        with _open(path) as h:
            p = json.load(h)
    except json.JSONDecodeError as e:
        raise IngestionError(f"JSON dataset is invalid: line {e.lineno}, column {e.colno}") from e
    if not isinstance(p, list):
        raise IngestionError("JSON dataset must contain an array of objects")
    for i, item in enumerate(p):
        if not isinstance(item, dict):
            raise IngestionError(f"JSON record {i} is not an object")
        yield item


def read_jsonl(path: Path, on_error: Handler | None = None) -> Iterator[dict[str, Any]]:
    with _open(path) as h:
        for i, line in enumerate(h, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                if on_error:
                    on_error(i, "json", "JSONL line is invalid JSON")
                    continue
                raise IngestionError(f"JSONL line {i} is invalid JSON") from e
            if not isinstance(item, dict):
                raise IngestionError(f"JSONL line {i} is not an object")
            yield item


def read_records(path: Path):
    readers = {
        ".csv": ("csv", read_csv),
        ".json": ("json", read_json),
        ".jsonl": ("jsonl", read_jsonl),
    }
    try:
        return readers[path.suffix.lower()][0], readers[path.suffix.lower()][1](path)
    except KeyError as e:
        raise IngestionError(f"Unsupported dataset format: {path.suffix or '<none>'}") from e


def read_records_resilient(path: Path, on_error: Handler | None = None):
    readers = {
        ".csv": ("csv", read_csv),
        ".json": ("json", read_json),
        ".jsonl": ("jsonl", read_jsonl),
    }
    try:
        fmt, reader = readers[path.suffix.lower()]
    except KeyError as e:
        raise IngestionError(f"Unsupported dataset format: {path.suffix or '<none>'}") from e
    return fmt, reader(path, on_error=on_error)
