"""Mirror explicit local support links outside the exposed leaf directory."""
import pathlib,re,shutil,os
P=pathlib.Path
MIRRORED={'P215','P226','P094','P321','L014','L020','P354','P357','X-CREATIVE-BLENDER-SKILLS','X-CREATIVE-UNREAL'}
def needs(s):return s['candidate_id'] in MIRRORED or (s['candidate_id']=='P119' and P(s['source_path']).parent.name=='formula-derivation')
def links(file):
 text=re.sub(r'(?ms)^```.*?^```[^\n]*','',file.read_text(errors='replace'));text=re.sub(r'`[^`\n]*`','',text)
 for target in re.findall(r'\]\(([^\s)]+)',text):
  target=target.split('#')[0]
  if target and ':' not in target and not target.startswith('/'):yield target

def support(source,out,transform=None,relocations=None,text_transform=None):
 source=source.resolve();out=out.resolve();done=set()
 while True:
  pending=[f for f in out.rglob('*.md') if f not in done]
  if not pending:break
  for file in pending:
   done.add(file)
   for rel in links(file):
    target=(file.parent/rel).resolve()
    if not target.is_relative_to(out):raise ValueError('Support link escapes mirrored closure: '+str(file.relative_to(out))+' -> '+rel)
    if target.exists():continue
    virtual=target.relative_to(out);mapped=virtual;prefix=P('.')
    for virtual_prefix,source_prefix in (relocations or {}).items():
     if virtual.is_relative_to(P(virtual_prefix)):
      mapped=P(source_prefix)/virtual.relative_to(virtual_prefix);prefix=P(virtual_prefix);break
    original=source/mapped
    if not original.exists() and prefix!=P('.'):
     for index in range(len(mapped.parts)):
      suffix=P(*mapped.parts[index:])
      if suffix.parts[0] in ('docs','modes','templates','lib') and (source/suffix).exists():
       target=out/prefix/suffix;replacement=os.path.relpath(target,file.parent)
       file.write_text(file.read_text().replace(']('+rel,']('+replacement));original=source/suffix;break
    if original.is_symlink() or not original.exists():raise ValueError('Missing pinned support '+str(original.relative_to(source)))
    if original.name=='SKILL.md' and prefix==P('.') and transform and transform(str(original.relative_to(source)),target.parent):continue
    files=[original] if original.is_file() else list(original.rglob('*'))
    for src in files:
     if src.is_symlink():raise ValueError('Linked support requires explicit review')
     if not src.is_file() or src.name=='.nstack-source.json' or any(p in src.parts for p in ('.git','node_modules','__pycache__')):continue
     dest=target if original.is_file() else target/src.relative_to(original);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
     if text_transform and dest.suffix=='.md':dest.write_text(text_transform(dest.read_text(),dest))
    # Preserve the support file's own ancestor notices without borrowing sibling grants.
    ancestor=original.parent if original.is_file() else original
    while ancestor.is_relative_to(source):
     for pattern in ('LICENSE*','COPYING*','NOTICE*'):
      for notice in ancestor.glob(pattern):
       if notice.is_file():
        dest=out/prefix/notice.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():shutil.copy2(notice,dest)
     if ancestor==source:break
     ancestor=ancestor.parent

def validate(out,provenance_roots=()):
 for file in out.rglob('*.md'):
  if any(file.is_relative_to(out/root) for root in provenance_roots):continue
  for rel in links(file):
   target=(file.parent/rel).resolve()
   if not target.is_relative_to(out.resolve()) or not target.exists():raise ValueError('Unresolved closure link '+str(file.relative_to(out))+': '+rel)
