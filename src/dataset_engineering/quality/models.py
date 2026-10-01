from pydantic import BaseModel
class CompletenessMetric(BaseModel):field:str;total:int;present:int;missing:int;null_rate:float;completeness_rate:float
class QualityReport(BaseModel):total_records:int;duplicate_rate:float;completeness:list[CompletenessMetric];numeric_statistics:list[dict];distributions:list[dict];consistency:list[dict];diversity:list[dict]
