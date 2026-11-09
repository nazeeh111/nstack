"""Inspect a packed Node artifact without extracting or running its scripts."""
import argparse,hashlib,json,pathlib,platform,re,sys,tarfile
P=pathlib.Path
def satisfies(spec,version):
 """Conservative npm semver subset. Unsupported expressions fail closed."""
 if spec==version or spec in ('*','latest'):return spec!='latest'
 def parsed(value):
  match=re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)',value)
  return tuple(map(int,match.groups())) if match else None
 actual=parsed(version)
 if actual is None:return False
 if spec.startswith(('^','~')):
  base=parsed(spec[1:])
  if base is None:return False
  upper=(base[0]+1,0,0) if spec[0]=='^' and base[0] else (0,base[1]+1,0) if spec[0]=='^' and base[1] else (0,0,base[2]+1) if spec[0]=='^' else (base[0],base[1]+1,0)
  return base<=actual<upper
 parts=spec.split()
 if not parts:return False
 for part in parts:
  match=re.fullmatch(r'(>=|<=|>|<|=)(\d+\.\d+\.\d+)',part)
  if not match:return False
  other=parsed(match[2]);op=match[1]
  if other is None or not {'>=':actual>=other,'<=':actual<=other,'>':actual>other,'<':actual<other,'=':actual==other}[op]:return False
 return True
def inspect(path,name=None,version=None):
 metadata=None;count=0
 with tarfile.open(path,'r:*') as archive:
  for member in archive:
   count+=1;relative=P(member.name)
   if count>200000 or relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0]!='package' or not (member.isfile() or member.isdir()):raise ValueError('Unsafe or unsupported package archive member')
   if any(part in ('.git','.aws','.ssh','.gnupg','Keychains','node_modules') for part in relative.parts) or relative.name in ('.env','.npmrc','.netrc','auth.json'):raise ValueError('Private or credential-related material is outside the portable package boundary')
   if str(relative)=='package/package.json':
    if metadata is not None or member.size>2*1024*1024:raise ValueError('Ambiguous or oversized package metadata')
    metadata=json.load(archive.extractfile(member))
 if not isinstance(metadata,dict) or not metadata.get('name') or not metadata.get('version'):raise ValueError('Package identity missing')
 if name is not None and metadata['name']!=name:raise ValueError('Packed name differs from selected source package')
 if version is not None and metadata['version']!=version:raise ValueError('Packed version differs from selected source package')
 for field in ('dependencies','optionalDependencies','peerDependencies'):
  for spec in metadata.get(field,{}).values():
   if not isinstance(spec,str) or spec.startswith(('workspace:','catalog:','link:','file:')):raise ValueError('Unresolved workspace/catalog/local dependency in packed runtime manifest')
 h=hashlib.sha256()
 with P(path).open('rb') as stream:
  while chunk:=stream.read(1024*1024):h.update(chunk)
 return {'name':metadata['name'],'version':metadata['version'],'archive':P(path).name,'sha256':h.hexdigest(),'archive_members':count,'runtime_dependencies':{field:metadata.get(field,{}) for field in ('dependencies','optionalDependencies','peerDependencies')},'runtime_dependency_protocols_resolved':True,'limits':'Packaging-boundary check only. Required local package closure, source rights, compiled exports, dependency locks and actual task output need their own checks.'}
def workspace_packages(source):
 source=P(source).resolve(strict=True);root=json.loads((source/'package.json').read_text());patterns=root.get('workspaces') or []
 if isinstance(patterns,dict):patterns=patterns.get('packages',[])
 if not patterns and (source/'pnpm-workspace.yaml').exists():
  # The admitted pnpm layouts use a literal top-level packages block. Refuse
  # unsupported YAML constructs rather than inventing a workspace graph.
  collecting=False
  for line in (source/'pnpm-workspace.yaml').read_text().splitlines():
   if line.startswith('packages:'):
    if line.strip()!='packages:':raise ValueError('Workspace packages must be an explicit block list for this verifier')
    collecting=True;continue
   if collecting:
    if line and not line[0].isspace() and not line.startswith('#'):break
    value=line.strip()
    if not value or value.startswith('#'):continue
    if not value.startswith('- '):raise ValueError('Unsupported workspace package expression')
    value=value[2:].strip()
    if value.startswith('"'):value=json.loads(value)
    elif value.startswith("'") and value.endswith("'"):value=value[1:-1].replace("''", "'")
    elif any(x in value for x in ('#','&','{','[','!<')):raise ValueError('Unsupported workspace package expression')
    patterns.append(value)
 if not isinstance(patterns,list) or any(not isinstance(x,str) for x in patterns):raise ValueError('Unsupported workspace declaration')
 included={source};excluded=set();skip={'node_modules','.git','.yarn','.pnpm','dist','out','.next'}
 for pattern in patterns:
  negative=pattern.startswith('!');pattern=pattern[1:] if negative else pattern
  if P(pattern).is_absolute() or '..' in P(pattern).parts:raise ValueError('Workspace pattern escaped source')
  for folder in source.glob(pattern):
   if any(part in skip for part in folder.relative_to(source).parts):continue
   if folder.is_symlink() or not folder.resolve().is_relative_to(source):raise ValueError('Workspace package path is redirected')
   if folder.is_dir() and (folder/'package.json').is_file():(excluded if negative else included).add(folder)
 result={}
 for folder in sorted(included-excluded):
  file=folder/'package.json'
  if file.is_symlink() or file.stat().st_size>2*1024*1024:raise ValueError('Unbounded or redirected workspace metadata')
  data=json.loads(file.read_text());name=data.get('name')
  if not name:raise ValueError('Workspace package lacks identity')
  if name in result:raise ValueError('Ambiguous workspace package identity')
  result[name]=(folder,data)
 return result
