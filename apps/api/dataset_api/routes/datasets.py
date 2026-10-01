from __future__ import annotations
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from dataset_engineering.application.services import ApplicationService
from dataset_engineering.persistence.models import DatasetRecord, DatasetVersionRecord, ProcessingRunRecord
from dataset_api.dependencies.repository import get_service
router=APIRouter(prefix="/datasets", tags=["datasets"])
class CreateDatasetRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); name:str=Field(min_length=1,max_length=200,pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$"); description:str=Field(default="",max_length=2000)
class CreateVersionRequest(BaseModel):
 model_config=ConfigDict(extra="forbid"); records:list[dict[str,Any]]=Field(min_length=0,max_length=100_000); schema:dict[str,Any]=Field(default_factory=dict); source_metadata:dict[str,Any]=Field(default_factory=dict,max_length=50)
def svc(): return get_service()
@router.post("",response_model=DatasetRecord,status_code=201)
def create_dataset(req:CreateDatasetRequest, service:ApplicationService=Depends(svc)):
 try:return service.create_dataset(req.name,req.description)
 except Exception as exc:
  if "UNIQUE" in str(exc).upper(): raise HTTPException(409,"Dataset name already exists") from exc
  raise
@router.get("",response_model=list[DatasetRecord])
def list_datasets(limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),service:ApplicationService=Depends(svc)): return service.repo.list_datasets()[offset:offset+limit]
@router.get("/{dataset_id}",response_model=DatasetRecord)
def get_dataset(dataset_id:UUID,service:ApplicationService=Depends(svc)):
 d=service.repo.get_dataset(dataset_id)
 if not d: raise HTTPException(404,"Dataset not found")
 return d
@router.post("/{dataset_id}/versions",response_model=DatasetVersionRecord,status_code=201)
def create_version(dataset_id:UUID,req:CreateVersionRequest,service:ApplicationService=Depends(svc)):
 try:return service.create_version(dataset_id,req.records,req.schema,req.source_metadata)
 except KeyError as exc: raise HTTPException(404,"Dataset not found") from exc
 except Exception as exc:
  if "UNIQUE" in str(exc).upper(): raise HTTPException(409,"Identical dataset version already exists") from exc
  raise
@router.get("/{dataset_id}/versions",response_model=list[DatasetVersionRecord])
def versions(dataset_id:UUID,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),service:ApplicationService=Depends(svc)):
 if not service.repo.get_dataset(dataset_id): raise HTTPException(404,"Dataset not found")
 return service.repo.list_versions(dataset_id)[offset:offset+limit]
@router.get("/{dataset_id}/runs",response_model=list[ProcessingRunRecord])
def dataset_runs(dataset_id:UUID,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),service:ApplicationService=Depends(svc)):
 if not service.repo.get_dataset(dataset_id): raise HTTPException(404,"Dataset not found")
 version_ids=[v.id for v in service.repo.list_versions(dataset_id)]; runs=[run for version_id in version_ids for run in service.repo.list_runs(version_id)]; ordered=sorted({run.id:run for run in runs}.values(),key=lambda run:run.started_at,reverse=True); return ordered[offset:offset+limit]
