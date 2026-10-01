from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,Query
from dataset_api.dependencies.repository import get_service
from dataset_engineering.application.services import ApplicationService
router=APIRouter(tags=["provenance"])
def svc()->ApplicationService:return get_service()
@router.get("/runs/{run_id}/replay")
def replay(run_id:UUID,service:ApplicationService=Depends(svc)):
 try:return service.replay(run_id)
 except KeyError as exc:raise HTTPException(404,str(exc).strip("'")) from exc
 except ValueError as exc:raise HTTPException(422,str(exc)) from exc
@router.get("/datasets/{dataset_id}/audit")
def audit(dataset_id:UUID,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),service:ApplicationService=Depends(svc)):
 if not service.repo.get_dataset(dataset_id):raise HTTPException(404,"Dataset not found")
 events=service.repo.list_audit(resource_type="dataset",resource_id=dataset_id); version_ids={v.id for v in service.repo.list_versions(dataset_id)}; events += [e for v in version_ids for e in service.repo.list_audit(resource_type="dataset_version",resource_id=v)]; ordered=sorted({e.id:e for e in events}.values(),key=lambda e:e.sequence,reverse=True); return ordered[offset:offset+limit]
@router.get("/datasets/{dataset_id}/provenance")
def provenance(dataset_id:UUID,service:ApplicationService=Depends(svc)):
 if not service.repo.get_dataset(dataset_id):raise HTTPException(404,"Dataset not found")
 versions=service.repo.list_versions(dataset_id); return {"dataset_id":str(dataset_id),"versions":[v.model_dump(mode="json") for v in versions],"runs":[r.model_dump(mode="json") for v in versions for r in service.repo.list_runs(v.id)],"audit":[e.model_dump(mode="json") for e in service.repo.list_audit(resource_type="dataset",resource_id=dataset_id)]}
