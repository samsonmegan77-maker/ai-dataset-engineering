from __future__
"""PostgreSQL repository adapter implementing the same boundary as SQLite."""
import json
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import create_engine, text
from dataset_engineering.persistence.models import AuditEventRecord, DatasetRecord, DatasetVersionRecord, ProcessingRunRecord
from dataset_engineering.provenance import event_hash

class SQLAlchemyRepository:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, future=True, pool_pre_ping=True)
        self._init_schema()
    def _init_schema(self) -> None:
        with self.engine.begin() as c:
            c.execute(text("CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, description TEXT NOT NULL, created_at TEXT NOT NULL, current_version INTEGER)"))
            c.execute(text("CREATE TABLE IF NOT EXISTS dataset_versions (id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, version INTEGER NOT NULL, fingerprint TEXT NOT NULL, record_count INTEGER NOT NULL, schema_json TEXT NOT NULL, created_at TEXT NOT NULL, source_metadata_json TEXT NOT NULL, UNIQUE(dataset_id, version), UNIQUE(dataset_id, fingerprint))"))
            c.execute(text("CREATE TABLE IF NOT EXISTS version_records (version_id TEXT NOT NULL, record_index INTEGER NOT NULL, record_json TEXT NOT NULL, PRIMARY KEY(version_id, record_index))"))
            c.execute(text("CREATE TABLE IF NOT EXISTS processing_runs (id TEXT PRIMARY KEY, operation TEXT NOT NULL, input_version_id TEXT, output_version_id TEXT, input_fingerprint TEXT, output_fingerprint TEXT, config_json TEXT NOT NULL, seed INTEGER, started_at TEXT NOT NULL, completed_at TEXT, output_count INTEGER, status TEXT NOT NULL, manifest_json TEXT NOT NULL)"))
            c.execute(text("CREATE TABLE IF NOT EXISTS processing_artifacts (id TEXT PRIMARY KEY, artifact_type TEXT NOT NULL, resource_id TEXT NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL)"))
            c.execute(text("CREATE TABLE IF NOT EXISTS audit_events (id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, run_id TEXT, metadata_json TEXT NOT NULL, sequence BIGINT UNIQUE NOT NULL, previous_hash TEXT, event_hash TEXT UNIQUE NOT NULL)"))
            c.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"))
            c.execute(text("CREATE INDEX IF NOT EXISTS idx_versions_dataset ON dataset_versions(dataset_id, version)"))
            c.execute(text("CREATE INDEX IF NOT EXISTS idx_runs_input ON processing_runs(input_version_id)"))
            c.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_events(resource_type, resource_id)"))
    def create_dataset(self, d: DatasetRecord) -> DatasetRecord:
        with self.engine.begin() as c: c.execute(text("INSERT INTO datasets VALUES (:id,:name,:description,:created_at,:current_version)"), {"id":str(d.id),"name":d.name,"description":d.description,"created_at":d.created_at.isoformat(),"current_version":d.current_version})
        return d
    def _dataset(self,r): return DatasetRecord(id=UUID(r[0]),name=r[1],description=r[2],created_at=datetime.fromisoformat(r[3]),current_version=r[4])
    def list_datasets(self):
        with self.engine.connect() as c: rows=c.execute(text("SELECT id,name,description,created_at,current_version FROM datasets ORDER BY created_at,id")).fetchall()
        return [self._dataset(r) for r in rows]
    def get_dataset(self,i):
        with self.engine.connect() as c:r=c.execute(text("SELECT id,name,description,created_at,current_version FROM datasets WHERE id=:id"),{"id":str(i)}).first()
        return None if r is None else self._dataset(r)
    def create_version(self,v):
        with self.engine.begin() as c:
            c.execute(text("INSERT INTO dataset_versions VALUES (:id,:dataset_id,:version,:fingerprint,:record_count,:schema_json,:created_at,:source_metadata_json)"),{"id":str(v.id),"dataset_id":str(v.dataset_id),"version":v.version,"fingerprint":v.fingerprint,"record_count":v.record_count,"schema_json":json.dumps(v.schema,sort_keys=True),"created_at":v.created_at.isoformat(),"source_metadata_json":json.dumps(v.source_metadata,sort_keys=True)})
            c.execute(text("UPDATE datasets SET current_version=:v WHERE id=:id AND (current_version IS NULL OR current_version < :v)"),{"v":v.version,"id":str(v.dataset_id)})
        return v
    def _version(self,r): return DatasetVersionRecord(id=UUID(r[0]),dataset_id=UUID(r[1]),version=r[2],fingerprint=r[3],record_count=r[4],schema=json.loads(r[5]),created_at=datetime.fromisoformat(r[6]),source_metadata=json.loads(r[7]))
    def list_versions(self,i):
        with self.engine.connect() as c: rows=c.execute(text("SELECT id,dataset_id,version,fingerprint,record_count,schema_json,created_at,source_metadata_json FROM dataset_versions WHERE dataset_id=:id ORDER BY version"),{"id":str(i)}).fetchall()
        return [self._version(r) for r in rows]
    def get_version(self,i):
        with self.engine.connect() as c:r=c.execute(text("SELECT id,dataset_id,version,fingerprint,record_count,schema_json,created_at,source_metadata_json FROM dataset_versions WHERE id=:id"),{"id":str(i)}).first()
        return None if r is None else self._version(r)
    def store_records(self, version_id, records):
        with self.engine.begin() as c:c.execute(text("INSERT INTO version_records(version_id,record_index,record_json) VALUES (:version_id,:record_index,:record_json)"),[{"version_id":str(version_id),"record_index":i,"record_json":json.dumps(r,sort_keys=True,ensure_ascii=False)} for i,r in enumerate(records)])
    def get_records(self, version_id):
        with self.engine.connect() as c: rows=c.execute(text("SELECT record_json FROM version_records WHERE version_id=:id ORDER BY record_index"),{"id":str(version_id)}).fetchall()
        return [json.loads(r[0]) for r in rows]
    def _run(self,r): return ProcessingRunRecord(id=UUID(r[0]),operation=r[1],input_version_id=UUID(r[2]) if r[2] else None,output_version_id=UUID(r[3]) if r[3] else None,input_fingerprint=r[4],output_fingerprint=r[5],config=json.loads(r[6]),seed=r[7],started_at=datetime.fromisoformat(r[8]),completed_at=datetime.fromisoformat(r[9]) if r[9] else None,output_count=r[10],status=r[11],manifest=json.loads(r[12]))
    def create_run(self,r):
        with self.engine.begin() as c:c.execute(text("INSERT INTO processing_runs VALUES (:id,:operation,:input_version_id,:output_version_id,:input_fingerprint,:output_fingerprint,:config_json,:seed,:started_at,:completed_at,:output_count,:status,:manifest_json)"),{"id":str(r.id),"operation":r.operation,"input_version_id":str(r.input_version_id) if r.input_version_id else None,"output_version_id":str(r.output_version_id) if r.output_version_id else None,"input_fingerprint":r.input_fingerprint,"output_fingerprint":r.output_fingerprint,"config_json":json.dumps(r.config,sort_keys=True),"seed":r.seed,"started_at":r.started_at.isoformat(),"completed_at":r.completed_at.isoformat() if r.completed_at else None,"output_count":r.output_count,"status":r.status,"manifest_json":json.dumps(r.manifest,sort_keys=True)})
        return r
    def get_run(self,i):
        with self.engine.connect() as c:r=c.execute(text("SELECT * FROM processing_runs WHERE id=:id"),{"id":str(i)}).first()
        return None if r is None else self._run(r)
    def list_runs(self,version_id=None):
        sql="SELECT * FROM processing_runs"; params={}
        if version_id: sql+=" WHERE input_version_id=:id"; params["id"]=str(version_id)
        sql+=" ORDER BY started_at DESC"
        with self.engine.connect() as c: rows=c.execute(text(sql),params).fetchall()
        return [self._run(r) for r in rows]
    def update_run(self,r):
        with self.engine.begin() as c:c.execute(text("UPDATE processing_runs SET output_version_id=:ov,output_fingerprint=:of,completed_at=:ca,output_count=:oc,status=:s,manifest_json=:m WHERE id=:id"),{"ov":str(r.output_version_id) if r.output_version_id else None,"of":r.output_fingerprint,"ca":r.completed_at.isoformat() if r.completed_at else None,"oc":r.output_count,"s":r.status,"m":json.dumps(r.manifest,sort_keys=True),"id":str(r.id)})
        return r
    def create_artifact(self,artifact_type,resource_id,payload):
        import uuid
        with self.engine.begin() as c:c.execute(text("INSERT INTO processing_artifacts VALUES (:id,:type,:resource,:payload,:created)"),{"id":str(uuid.uuid4()),"type":artifact_type,"resource":str(resource_id),"payload":json.dumps(payload,sort_keys=True,default=str),"created":datetime.now(timezone.utc).isoformat()})
    def create_audit(self,e):
        with self.engine.begin() as c:
            row=c.execute(text("SELECT sequence,event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1")).first(); sequence=(int(row[0])+1) if row else 1; previous=row[1] if row else None
            digest=event_hash(sequence,e.timestamp.isoformat(),e.action,e.resource_type,str(e.resource_id),str(e.run_id) if e.run_id else None,e.metadata,previous)
            c.execute(text("INSERT INTO audit_events VALUES (:id,:timestamp,:action,:resource_type,:resource_id,:run_id,:metadata_json,:sequence,:previous_hash,:event_hash)"),{"id":str(e.id),"timestamp":e.timestamp.isoformat(),"action":e.action,"resource_type":e.resource_type,"resource_id":str(e.resource_id),"run_id":str(e.run_id) if e.run_id else None,"metadata_json":json.dumps(e.metadata,sort_keys=True,default=str),"sequence":sequence,"previous_hash":previous,"event_hash":digest})
        return e.model_copy(update={"sequence":sequence,"previous_hash":previous,"event_hash":digest})
    def list_audit(self,resource_type=None,resource_id=None):
        sql="SELECT * FROM audit_events WHERE 1=1"; params={}
        if resource_type: sql+=" AND resource_type=:type"; params["type"]=resource_type
        if resource_id: sql+=" AND resource_id=:resource"; params["resource"]=str(resource_id)
        sql+=" ORDER BY sequence"
        with self.engine.connect() as c: rows=c.execute(text(sql),params).fetchall()
        return [AuditEventRecord(id=UUID(r[0]),timestamp=datetime.fromisoformat(r[1]),action=r[2],resource_type=r[3],resource_id=UUID(r[4]),run_id=UUID(r[5]) if r[5] else None,metadata=json.loads(r[6]),sequence=r[7],previous_hash=r[8],event_hash=r[9]) for r in rows]
    def list_artifacts(self,resource_id):
        with self.engine.connect() as c: rows=c.execute(text("SELECT id,artifact_type,resource_id,payload_json,created_at FROM processing_artifacts WHERE resource_id=:id ORDER BY created_at"),{"id":str(resource_id)}).fetchall()
        return [{"id":r[0],"artifact_type":r[1],"resource_id":r[2],"payload":json.loads(r[3]),"created_at":r[4]} for r in rows]
    def close(self): self.engine.dispose()
