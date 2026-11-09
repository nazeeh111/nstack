"""Execute actual patched save/publish tails with inert doubles, never train/upload."""
import ast,json,pathlib,sys,tempfile,logging,importlib.util,os
P=pathlib.Path
release=P(sys.argv[1]).resolve();scripts=release/'scripts';sys.path.insert(0,str(scripts));from nstack_publish_scope import publish_if_authorized
examples=sorted(scripts.glob('train_*_example.py'));assert len(examples)==13
class Model:
 def __init__(self):self.pushes=[];self.saved=[]
 def save_pretrained(self,path):self.saved.append(path);P(path).mkdir(parents=True,exist_ok=True);(P(path)/'config.json').write_text('{"synthetic":true}')
 def push_to_hub(self,*args,**kw):self.pushes.append((args,kw))
with tempfile.TemporaryDirectory() as temp:
 os.chdir(temp)
 for script in examples:
  tree=ast.parse(script.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  doc=ast.get_docstring(tree) or ''
  assert 'Default Hub push' not in doc and 'push_to_hub=True' not in doc and 'hub_strategy="every_save"' not in doc, script
  save_index=next(i for i,n in enumerate(main.body) if any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='save_pretrained' for c in ast.walk(n)))
  start=save_index-1 if save_index and isinstance(main.body[save_index-1],ast.Assign) and any(isinstance(t,ast.Name) and t.id=='final_dir' for t in main.body[save_index-1].targets) else save_index
  tail=ast.FunctionDef(name='tail',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=main.body[start:],decorator_list=[]);module=ast.fix_missing_locations(ast.Module(body=[tail],type_ignores=[]))
  reports=[n.value for n in ast.walk(tree) if isinstance(n,ast.keyword) and n.arg=='report_to'];assert len(reports)==1 and isinstance(reports[0],ast.Constant) and reports[0].value=='none'
  for smoke in [True,False]:
   model=Model();out=P(temp)/script.stem/str(smoke);namespace={'model':model,'student':model,'OUTPUT_DIR':str(out),'SMOKE_TEST':smoke,'logging':logging,'publish_if_authorized':lambda m,p:publish_if_authorized(m,p,[])};exec(compile(module,str(script),'exec'),namespace);namespace['tail']();assert not model.pushes;assert json.loads((P(model.saved[-1])/'config.json').read_text())=={'synthetic':True}
print(json.dumps({'templates':len(examples),'save_and_reopen_tail_paths':26,'default_upload_calls':0,'default_report_to':'none','scope':'inert mocked tails, not model training or network transmission'}))
