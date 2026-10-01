from uuid import uuid4
from dataset_engineering.core.models import DatasetSchema,FieldDefinition
from dataset_engineering.validation.engine import validate_records
def test_validation_accepts_valid_records():
 s=DatasetSchema(fields=[FieldDefinition(name='name',data_type='string',required=True),FieldDefinition(name='age',data_type='integer')]);r=validate_records([{'name':'Ada','age':36}],s,uuid4());assert r.valid_records==1 and r.invalid_records==0
def test_validation_reports_missing():
 s=DatasetSchema(fields=[FieldDefinition(name='name',data_type='string',required=True)]);r=validate_records([{}],s,uuid4());assert r.invalid_records==1 and r.issue_counts['required']==1
