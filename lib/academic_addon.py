"""Optional pinned CC-BY-NC source adaptation; upstream payload is fetched privately."""
import hashlib,json,pathlib,re
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
BOUNDARY='''## Codex integration

This is a pinned, private Codex adaptation of Academic Research Skills. The upstream
workflow below and its full relative support are retained. Interpret their Claude
platform bindings through the available native Codex tools. This integration has
precedence over conflicting platform recipes in this bundle.

- Use the current Codex subscription, model and effort. Do not run Claude, plugin
  installation, hooks, session-start/update scripts, external model transports,
  credential provisioning, auth-copy helpers, smoke-test launchers or evaluators.
  No separately billed API call is part of this skill. Do not inspect credentials.
- Use native search/source-reading/document tools already available. Keep local
  source and unpublished research private. Read the relevant complete upstream
  skill below and its required mode references, resolving paths from this bundle's
  root. This skill directory is one level below the bundle root. Resolve
  shared/, scripts/, docs/ and named sibling-skill paths from that parent root;
  resolve agents/, references/ and templates/ from this skill directory.
  For sr-screener only, scripts/ is also leaf-relative. Invoke scripts with an
  absolute source path and a separate project working directory; never write
  into this immutable installed bundle. Native authority remains controlling.
- Use roles as useful perspectives, not a mandatory swarm. Keep narrow tasks
  narrow. Resolve routine choices from supplied materials; ask only for information
  that materially changes the research, or authority not already granted. Do not
  insert blanket confirmations or override an explicitly requested workflow.
- Inspect a helper and its imports before executing it. Prefer deterministic local
  helpers; verify dependencies and use explicit project-local input/output paths.
  The upstream hooks and write guards are not installed or claimed active here.
  Native permission enforcement is the actual boundary. Account-bearing scripts
  and network/provider transports remain disabled. In particular never execute
  scripts/cross_model_codex_transport.py: it reads/copies the Codex auth file,
  despite its subscription-transport label. Screening preparation requires a
  fresh dedicated --work directory, separate from input folders; upstream
  prepare_records.py can clear batch files before validation. Use native public-source lookup
  instead of reading API-key environment variables or creating accounts.
- Preserve stable claims, source locators, uncertainty and correction history.
  Never invent citations, results, screening decisions or evidence. Report a check
  that was not run as untested. Produce the requested artifact and independently
  check it; role-separated model opinions are not independent empirical validation.

License: CC BY-NC 4.0, copyright 2026 Cheng-I Wu. This source remains separate
from nstack's MIT code. Noncommercial scope applies to the upstream material.
See the retained LICENSE and NOTICE.md. Original entry is UPSTREAM_SKILL.md.

'''

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
 # Keep source metadata while making native discovery precise and avoiding broad
 # fixed agent-count promises or triggers that capture ordinary work.
 front,count=re.subn(r'(?m)^description:.*$', 'description: '+json.dumps(DESCRIPTIONS[name]),front,count=1)
 if count!=1:raise ValueError('Academic source description missing')
 body = re.sub(r'<!-- routing-core:begin -->.*?<!-- routing-core:end -->',
               "Use the user's stated objective and supplied materials to choose the relevant mode. Clarify only material ambiguity.", body, flags=re.S)
 body = re.sub(r'^> \*\*Routing discipline.*?\n', '', body, flags=re.M)
 body = body.replace('Claude Code session', 'Codex session').replace('DOI or WebSearch', 'DOI or native web search')
 if name == 'sr-screener':
  a = body.index('Roles 3-5 and the QC rechecks')
  b = body.index('\n---', a)
  body = body[:a] + ('Use the retained reviewer-role references as requested perspectives. Native Codex delegation is optional and respects task instructions. '
                    'Label single-reviewer triage honestly; claim blinded independent review only when separate contexts actually ran. '
                    'Claude Workflow templates are not a Codex runtime port. No agent registration is installed. '
                    'See references/reviewer_roles.md.\n') + body[b:]
 adapted='---\n'+front+'\n---\n\n'+BOUNDARY+body
 provenance={'repository':REPOSITORY,'revision':REVISION,'source_path':str(entry),'license':'CC-BY-NC-4.0','adaptation':'Native Codex bindings; no Claude runtime/hooks/credential or provider transport; complete support retained.','source_tree_sha256':SOURCE_TREE_SHA256}
 overrides={str(entry):adapted.encode(),str(P(name)/'UPSTREAM_SKILL.md'):original.encode(),'SOURCE.json':(json.dumps(provenance,sort_keys=True,indent=2)+'\n').encode()}
 return {'source':source,'entry':P(name),'provenance':provenance,'overrides':overrides,'frozen_files':frozen}
