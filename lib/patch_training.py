"""Registered S1 patch, preserving all thirteen training routes and local saves."""
import ast,pathlib,re,shutil
P=pathlib.Path
AUTHORITY_NOTE = "> Native authority binding: Local saves and `report_to=\"none\"` are the default. Use the upload, hosted-tracker and Jobs recipes only within the user's existing named destination, data/rights, visibility and spending scope. They grant no account or publication authority. Reuse authority already given; never inspect token stores or echo keys. Use supported native account status/setup.\n\n"

def authority_note(text):
 match=re.search(r'(?m)^# [^\n]+\n',text)
 if not match:raise ValueError('Training reference heading missing')
 return text[:match.end()]+'\n'+AUTHORITY_NOTE+text[match.end():].lstrip('\n')

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
 p.write_text(authority_note('\n'.join(lines)+'\n'))
 # Retain complete source recipes. Only automatic remote tracking changes;
 # native account-status commands are not manual credential-store inspection.
 p=out/'references/training_args.md';text=p.read_text()
 if text.count('report_to="trackio"')!=2:raise ValueError('Training logging defaults changed')
 p.write_text(authority_note(text.replace('report_to="trackio"','report_to="none"')))
 p=out/'references/hf_jobs_execution.md';p.write_text(authority_note(p.read_text()))
 p=out/'references/troubleshooting.md';p.write_text(authority_note(p.read_text()))
