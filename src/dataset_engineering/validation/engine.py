from __future__ import annotations
import re
from collections import Counter
from collections.abc import Iterable
from typing import Any
from uuid import UUID
from dataset_engineering.core.models import Dataset,DatasetSchema,FieldDefinition,IssueSeverity,ValidationIssue,ValidationReport
SUPPORTED={'string','integer','number','boolean','object','array'}
def _type(v,t):return {'string':isinstance(v,str),'integer':isinstance(v,int) and not isinstance(v,bool),'number':isinstance(v,(int,float)) and not isinstance(v,bool),'boolean':isinstance(v,bool),'object':isinstance(v,dict),'array':isinstance(v,list)}.get(t,False)
def _issue(i,f,r,v,m):return ValidationIssue(record_index=i,field=f,rule=r,value=v,severity=IssueSeverity.ERROR,message=m)
def _validate(i,f:FieldDefinition,v):
 out=[]
 if f.data_type not in SUPPORTED:return[_issue(i,f.name,'schema_type',v,f'Unsupported schema type: {f.data_type}')]
 if v is None:
  if not f.nullable:out.append(_issue(i,f.name,'nullable',v,'Null is not allowed'))
  return out
 if not _type(v,f.data_type):return[_issue(i,f.name,'type',v,f'Expected {f.data_type}')]
 if f.minimum is not None and isinstance(v,(int,float)) and v<f.minimum:out.append(_issue(i,f.name,'minimum',v,f'Value must be >= {f.minimum:g}'))
 if f.maximum is not None and isinstance(v,(int,float)) and v>f.maximum:out.append(_issue(i,f.name,'maximum',v,f'Value must be <= {f.maximum:g}'))
 if f.min_length is not None and isinstance(v,(str,list)) and len(v)<f.min_length:out.append(_issue(i,f.name,'min_length',v,f'Length must be >= {f.min_length}'))
 if f.max_length is not None and isinstance(v,(str,list)) and len(v)>f.max_length:out.append(_issue(i,f.name,'max_length',v,f'Length must be <= {f.max_length}'))
 if f.pattern is not None and isinstance(v,str) and re.fullmatch(f.pattern,v) is None:out.append(_issue(i,f.name,'pattern',v,'Value does not match pattern'))
 if f.enum is not None and v not in f.enum:out.append(_issue(i,f.name,'enum',v,'Value is not one of the allowed values'))
 return out
def validate_records(records:Iterable[dict[str,Any]],schema:DatasetSchema,dataset_id:UUID):
 issues=[];invalid=set();total=0
 for i,r in enumerate(records):
  total+=1
  for f in schema.fields:
   if f.name not in r:
    if f.required and not f.has_default:issues.append(_issue(i,f.name,'required',None,'Required field is missing'));invalid.add(i)
   else:
    x=_validate(i,f,r[f.name]);issues.extend(x)
    if x:invalid.add(i)
 return ValidationReport(dataset_id=dataset_id,total_records=total,valid_records=total-len(invalid),invalid_records=len(invalid),fields_checked=len(schema.fields),issue_counts=dict(Counter(x.rule for x in issues)))
def validate_dataset(dataset:Dataset,schema:DatasetSchema):return validate_records(dataset.records,schema,dataset.id)
