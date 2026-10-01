from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from dataset_engineering.core.models import DatasetSchema, FieldDefinition
from dataset_engineering.quality.models import QualityReport
class EvaluationStatus(StrEnum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"
class Threshold(BaseModel):
 model_config=ConfigDict(extra="forbid")
 minimum:float|None=None
 maximum:float|None=None
class EvaluationMetric(BaseModel):
 model_config=ConfigDict(extra="forbid")
 name:str=Field(min_length=1); value:float; unit:str="ratio"; threshold:Threshold|None=None; status:EvaluationStatus
class EvaluationFinding(BaseModel):
 model_config=ConfigDict(extra="forbid")
 metric:str=Field(min_length=1); status:EvaluationStatus; message:str=Field(min_length=1)
class Evaluation(BaseModel):
 model_config=ConfigDict(extra="forbid")
 id:UUID=Field(default_factory=uuid4); evaluator:str; dataset:str; started_at:datetime; completed_at:datetime
 metrics:list[EvaluationMetric]=Field(default_factory=list); findings:list[EvaluationFinding]=Field(default_factory=list); status:EvaluationStatus
