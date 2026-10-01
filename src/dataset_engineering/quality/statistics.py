from collections import Counter
from statistics import mean, median
from typing import Any
def _hashable(value: Any) -> Any:
    if isinstance(value, dict): return tuple(sorted((k, _hashable(v)) for k,v in value.items()))
    if isinstance(value, list): return tuple(_hashable(v) for v in value)
    return value
def uniqueness(records: list[dict[str, Any]], fields: list[str]) -> list[Any]:
    from dataset_engineering.quality.models import UniquenessMetric
    values={f:[] for f in fields}
    for row in records:
        for f in fields:
            if f in row and row[f] is not None: values[f].append(_hashable(row[f]))
    return [UniquenessMetric(field=f,total=len(v),unique=len(set(v)),duplicate_values=len(v)-len(set(v)),uniqueness_rate=len(set(v))/len(v) if v else 1.0) for f,v in values.items()]
def numeric_statistics(records: list[dict[str, Any]], fields: list[str]) -> list[Any]:
    from dataset_engineering.quality.models import NumericStatistics
    values={f:[] for f in fields}
    for row in records:
        for f in fields:
            v=row.get(f)
            if isinstance(v,(int,float)) and not isinstance(v,bool): values[f].append(float(v))
    return [NumericStatistics(field=f,count=len(v),minimum=min(v) if v else None,maximum=max(v) if v else None,mean=mean(v) if v else None,median=median(v) if v else None) for f,v in values.items()]
def categorical_distributions(records: list[dict[str, Any]], fields: list[str], limit: int=20) -> dict[str, dict[str,int]]:
    counts={f:Counter() for f in fields}
    for row in records:
        for f in fields:
            if f in row and row[f] is not None: counts[f][str(row[f])] += 1
    return {f:dict(c.most_common(limit)) for f,c in counts.items()}
def top_issue_counts(issue_counts: dict[str,int], limit:int=10) -> list[tuple[str,int]]:
    return Counter(issue_counts).most_common(limit)
