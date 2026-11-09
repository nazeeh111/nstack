"""Narrow Resume Matcher to its evaluated conditional verification role."""
import ast,json,pathlib
P=pathlib.Path

def materialize(source,out):
 tools=source/'apps/backend/app/mcp_server/tools'
 signatures={}
 for name in ('verify_resume','parse_check_file','parse_check_resume','export_resume_pdf','save_tailored_resume','tailor_and_verify'):
  file=tools/(name+'.py')
  if not file.is_file():raise ValueError('Complete the exact pinned source cache before building Resume Matcher: '+str(file.relative_to(source)))
  module=ast.parse(file.read_text());function=next((f for f in module.body if isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)) and f.name==name),None)
  if function is None:raise ValueError('Pinned Resume Matcher tool signature changed: '+name)
  signatures[name]=[a.arg for a in function.args.args]
  if name in ('save_tailored_resume','tailor_and_verify') and 'track_application' not in signatures[name]:raise ValueError('Pinned tool cannot disable application tracking')
 ref=out/'references';ref.mkdir(exist_ok=True)
 (ref/'tool-contract.json').write_text(json.dumps({'source_repository':'srbhr/Resume-Matcher','revision':'d480551798b7aa97f5b57ba1972ee383bd882238','inspected_function_arguments':signatures,'default_operations':['parse_check_file','parse_check_resume','verify_resume'],'writes_require_task_scope':['export_resume_pdf','save_tailored_resume','tailor_and_verify'],'required_save_arguments':{'track_application':False},'status':'Source contract only. Actual isolated runtime/print/parse and mutation controls must pass before trial activation.'},indent=2)+'\n')
 return '''---
name: resume-matcher
description: Conditional project-local Resume Matcher print/parse verification for a difficult resume layout or repeated campaign. No automatic setup, tracking, provider call or application submission.
---

# Resume print and parse verification

This is the evaluated P357 trial at source commit
`d480551798b7aa97f5b57ba1972ee383bd882238`. Keep it outside active
discovery until its per-ID trial verifier passes. Read the registered trigger,
rights, prerequisites and acceptance; a staged build is not activation.

Use only for a difficult layout or repeated campaign where an actual final-file
print/parse comparison adds value. Native document output remains the ordinary
route. Keep master facts, candidate/requisition identity and source files intact.
No API key, provider account, master-resume import, database migration, server
startup or background job follows from reading or building this leaf.

## Commission an eligible trial

Use a private disposable exact-commit checkout and a new owned resume database,
with no production database, credentials or personal defaults mounted. The pinned
backend is Python >=3.13; its project lock, Node 24.22.1, frontend package lock and
Playwright/Chromium must be resolved and hash-verified together. Inspect build
scripts and use locked dependencies with install scripts disabled unless a
specific reviewed build step requires them. Never copy a user's .env or run the
upstream broad setup/startup sequence as incidental installation.

An actual print trial needs an explicitly commissioned compatible local backend,
frontend/print service and browser. Bind loopback endpoints, data directory,
process ownership and shutdown path before launch. Select the no-provider agent
mode in the disposable fixture only, preserving real app settings. Capture the
exact executable/runtime versions and hashes. If those target prerequisites or
the verifier are unavailable, keep this trial conditional and use the native
accepted document path. Do not start persistent services merely to prove setup.

## Verify, then inspect the actual artifact

Use the locked environment's CLI by absolute path. From the exact checkout,
`uv run --locked --directory "$SOURCE/apps/backend" resume-matcher TOOL ARGS`
is the upstream invocation shape; use the verified environment without changing
its lock. Even TOOL --help enters upstream MCP startup, which may run migrations
and legacy-key handling. Bind the empty disposable fixture environment before
help or any tool invocation; never point it at a real app database or settings.
Arguments may be a JSON file via `@/absolute/args.json`.
Use `TOOL --help` to compare the actual schema with
[the inspected source contract](references/tool-contract.json).

Start with `parse_check_file file_path=/absolute/fixture.pdf` for a named
synthetic PDF/DOCX, or `parse_check_resume resume_id=FIXTURE_ID` and
`verify_resume resume_id=FIXTURE_ID` for an already prepared disposable record.
Treat rendering errors, missing text, uncertain order, garbled glyphs and missing
fields as unresolved or failed, never a pass. An ATS or writing score does not
establish truth or authorize a rewrite. Reopen every page and independently
compare extracted text, reading order, units and page fit with accepted source.

Export only to a new explicitly named output file with `export_resume_pdf`.
It overwrites existing paths, so retain the last accepted artifact first and
refuse an unintended existing output. Keep all candidate material and exports
outside public Git. No form is submitted and no email or outreach is sent.

## Optional fixture writes

The normal role is verification. If the actual trial explicitly needs a fixture
save, first read the exact source record and bind candidate/requisition identity.
Every `save_tailored_resume` or `tailor_and_verify` argument object MUST contain
`"track_application": false`. Reject an absent or true value before invoking it;
upstream defaults to true. Save at most once per business fixture. If a response
is lost or reports saved:true with verify_error, reconcile the database and saved
resume ID, then verify that ID. Never repeat the save merely to obtain a report.
Independently compare the tracker before/after and require zero Applied cards.
Do not invoke create_application or update_application in this preparation lane.

## Acceptance and retirement

Compare the strongest native incumbent on the same representative consented or
synthetic samples. Inject metric, negation, ownership and skill changes; require
their detection while truthful facts and final-file parse quality are preserved.
Check the actual reopened PDF and parse output, database/tracker effects, source
hashes and changed-input regeneration. Do not promote a heuristic repair as a
truth oracle. Stop only owned trial processes, reverse only recorded project
registrations, and preserve inputs, accepted artifacts, locks and evidence.
'''
