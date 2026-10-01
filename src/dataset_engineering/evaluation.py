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

from dataset_engineering.quality.completeness import completeness
from dataset_engineering.quality.consistency import consistency
from dataset_engineering.quality.distributions import distributions
from dataset_engineering.quality.diversity import diversity
from dataset_engineering.quality.statistics import numeric_statistics, uniqueness

def _status(value:float, threshold:Threshold|None)->EvaluationStatus:
 if threshold is None:return EvaluationStatus.PASS
 if threshold.minimum is not None and value<threshold.minimum:return EvaluationStatus.FAIL
 if threshold.maximum is not None and value>threshold.maximum:return EvaluationStatus.FAIL
 return EvaluationStatus.PASS

def evaluate_quality(records:list[dict[str,Any]], fields:list[str], dataset:str, thresholds:dict[str,Threshold]|None=None):
 start=datetime.now(timezone.utc); thresholds=thresholds or {}
 schema=DatasetSchema(fields=[FieldDefinition(name=f,data_type="string") for f in fields])
 comp=completeness(records,schema).completeness
 uniq=uniqueness(records,fields)
 numeric_fields=[f for f in fields if any(isinstance(r.get(f),(int,float)) and not isinstance(r.get(f),bool) for r in records)]
 numeric=numeric_statistics(records,numeric_fields)
 dist=distributions(records,fields)
 cons=consistency(records,fields)
 div=diversity(records,fields)
 signatures={_signature(r) for r in records}; total=len(records)
 duplicate_rate=1-len(signatures)/total if total else 0.0
 report=QualityReport(total_records=total,completeness=comp,uniqueness=uniq,numeric_statistics=numeric,distributions=dist,consistency=cons,diversity=div,duplicate_rate=max(0.0,duplicate_rate))
 metrics=[]; findings=[]

 avg=sum(m.completeness_rate for m in comp)/len(comp) if comp else 1.0
 for name,value in (("completeness",avg),("duplicate_rate",report.duplicate_rate)):
  threshold=thresholds.get(name); status=_status(value,threshold)
  metrics.append(EvaluationMetric(name=name,value=value,threshold=threshold,status=status))
  if status!=EvaluationStatus.PASS: findings.append(EvaluationFinding(metric=name,status=status,message=f"{name} is outside configured threshold"))
 if cons: findings.append(EvaluationFinding(metric="consistency",status=EvaluationStatus.WARN,message=f"{len(cons)} consistency finding(s) detected"))
 statuses=[m.status for m in metrics]+[f.status for f in findings]
 overall=EvaluationStatus.FAIL if EvaluationStatus.FAIL in statuses else EvaluationStatus.WARN if EvaluationStatus.WARN in statuses else EvaluationStatus.PASS
 end=datetime.now(timezone.utc)
 return report,Evaluation(evaluator="quality-engine",dataset=dataset,started_at=start,completed_at=end,metrics=metrics,findings=findings,status=overall)

def _signature(record:dict[str,Any])->Any:
 def h(value:Any)->Any:
  if isinstance(value,dict): return tuple(sorted((k,h(v)) for k,v in value.items()))
  if isinstance(value,list): return tuple(h(v) for v in value)
  return value
 return h(record)
