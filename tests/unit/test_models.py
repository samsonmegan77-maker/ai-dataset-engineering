import pytest
from dataset_engineering.core.models import Dataset,DatasetSchema,FieldDefinition
def test_dataset_has_stable_identity(): assert Dataset(name='sample',source_format='jsonl').id is not None
def test_schema_rejects_empty_fields():
 with pytest.raises(ValueError): DatasetSchema(fields=[])
def test_field_definition_requires_name():
 with pytest.raises(ValueError): FieldDefinition(name='',data_type='string')
def test_schema_rejects_duplicate_field_names():
 with pytest.raises(ValueError,match='duplicate'): DatasetSchema(fields=[FieldDefinition(name='name',data_type='string'),FieldDefinition(name='name',data_type='string')])
def test_field_type_is_normalized(): assert FieldDefinition(name='age',data_type=' INTEGER ').data_type=='integer'
