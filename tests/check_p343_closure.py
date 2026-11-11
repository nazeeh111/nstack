"""Independent structural/contract check of P343's selected source-derived closure."""
import hashlib,json,pathlib,re,sys
P=pathlib.Path;root=P(sys.argv[1]).resolve()
expected={'skills/prospecting/SKILL.md','skills/cold-email/SKILL.md','skills/prospecting/references/demand-signals.md','skills/prospecting/references/account-research.md','skills/cold-email/references/personalization.md','skills/cold-email/references/reply-handling.md','skills/revops/references/lifecycle-definitions.md','skills/sales-enablement/references/win-loss-analysis.md'}
assert {str(p.relative_to(root)) for p in (root/'skills').rglob('*') if p.is_file()}==expected
receipt=json.loads((root/'SOURCE-ADAPTATION.json').read_text());assert {r['source_path'] for r in receipt['files']}==expected
for row in receipt['files']:
 assert hashlib.sha256((root/row['archive']).read_bytes()).hexdigest()==row['source_sha256']
 assert hashlib.sha256((root/row['active_path']).read_bytes()).hexdigest()==row['active_sha256']
 assert (root/row['diff']).is_file()
want={('skills/prospecting/SKILL.md','references/demand-signals.md'),('skills/prospecting/SKILL.md','references/account-research.md'),('skills/prospecting/references/demand-signals.md','../SKILL.md'),('skills/cold-email/SKILL.md','references/personalization.md'),('skills/cold-email/SKILL.md','references/reply-handling.md'),('skills/cold-email/references/personalization.md','../../prospecting/references/account-research.md')};edges=set()
for f in (root/'skills').rglob('*.md'):
 for link in re.findall(r'\]\(([^\s)]+)',f.read_text()):
  assert ':' not in link,'Unexpected outbound dependency';resolved=(f.parent/link).resolve();assert resolved.is_relative_to(root) and resolved.is_file();edges.add((str(f.relative_to(root)),link))
assert want<=edges,(want-edges)
assert 'Copyright (c) 2025 Corey Haines' in (root/'LICENSE').read_text()
for branch in ['prospecting','cold-email']:
 text=(root/'skills'/branch/'SKILL.md').read_text();assert text.startswith('---\n')
 assert all(bad not in text for bad in ['saas-prospecting.md','multichannel-cadence.md','sourcing-and-enrichment.md','Tool Integrations','Related Skills'])
reply=(root/'skills/cold-email/references/reply-handling.md').read_text();assert all(term in reply for term in ['Suppress the recipient','address invalid','Pause without automatic resumption','no inherited send authority','Unknown provider outcomes','local pause'])
life=(root/'skills/revops/references/lifecycle-definitions.md').read_text();assert all(term in life.lower() for term in ['genuine reply','positive interest','accepted booking','held meeting','realized revenue'])
print(json.dumps({'operative_source_files':8,'archived_source_files':8,'unique_resolved_links':len(edges),'unselected_dependencies':0,'stop_state_and_outcome_contracts':True,'limits':'Structural and written contract checks only; no sender, suppression service or production delivery implemented.'}))
