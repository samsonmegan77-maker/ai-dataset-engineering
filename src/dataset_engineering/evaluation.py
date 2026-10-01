from __future__ import annotations
from pydantic import BaseModel,Field
from .quality.completeness import completeness_metrics
class Threshold(BaseModel):minimum:float|None=None;maximum:float|None=None
class MetricResult(BaseModel):name:str;value:float;unit:str;status:str
class EvaluationResult(BaseModel):status:str;evaluator:str='deterministic';metrics:list[MetricResult];findings:list[dict]
def evaluate_quality(records,fields,name,thresholds):
 from .quality.models import QualityReport
 report=QualityReport(total_records=len(records),duplicate_rate=0.0,completeness=completeness_metrics(records,fields),numeric_statistics=[],distributions=[],consistency=[],diversity=[])
 metrics=[MetricResult(name=m.field,value=m.completeness_rate,unit='ratio',status='PASS') for m in report.completeness]
 findings=[]
 for m in metrics:
  t=thresholds.get(m.name)
  if t and t.minimum is not None and m.value<t.minimum:m.status='FAIL';findings.append({'status':'FAIL','metric':m.name,'message':'Below minimum'})
 status='FAIL' if any(m.status=='FAIL' for m in metrics) else 'PASS'
 return report,EvaluationResult(status=status,metrics=metrics,findings=findings)
