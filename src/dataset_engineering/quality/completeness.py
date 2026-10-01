from .models import CompletenessMetric


def completeness_metrics(records, fields):
    n = len(records)
    return [
        CompletenessMetric(
            field=f,
            total=n,
            present=sum(1 for r in records if f in r and r[f] is not None),
            missing=sum(1 for r in records if f not in r),
            null_rate=(sum(1 for r in records if r.get(f) is None) / n if n else 0),
            completeness_rate=(
                sum(1 for r in records if f in r and r[f] is not None) / n if n else 1
            ),
        )
        for f in fields
    ]


def completeness(records, schema):
    fields = [f.name for f in schema.fields]
    return type("Report", (), {"completeness": completeness_metrics(records, fields)})()
