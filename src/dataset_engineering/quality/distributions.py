from __future__ import annotations
from collections.abc import Iterable
from typing import Any
from dataset_engineering.quality.models import DistributionMetric
from dataset_engineering.quality.statistics import categorical_distributions

def distributions(records: Iterable[dict[str, Any]], fields: list[str], limit: int = 20) -> list[DistributionMetric]:
    return [DistributionMetric(field=f,counts=counts,distinct_values=len(counts)) for f,counts in categorical_distributions(records,fields,limit).items()]
