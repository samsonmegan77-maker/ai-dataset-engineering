from __future__ import annotations
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from dataset_engineering.application.services import ApplicationService
from dataset_api.dependencies.repository import get_service
from dataset_engineering.persistence.models import ProcessingRunRecord
router=APIRouter(tags=["processing"])
class DedupRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); fields:list[str]|None=None; normalize:bool=False
class TransformRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); select:list[str]|None=None; filter_field:str|None=None; filter_equals:Any=None; normalize_fields:list[str]|None=None
class SampleRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); size:int|None=Field(None,ge=0,le=100_000); fraction:float|None=Field(None,ge=0,le=1); seed:int=Field(0,ge=-2**31,le=2**31-1)
class SplitRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); train:float=Field(ge=0,le=1); validation:float=Field(ge=0,le=1); test:float=Field(ge=0,le=1); seed:int=Field(0,ge=-2**31,le=2**31-1)
class EvaluateRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); thresholds:dict[str,dict[str,float|None]]=Field(default_factory=dict)
def svc(): return get_service()
def resolve_version(service,dataset_id:UUID)->UUID:
 d=service.repo.get_dataset(dataset_id)
 if not d or d.current_version is None: raise HTTPException(404,"Dataset or current version not found")
 for v in service.repo.list_versions(dataset_id):
  if v.version==d.current_version:return v.id
 raise HTTPException(404,"Current dataset version not found")
def records(service,vid):
 if not service.repo.get_version(vid): raise HTTPException(404,"Dataset version not found")
 return service.repo.get_records(vid)
def process(service,vid,operation,fn,config=None,seed=None):
 try: run,result=service.run(operation,vid,fn,config,seed); return {"run":run,"result":result}
 except KeyError as exc: raise HTTPException(404,str(exc).strip("'")) from exc
 except ValueError as exc: raise HTTPException(422,str(exc)) from exc
@router.post("/datasets/{dataset_id}/validate")
def validate(dataset_id:UUID,service:ApplicationService=Depends(svc)):
 from dataset_engineering.core.models import DatasetSchema
 version_id=resolve_version(service,dataset_id); v=service.repo.get_version(version_id)
 if not v: raise HTTPException(404,"Dataset version not found")
 schema=DatasetSchema.model_validate(v.schema); report=service.validate(version_id,records(service,version_id),schema); service.persist_artifact("validation_report",version_id,report.model_dump(mode="json")); service.audit("VALIDATION_COMPLETED","dataset_version",version_id,metadata={"invalid_records":report.invalid_records}); return report
@router.post("/datasets/{dataset_id}/quality")
def quality(dataset_id:UUID,service:ApplicationService=Depends(svc)):
 version_id=resolve_version(service,dataset_id); rs=records(service,version_id); fields=sorted({k for r in rs for k in r}); report,_=service.quality(rs,fields,str(version_id)); service.persist_artifact("quality_report",version_id,report.model_dump(mode="json")); service.audit("QUALITY_COMPLETED","dataset_version",version_id); return report
@router.post("/datasets/{dataset_id}/deduplicate")
def deduplicate(dataset_id:UUID,req:DedupRequest,service:ApplicationService=Depends(svc)):
 version_id=resolve_version(service,dataset_id); return process(service,version_id,"deduplication",lambda:service.dedup(records(service,version_id),req.fields,req.normalize),req.model_dump())
@router.post("/datasets/{dataset_id}/transform")
def transform(dataset_id:UUID,req:TransformRequest,service:ApplicationService=Depends(svc)):
 version_id=resolve_version(service,dataset_id); return process(service,version_id,"transformation",lambda:service.transform(records(service,version_id),select=req.select,filter_field=req.filter_field,filter_equals=req.filter_equals,normalize_fields=req.normalize_fields),req.model_dump())
@router.post("/datasets/{dataset_id}/sample")
def sample(dataset_id:UUID,req:SampleRequest,service:ApplicationService=Depends(svc)):
 version_id=resolve_version(service,dataset_id); return process(service,version_id,"sampling",lambda:service.sample(records(service,version_id),size=req.size,fraction=req.fraction,seed=req.seed),req.model_dump(),req.seed)
@router.post("/datasets/{dataset_id}/split")
def split(dataset_id:UUID,req:SplitRequest,service:ApplicationService=Depends(svc)):
 version_id=resolve_version(service,dataset_id); return process(service,version_id,"split",lambda:service.split(records(service,version_id),train=req.train,validation=req.validation,test=req.test,seed=req.seed),req.model_dump(),req.seed)
@router.post("/datasets/{dataset_id}/evaluate")
def evaluate(dataset_id:UUID,req:EvaluateRequest,service:ApplicationService=Depends(svc)):
 version_id=resolve_version(service,dataset_id); rs=records(service,version_id); fields=sorted({k for r in rs for k in r})
 from dataset_engineering.evaluation import Threshold
 thresholds={k:Threshold.model_validate(v) for k,v in req.thresholds.items()}; report,result=service.quality(rs,fields,str(version_id),thresholds); service.persist_artifact("quality_report",version_id,report.model_dump(mode="json")); service.persist_artifact("evaluation",version_id,result.model_dump(mode="json")); service.audit("EVALUATION_COMPLETED","dataset_version",version_id,metadata={"status":result.status}); return {"quality":report,"evaluation":result}
@router.get("/runs/{run_id}",response_model=ProcessingRunRecord)
def get_run(run_id:UUID,service:ApplicationService=Depends(svc)):
 r=service.repo.get_run(run_id)
 if not r: raise HTTPException(404,"Processing run not found")
 return r
@router.get("/datasets/{dataset_id}/reports/{format}")
def report(dataset_id:UUID,format:str,service:ApplicationService=Depends(svc)):
 from fastapi.responses import Response
 from dataset_engineering.reporting.render import quality_as_csv,quality_as_html,quality_as_json,quality_as_markdown
 version_id=resolve_version(service,dataset_id); rs=records(service,version_id); fields=sorted({k for r in rs for k in r}); quality_report,_=service.quality(rs,fields,str(version_id)); renderers={"json":(quality_as_json,"application/json"),"markdown":(quality_as_markdown,"text/markdown; charset=utf-8"),"html":(quality_as_html,"text/html; charset=utf-8"),"csv":(quality_as_csv,"text/csv; charset=utf-8")}
 try: renderer,media=renderers[format.lower()]
 except KeyError as exc: raise HTTPException(422,"Unsupported report format") from exc
 return Response(content=renderer(quality_report),media_type=media,headers={"Content-Disposition":f'attachment; filename="dataset-quality.{format.lower()}"'})
