from dataset_engineering.core.models import DatasetSchema,FieldDefinition
from dataset_engineering.evaluation import EvaluationStatus,Threshold,evaluate_quality
from dataset_engineering.quality import completeness,consistency,distributions,diversity,numeric_statistics,uniqueness
from dataset_engineering.reporting.render import quality_as_csv,quality_as_html,evaluation_as_csv,evaluation_as_html
def schema(): return DatasetSchema(fields=[FieldDefinition(name='name',data_type='string'),FieldDefinition(name='age',data_type='integer')])
def records(): return [{'name':' Alice ','age':10},{'name':'Bob','age':20},{'name':'Bob','age':20},{'name':None,'age':30}]
def test_quality_metrics():
 rs=records(); assert completeness(rs,schema()).completeness[0].completeness_rate==1.0; assert uniqueness(rs,['name'])[0].duplicate_values==1; stats=numeric_statistics(rs,['age'])[0]; assert (stats.minimum,stats.maximum,stats.median)==(10.0,30.0,20.0); assert distributions(rs,['name'])[0].distinct_values==2; assert diversity(rs,['name'])['name']==2.0; assert consistency(rs,['name'])[0].violations==1
def test_evaluation_thresholds_and_determinism():
 rs=[{'name':'Alice','age':10},{'name':'Bob','age':20},{'name':'Bob','age':20},{'name':'Carol','age':30}]; t={'completeness':Threshold(minimum=.95),'duplicate_rate':Threshold(maximum=.30)}; report,e=evaluate_quality(rs,['name','age'],'sample',t); _,e2=evaluate_quality(rs,['name','age'],'sample',t); assert report.total_records==4 and e.status==EvaluationStatus.PASS; assert [(m.name,m.value,m.status) for m in e.metrics]==[(m.name,m.value,m.status) for m in e2.metrics]
def test_evaluation_failure(): assert evaluate_quality([{'x':1},{'x':1}],['x'],'bad',{'duplicate_rate':Threshold(maximum=0.0)})[1].status==EvaluationStatus.FAIL
def test_report_alternate_formats():
 report,e=evaluate_quality(records(),['name','age'],'sample'); assert 'field,total' in quality_as_csv(report); assert '<html>' in quality_as_html(report); assert 'metric,value' in evaluation_as_csv(e); assert 'Dataset Evaluation' in evaluation_as_html(e)