def inspect_bundle(directory,source,name,version=None):
 directory=P(directory).resolve(strict=True);packages=workspace_packages(source)
 if name not in packages:raise ValueError('Selected package is not in the source workspace')
 if version is not None and packages[name][1]['version']!=version:raise ValueError('Selected source version differs from the requested pinned package')
 target_os={'darwin':'darwin','linux':'linux','win32':'win32'}.get(sys.platform,sys.platform);target_cpu={'aarch64':'arm64','arm64':'arm64','x86_64':'x64','AMD64':'x64'}.get(platform.machine(),platform.machine())
 target_libc=None
 if target_os=='linux':
  libc=platform.libc_ver()[0].lower();target_libc='glibc' if libc in ('glibc','gnu') else 'musl' if 'musl' in libc else None
 def matches(values,target):
  if not values:return True
  return '!'+target not in values and (not [v for v in values if not v.startswith('!')] or target in values or 'any' in values)
 expected={};visiting=[(name,False)]
 while visiting:
  current,optional=visiting.pop()
  if current in expected:continue
  folder,data=packages[current]
  if target_os=='linux' and data.get('libc') and target_libc is None:raise ValueError('Native libc could not be established for a constrained package')
  if not matches(data.get('os',[]),target_os) or not matches(data.get('cpu',[]),target_cpu):
   if optional:continue
   raise ValueError('A required source package does not support this native target')
  if target_os=='linux' and not matches(data.get('libc',[]),target_libc):
   if optional:continue
   raise ValueError('A required source package does not support this native libc')
  expected[current]=data['version']
  for field in ('dependencies','optionalDependencies','peerDependencies'):
   for dep,spec in data.get(field,{}).items():
    is_optional=field=='optionalDependencies' or (field=='peerDependencies' and data.get('peerDependenciesMeta',{}).get(dep,{}).get('optional',False))
    if dep in packages:visiting.append((dep,is_optional))
    elif isinstance(spec,str) and spec.startswith('workspace:'):raise ValueError('Unresolved source workspace alias or missing package')
 archives=list(directory.glob('*.tgz'))
 if not archives:raise ValueError('No packed archives; installation blocked')
 observed={}
 for archive in archives:
  if archive.is_symlink():raise ValueError('Linked packed artifact')
  item=inspect(archive);key=(item['name'],item['version'])
  if key in observed:raise ValueError('Ambiguous duplicate packed artifact')
  observed[key]=item
 missing=[key for key,value in expected.items() if (key,value) not in observed]
 if missing:raise ValueError('Required native workspace package closure is incomplete; installation blocked')
 for key,value in expected.items():
  packed=observed[(key,value)]['runtime_dependencies']
  for field in ('dependencies','optionalDependencies','peerDependencies'):
   for dep in packages[key][1].get(field,{}):
    if dep in packages:
     if dep not in packed[field]:raise ValueError('Packed artifact dropped a source workspace dependency')
     if not satisfies(packed[field][dep],packages[dep][1]['version']):raise ValueError('Packed dependency cannot be satisfied by the pinned local source version; unsupported ranges fail closed')
 return {'target':{'os':target_os,'cpu':target_cpu,'libc':target_libc},'selected':name,'required_packages':[observed[(key,value)] for key,value in sorted(expected.items())],'additional_uninstalled_archives':len(observed)-len(expected),'complete_native_source_closure':True,'limits':'Only this required target closure may be installed. Actual compiled exports, rights and task output remain separate checks.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',nargs='?');p.add_argument('--name');p.add_argument('--version');p.add_argument('--directory');p.add_argument('--source');a=p.parse_args()
 try:
  if a.directory:
   if a.archive or not a.source or not a.name:raise ValueError('Bundle verification requires --directory, --source and selected --name only')
   result=inspect_bundle(a.directory,a.source,a.name,a.version)
  else:
   if not a.archive:raise ValueError('An archive or complete bundle is required')
   result=inspect(a.archive,a.name,a.version)
  print(json.dumps(result,indent=2))
 except (ValueError,OSError,tarfile.TarError) as e:p.exit(1,str(e)+'\n')
