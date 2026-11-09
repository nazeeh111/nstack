"""P190 default scan: exact rules, full redaction and no silent suppression."""
import argparse,json,os,pathlib,re,subprocess,tempfile,time,hashlib
P=pathlib.Path
class Arguments(argparse.ArgumentParser):
 def error(self,message):raise ValueError(message)
def parse(args):
 p=Arguments(add_help=False);p.add_argument('mode',choices=['dir','git']);p.add_argument('target');p.add_argument('--report',required=True);p.add_argument('--revision');a=p.parse_args(args)
 if a.mode=='git' and (not a.revision or not re.fullmatch('[0-9a-f]{40}',a.revision)):raise ValueError('Git scan requires an explicit immutable commit SHA; use dir for working files')
 if a.mode=='dir' and a.revision:raise ValueError('Revision applies only to Git history')
 return a
def validate(n,target,report):
 scope=n.project_paths(P.cwd());target=P(target).expanduser().resolve(strict=True);report=P(report).expanduser().absolute()
 if not target.is_relative_to(scope):raise ValueError('Scan target must belong to the current bounded project')
 if any(part in ('.aws','.ssh','.gnupg','.azure','.kube','Keychains') for part in target.parts):raise ValueError('Credential stores are outside this operation')
 if report.exists() or report.is_symlink():raise ValueError('Existing report retained; choose a new explicit path')
 if report.parent.resolve()!=report.parent:raise ValueError('Linked report parent')
 if not report.is_relative_to(n.STATE/'checks'):raise ValueError('Keep audit reports in private nstack checks, outside worker-writable source')
 if target.is_dir() and report.is_relative_to(target):raise ValueError('Keep the private report outside the scanned tree')
 if not target.is_file() and not target.is_dir():raise ValueError('Ordinary file or directory input required')
 def incomplete(error):raise ValueError('Source traversal is incomplete; no coverage claim') from None
 def walk():
  if target.is_file():yield target;return
  for folder,dirs,files in os.walk(target,followlinks=False,onerror=incomplete):
   for name in dirs+files:yield P(folder)/name
   dirs[:]=[name for name in dirs if name!='.git']
 nodes=walk()
 for path in nodes:
  rel=path.relative_to(target) if path!=target else P(path.name)
  if path.is_symlink() and not path.resolve().is_relative_to(target if target.is_dir() else target.parent):raise ValueError('Source link escapes the selected scan tree')
  if '.git' in rel.parts:continue
  if any(part in ('.aws','.ssh','.gnupg','.azure','.kube','Keychains') for part in rel.parts):raise ValueError('Credential-store directory inside scan scope; select a narrower source scope')
  if path.name=='.gitleaksignore':raise ValueError('Source ignore files can suppress new leaks; use a reviewed narrower scope instead')
  if not path.is_dir() and not path.is_file():raise ValueError('Nonregular or broken source input; no coverage claim')
 return target,report
def snapshot(target):
 """Read every scoped regular file; permission errors cannot become clean scans."""
 result={}
 def failed(error):raise ValueError('Unreadable source directory; no coverage claim') from None
 paths=[]
 if target.is_file():paths=[target]
 else:
  for folder,dirs,files in os.walk(target,followlinks=False,onerror=failed):
   dirs[:]=[x for x in dirs if x!='.git'];paths.extend(P(folder)/name for name in files)
 for file in paths:
  h=hashlib.sha256()
  try:
   with file.open('rb') as stream:
    while chunk:=stream.read(1024*1024):h.update(chunk)
  except OSError:raise ValueError('Unreadable source file; no coverage claim') from None
  result[str(file.relative_to(target)) if target.is_dir() else file.name]=h.hexdigest()
 return result
