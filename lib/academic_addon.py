"""Optional pinned CC-BY-NC source adaptation; upstream payload is fetched privately."""
import difflib,hashlib,json,pathlib,re
P=pathlib.Path
REPOSITORY='Imbad0202/academic-research-skills'
REVISION='6d9388674de1ad0437ad95db3d52f92b92204d84'
SOURCE_TREE_SHA256='6c4f2b4ecafb498535f106081a6d3f9859fdaca1d3dd385d5e1f793b19e45c35'
DESCRIPTIONS={
 'deep-research':'Investigate an academic question, synthesize literature, or check source support for research claims. Use scoped evidence and existing native research tools.',
 'academic-paper':'Plan, outline, draft or revise an academic manuscript from the user\'s sources and findings; verify citations and identify material gaps.',
 'academic-paper-reviewer':'Critique an academic manuscript for methods, claims, citations and revision priorities. Simulated feedback does not constitute actual journal review.',
 'academic-pipeline':'Coordinate a requested multi-stage academic research and manuscript workflow, preserving source provenance, checkpoints and the user\'s chosen scope.',
 'sr-screener':'Screen supplied study records against explicit systematic-review eligibility criteria, record inclusion/exclusion reasons and reconcile screening counts.'
}
BOUNDARY="""## Native host bindings

Use the current host's tools and model settings for platform-specific operations;
retain the upstream routing, modes, review roles and independent-review requirements.
Original platform setup examples do not install a retired host, hooks or agents.
Account/provider transports are not admitted: in particular,
`scripts/cross_model_codex_transport.py` reads/copies authentication material.
Use native public-source lookup without reading credentials. Check a helper before
execution; `sr-screener/scripts/prepare_records.py` needs a fresh dedicated work
folder because it can remove prior batches. Report unavailable runtime capabilities.

Resolve shared/, scripts/ and docs/ from this bundle's parent root; resolve agents/,
references/ and templates/ from the leaf. sr-screener/scripts/ is leaf-relative.
Write outputs in the task project, never this immutable source bundle.

The source is CC BY-NC 4.0, copyright 2026 Cheng-I Wu, separate from nstack MIT code.
Exact original: UPSTREAM_SKILL.md; minimal changes: NATIVE-PORT.patch.
"""


def definition(n,name):
 if name not in DESCRIPTIONS:raise ValueError('Unknown academic skill')
 source=n.acquire(REPOSITORY,REVISION)
 frozen={}
 for p in source.rglob('*'):
  if p.is_symlink():raise ValueError('Linked academic source is not allowed')
  if p.is_file():frozen[str(p.relative_to(source))]=(p.read_bytes(),0o555 if p.stat().st_mode & 0o111 else 0o444)
 files={rel:hashlib.sha256(data).hexdigest() for rel,(data,mode) in frozen.items() if rel!='.nstack-source.json'}
 if hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()!=SOURCE_TREE_SHA256:
  raise ValueError('Academic source differs from the reviewed pinned tree')
 entry=P(name)/'SKILL.md';original=frozen[str(entry)][0].decode()
 if not original.startswith('---\n') or '\n---\n' not in original[4:]:raise ValueError('Academic source frontmatter missing')
 front,body=original[4:].split('\n---\n',1)
 # Preserve the full upstream method and discovery metadata. Only the host
 # name is generalized; native execution bindings stay separate from the method.
 body=body.replace('Claude Code session','native host session')
 adapted='---\n'+front+'\n---\n\n> Native host execution: read [bindings](../NATIVE-BINDINGS.md).\n\n'+body
 port=''.join(difflib.unified_diff(original.splitlines(keepends=True),adapted.splitlines(keepends=True),fromfile=str(entry),tofile=str(entry)))
 provenance={'repository':REPOSITORY,'revision':REVISION,'source_path':str(entry),'license':'CC-BY-NC-4.0','adaptation':'Upstream metadata and complete workflow retained; one host-session wording generalized and a separate native-execution binding linked.','source_tree_sha256':SOURCE_TREE_SHA256}
 overrides={str(entry):adapted.encode(),str(P(name)/'UPSTREAM_SKILL.md'):original.encode(),str(P(name)/'NATIVE-PORT.patch'):port.encode(),'NATIVE-BINDINGS.md':BOUNDARY.encode(),'SOURCE.json':(json.dumps(provenance,sort_keys=True,indent=2)+'\n').encode()}
 return {'source':source,'entry':P(name),'provenance':provenance,'overrides':overrides,'frozen_files':frozen}
