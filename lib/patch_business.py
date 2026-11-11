"""Scoped marketing/audit/career ports; no delivery authority is inferred."""
import pathlib,re,shutil,hashlib,json
P=pathlib.Path

def change(s,old,new):
 if old not in s:raise ValueError('Missing business port anchor: '+old[:90])
 return s.replace(old,new)
def retain_roles(source,out,roles,family):
 folder=out/'references/domain-prompts';folder.mkdir(parents=True,exist_ok=True)
 rows=[];links=[]
 for role in dict.fromkeys(roles):
  origin=source/'agents'/(role+'.md')
  if not origin.exists() and role=='seo-matomo':origin=source/'extensions/matomo/agents/seo-matomo.md'
  if not origin.is_file():raise ValueError('Missing pinned domain prompt: '+role)
  target=folder/(role+'.md');shutil.copy2(origin,target)
  rows.append({'source_path':str(origin.relative_to(source)),'path':str(target.relative_to(out)),'sha256':hashlib.sha256(origin.read_bytes()).hexdigest()})
  links.append('- ['+role+'](domain-prompts/'+role+'.md)')
 if family=='ads':
  origin=source/'ads/SKILL.md';target=folder/'operating-contract.md';shutil.copy2(origin,target)
  rows.append({'source_path':'ads/SKILL.md','path':str(target.relative_to(out)),'sha256':hashlib.sha256(origin.read_bytes()).hexdigest()})
  links.append('- [ads operating contract](domain-prompts/operating-contract.md)')
 (out/'references/domain-prompts.md').write_text('# Retained source role prompts\n\nOriginal source references, not separately installed skills. Apply the active entry host and authority binding. Resolve source-relative runtime paths against the verified source package root.\n\n'+'\n'.join(links)+'\n')
 (out/'references/domain-prompts-source.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')

def patch(id,name,source,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='P343':
  if name=='pricing':
   s=change(s,'your cheapest customers churn most and complain loudest','the source claims that your cheapest customers churn most and complain loudest (unverified; check the cited evidence before using this as a decision rule)')
   ref=out/'references/pricing-models.md';t=ref.read_text();anchor='## The Low-Price Retention Counterpoint'
   t=change(t,anchor,anchor+'\n\nSource claim, not an established general rule: the cited churn relationship and roughly 2x discount effect require verification for the actual market; do not infer causation or a price change from them alone.')
   ref.write_text(t)
 elif id=='P347':
  s=s.replace('${CLAUDE_PLUGIN_ROOT}','${NSTACK_SEO_ROOT}')
  # Preserve every domain and trigger; only replace credential-discovery probes.
  s=re.sub(r'Google API credentials detected via `[^`]+google_auth.py --check`', 'already authorized Google API access or supplied Google exports are available',s)
  s=re.sub(r'Matomo credentials detected via `[^`]+matomo_auth.py --check`', 'already authorized Matomo access or supplied Matomo exports are available',s)
  s=re.sub(r'Moz or Bing API credentials detected via `[^`]+backlinks_auth.py --check`', 'already authorized Moz/Bing access or supplied backlink exports are available',s)
  s=re.sub(r'Google API credentials are configured \(`[^`]+google_auth.py --check`\)', 'already authorized Google API access or supplied Google exports are available',s)
  s=re.sub(r'Matomo credentials are configured \(`[^`]+matomo_auth.py --check`\)', 'already authorized Matomo access or supplied Matomo exports are available',s)
  if name=='seo-audit':
   roles=re.findall(r'^   - `(seo-[a-z-]+)`',s,re.M)+['seo-dataforseo']
   retain_roles(source,out,roles,'seo')
   s+='\n## Host binding\n\nRead the complete selected role prompts in [the retained source index](references/domain-prompts.md); use native delegation or the original inline sequential fallback. Keep the selected model and effort; source tool names/frontmatter are host bindings. NSTACK_SEO_ROOT is the verified package root. Credential-discovery probes in source references are inactive: use only already authorized connected access or supplied exports, and report unavailable data. No paid API or account change follows from an audit.\n'
 elif id=='P351':
  if name=='ads-audit':
   roles=re.findall(r'^- `(audit-[a-z-]+)`',s,re.M)+['audit-tracking','audit-creative','audit-budget','audit-policy-compliance','audit-regulatory-compliance']
   retain_roles(source,out,roles,'ads')
   s+='\n## Host binding\n\nRead the complete selected roles and operating contract in [the retained source index](references/domain-prompts.md). Use native independent workers, preserving the source result schema and partial-run rules. Keep the selected model and effort; source tool names/frontmatter are host bindings. Use only already authorized connected account access or supplied exports. No credential-store probes, paid API or account mutation follows from this audit.\n'
 elif id=='P357':
  from patch_resume import materialize
  s=materialize(source,out)
 elif id=='P354':
  from patch_career import materialize
  s=materialize(source,out)
 else:raise ValueError('Business leaf is not mapped')
 p.write_text(s)
