from __future__ import annotations
import random
from .fingerprint import dataset_fingerprint
from .models import SampleResult,SplitResult
def sample_records(records:list[dict],*,size:int|None=None,fraction:float|None=None,seed:int=0):
 if size is not None and fraction is not None:raise ValueError('size and fraction are mutually exclusive')
 if size is None:size=round(len(records)*(fraction or 1.0))
 if size<0 or size>len(records):raise ValueError('sample size out of range')
 rng=random.Random(seed);out=rng.sample(records,size);return SampleResult(records=out,output_count=len(out),output_fingerprint=dataset_fingerprint(out))
def split_records(records:list[dict],*,train:float,validation:float,test:float,seed:int=0):
 if abs(train+validation+test-1)>1e-9:raise ValueError('split proportions must sum to 1')
 data=list(records);random.Random(seed).shuffle(data);a=round(len(data)*train);b=a+round(len(data)*validation);parts={'train':data[:a],'validation':data[a:b],'test':data[b:]};return SplitResult(splits=parts,output_counts={k:len(v) for k,v in parts.items()})
