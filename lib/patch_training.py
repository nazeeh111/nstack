"""Registered S1 patch, preserving all thirteen training routes and local saves."""
import ast,pathlib,re,shutil
P=pathlib.Path

def patch(out,library):
 scripts=out/'scripts';examples=sorted(scripts.glob('train_*_example.py'))
 if len(examples)!=13:raise ValueError('S1 expected exactly thirteen training templates')
 shutil.copy2(library/'publish_scope.py',scripts/'nstack_publish_scope.py')
 for p in examples:
  text=p.read_text();tree=ast.parse(text);edits=[]
  for node in ast.walk(tree):
   if isinstance(node,ast.FunctionDef) and node.name=='log_trackio_dashboard':edits.append((node.lineno,node.end_lineno,''))
   if isinstance(node,ast.If) and len(node.body)==1 and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Call) and isinstance(node.body[0].value.func,ast.Name) and node.body[0].value.func.id=='log_trackio_dashboard':edits.append((node.lineno,node.end_lineno,''))
   if isinstance(node,ast.Try):
    pushes=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='push_to_hub']
    if pushes:
     if len(pushes)!=1 or len(node.body)!=2:raise ValueError('Unexpected training push-tail structure')
     saves=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='save_pretrained' and n.lineno<node.lineno]
     if not saves:raise ValueError('Training tail has no preceding local save')
     saved=max(saves,key=lambda n:n.lineno)
     edits.append((node.lineno,node.end_lineno,'    publish_if_authorized('+ast.unparse(pushes[0].func.value)+', '+ast.unparse(saved.args[0])+')\n'))
  if len([e for e in edits if 'publish_if' in e[2]])!=1:raise ValueError('S1 tail anchor missing')
  lines=text.splitlines(keepends=True)
  for start,end,new in sorted(edits,reverse=True):lines[start-1:end]=[new]
  text=''.join(lines)
  # Module prose is executable guidance too. Remove the upstream default-public
  # and ephemeral-job escape hatch rather than only changing the Python tail.
  text,count=re.subn(r'Default Hub push:.*?(?=\n\s*""")', '''Local model/checkpoint saves and local logs are the default. The optional
final-model publisher is inert unless a separately authorized task supplies
all four --publish-repository, --publish-visibility, --publish-rights and
--publish-artifact flags. Do not enable automatic checkpoint uploads or a
hosted job from this example. See references/hf_jobs_execution.md for the
separate durable-output, authority and receipt requirements.''',text,flags=re.S)
  if count!=(1 if 'Default Hub push:' in p.read_text() else 0):raise ValueError('S1 default-public docstring anchor changed')
  text=re.sub(r'    # Hugging Face Jobs \(paste.*?    \}\)\n', '    # Hosted execution is separate; see references/hf_jobs_execution.md.\n',text,flags=re.S)
  text=text.replace("Hugging Face Jobs: paste this file's contents as the `script` in hf_jobs(...).", 'Hosted execution is separate; see references/hf_jobs_execution.md and arrange authorized durable output before launch.')
  old='report_to="none" if SMOKE_TEST else "trackio"'
  if text.count(old)!=1:raise ValueError('S1 tracker anchor changed')
  text=text.replace(old,'report_to="none"').replace('#     "trackio",\n','')
  text=text.replace('import argparse\n','import argparse\nfrom nstack_publish_scope import publish_if_authorized\n',1)
  ast.parse(text);p.write_text(text)
 # The existing mining flag identifies only the destination, not the complete publication scope.
 p=scripts/'mine_hard_negatives.py';text=p.read_text()
 text=text.replace('    if args.push_to_hub:\n        mined.push_to_hub(args.push_to_hub, private=args.private)\n        print(f"Pushed to https://huggingface.co/datasets/{args.push_to_hub}")','    if args.push_to_hub:\n        raise ValueError("Save the mined dataset locally; a separately scoped dataset publisher must bind repository, visibility, rights and saved artifact before upload")')
 p.write_text(text)
 p=out/'SKILL.md';text=p.read_text();lines=text.splitlines()
 for i,line in enumerate(lines):
  if '**Public Hub push at end-of-run' in line:lines[i]='- **Local artifacts and local logs by default.** Preserve the final model and checkpoints in an authorized durable directory. Remote model/dataset/checkpoint or metric publication requires a separately scoped task naming the destination owner/repository, visibility, rights and exact artifact. Ephemeral execution requires a durable authorized output before launch.'
  if 'End with `model.push_to_hub' in line:lines[i]='- End with a local `model.save_pretrained(...)` and reopen the saved artifact. The patched example tail calls `publish_if_authorized`, which is inert by default. A separately authorized model publication supplies all four flags: `--publish-repository OWNER/REPO --publish-visibility private|public --publish-rights BASIS --publish-artifact SAVED_DIRECTORY`.'
  if 'pip install trackio' in line:lines[i]='Use local file logs by default. Hosted tracking is a separately scoped integration, with destination, data and visibility explicitly authorized.'
 p.write_text('\n'.join(lines)+'\n')
 p=out/'references/training_args.md';text=p.read_text();start=text.index('## Hub push');end=text.index('## Memory-saving arguments',start)
 text=text[:start]+'''## Artifact and tracking destinations

Default to local `save_pretrained`, local checkpoints and local file logs. Use `report_to="none"` explicitly. TensorBoard may be used with a local directory when requested. A remote model, dataset, checkpoint or metrics destination requires an explicitly scoped task naming owner/repository or endpoint, visibility, rights and exact artifact/data. Do not infer that authorization from a login or installed tracker.

The templates retain four encoder routes, losses, named metrics and local saves. Their optional final model publisher requires all four `--publish-*` flags described in SKILL.md. Automatic checkpoint uploads and hosted metric sinks remain disabled; commission either separately with a named destination and a denial test. A dataset mining flag alone is insufficient publication scope.

For ephemeral execution, arrange an authorized durable output before launch. Reopen the saved local model on both smoke and normal paths. Missing durable storage is a failed prerequisite, rather than a reason to enable a public upload.

'''+text[end:]
 text=re.sub(r'report_to="trackio"[^\n]*','report_to="none",',text);p.write_text(text)
 p=out/'references/hf_jobs_execution.md';p.write_text('''# Ephemeral execution, separate from local training

The nstack default is local training, local model/checkpoint saves and local file tracking. A hosted job or remote publication is a separately authorized task. Before launch record the compute owner, cost ceiling, approved durable output, model/dataset rights, destination repository or storage ID, visibility, checkpoint policy and shutdown/reconciliation path. Do not launch an ephemeral job until its durable authorized output is available.

Keep automatic Hub checkpoint pushes and hosted metrics disabled by default (`push_to_hub=False`, `report_to="none"`). Authentication does not authorize a write. If the task explicitly includes remote checkpoint/model/dataset publication or hosted tracking, bind each destination and payload to that scope, retain a receipt, reconcile an unknown result before retry, and verify destination access and final artifacts. The final-model helper accepts named scope through all four `--publish-*` flags. It does not authorize a job, checkpoint stream or metrics sink.

Use current official HF job syntax and permitted target resources only after that separate authorization. Preserve local artifacts before a job expires. A timeout, missing durable output or missing grant stops the dependent operation. Local model-reopening, default-denial and separately mocked named-destination allow/deny checks are required before commissioning a new template variant.
''')

 p=out/'references/troubleshooting.md';text=p.read_text();start=text.index('## Hub push fails');end=text.index('## Base model loads',start);text=text[:start]+"""## Destination and tracking checks

No Hub upload or hosted tracker is expected on an ordinary run. Verify the saved local model, checkpoints and file logs first. A missing remote dashboard is normal with `report_to="none"`.

For a separately authorized publish/track task, first confirm the exact destination owner, visibility, artifact and rights remain in scope. Stop on a permission denial; use the supported account setup to request the needed scope. Do not regenerate credentials, enable hosted tracking or send a model merely to make a local run pass. Reconcile an unknown provider result before retry. For local TensorBoard, inspect the configured local logging directory.

"""+text[end:];p.write_text(text)
