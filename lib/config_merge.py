"""Format-preserving TOML ownership edits using the pinned, licensed TOMLKit parser."""
import copy,pathlib,sys,tomllib,math
from collections.abc import Mapping
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'vendor'))
import tomlkit
MISSING=object()

def get(data,path):
 for key in path:
  if not isinstance(data,Mapping) or key not in data:return MISSING
  data=data[key]
 return data

def equal(a,b):
 if a is MISSING or b is MISSING:return a is b
 if type(a) is not type(b):return False
 if isinstance(a,dict):return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
 if isinstance(a,float) and math.isnan(a) and math.isnan(b):return True
 return a==b

def remove(data,path,prune=False):
 parent=data;trail=[]
 for key in path[:-1]:
  if key not in parent:return
  trail.append((parent,key));parent=parent[key]
  if not isinstance(parent,Mapping):raise ValueError('Setting parent is not a table')
 if path[-1] in parent:del parent[path[-1]]
 if prune:
  for parent,key in reversed(trail):
   if len(parent[key])==0:del parent[key]
   else:break

def put(doc,path,value):
 parent=doc
 for key in path[:-1]:
  if key not in parent:parent[key]=tomlkit.table()
  parent=parent[key]
  if not isinstance(parent,Mapping):raise ValueError('Setting parent is not a table')
 if value is MISSING:remove(doc,path)
 else:parent[path[-1]]=copy.deepcopy(value)

def unowned(data,paths):
 result=copy.deepcopy(data)
 for path in paths:remove(result,path,True)
 return result

def validate(before,after,updates,retire):
 a=tomllib.loads(before);b=tomllib.loads(after);paths=retire+[path for path,_ in updates]
 if not equal(unowned(a,paths),unowned(b,paths)):raise ValueError('Configuration edit changed an unowned setting')
 for path in retire:
  if get(b,path) is not MISSING:raise ValueError('Retired registration is still present')
 for path,value in updates:
  actual=get(b,path)
  if value is MISSING:
   if actual is not MISSING:raise ValueError('Owned key removal failed')
  elif not equal(actual,value):raise ValueError('Owned setting update failed')

def apply(text,updates,retire):
 doc=tomlkit.parse(text)
 for path in retire:remove(doc,path)
 for path,value in updates:put(doc,path,value)
 result=tomlkit.dumps(doc);validate(text,result,updates,retire)
 # Avoid formatting-only writes on a second install.
 return text if equal(tomllib.loads(text),tomllib.loads(result)) else result

def inverse(current,before,after,updates,retire):
 now=tomllib.loads(current);old=tomllib.loads(before);installed=tomllib.loads(after);doc=tomlkit.parse(current);original=tomlkit.parse(before)
 paths=retire+[path for path,_ in updates]
 for path in paths:
  if not equal(get(now,path),get(installed,path)):raise ValueError('Rollback conflict in owned setting: '+'.'.join(path))
 for path in retire:
  value=get(original,path)
  if value is MISSING:remove(doc,path)
  else:put(doc,path,value)
 for path,_ in updates:
  value=get(original,path)
  if value is MISSING:remove(doc,path,True)
  else:put(doc,path,value)
 result=tomlkit.dumps(doc);restored=tomllib.loads(result)
 if not equal(unowned(now,paths),unowned(restored,paths)):raise ValueError('Rollback changed an unowned setting')
 for path in paths:
  if not equal(get(restored,path),get(old,path)):raise ValueError('Rollback did not restore an owned setting')
 return result
