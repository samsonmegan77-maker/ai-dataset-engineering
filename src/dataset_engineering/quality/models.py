from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CompletenessMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    total: int = Field(ge=0)
    present: int = Field(ge=0)
    missing: int = Field(ge=0)
    null_rate: float = Field(ge=0, le=1)
    completeness_rate: float = Field(ge=0, le=1)


class UniquenessMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    total: int = Field(ge=0)
    unique: int = Field(ge=0)
    duplicate_values: int = Field(ge=0)
    uniqueness_rate: float = Field(ge=0, le=1)


class NumericStatistics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    count: int = Field(ge=0)
    minimum: float | None = None
    maximum: float | None = None
    mean: float | None = None
    median: float | None = None


class DistributionMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    counts: dict[str, int] = Field(default_factory=dict)
    distinct_values: int = Field(ge=0)


class ConsistencyFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    rule: str = Field(min_length=1)
    violations: int = Field(ge=0)
    message: str = Field(min_length=1)


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_records: int = Field(ge=0)
    completeness: list[CompletenessMetric] = Field(default_factory=list)
    uniqueness: list[UniquenessMetric] = Field(default_factory=list)
    numeric_statistics: list[NumericStatistics] = Field(default_factory=list)
    distributions: list[DistributionMetric] = Field(default_factory=list)
    consistency: list[ConsistencyFinding] = Field(default_factory=list)
    diversity: dict[str, float] = Field(default_factory=dict)
    duplicate_rate: float = Field(default=0.0, ge=0, le=1)
