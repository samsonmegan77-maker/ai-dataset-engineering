import csv,io,json
from pathlib import Path
pytest=__import__('pytest'); hypothesis=pytest.importorskip('hypothesis'); from hypothesis import given,strategies as st
from dataset_engineering.ingestion.readers import read_records_resilient
@given(st.lists(st.one_of(st.text(max_size=30),st.none()),min_size=0,max_size=30))
def test_csv_round_trip_for_generated_values(tmp_path:Path,values:list[str|None])->None:
 path=tmp_path/'generated.csv'; output=io.StringIO(newline=''); writer=csv.writer(output); writer.writerow(['value']); [writer.writerow(['' if v is None else v]) for v in values]; path.write_text(output.getvalue(),encoding='utf-8'); _,records=read_records_resilient(path); assert len(list(records))==len(values)
@given(st.integers(min_value=-5,max_value=5))
def test_jsonl_generated_integer_round_trip(tmp_path:Path,value:int)->None:
 path=tmp_path/'generated.jsonl'; path.write_text(json.dumps({'value':value})+'\n',encoding='utf-8'); _,records=read_records_resilient(path); assert list(records)==[{'value':value}]
