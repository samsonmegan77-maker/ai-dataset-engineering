from dataset_engineering.quality.completeness import completeness_metrics
def test_completeness():r=completeness_metrics([{'a':1},{'a':None},{}],['a']);assert r[0].present==1 and r[0].missing==1
