import json
from pathlib import Path
from typer.testing import CliRunner
from dataset_engineering.cli import app
runner=CliRunner()
def test_deduplicate_cli_json(tmp_path:Path):
 data=tmp_path/'data.jsonl'; data.write_text('{"id":1}\n{"id":1}\n{"id":2}\n',encoding='utf-8'); result=runner.invoke(app,['deduplicate',str(data),'--format','json']); assert result.exit_code==0; assert json.loads(result.stdout)['duplicate_records']==1
def test_transform_cli_json(tmp_path:Path):
 data=tmp_path/'data.jsonl'; config=tmp_path/'config.json'; data.write_text('{"id":1,"name":"  Ada  ","status":"ready"}\n{"id":2,"name":"Grace","status":"hold"}\n',encoding='utf-8'); config.write_text(json.dumps({'filter':{'field':'status','equals':'ready'},'normalize_fields':['name'],'select':['id','name']}),encoding='utf-8'); result=runner.invoke(app,['transform',str(data),'--config',str(config)]); assert result.exit_code==0; assert json.loads(result.stdout)['records']==[{'id':1,'name':'Ada'}]
