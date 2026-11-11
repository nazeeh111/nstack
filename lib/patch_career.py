"""Explicit career-preparation closure, without upstream installers or model runners."""
import difflib,hashlib,json,pathlib,re,shutil
P=pathlib.Path
MODULES=('tracker.mjs','verify-cv-facts.mjs','ats-payload.mjs','prepare-application.mjs','followup-cadence.mjs','followup-seed.mjs','path-resolver.mjs','tracker-parse.mjs','tracker-utils.mjs','funnel-velocity.mjs','funnel-stages.mjs','stats.mjs','lib/cli-flags.mjs','lib/dir-lock.mjs','lib/is-main-module.mjs','lib/local-today.mjs','lib/scan-history-columns.mjs','lib/tsv-formula-escape.mjs','lib/yaml-document.mjs')
YAML_INTEGRITY='sha512-muutsYr+e2+d3rTgUGslq5rxbBlUy3cJ61IsHag2QNDQV+7zXWjkUpmALIajhrlLlrgRUiymj6U3zUr/TMK84Q=='
ARGPARSE_INTEGRITY='sha512-8+9WqebbFzpX9OR+Wa6O29asIogeRMzcGtAINdpMHHyAg10f05aSFVBbcEqGf/PXw1EjAZ+q2/bEBg3DvurK3Q=='
WRAPPER=r'''// Original nstack read-only adapter. Node >=24; no network operation.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const [operation,rawRoot,...args]=process.argv.slice(2);
if (!rawRoot || !path.isAbsolute(rawRoot)) throw Error('An explicit absolute campaign directory is required');
const root=fs.realpathSync(rawRoot), runtime=path.dirname(fileURLToPath(import.meta.url));
if (!fs.statSync(root).isDirectory() || root===runtime || root.startsWith(runtime+path.sep) || runtime.startsWith(root+path.sep)) throw Error('Campaign must be separate from immutable runtime');
for (const key of Object.keys(process.env)) if (key.startsWith('CAREER_OPS_')) delete process.env[key];
process.env.CAREER_OPS_DATA_DIR=root;
// Upstream modules read the profile at import time. Reject redirected campaign
// entries before any import, including implicit config/history paths.
let inspected=0;
function boundary(folder) {
 for(const entry of fs.readdirSync(folder,{withFileTypes:true})) {
  if(++inspected>100000) throw Error('Campaign metadata exceeds bounded scan');
  if(entry.isSymbolicLink() || (!entry.isFile() && !entry.isDirectory())) throw Error('Campaign contains a redirected or unsupported entry');
  if(entry.isDirectory()) boundary(path.join(folder,entry.name));
 }
}
boundary(root);
function read(name) {
 if (!name || path.isAbsolute(name)) throw Error('Use a campaign-relative input file');
 const file=fs.realpathSync(path.resolve(root,name));
 if (!file.startsWith(root+path.sep) || !fs.statSync(file).isFile() || fs.statSync(file).size>5*1024*1024) throw Error('Input escaped bounded campaign or exceeded limit');
 return fs.readFileSync(file,'utf8');
}
let result;
if (operation==='facts' && args.length===2) {
 const {auditClaims}=await import('./verify-cv-facts.mjs');
 result={...auditClaims(read(args[1]),read(args[0])),limits:'Numeric/phrase heuristic only. Independently verify negation, ownership, units and skills against source fact IDs.'};
} else if (operation==='payload' && args.length===1) {
 const {lintPayload}=await import('./ats-payload.mjs'); result=lintPayload(JSON.parse(read(args[0])));
} else if (operation==='tracker-check' && args.length===1) {
 read(args[0]); const {runTracker}=await import('./tracker.mjs'); let stdout='',stderr='';
 const code=await runTracker('sync',['--check'],{mdPath:fs.realpathSync(path.resolve(root,args[0])),stdout:{write:x=>stdout+=x},stderr:{write:x=>stderr+=x}});
 result={code,stdout,stderr,read_only:true};if(code) process.exitCode=1;
} else if (operation==='followup' && args.length===2 && /^\d+$/.test(args[0])) {
 const tracker=read(args[1]),followups=read('followups.md'),status=read('application-status-log.md');read('config/profile.yml');
 const {analyzeFromContent,loadFollowupsEnabled}=await import('./followup-cadence.mjs');
 const {parseTrackerRows}=await import('./funnel-velocity.mjs');const rows=parseTrackerRows(tracker);
 if(rows.length!==1 || Number(rows[0].num)!==Number(args[0])) throw Error('Supply a one-application tracker matching the requested application number');
 const enabled=loadFollowupsEnabled(path.join(root,'config/profile.yml'));
 // Only the one named application is analyzed; the upstream parser joins its
 // actual same-campaign followup, pin, suppression and status history by ID.
 result=analyzeFromContent(tracker,followups,{enabled,statusLogContent:status});
 if(enabled && (result.metadata?.totalTracked!==1 || result.entries?.length!==1 || Number(result.entries[0].num ?? result.entries[0].appNum)!==Number(args[0]))) throw Error('Named application analysis did not preserve identity');
 result.authority='Preparation only. No contact/suppression authorization or sending follows from cadence.';
} else throw Error('Use facts ROOT SOURCE TARGET | payload ROOT FILE | tracker-check ROOT FILE | followup ROOT NUM ONE_ROW_TRACKER');
console.log(JSON.stringify(result,null,2));
'''
def materialize(source,out):
 runtime=out.parents[2]/'runtime/career-ops';runtime.mkdir(parents=True,exist_ok=True)
 for name in (*MODULES,'tracker-aliases.json','templates/states.yml','templates/benchmarks.yml','LICENSE'):
  target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,target)
 # Preserve data semantics as reference, but never expand Markdown links into
 # an unrelated executable collection.
 contract=(source/'DATA_CONTRACT.md').read_text()
 base='https://github.com/career-ops-hq/career-ops/blob/9a72d7261255ccd46d732d1fe5a5c3c9376d3ceb/'
 contract=re.sub(r'\]\((?![a-zA-Z][a-zA-Z0-9+.-]*:|#|/)([^)]+)\)',lambda m:']('+base+m[1]+')',contract)
 (runtime/'DATA_CONTRACT.md').write_text(contract)
 boundary='Do not submit the form. Stop before Submit, Send, or Apply. Continue only after the candidate confirms they submitted it.'
 if boundary not in (source/'modes/apply.md').read_text():raise ValueError('Pinned draft-only boundary changed')
 package={'name':'nstack-career-preparation','version':'0.0.0','private':True,'type':'module','dependencies':{'js-yaml':'5.3.0'}}
 lock={'name':package['name'],'version':package['version'],'lockfileVersion':3,'requires':True,'packages':{'':package,'node_modules/js-yaml':{'version':'5.3.0','resolved':'https://registry.npmjs.org/js-yaml/-/js-yaml-5.3.0.tgz','integrity':YAML_INTEGRITY,'license':'MIT','dependencies':{'argparse':'^2.0.1'},'bin':{'js-yaml':'bin/js-yaml.js'}},'node_modules/argparse':{'version':'2.0.1','resolved':'https://registry.npmjs.org/argparse/-/argparse-2.0.1.tgz','integrity':ARGPARSE_INTEGRITY,'license':'Python-2.0'}}}
 for name,data in [('package.json',package),('package-lock.json',lock)]: (runtime/name).write_text(json.dumps(data,indent=2)+'\n')
 (runtime/'nstack-prepare.mjs').write_text(WRAPPER)
 (runtime/'AGENTS.md').write_text('''# Isolated preparation only

Current user authority, Codex model and native output control. No author profile,
model router, provider SDK, installer, updater, scheduler or PDF hook is included.
Keep immutable code separate from campaign data. Start with an empty environment,
private empty HOME and explicit absolute CAREER_OPS_DATA_DIR before imports.
Clear every inherited CAREER_OPS_* override, especially CAREER_OPS_ROOT.

'''+boundary+'''

An unknown posting or delivery attempt remains unknown. Deduplicate employer,
requisition and candidate across channels and sender identities. Column/status
aliases in tracker-aliases.json normalize schema only; never use email aliases
to bypass duplicate handling. Facts, generated stories, payloads and application
ledger stay separate. A heuristic pass cannot establish a fact. Review numbers,
units, negation, ownership and skills against attributed immutable fact IDs.
Follow-up preparation names exactly one application, contact, purpose and
suppression state. No blanket sweep or sending is authorized by preparation.
An explicitly authorized release uses a separate one-shot dispatcher binding
account, business identity, payload hash, expiry and remote receipt reconciliation.
''')
 # Retain the actual upstream method instead of replacing its modes with the
 # optional four-operation native preparation adapter.
 original=(source/'.agents/skills/career-ops/SKILL.md').read_text()
 method=original.replace('Claude Code','native host')
 marker=method.index('\n---\n',4)+5
 active=method[:marker]+'\n> Native execution bindings: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md).\n\n'+method[marker:]
 (out/'UPSTREAM_SKILL.md').write_text(original)
 (out/'NATIVE-PORT.patch').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True),active.splitlines(keepends=True),fromfile='upstream/SKILL.md',tofile='SKILL.md')))
 (out/'NATIVE-BINDINGS.md').write_text("""# Native execution bindings

Keep the original career modes and review requirements below. Use the current
host/model and the user's explicit campaign, never the source author's data or
profile. Installation does not authorize applications, messages, account access,
provider calls, hooks, schedulers or an upstream controller.

Required mode playbooks are retained at ../../../runtime/career-ops/modes/.
The optional native preparation lane is separate: read ../../../runtime/career-ops/AGENTS.md
and DATA_CONTRACT.md. Its nstack-prepare.mjs supports facts, payload, tracker-check
and one-application followup only, using explicit campaign-relative files and an
isolated copy with the included dependency lock. It does not implement every
original CLI mode. Use the actual upstream project/runtime only after its own
prerequisites are established; an unavailable runtime remains a reported gap.
The source draft-only stop before Submit, Send or Apply is retained.
""")
 # Plain mode paths are part of this skill's method. Retain those actual source
 # documents without globally installing their related skills or data profiles.
 for file in (source/'modes').rglob('*'):
  if file.is_file()and file.suffix=='.md':
   target=runtime/'modes'/file.relative_to(source/'modes');target.parent.mkdir(parents=True,exist_ok=True)
   text=file.read_text();base='https://github.com/career-ops-hq/career-ops/blob/9a72d7261255ccd46d732d1fe5a5c3c9376d3ceb/'
   def locator(match):
    rel=match[1];resolved=(file.parent/rel).resolve()
    if resolved.is_relative_to(source.resolve()):return ']('+base+str(resolved.relative_to(source.resolve()))+')'
    return match[0]
   text=re.sub(r'\]\((?![a-zA-Z][a-zA-Z0-9+.-]*:|#|/)([^)]+)\)',locator,text)
   target.write_text(text)
 (out/'NATIVE-ADAPTATION.json').write_text(json.dumps({'repository':'career-ops-hq/career-ops','revision':'9a72d7261255ccd46d732d1fe5a5c3c9376d3ceb','source_path':'.agents/skills/career-ops/SKILL.md','source_sha256':hashlib.sha256(original.encode()).hexdigest(),'adapted_sha256':hashlib.sha256(active.encode()).hexdigest(),'adaptation':'Complete original modes retained with model-agnostic wording and a separate native execution binding; optional scoped preparation helper is not the complete upstream controller.'},indent=2)+'\n')
 return active
