from dataset_engineering.pipeline import process_records

def test_process_records_deduplicates_then_transforms():
 records=[{'id':1,'status':'ready','name':' Ada '},{'id':1,'status':'ready','name':' Ada '},{'id':2,'status':'hold','name':'Grace'}]; output,dedup,transformed=process_records(records,deduplicate_fields=['id'],transform_filter_field='status',transform_filter_equals='ready',transform_normalize_fields=['name'],transform_select=['id','name']); assert output==[{'id':1,'name':'Ada'}]; assert dedup['duplicate_records']==1; assert transformed.output_count==1

def test_process_records_optional_sampling_is_reproducible():
 records=[{'id':i,'status':'ready'} for i in range(20)]; a,ma,_=process_records(records,sample_size=5,seed=42); b,mb,_=process_records(records,sample_size=5,seed=42); assert a==b; assert ma['sampling']['input_fingerprint']==mb['sampling']['input_fingerprint']; assert ma['sampling']['output_fingerprint']==mb['sampling']['output_fingerprint']
