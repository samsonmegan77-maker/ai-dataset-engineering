from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class IssueSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    data_type: str = Field(min_length=1)
    required: bool = False
    nullable: bool = True
    default: Any = None
    has_default: bool = False
    minimum: float | None = None
    maximum: float | None = None
    min_length: int | None = Field(None, ge=0)
    max_length: int | None = Field(None, ge=0)
    pattern: str | None = None
    enum: list[Any] | None = None
    properties: list[FieldDefinition] | None = None
    items: FieldDefinition | None = None

    @field_validator("data_type")
    @classmethod
    def normalize(cls, v):
        return v.strip().lower()

    @model_validator(mode="after")
    def constraints(self):
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot be greater than maximum")
        if (
            self.min_length is not None
            and self.max_length is not None
            and self.min_length > self.max_length
        ):
            raise ValueError("min_length cannot be greater than max_length")
        return self


class DatasetSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fields: list[FieldDefinition] = Field(min_length=1)

    @field_validator("fields")
    @classmethod
    def unique(cls, v):
        names = [f.name for f in v]
        if len(names) != len(set(names)):
            raise ValueError("Schema contains duplicate field names")
        return v


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    source_format: str = Field(min_length=1)
    records: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_index: int = Field(ge=0)
    field: str | None = None
    rule: str = Field(min_length=1)
    value: Any = None
    severity: IssueSeverity
    message: str = Field(min_length=1)


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: UUID
    total_records: int = Field(ge=0)
    valid_records: int = Field(ge=0)
    invalid_records: int = Field(ge=0)
    fields_checked: int = Field(0, ge=0)
    issue_counts: dict[str, int] = Field(default_factory=dict)
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return 100.0 if self.total_records == 0 else self.valid_records / self.total_records * 100

    @property
    def validity_rate(self) -> float:
        return self.success_rate
