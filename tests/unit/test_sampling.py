from dataset_engineering.sample import dataset_fingerprint,sample_records,split_records
def rows(n):return [{'id':i} for i in range(n)]
def test_sampling_reproducible():assert sample_records(rows(20),size=5,seed=42).records==sample_records(rows(20),size=5,seed=42).records
def test_fingerprint_changes():assert dataset_fingerprint(rows(2))!=dataset_fingerprint(rows(3))
def test_split_partition():r=split_records(rows(10),train=.8,validation=.1,test=.1,seed=1);assert sum(r.output_counts.values())==10
