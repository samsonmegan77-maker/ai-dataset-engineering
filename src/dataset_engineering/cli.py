from __future__ import annotations

import json
from pathlib import Path

import typer

from dataset_engineering.core.models import DatasetSchema
from dataset_engineering.deduplication import deduplicate_records
from dataset_engineering.ingestion.readers import read_records
from dataset_engineering.sample import dataset_fingerprint, sample_records, split_records
from dataset_engineering.validation.engine import validate_records

app = typer.Typer(help="Prepare, validate, profile and audit AI/ML datasets.")


@app.command()
def fingerprint(data: Path):
    fmt, it = read_records(data)
    rows = list(it)
    typer.echo(dataset_fingerprint(rows))


@app.command()
def validate(data: Path, schema: Path):
    fmt, it = read_records(data)
    rows = list(it)
    report = validate_records(
        rows,
        DatasetSchema.model_validate(json.loads(schema.read_text())),
        __import__("uuid").uuid4(),
    )
    typer.echo(json.dumps(report.model_dump(), default=str, indent=2))


@app.command()
def deduplicate(data: Path):
    _, it = read_records(data)
    typer.echo(json.dumps(deduplicate_records(list(it)).model_dump(), indent=2))


@app.command()
def sample(data: Path, size: int = typer.Option(...), seed: int = 42):
    _, it = read_records(data)
    r = sample_records(list(it), size=size, seed=seed)
    typer.echo(json.dumps(r.model_dump(), default=str, indent=2))


@app.command()
def split(
    data: Path, train: float = 0.8, validation: float = 0.1, test: float = 0.1, seed: int = 42
):
    _, it = read_records(data)
    r = split_records(list(it), train=train, validation=validation, test=test, seed=seed)
    typer.echo(json.dumps(r.model_dump(), indent=2))


if __name__ == "__main__":
    app()
