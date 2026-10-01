from dataset_engineering.core.models import DatasetSchema, FieldDefinition
from dataset_engineering.quality.completeness import completeness

def test_completeness_metrics() -> None:
    schema = DatasetSchema(fields=[FieldDefinition(name="email", data_type="string")])
    report = completeness([{"email": "a@example.com"}, {"email": None}, {}], schema)
    metric = report.completeness[0]
    assert metric.total == 3
    assert metric.present == 2
    assert metric.missing == 1
    assert metric.null_rate == 1 / 3
    assert metric.completeness_rate == 2 / 3
