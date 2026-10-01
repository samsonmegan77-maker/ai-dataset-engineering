from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter,Depends,File,Form,HTTPException,UploadFile
from dataset_api.dependencies.repository import get_service
from dataset_engineering.application.services import ApplicationService
from dataset_engineering.ingestion.readers import read_records
router=APIRouter(tags=['imports'])
@router.post('/imports/preview')
async def preview(file:UploadFile=File(...)):
 payload=await file.read(10*1024*1024+1)
 if len(payload)>10*1024*1024:raise HTTPException(413,'Upload exceeds configured limit')
 path=Path('/tmp')/('ade-'+(file.filename or 'dataset.jsonl'));path.write_bytes(payload)
 try:
  fmt,it=read_records(path);rows=list(it);return {'format':fmt,'record_count':len(rows),'preview':rows[:10]}
 finally:path.unlink(missing_ok=True)
@router.post('/imports')
async def import_dataset(name:str=Form(...),description:str=Form(''),file:UploadFile=File(...),service:ApplicationService=Depends(get_service)):
 payload=await file.read(10*1024*1024+1)
 if len(payload)>10*1024*1024:raise HTTPException(413,'Upload exceeds configured limit')
 path=Path('/tmp')/('ade-'+(file.filename or 'dataset.jsonl'));path.write_bytes(payload)
 try:
  fmt,it=read_records(path);rows=list(it);d=service.create_dataset(name,description);v=service.create_version(d.id,rows,{}, {'source_format':fmt,'filename':file.filename});return {'dataset':d,'version':v}
 except Exception as e:raise HTTPException(422,str(e)) from e
 finally:path.unlink(missing_ok=True)
