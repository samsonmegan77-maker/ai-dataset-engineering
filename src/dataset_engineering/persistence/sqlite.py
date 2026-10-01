from __future__ import annotations
import json,sqlite3
from pathlib import Path
from uuid import UUID
from .models import DatasetRecord,DatasetVersionRecord,ProcessingRunRecord
class SQLiteRepository:
 def __init__(self,path):
  p=str(path).replace('sqlite:///','');self.conn=sqlite3.connect(p if p!=':memory:' else ':memory:');self.conn.row_factory=sqlite3.Row;self._init()
 def _init(self):
  self.conn.executescript('''CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY,name TEXT UNIQUE,description TEXT,created_at TEXT,current_version INTEGER);CREATE TABLE IF NOT EXISTS dataset_versions(id TEXT PRIMARY KEY,dataset_id TEXT,version INTEGER,fingerprint TEXT UNIQUE,record_count INTEGER,schema_json TEXT,created_at TEXT,source_metadata_json TEXT);CREATE TABLE IF NOT EXISTS version_records(version_id TEXT,record_index INTEGER,record_json TEXT);CREATE TABLE IF NOT EXISTS processing_runs(id TEXT PRIMARY KEY,operation TEXT,input_version_id TEXT,output_version_id TEXT,input_fingerprint TEXT,output_fingerprint TEXT,config_json TEXT,seed INTEGER,started_at TEXT,completed_at TEXT,output_count INTEGER,status TEXT,manifest_json TEXT);''');self.conn.commit()
 def create_dataset(self,d):self.conn.execute('INSERT INTO datasets VALUES(?,?,?,?,?)',(str(d.id),d.name,d.description,d.created_at.isoformat(),d.current_version));self.conn.commit();return d
 def list_datasets(self):return [DatasetRecord(id=UUID(r['id']),name=r['name'],description=r['description'],created_at=r['created_at'],current_version=r['current_version']) for r in self.conn.execute('SELECT * FROM datasets ORDER BY created_at')]
 def get_dataset(self,id):
  r=self.conn.execute('SELECT * FROM datasets WHERE id=?',(str(id),)).fetchone();return None if not r else DatasetRecord(id=UUID(r['id']),name=r['name'],description=r['description'],created_at=r['created_at'],current_version=r['current_version'])
 def create_version(self,v):
  self.conn.execute('INSERT INTO dataset_versions VALUES(?,?,?,?,?,?,?,?)',(str(v.id),str(v.dataset_id),v.version,v.fingerprint,v.record_count,json.dumps(v.schema),v.created_at.isoformat(),json.dumps(v.source_metadata)));self.conn.execute('UPDATE datasets SET current_version=? WHERE id=?',(v.version,str(v.dataset_id)));self.conn.commit();return v
 def _v(self,r):return DatasetVersionRecord(id=UUID(r['id']),dataset_id=UUID(r['dataset_id']),version=r['version'],fingerprint=r['fingerprint'],record_count=r['record_count'],schema=json.loads(r['schema_json']),created_at=r['created_at'],source_metadata=json.loads(r['source_metadata_json']))
 def list_versions(self,id):return [self._v(r) for r in self.conn.execute('SELECT * FROM dataset_versions WHERE dataset_id=? ORDER BY version',(str(id),))]
 def get_version(self,id):
  r=self.conn.execute('SELECT * FROM dataset_versions WHERE id=?',(str(id),)).fetchone();return None if not r else self._v(r)
 def store_records(self,id,records):self.conn.executemany('INSERT INTO version_records VALUES(?,?,?)',[(str(id),i,json.dumps(r,sort_keys=True)) for i,r in enumerate(records)]);self.conn.commit()
 def get_records(self,id):return [json.loads(r['record_json']) for r in self.conn.execute('SELECT record_json FROM version_records WHERE version_id=? ORDER BY record_index',(str(id),))]
 def create_run(self,r):self.conn.execute('INSERT INTO processing_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(str(r.id),r.operation,str(r.input_version_id) if r.input_version_id else None,str(r.output_version_id) if r.output_version_id else None,r.input_fingerprint,r.output_fingerprint,json.dumps(r.config),r.seed,r.started_at.isoformat(),r.completed_at.isoformat() if r.completed_at else None,r.output_count,r.status,json.dumps(r.manifest)));self.conn.commit();return r
 def _r(self,x):return ProcessingRunRecord(id=UUID(x['id']),operation=x['operation'],input_version_id=UUID(x['input_version_id']) if x['input_version_id'] else None,output_version_id=UUID(x['output_version_id']) if x['output_version_id'] else None,input_fingerprint=x['input_fingerprint'],output_fingerprint=x['output_fingerprint'],config=json.loads(x['config_json']),seed=x['seed'],started_at=x['started_at'],completed_at=x['completed_at'],output_count=x['output_count'],status=x['status'],manifest=json.loads(x['manifest_json']))
 def list_runs(self,id=None):return [self._r(x) for x in self.conn.execute('SELECT * FROM processing_runs'+(' WHERE input_version_id=?' if id else '')+' ORDER BY started_at DESC',((str(id),) if id else ())) ]
 def get_run(self,id):
  x=self.conn.execute('SELECT * FROM processing_runs WHERE id=?',(str(id),)).fetchone();return None if not x else self._r(x)
