from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from .models import DeduplicationReport, DuplicateGroup


def _norm(v):
    if isinstance(v, str):
        return " ".join(v.casefold().split())
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_norm(x) for x in v]
    return v


def _key(v):
    return hashlib.sha256(
        json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def deduplicate_records(
    records: Iterable[dict[str, Any]], *, fields: list[str] | None = None, normalize: bool = False
):
    groups = defaultdict(list)
    total = 0
    for i, r in enumerate(records):
        total += 1
        v = {f: r.get(f) for f in fields} if fields else r
        groups[_key(_norm(v) if normalize else v)].append(i)
    dup = [
        DuplicateGroup(key=k, record_indexes=v, count=len(v))
        for k, v in groups.items()
        if len(v) > 1
    ]
    d = sum(len(x.record_indexes) - 1 for x in dup)
    return DeduplicationReport(
        total_records=total,
        unique_records=total - d,
        duplicate_records=d,
        duplicate_groups=dup,
        strategy="fields" if fields else "exact",
        fields=fields or [],
    )
