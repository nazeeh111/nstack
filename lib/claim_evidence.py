#!/usr/bin/env python3
"""Read-only structured evidence reconciliation. Consistency is not execution proof."""
import argparse,csv,glob,hashlib,json,pathlib,re
P=pathlib.Path
class Unknown(ValueError):pass

def digest(file):
 h=hashlib.sha256()
 with file.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()

def unique(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise Unknown('Duplicate JSON key')
  out[k]=v
 return out

def read_json(file):return json.loads(file.read_text(),object_pairs_hook=unique)

def pointer(value,path):
 if path=='':return value
 if not path.startswith('/'):raise Unknown('JSON Pointer must be empty or begin with /')
 for token in path[1:].split('/'):
  if re.search(r'~(?![01])',token):raise Unknown('Invalid JSON Pointer escape')
  token=token.replace('~1','/').replace('~0','~')
  if isinstance(value,list):
   if not re.fullmatch(r'0|[1-9][0-9]*',token):raise Unknown('Invalid array index')
   value=value[int(token)]
  elif isinstance(value,dict):value=value[token]
  else:raise Unknown('JSON Pointer traverses a scalar')
 return value

def same_value(actual,expected):
 if isinstance(actual,bool) or isinstance(expected,bool):return type(actual)==type(expected) and actual==expected
 if isinstance(expected,(int,float)) and isinstance(actual,str):
  from decimal import Decimal,InvalidOperation
  try:return Decimal(actual)==Decimal(str(expected))
  except InvalidOperation:return False
 return type(actual)==type(expected) and actual==expected

class Scope:
 def __init__(self,project,roots):
  self.project=P(project).resolve(strict=True);self.roots=[]
  for raw in roots:
   path=(self.project/raw).resolve(strict=True)
   if not path.is_relative_to(self.project) or not path.is_dir():raise Unknown('Declared root must be a project directory')
   self.roots.append(path)
  if not self.roots:raise Unknown('At least one explicit evidence root is required')
 def file(self,name):
  raw=P(name)
  if raw.is_absolute() or '..' in raw.parts:raise Unknown('Evidence path must be project relative without traversal')
  found=glob.glob(str(self.project/raw),recursive=True)
  # Resolve every match before reading any; a safe first match cannot hide an escape.
  matches=[P(p).resolve(strict=True) for p in found]
  if any(not any(p.is_relative_to(root) for root in self.roots) for p in matches):raise Unknown('Evidence path escapes declared roots')
  if len(matches)!=1 or not matches[0].is_file():raise Unknown('Evidence path is missing, ambiguous or not a regular file')
  return matches[0]
 def check(self,claim):
  try:
   file=self.file(claim['path'])
   if claim['format']=='json':actual=pointer(read_json(file),claim['pointer'])
   elif claim['format']=='csv':
    with file.open(newline='') as f:
     reader=csv.DictReader(f);headers=reader.fieldnames or []
     if len(headers)!=len(set(headers)):raise Unknown('Duplicate CSV header')
     key=claim['row_key'];column=claim['column']
     if key['column'] not in headers or column not in headers:raise Unknown('CSV key/metric header absent')
     rows=[r for r in reader if r[key['column']]==str(key['value'])]
    if len(rows)!=1:raise Unknown('CSV row key is missing or ambiguous')
    actual=rows[0][column]
   else:raise Unknown('Only structured JSON/CSV evidence is supported; lexical presence is not validation')
   if not same_value(actual,claim['value']):raise Unknown('Structured value differs')
   expected=claim.get('provenance')
   if not isinstance(expected,dict):raise Unknown('Provenance is absent')
   receipt_file=self.file(expected['path']);receipt=read_json(receipt_file)
   if digest(receipt_file)!=expected['sha256']:raise Unknown('Provenance receipt hash differs')
   required=('unit','metric','split_sha256','run_sha256','command')
   for key in required:
    if key not in expected or key not in receipt or not same_value(receipt[key],expected[key]):raise Unknown('Missing or inconsistent '+key)
   if not isinstance(receipt['command'],list) or not receipt['command'] or not all(isinstance(x,str) for x in receipt['command']):raise Unknown('Producing command must be a nonempty argv record')
   for key in ('split_sha256','run_sha256'):
    if not re.fullmatch(r'[a-f0-9]{64}',receipt[key]):raise Unknown('Invalid '+key)
    if digest(self.file(receipt[key.replace('_sha256','_path')]))!=receipt[key]:raise Unknown('Actual '+key+' dependency differs')
   if receipt.get('artifact_sha256')!=digest(file):raise Unknown('Receipt does not bind this artifact')
   sources=receipt.get('sources')
   if not isinstance(sources,list) or not sources:raise Unknown('Producing sources are absent')
   for source in sources:
    if digest(self.file(source['path']))!=source['sha256']:raise Unknown('Producing source changed')
   return {'id':claim['id'],'state':'consistent-record','value':actual,'unit':receipt['unit'],'artifact_sha256':digest(file),'receipt_sha256':digest(receipt_file),'limits':'Structured records and hashes agree. Inspect actual producer/run evidence independently; this check does not prove execution, causal provenance, fair splitting or a scientific claim.'}
  except (Unknown,KeyError,IndexError,TypeError,OSError,ValueError) as e:
   return {'id':claim.get('id'),'state':'unknown','reason':str(e),'limits':'Missing or inconsistent evidence is not evidence of fabrication.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('project');p.add_argument('claims');p.add_argument('--root',action='append',required=True);a=p.parse_args();scope=Scope(a.project,a.root);claims=read_json(P(a.claims));results=[scope.check(c) for c in claims];print(json.dumps(results,indent=2));return 0 if all(r['state']=='consistent-record' for r in results) else 2
if __name__=='__main__':raise SystemExit(main())
