from fastapi.testclient import TestClient
from pathlib import Path

def test_api_end_to_end(tmp_path:Path,monkeypatch):
 monkeypatch.setenv('DATABASE_URL',f"sqlite:///{tmp_path/'api.db'}"); from dataset_api.main import app; from dataset_api.dependencies.repository import get_service; get_service.cache_clear(); client=TestClient(app); assert client.get('/health').status_code==200; r=client.post('/datasets',json={'name':'customers','description':'demo'}); assert r.status_code==201; did=r.json()['id']; r=client.post(f'/datasets/{did}/versions',json={'records':[{'id':1,'email':'a@example.com'},{'id':2,'email':'b@example.com'}],'schema':{'fields':[{'name':'id','data_type':'integer','required':True,'nullable':False},{'name':'email','data_type':'string','required':True,'nullable':False}]}}); assert r.status_code==201 and r.json()['version']==1; assert client.get(f'/datasets/{did}/versions').status_code==200; assert client.post(f'/datasets/{did}/quality').status_code==200; assert client.post(f'/datasets/{did}/deduplicate',json={'normalize':False}).status_code==200; assert client.post(f'/datasets/{did}/sample',json={'size':1,'seed':7}).status_code==200; assert client.post(f'/datasets/{did}/split',json={'train':.5,'validation':0.0,'test':.5,'seed':7}).status_code==200; assert client.post(f'/datasets/{did}/evaluate',json={}).status_code==200

def test_api_404_and_422():
 from dataset_api.main import app
 client=TestClient(app); assert client.get('/datasets/not-a-uuid').status_code==422; assert client.get('/datasets/00000000-0000-0000-0000-000000000000').status_code==404
