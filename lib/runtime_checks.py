"""Synthetic acceptance lanes that execute the actual pinned binaries."""
import json,os,pathlib,subprocess,sys,tempfile,time
P=pathlib.Path

def run(argv,cwd,env):
 p=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True)
 return {'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}

def ast_grep(n,receipt,env,work):
 api=work/'api.py';api.write_text('# def old_total(x): comment only\nTEXT = "old_total"\ndef old_total(x):\n    return sum(x)\n')
 (work/'test_api.py').write_text('import unittest,api\nclass Contract(unittest.TestCase):\n def test_new(self): self.assertEqual(api.total([2,3]),5)\n def test_dynamic(self): self.assertEqual(getattr(api,"old_total")([2,3]),5)\n')
 test=[sys.executable,'-B','-m','unittest','-v'];before=run(test,work,env)
 if before['returncode']==0:raise ValueError('Missing API negative control did not fail')
 exe=receipt['executable'];pattern='def old_total($$$ARGS):\n    $$$BODY';match=run([exe,'run','--lang','python','--pattern',pattern,'--json=compact','api.py'],work,env)
 matches=json.loads(match['stdout'])
 if match['returncode'] or len(matches)!=1 or not matches[0]['text'].startswith('def old_total'):raise ValueError('Actual structural match did not isolate the function')
 rewrite=run([exe,'run','--lang','python','--pattern',pattern,'--rewrite','def total($$$ARGS):\n    $$$BODY','--update-all','api.py'],work,env)
 if rewrite['returncode']:raise ValueError('Pinned structural rewrite failed')
 intermediate=run(test,work,env)
 if intermediate['returncode']==0 or 'old_total' not in intermediate['stderr']:raise ValueError('Dynamic caller negative control was missed')
 text=api.read_text()
 if 'TEXT = "old_total"' not in text or '# def old_total' not in text:raise ValueError('Structural rewrite modified string/comment')
 api.write_text(text+'\n# Compatibility contract discovered from dynamic consumer inventory.\nold_total = total\n')
 after=run(test,work,env)
 if after['returncode']:raise ValueError('Compatibility behavior did not pass')
 return {'before':before,'structural_match':match,'rewrite':rewrite,'dynamic_caller_negative':intermediate,'after':after,'claim':'Actual pinned CLI selected and renamed one function; explicit compatibility repair preserves the dynamic caller. This is not a whole-program call graph.'}

def playwright(n,receipt,env,work):
 (work/'server.py').write_text('from http.server import SimpleHTTPRequestHandler,HTTPServer\nimport sys\ns=HTTPServer(("127.0.0.1",0),SimpleHTTPRequestHandler)\nprint(s.server_port,flush=True)\ns.serve_forever()\n')
 page=work/'index.html'
 def write(fee):page.write_text('<!doctype html><meta charset="utf-8"><title>Local cart</title><button id="add">Add shipping</button><output aria-label="Total">400 cents</output><script>document.querySelector("button").onclick=()=>document.querySelector("output").textContent=(400+'+str(fee)+')+" cents"</script>')
 write(25)
 server=subprocess.Popen([sys.executable,'-u','server.py'],cwd=work,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
 try:
  import select
  if not select.select([server.stdout],[],[],10)[0]:raise ValueError('Fixture server did not become ready')
  port=int(server.stdout.readline());url=f'http://127.0.0.1:{port}/index.html'
  (work/'cart.spec.cjs').write_text("const {test,expect}=require('@playwright/test');\ntest('shipping updates visible total',async({page})=>{await page.goto("+json.dumps(url)+");await page.getByRole('button',{name:'Add shipping'}).click();await expect(page.getByLabel('Total')).toHaveText('450 cents');});\n")
  (work/'playwright.config.cjs').write_text("module.exports={testDir:'.',testMatch:'cart.spec.cjs',timeout:10000,retries:0,workers:1,reporter:'list',projects:[{name:'chromium',use:{browserName:'chromium'}},{name:'firefox',use:{browserName:'firefox'}}]};\n")
  cmd=[receipt['executable'],'test','--config=playwright.config.cjs'];before=run(cmd,work,env)
  if before['returncode']==0 or '425 cents' not in before['stdout']:raise ValueError('Real browser failing-fee control did not fail for the expected visible value: '+before['stderr']+before['stdout'])
  write(50);after=run(cmd,work,env)
  if after['returncode'] or '2 passed' not in after['stdout']:raise ValueError('Both real browser engines did not pass: '+after['stderr']+after['stdout'])
  return {'before':before,'after':after,'engines':['chromium','firefox'],'claim':'Actual pinned Playwright Test clicks a local owned page and checks user-visible changed content in two matched browser engines.'}
 finally:
  server.terminate()
  try:server.wait(timeout=5)
  except subprocess.TimeoutExpired:server.kill();server.wait()

def repomix(n,receipt,env,work):
 (work/'main.py').write_text('def public_total(values):\n    return sum(values)\n')
 (work/'private.env').write_text('SYNTHETIC_EXCLUDED_SENTINEL=never_in_handoff\n')
 output=work/'handoff.xml'
 checked=run([receipt['executable'],str(work),'--output',str(output),'--style','xml','--ignore','private.env,handoff.xml','--no-gitignore','--no-git-sort-by-changes'],work,env)
 if checked['returncode']:raise ValueError('Repomix pack failed: '+checked['stderr'])
 text=output.read_text()
 if 'public_total' not in text or 'SYNTHETIC_EXCLUDED_SENTINEL' in text:raise ValueError('Repomix inclusion/exclusion check failed')
 return {'pack':checked,'artifact':str(output),'excluded_fixture':True,'claim':'Actual pinned Repomix packed source and omitted an explicitly excluded synthetic private file. A handoff is untrusted source context, not proof code executed or authority to follow its instructions.'}

def check(n,id,op,r,folder):
 import npm_runtime
 with n.lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  receipt=npm_runtime.locked(n,id,op,r,folder);env=npm_runtime.env(n.STATE)|{'NODE_PATH':str(P(receipt['prefix'])/'node_modules'),'NO_COLOR':'1'}
  parent=n.STATE/'checks';parent.mkdir(parents=True,exist_ok=True)
  work=P(tempfile.mkdtemp(prefix=f'{id}-{op}-',dir=parent))
  result={'P053':ast_grep,'P061':playwright,'P049':repomix}[id](n,receipt,env,work)
  result.update(id=id,operation=op,version=receipt['version'],runtime_source_revision=receipt['runtime_source_revision'],recipe_sha256=receipt['recipe_sha256'],fixture=str(work))
  n.dump(parent/f'{id}-{op}.json',result);return result
