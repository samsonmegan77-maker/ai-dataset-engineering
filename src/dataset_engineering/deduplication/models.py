from pydantic import BaseModel, ConfigDict, Field


class DuplicateGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: str = Field(min_length=1)
    record_indexes: list[int] = Field(min_length=2)
    count: int = Field(ge=2)


class DeduplicationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_records: int = Field(ge=0)
    unique_records: int = Field(ge=0)
    duplicate_records: int = Field(ge=0)
    duplicate_groups: list[DuplicateGroup] = Field(default_factory=list)
    strategy: str
    fields: list[str] = Field(default_factory=list)
