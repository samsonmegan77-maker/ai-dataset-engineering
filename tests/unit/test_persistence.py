from pathlib import Path
import pytest
from dataset_engineering.persistence.models import DatasetRecord,DatasetVersionRecord,ProcessingRunRecord
from dataset_engineering.persistence.sqlite import SQLiteRepository

def test_sqlite_persists_versions_records_runs_and_artifacts(tmp_path:Path):
 db=tmp_path/'state.db'; repo=SQLiteRepository(db); d=repo.create_dataset(DatasetRecord(name='demo')); v=repo.create_version(DatasetVersionRecord(dataset_id=d.id,version=1,fingerprint='a'*64,record_count=2,schema={'fields':[]},source_metadata={'source':'test'})); repo.store_records(v.id,[{'id':1},{'id':2}]); run=repo.create_run(ProcessingRunRecord(operation='quality',input_version_id=v.id,input_fingerprint=v.fingerprint,config={'x':1})); repo.create_artifact('quality_report',v.id,{'status':'PASS'}); repo.close(); reopened=SQLiteRepository(db); assert reopened.get_dataset(d.id).current_version==1; assert reopened.get_version(v.id).fingerprint=='a'*64; assert reopened.get_records(v.id)==[{'id':1},{'id':2}]; assert reopened.get_run(run.id).operation=='quality'; reopened.close()
def test_dataset_version_is_immutable_and_duplicate_fingerprint_is_rejected(tmp_path:Path):
 repo=SQLiteRepository(tmp_path/'state.db'); d=repo.create_dataset(DatasetRecord(name='demo')); repo.create_version(DatasetVersionRecord(dataset_id=d.id,version=1,fingerprint='b'*64,record_count=0,schema={}));
 with pytest.raises(Exception): repo.create_version(DatasetVersionRecord(dataset_id=d.id,version=1,fingerprint='c'*64,record_count=0,schema={}))
 with pytest.raises(Exception): repo.create_version(DatasetVersionRecord(dataset_id=d.id,version=2,fingerprint='b'*64,record_count=0,schema={}))
 repo.close()
def test_audit_events_form_hash_chain_and_are_queryable(tmp_path:Path):
 repo=SQLiteRepository(tmp_path/'audit.db'); d=repo.create_dataset(DatasetRecord(name='audit-demo')); from dataset_engineering.persistence.models import AuditEventRecord; first=repo.create_audit(AuditEventRecord(action='DATASET_CREATED',resource_type='dataset',resource_id=d.id)); second=repo.create_audit(AuditEventRecord(action='VERSION_CREATED',resource_type='dataset',resource_id=d.id)); events=repo.list_audit(resource_type='dataset',resource_id=d.id); assert [e.sequence for e in events]==[first.sequence,second.sequence]==[1,2]; assert second.previous_hash==first.event_hash and second.event_hash; repo.close()
def test_replay_identity_is_deterministic(tmp_path:Path):
 from dataset_engineering.application.services import ApplicationService
 repo=SQLiteRepository(tmp_path/'replay.db'); service=ApplicationService(repo); d=service.create_dataset('replay-demo'); v=service.create_version(d.id,[{'id':1},{'id':2}]); run,_=service.run('sample',v.id,lambda:service.sample(repo.get_records(v.id),size=1,seed=42),{'size':1},42); result=service.replay(run.id); assert result['status']=='REPRODUCIBLE' and result['input_fingerprint']==v.fingerprint; repo.close()
