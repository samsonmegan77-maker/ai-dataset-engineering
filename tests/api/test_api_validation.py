from fastapi.testclient import TestClient
from dataset_api.main import app
from dataset_api.dependencies.repository import get_service

def test_api_rejects_bad_payloads_and_missing_resources(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path}/api.db'); get_service.cache_clear(); c=TestClient(app)
    bad=c.post('/datasets',json={'name':'bad name'}); assert bad.status_code==422; assert bad.json()['error']=='validation_error'; assert 'details' in bad.json()
    assert c.post('/datasets',json={'name':'valid'}).status_code==201; assert c.post('/datasets',json={'name':'valid'}).status_code==409
    assert c.post('/datasets/00000000-0000-0000-0000-000000000000/quality').status_code==404

def test_import_preview_and_report_formats(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path}/imports.db'); get_service.cache_clear(); c=TestClient(app); payload=b'id,email\n1,a@example.com\n2,b@example.com\n'
    r=c.post('/imports/preview',files={'file':('customers.csv',payload,'text/csv')}); assert r.status_code==200; assert r.json()['format']=='csv'; assert r.json()['record_count']==2
    r=c.post('/imports',data={'name':'imported','description':'test'},files={'file':('customers.csv',payload,'text/csv')}); assert r.status_code==201; did=r.json()['dataset']['id']; assert c.get(f'/datasets/{did}/runs').status_code==200
    for fmt in ('json','markdown','html','csv'):
        rr=c.get(f'/datasets/{did}/reports/{fmt}'); assert rr.status_code==200 and rr.content

def test_import_rejects_unsupported_format(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path}/bad-import.db'); get_service.cache_clear(); c=TestClient(app); assert c.post('/imports/preview',files={'file':('customers.txt',b'hello','text/plain')}).status_code==415

def test_api_pagination_bounds(tmp_path, monkeypatch):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path}/pagination.db'); get_service.cache_clear(); c=TestClient(app)
    for i in range(3): assert c.post('/datasets',json={'name':f'ds{i}'}).status_code==201
    assert len(c.get('/datasets?limit=2&offset=0').json())==2; assert len(c.get('/datasets?limit=2&offset=2').json())==1; assert c.get('/datasets?limit=1001').status_code==422; assert c.get('/datasets?offset=-1').status_code==422
