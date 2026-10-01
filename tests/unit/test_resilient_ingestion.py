from pathlib import Path
from dataset_engineering.ingestion.readers import read_records_resilient
def test_jsonl_malformed_middle_does_not_stop_following_records(tmp_path:Path):
 p=tmp_path/'data.jsonl'; p.write_text('{"n":1}\n{bad}\n{"n":3}\n',encoding='utf-8'); errors=[]; _,r=read_records_resilient(p,on_error=lambda *a:errors.append(a)); assert list(r)==[{'n':1},{'n':3}] and errors[0][0]==2
def test_jsonl_malformed_eof_isolated(tmp_path:Path):
 p=tmp_path/'data.jsonl'; p.write_text('{"n":1}\n{',encoding='utf-8'); errors=[]; _,r=read_records_resilient(p,on_error=lambda *a:errors.append(a)); assert list(r)==[{'n':1}] and len(errors)==1
def test_csv_malformed_row_does_not_stop_following_rows(tmp_path:Path):
 p=tmp_path/'data.csv'; p.write_text('n,value\n1,a\n2\n3,c\n',encoding='utf-8'); errors=[]; _,r=read_records_resilient(p,on_error=lambda *a:errors.append(a)); assert list(r)==[{'n':'1','value':'a'},{'n':'3','value':'c'}] and errors[0][0]==1
def test_streaming_large_jsonl(tmp_path:Path):
 p=tmp_path/'large.jsonl'; p.write_text(''.join(f'{{"n":{i}}}\n' for i in range(10000)),encoding='utf-8'); _,r=read_records_resilient(p); it=iter(r); assert next(it)=={'n':0}; assert next(it)=={'n':1}; assert sum(1 for _ in it)==9998
