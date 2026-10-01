from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from dataset_engineering.quality.models import ConsistencyFinding


def consistency(records: Iterable[dict[str, Any]], fields: list[str]) -> list[ConsistencyFinding]:
    findings = []
    for field in fields:
        violations = sum(
            isinstance(r.get(field), str) and r[field] != r[field].strip() for r in records
        )
        if violations:
            findings.append(
                ConsistencyFinding(
                    field=field,
                    rule="trimmed_string",
                    violations=violations,
                    message="String values contain leading or trailing whitespace",
                )
            )
    return findings
