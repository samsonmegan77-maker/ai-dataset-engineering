from dataset_engineering.core.models import Dataset,ValidationReport
from dataset_engineering.reporting.render import report_as_json,report_as_markdown
def test_markdown_report_contains_summary():
 report=ValidationReport(dataset_id=Dataset(name='x',source_format='json').id,total_records=2,valid_records=1,invalid_records=1); rendered=report_as_markdown(report); assert 'Success rate: **50.0%**' in rendered and '# Dataset Validation' in rendered
def test_json_report_is_machine_readable():
 report=ValidationReport(dataset_id=Dataset(name='x',source_format='json').id,total_records=1,valid_records=1,invalid_records=0); assert '"valid_records": 1' in report_as_json(report)
