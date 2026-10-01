import json
from pathlib import Path
from typer.testing import CliRunner
from dataset_engineering.cli import app

def test_cli_validates_example_dataset():
 r=CliRunner().invoke(app,['validate',str(Path(__file__).parents[2]/'examples'/'sample.jsonl'),'--schema',str(Path(__file__).parents[2]/'examples'/'schema.json'),'--format','json']); assert r.exit_code==0,r.stdout; p=json.loads(r.stdout); assert p['total_records']==3 and p['invalid_records']==1

def test_cli_writes_markdown_report(tmp_path:Path):
 root=Path(__file__).parents[2]; out=tmp_path/'report.md'; r=CliRunner().invoke(app,['validate',str(root/'examples'/'sample.jsonl'),'--schema',str(root/'examples'/'schema.json'),'--output',str(out)]); assert r.exit_code==0,r.stdout; assert '# Dataset Validation' in out.read_text(encoding='utf-8')

def test_cli_rejects_unknown_report_format():
 root=Path(__file__).parents[2]; r=CliRunner().invoke(app,['validate',str(root/'examples'/'sample.jsonl'),'--schema',str(root/'examples'/'schema.json'),'--format','xml']); assert r.exit_code!=0; assert "Format must be 'markdown' or 'json'." in r.stderr
