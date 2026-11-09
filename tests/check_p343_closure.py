"""Independent structural/contract check of P343's retained scoped file bundle."""
import json,pathlib,re,sys
P=pathlib.Path;root=P(sys.argv[1]).resolve();expected={'skills/prospecting/SKILL.md','skills/cold-email/SKILL.md','skills/prospecting/references/demand-signals.md','skills/prospecting/references/account-research.md','skills/cold-email/references/personalization.md','skills/cold-email/references/reply-handling.md','skills/revops/references/lifecycle-definitions.md','skills/sales-enablement/references/win-loss-analysis.md','LICENSE'}
actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p!=root/'.nstack-release.json'};assert actual==expected,(actual-expected,expected-actual)
want={('skills/prospecting/SKILL.md','references/demand-signals.md'),('skills/prospecting/SKILL.md','references/account-research.md'),('skills/prospecting/references/demand-signals.md','../SKILL.md'),('skills/cold-email/SKILL.md','references/personalization.md'),('skills/cold-email/SKILL.md','references/reply-handling.md'),('skills/cold-email/references/personalization.md','../../prospecting/references/account-research.md')};edges=set()
for f in root.rglob('*.md'):
 for link in re.findall(r'\]\(([^\s)]+)',f.read_text()):
  assert ':' not in link,'Unexpected outbound dependency';resolved=(f.parent/link).resolve();assert resolved.is_relative_to(root) and resolved.is_file();edges.add((str(f.relative_to(root)),link))
assert edges==want,(edges-want,want-edges)
assert 'Copyright (c) 2025 Corey Haines' in (root/'LICENSE').read_text()
for branch in ['prospecting','cold-email']:
 text=(root/'skills'/branch/'SKILL.md').read_text();assert text.startswith('---\n')
 assert all(bad not in text for bad in ['saas-prospecting.md','multichannel-cadence.md','sourcing-and-enrichment.md','Tool Integrations','Related Skills'])
reply=(root/'skills/cold-email/references/reply-handling.md').read_text();assert all(term in reply for term in ['Suppress the recipient','address invalid','Pause without automatic resumption','no inherited send authority','Unknown provider outcomes','local pause'])
life=(root/'skills/revops/references/lifecycle-definitions.md').read_text();assert all(term in life for term in ['Genuine reply','Positive reply','Accepted booking','Held meeting','Realized revenue','cohort/denominator'])
print(json.dumps({'source_files':8,'notice_files':1,'unique_resolved_links':6,'unselected_dependencies':0,'stop_state_and_outcome_contracts':True,'limits':'Structural and written contract checks only; no sender, suppression service or production delivery implemented.'}))
