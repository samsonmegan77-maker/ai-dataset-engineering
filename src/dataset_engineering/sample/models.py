from pydantic import BaseModel
class SampleResult(BaseModel): records:list[dict];output_count:int;output_fingerprint:str
class SplitResult(BaseModel): splits:dict[str,list[dict]];output_counts:dict[str,int]
