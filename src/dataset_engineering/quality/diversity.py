from typing import Any


def diversity(records: list[dict[str, Any]], fields: list[str]) -> dict[str, float]:
    return {
        field: float(
            len({str(row[field]) for row in records if field in row and row[field] is not None})
        )
        for field in fields
    }