def environment(prefix):
 # Do not inherit token/config/debug environment overrides into an audit.
 return {'PATH':'/usr/bin:/bin:/usr/sbin:/sbin','HOME':str(prefix/'build-home'),'LC_ALL':'C','NO_COLOR':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1','GIT_GRAFT_FILE':'/dev/null','GIT_PAGER':'/bin/cat','GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'core.fsmonitor','GIT_CONFIG_VALUE_0':'false','GIT_CONFIG_KEY_1':'advice.graftFileDeprecated','GIT_CONFIG_VALUE_1':'false'}
def execute(n,r,saved,mode,target,report,revision=None,fixture_config=None):
 target,report=validate(n,target,report);prefix=P(saved['prefix']);source=n.STATE/'sources'/r['source_repository'].replace('/','--')/r['revision'];n.check_source(source)
 config=fixture_config or source/'config/gitleaks.toml'
 if mode=='git':
  repo=P(subprocess.check_output(['/usr/bin/git','-C',str(target),'rev-parse','--show-toplevel'],text=True,env=environment(prefix)).strip()).resolve()
  if repo!=target:raise ValueError('Git audit requires the exact repository root, not a misleading subtree scope')
  shallow=subprocess.check_output(['/usr/bin/git','-C',str(target),'rev-parse','--is-shallow-repository'],text=True,env=environment(prefix)).strip()
  if shallow!='false':raise ValueError('Shallow history is incomplete; no full-history coverage claim')
  actual=subprocess.check_output(['/usr/bin/git','-C',str(target),'rev-parse','--verify',revision+'^{commit}'],text=True,env=environment(prefix)).strip()
  if actual!=revision:raise ValueError('Git revision is not the explicit commit')
 before=snapshot(target)
 report.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
 argv=[str(prefix/'bin'/r['binary']),mode,str(target),'--config',str(config),'--redact=100','--report-format=json','--report-path','-','--gitleaks-ignore-path','/dev/null','--ignore-gitleaks-allow','--no-banner','--no-color','--log-level=warn','--timeout=120']
 if mode=='git':argv+=['--log-opts=--text --no-textconv --no-ext-diff '+revision]
 p=subprocess.run(argv,capture_output=True,text=True,env=environment(prefix))
 # Native output is not echoed: failures must never dump configuration or a
 # potentially unredacted auxiliary finding into a model transcript.
 if p.returncode not in (0,1):raise ValueError('Native scanner failed; no coverage claim')
 try:findings=json.loads(p.stdout)
 except ValueError:raise ValueError('Native scanner produced no standalone machine-readable report; no coverage claim') from None
 if not isinstance(findings,list) or any(f.get('Secret')!='REDACTED' for f in findings):raise ValueError('Native scanner did not satisfy full-redaction contract')
 if (p.returncode==0)!=(not bool(findings)):raise ValueError('Scanner exit/report disagree')
 for line in p.stderr.splitlines():
  # The pinned scanner emits this one warning for a completed positive scan.
  if not re.fullmatch(r'\d{1,2}:\d{2}(?:AM|PM)\s+WRN\s+leaks found:\s*'+str(len(findings)),line.strip()):raise ValueError('Scanner warnings/errors indicate incomplete or unexpected coverage; report withheld')
 if snapshot(target)!=before:raise ValueError('Source changed during scan; no passing coverage claim')
 # Commit messages, author fields, matched source text and arbitrary auxiliary
 # fields are not safe merely because Secret was redacted. Retain locators only.
 safe_fields=('RuleID','StartLine','EndLine','StartColumn','EndColumn','Commit')
 safe=[]
 for finding in findings:
  item={**{key:finding[key] for key in safe_fields if key in finding},'Secret':'REDACTED'}
  # Source-controlled paths can themselves contain the detected value. Hash
  # both textual locators; the owner can match a local path by its SHA-256.
  for key in ('File','Fingerprint'):
   if key in finding:item[key+'SHA256']=hashlib.sha256(str(finding[key]).encode()).hexdigest()
  safe.append(item)
 # The scanner never writes through an untrusted report path. Publish validated
 # redacted JSON exclusively inside private state; never replace existing bytes.
 fd=os.open(report,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
 with os.fdopen(fd,'w') as out:json.dump(safe,out,indent=2);out.write('\n');out.flush();os.fsync(out.fileno())
 return {'source_revision':r['revision'],'mode':mode,'target':str(target),'commit':revision,'findings':len(findings),'redaction_percent':100,'source_files_verified_readable_and_stable':len(before),'source_ignore_and_baseline_suppression':'refused','inline_allow_comments':'ignored','git_replacements_textconv_external_diff':'disabled','rules_sha256':n.sha(P(config).read_bytes()),'report':str(report),'exit_code':p.returncode,'limits':'Pattern detection is not proof of absence of all credentials; binary/archive support and source rights require separate review. Git mode covers the explicit commit ancestry, not all other refs.'},p.stderr
def invoke(n,r,saved,args):
 a=parse(args);result,_=execute(n,r,saved,a.mode,a.target,a.report,a.revision);print(json.dumps(result,indent=2))
 if result['exit_code']:raise subprocess.CalledProcessError(result['exit_code'],['gitleaks',a.mode,a.target])
def check(n,r,saved):
 import contextlib
 artifacts=n.STATE/'checks/artifacts/P190'/('run-'+str(time.time_ns()));artifacts.mkdir(parents=True,exist_ok=True);result={}
 with tempfile.TemporaryDirectory(prefix='nstack-scanner-',dir='/private/tmp') as temp,contextlib.chdir(temp):
  root=P(temp);target=root/'inputs';target.mkdir();reports=artifacts;config=root/'fixture.toml'
  config.write_text('title="Synthetic nstack sentinel only"\n[[rules]]\nid="nstack-fixture"\nregex="NSTACK_SYNTHETIC_SENTINEL_[A-Z0-9]{8}"\nkeywords=["NSTACK_SYNTHETIC_SENTINEL_"]\n')
  (target/'clean.txt').write_text('Ordinary nonsecret fixture.\n');clean,_=execute(n,r,saved,'dir',target,reports/'clean.json',fixture_config=config);assert clean['exit_code']==0 and clean['findings']==0
  marker='NSTACK_SYNTHETIC_SENTINEL_'+'ALPHA123';(target/'sample.txt').write_text(marker+' #gitleaks:allow\n');red,output=execute(n,r,saved,'dir',target,reports/'red.json',fixture_config=config);assert red['exit_code']==1 and red['findings']==1 and marker not in output+(reports/'red.json').read_text()
  # A baseline cannot silently turn a later leak green: this adapter rejects
  # suppression flags entirely, while preserving the user's original files.
  try:parse(['dir',str(target),'--report',str(reports/'bad.json'),'--baseline-path',str(reports/'red.json')])
  except ValueError:baseline_denied=True
  else:raise AssertionError('Unreviewed baseline was accepted')
  second='NSTACK_SYNTHETIC_SENTINEL_'+'BRAVO456';(target/'new.txt').write_text(second+'\n');new,output=execute(n,r,saved,'dir',target,reports/'new.json',fixture_config=config);assert new['findings']==2 and marker not in output and second not in output+(reports/'new.json').read_text()
  named=target/(marker+'.txt');named.write_text(marker+'\n');named_result,output=execute(n,r,saved,'dir',target,reports/'filename.json',fixture_config=config);assert named_result['findings']==3 and marker not in output+(reports/'filename.json').read_text();named.unlink()
  ignore=target/'.gitleaksignore';ignore.write_text('unreviewed-suppression\n')
  try:execute(n,r,saved,'dir',target,reports/'ignored.json',fixture_config=config)
  except ValueError:ignore_denied=True
  else:raise AssertionError('Source ignore could hide a new finding')
  assert not (reports/'ignored.json').exists()
  ignore.unlink()
  # Exercise the actual Git backend against hostile local presentation metadata.
  # These strings are invented sentinels, never provider credentials.
  repo=root/'history';repo.mkdir();empty=root/'empty-template';empty.mkdir()
  git_env=environment(P(saved['prefix']));git_env.update({'GIT_AUTHOR_NAME':'Nstack Fixture','GIT_AUTHOR_EMAIL':'fixture@example.test','GIT_COMMITTER_NAME':'Nstack Fixture','GIT_COMMITTER_EMAIL':'fixture@example.test'})
  def git(*args,input=None):
   return subprocess.check_output(['/usr/bin/git','-C',str(repo),'-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false',*args],input=input,text=True,env=git_env).strip()
  git('init','-q','--template='+str(empty));(repo/'sample.txt').write_text(marker+'\n');git('add','sample.txt');git('commit','-q','-m',marker);revision=git('rev-parse','HEAD')
  changed,output=execute(n,r,saved,'git',repo,reports/'history.json',revision,config)
  persisted=(reports/'history.json').read_text();assert changed['findings']>=1 and marker not in persisted+output
  assert all(set(f).issubset({'RuleID','FileSHA256','StartLine','EndLine','StartColumn','EndColumn','Commit','FingerprintSHA256','Secret'}) for f in json.loads(persisted))
  # A local replace ref must not substitute an unrelated clean object.
  (repo/'sample.txt').write_text('clean replacement\n');git('add','sample.txt');tree=git('write-tree');replacement=git('commit-tree',tree,input='clean\n');git('replace',revision,replacement)
  replaced,_=execute(n,r,saved,'git',repo,reports/'replace.json',revision,config);assert replaced['findings']>=1
  helper=root/'textconv.sh';called=root/'textconv-called';helper.write_text('#!/bin/sh\nprintf called > "'+str(called)+'"\nprintf clean\n');helper.chmod(0o700)
  git('config','diff.nstack.textconv',str(helper));git('config','diff.nstack.command',str(helper));(repo/'.gitattributes').write_text('sample.txt diff=nstack\n')
  presented,_=execute(n,r,saved,'git',repo,reports/'textconv.json',revision,config);assert presented['findings']>=1 and not called.exists()
  (repo/'.gitattributes').write_text('sample.txt -diff\n')
  binary,_=execute(n,r,saved,'git',repo,reports/'binary-attribute.json',revision,config);assert binary['findings']>=1
  subtree=repo/'public';subtree.mkdir()
  try:execute(n,r,saved,'git',subtree,reports/'subtree.json',revision,config)
  except ValueError as error:assert 'repository root' in str(error)
  else:raise AssertionError('Git subtree masqueraded as full audit scope')
  assert not (reports/'subtree.json').exists()
  unreadable=target/'unreadable';unreadable.mkdir();(unreadable/'file').write_text('ordinary fixture');unreadable.chmod(0)
  try:
   try:execute(n,r,saved,'dir',target,reports/'unreadable.json',fixture_config=config)
   except ValueError:pass
   else:raise AssertionError('Unreadable directory became a clean scan')
   assert not (reports/'unreadable.json').exists()
  finally:unreadable.chmod(0o700)
  result={'id':'P190','operation':'cli','source_revision':r['revision'],'binary_sha256':saved['files']['bin/gitleaks'],'actual_native_scanner':True,'synthetic_noncredential_sentinel_detected':True,'report_and_output_redacted':True,'inline_allow_cannot_hide_sentinel':True,'nonsecret_control_passed':True,'new_file_detected':True,'unreviewed_baseline_denied':baseline_denied,'source_ignore_suppression_denied':ignore_denied,'reports':str(artifacts),'limits':'Synthetic custom-rule controls validate execution/redaction/suppression policy. Built-in rule coverage is separately exercised on the actual release tree; no claim of complete secret detection.'}
  result.update({'commit_message_not_persisted':True,'filename_and_fingerprint_hashed':True,'git_replace_cannot_hide_finding':True,'textconv_external_diff_not_executed':True,'binary_attribute_cannot_hide_text':True,'git_subtree_scope_refused':True,'unreadable_directory_refused':True})
 n.dump(n.STATE/'checks/P190-cli.json',result);return result
