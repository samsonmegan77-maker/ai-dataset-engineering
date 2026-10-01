from __future__ import annotations
from datetime import datetime,timezone
from typing import Any
from uuid import UUID,uuid4
from pydantic import BaseModel,Field
class DatasetRecord(BaseModel):id:UUID=Field(default_factory=uuid4);name:str;description:str='';created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc));current_version:int|None=None
class DatasetVersionRecord(BaseModel):id:UUID=Field(default_factory=uuid4);dataset_id:UUID;version:int;fingerprint:str;record_count:int;schema:dict[str,Any]={};created_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc));source_metadata:dict[str,Any]={}
class ProcessingRunRecord(BaseModel):id:UUID=Field(default_factory=uuid4);operation:str;input_version_id:UUID|None=None;output_version_id:UUID|None=None;input_fingerprint:str|None=None;output_fingerprint:str|None=None;config:dict[str,Any]={};seed:int|None=None;started_at:datetime=Field(default_factory=lambda:datetime.now(timezone.utc));completed_at:datetime|None=None;output_count:int|None=None;status:str='completed';manifest:dict[str,Any]={}
class AuditEventRecord(BaseModel):id:UUID=Field(default_factory=uuid4);timestamp:datetime=Field(default_factory=lambda:datetime.now(timezone.utc));action:str;resource_type:str;resource_id:UUID;run_id:UUID|None=None;metadata:dict[str,Any]={};sequence:int|None=None;previous_hash:str|None=None;event_hash:str|None=None
