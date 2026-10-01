from dataset_engineering.core.models import Dataset,DatasetSchema,FieldDefinition
from dataset_engineering.validation.engine import validate_dataset
def test_numeric_boundaries():
 schema=DatasetSchema(fields=[FieldDefinition(name='age',data_type='integer',minimum=0,maximum=130)]); report=validate_dataset(Dataset(name='x',source_format='jsonl',records=[{'age':0},{'age':130},{'age':-1},{'age':131}]),schema); assert [i.rule for i in report.issues]==['minimum','maximum']
def test_string_constraints_and_enum():
 schema=DatasetSchema(fields=[FieldDefinition(name='country',data_type='string',min_length=2,max_length=2,pattern=r'[A-Z]{2}',enum=['ZA','BW'])]); report=validate_dataset(Dataset(name='x',source_format='jsonl',records=[{'country':'ZA'},{'country':'z'},{'country':'USA'},{'country':'XX'}]),schema); assert {i.rule for i in report.issues}=={'pattern','min_length','max_length','enum'}
def test_non_nullable_and_default_metadata():
 schema=DatasetSchema(fields=[FieldDefinition(name='name',data_type='string',nullable=False,has_default=True,default='Unknown')]); report=validate_dataset(Dataset(name='x',source_format='json',records=[{'name':None},{}]),schema); assert {i.rule for i in report.issues}=={'nullable'}
def test_nested_objects_and_arrays():
 address=FieldDefinition(name='address',data_type='object',properties=[FieldDefinition(name='country',data_type='string',required=True)]); tags=FieldDefinition(name='tags',data_type='array',items=FieldDefinition(name='tag',data_type='string',min_length=2)); schema=DatasetSchema(fields=[address,tags]); report=validate_dataset(Dataset(name='x',source_format='json',records=[{'address':{},'tags':['ok','x']}]),schema); assert {i.rule for i in report.issues}=={'required','min_length'}
