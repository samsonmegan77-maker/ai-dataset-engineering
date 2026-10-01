from pathlib import Path
import pytest
from dataset_engineering.ingestion.readers import IngestionError,read_records

def test_jsonl_reader_skips_blank_lines(tmp_path:Path):
 p=tmp_path/'data.jsonl'; p.write_text('{"name":"Ada"}\n\n{"name":"Grace"}\n',encoding='utf-8'); f,r=read_records(p); assert f=='jsonl'; assert list(r)==[{'name':'Ada'},{'name':'Grace'}]
def test_invalid_jsonl_is_rejected(tmp_path:Path):
 p=tmp_path/'data.jsonl'; p.write_text('{bad}\n',encoding='utf-8'); _,r=read_records(p); 
 with pytest.raises(IngestionError,match='line 1'): list(r)
def test_jsonl_non_object_is_rejected(tmp_path:Path):
 p=tmp_path/'data.jsonl'; p.write_text('[1,2]\n',encoding='utf-8'); _,r=read_records(p)
 with pytest.raises(IngestionError,match='not an object'): list(r)
def test_json_array_is_read(tmp_path:Path):
 p=tmp_path/'data.json'; p.write_text('[{"name":"Ada"}]',encoding='utf-8'); f,r=read_records(p); assert f=='json'; assert list(r)==[{'name':'Ada'}]
def test_json_requires_array_of_objects(tmp_path:Path):
 p=tmp_path/'data.json'; p.write_text('{"name":"Ada"}',encoding='utf-8'); _,r=read_records(p)
 with pytest.raises(IngestionError,match='array of objects'): list(r)
def test_csv_reader_handles_normal_rows(tmp_path:Path):
 p=tmp_path/'data.csv'; p.write_text('name,age\nAda,36\nGrace,28\n',encoding='utf-8'); f,r=read_records(p); assert f=='csv'; assert list(r)==[{'name':'Ada','age':'36'},{'name':'Grace','age':'28'}]
def test_csv_rejects_extra_columns(tmp_path:Path):
 p=tmp_path/'data.csv'; p.write_text('name,age\nAda,36,extra\n',encoding='utf-8'); _,r=read_records(p)
 with pytest.raises(IngestionError,match='unexpected columns'): list(r)
def test_csv_rejects_missing_columns(tmp_path:Path):
 p=tmp_path/'data.csv'; p.write_text('name,age\nAda\n',encoding='utf-8'); _,r=read_records(p)
 with pytest.raises(IngestionError,match='missing columns'): list(r)
def test_csv_rejects_duplicate_header(tmp_path:Path):
 p=tmp_path/'data.csv'; p.write_text('name,name\nAda,Grace\n',encoding='utf-8'); _,r=read_records(p)
 with pytest.raises(IngestionError,match='duplicate'): list(r)
def test_unsupported_format_is_rejected(tmp_path:Path):
 p=tmp_path/'data.txt'; p.write_text('hello',encoding='utf-8')
 with pytest.raises(IngestionError): read_records(p)
