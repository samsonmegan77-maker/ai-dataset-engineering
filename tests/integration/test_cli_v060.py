from typer.testing import CliRunner
from dataset_engineering.cli import app
runner=CliRunner()
def write_jsonl(tmp_path):
 p=tmp_path/'data.jsonl'; p.write_text('\n'.join('{"id": %d}'%i for i in range(10))+'\n',encoding='utf-8'); return p
def test_fingerprint_cli(tmp_path):
 p=write_jsonl(tmp_path); result=runner.invoke(app,['fingerprint',str(p)]); assert result.exit_code==0 and 'fingerprint' in result.stdout
def test_sample_cli_json(tmp_path):
 p=write_jsonl(tmp_path); result=runner.invoke(app,['sample',str(p),'--size','3','--seed','42']); assert result.exit_code==0 and 'output_count' in result.stdout
def test_sample_cli_jsonl(tmp_path):
 p=write_jsonl(tmp_path); result=runner.invoke(app,['sample',str(p),'--fraction','.2','--seed','42','--format','jsonl']); assert result.exit_code==0 and result.stdout.count('{')==2
def test_split_cli(tmp_path):
 p=write_jsonl(tmp_path); result=runner.invoke(app,['split',str(p),'--train','.8','--validation','.1','--test','.1','--seed','42']); assert result.exit_code==0 and 'output_counts' in result.stdout
