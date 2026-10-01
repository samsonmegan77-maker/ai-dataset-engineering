from dataset_engineering.deduplication import deduplicate_records
from dataset_engineering.transforms import transform_records

def test_pipeline_deduplicates_then_transforms():
 records=[{'id':1,'status':'ready'},{'id':1,'status':'ready'},{'id':2,'status':'hold'}]; report=deduplicate_records(records,fields=['id']); assert report.duplicate_records==1; transformed=transform_records(records,filter_field='status',filter_equals='ready',select=['id']); assert transformed.records==[{'id':1},{'id':1}]
