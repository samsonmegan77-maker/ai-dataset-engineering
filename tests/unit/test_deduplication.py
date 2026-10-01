from dataset_engineering.deduplication import deduplicate_records
def test_exact_duplicates():r=deduplicate_records([{'id':1},{'id':1},{'id':2}]);assert r.duplicate_records==1 and r.unique_records==2
