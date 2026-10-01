from dataset_engineering.transforms import transform_records
def test_transform_filter_and_select():r=transform_records([{'id':1,'ok':True},{'id':2,'ok':False}],filter_field='ok',filter_equals=True,select=['id']);assert r.records==[{'id':1}]
