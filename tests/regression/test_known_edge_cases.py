from pathlib import Path
import pytest
from dataset_engineering.ingestion.readers import IngestionError,read_records

def test_empty_csv_is_rejected(tmp_path:Path)->None:
 path=tmp_path/'empty.csv'; path.write_text('',encoding='utf-8'); _,records=read_records(path)
 with pytest.raises(IngestionError,match='no header'): list(records)
def test_blank_jsonl_file_is_valid_empty_dataset(tmp_path:Path)->None:
 path=tmp_path/'empty.jsonl'; path.write_text('\n\n',encoding='utf-8'); _,records=read_records(path); assert list(records)==[]
