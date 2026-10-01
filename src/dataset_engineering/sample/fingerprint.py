import hashlib,json
from typing import Any
def dataset_fingerprint(records:list[dict[str,Any]])->str:
 h=hashlib.sha256()
 for r in records:h.update(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode());h.update(b'\n')
 return h.hexdigest()
