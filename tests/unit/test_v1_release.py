from pathlib import Path
def test_sqlite_migrations_record_baseline(tmp_path:Path):
 from dataset_engineering.persistence.sqlite import SQLiteRepository
 repo=SQLiteRepository(tmp_path/'migration.db'); assert [int(x[0]) for x in repo.conn.execute('SELECT version FROM schema_migrations ORDER BY version').fetchall()]==[1]; repo.close()
def test_replay_detects_output_tampering(tmp_path:Path):
 from dataset_engineering.application.services import ApplicationService
 from dataset_engineering.persistence.sqlite import SQLiteRepository
 repo=SQLiteRepository(tmp_path/'replay.db'); service=ApplicationService(repo); dataset=service.create_dataset('tamper-check'); version=service.create_version(dataset.id,[{'id':1}]); run,result=service.run('sampling',version.id,lambda:[{'id':2}],{'size':1},42); assert result==[{'id':2}]; repo.conn.execute('UPDATE version_records SET record_json=? WHERE version_id=?',('{"id":999}',str(run.output_version_id))); repo.conn.commit(); assert service.replay(run.id)['status']=='MISMATCH'; repo.close()
def test_version_creation_rolls_back_on_duplicate_fingerprint(tmp_path):
 from dataset_engineering.application.services import ApplicationService
 from dataset_engineering.persistence.sqlite import SQLiteRepository
 repo=SQLiteRepository(tmp_path/'rollback.db'); service=ApplicationService(repo); dataset=service.create_dataset('rollback-check'); first=service.create_version(dataset.id,[{'id':1}])
 try: service.create_version(dataset.id,[{'id':1}])
 except Exception: pass
 else: raise AssertionError('duplicate version creation should fail')
 assert [v.version for v in repo.list_versions(dataset.id)]==[first.version] and repo.get_dataset(dataset.id).current_version==first.version; repo.close()
