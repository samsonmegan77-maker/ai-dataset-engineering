from __future__ import annotations
import os
from pydantic import BaseModel
class Settings(BaseModel):database_url:str='sqlite:///./dataset_engineering.db';cors_origins:tuple[str,...]=('http://localhost:5173',);max_upload_bytes:int=10*1024*1024;log_level:str='INFO'
 @classmethod
 def from_env(cls):return cls(database_url=os.getenv('DATABASE_URL',cls().database_url),cors_origins=tuple(x.strip() for x in os.getenv('CORS_ORIGINS',','.join(cls().cors_origins)).split(',') if x.strip()),max_upload_bytes=int(os.getenv('MAX_UPLOAD_BYTES',str(cls().max_upload_bytes))),log_level=os.getenv('LOG_LEVEL','INFO'))
