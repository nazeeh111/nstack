"""Pinned Unslop method adaptation. Generated skill retains CC BY 4.0 attribution."""
import hashlib,json,pathlib
P=pathlib.Path
REPOSITORY='heydamir/unslop'
REVISION='97daa3eb365670ea3f87ed85356cbfcee18105a5'
SOURCE_TREE_SHA256='0658ef3b5fd484f1de791ddeb7b845d5a7783642279856b8ea76aac8fb3e6dd0'

def definition(n):
 source=n.acquire(REPOSITORY,REVISION)
 frozen={}
 for p in source.rglob('*'):
  if p.is_symlink():raise ValueError('Linked Unslop source is not allowed')
  if p.is_file():frozen[str(p.relative_to(source))]=(p.read_bytes(),0o555 if p.stat().st_mode & 0o111 else 0o444)
 hashes={rel:hashlib.sha256(data).hexdigest() for rel,(data,_) in frozen.items() if rel!='.nstack-source.json'}
 if hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()!=SOURCE_TREE_SHA256:
  raise ValueError('Unslop source differs from the reviewed pinned tree')
 entry=P('skills/unslop');original=frozen[str(entry/'SKILL.md')][0]
 authored=n.ROOT/'addons/unslop'
 provenance={'repository':REPOSITORY,'revision':REVISION,'source_path':str(entry),'license':'CC-BY-4.0','attribution':'Unslop by Damir Sokolovsky (@heydamir), https://heydamir.design/unslop','source_tree_sha256':SOURCE_TREE_SHA256,'adaptation':'Existing-screen native Codex polish; brand/reference-first defaults, no blanket style bans or redundant approval loop. Complete source and visual support retained. Original snapshot/story scripts are reference-only, not registered/executed browser or video runtimes.'}
 overrides={str(entry/'SKILL.md'):(authored/'SKILL.md').read_bytes(),str(entry/'agents/openai.yaml'):(authored/'agents/openai.yaml').read_bytes(),str(entry/'UPSTREAM_SKILL.md'):original,'SOURCE.json':(json.dumps(provenance,sort_keys=True,indent=2)+'\n').encode()}
 return {'source':source,'entry':entry,'provenance':provenance,'overrides':overrides,'frozen_files':frozen}
