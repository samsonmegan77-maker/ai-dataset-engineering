from dataset_engineering.deduplication import deduplicate_records
def test_deduplication_handles_large_iterator():
 def records():
  for i in range(10000): yield {'id':i//2,'value':i%5}
 report=deduplicate_records(records(),fields=['id']); assert report.total_records==10000; assert report.unique_records==5000; assert report.duplicate_records==5000
