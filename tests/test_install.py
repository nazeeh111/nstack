import pathlib,tempfile,unittest,sys,importlib.util,argparse,subprocess,json,os,plistlib
from unittest.mock import patch
P=pathlib.Path;root=P(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('nstack_install',root/'install.py');i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
class InstallTests(unittest.TestCase):
 def test_cli_entry_installs_companion_and_full_rollback_chain(self):
  with tempfile.TemporaryDirectory() as t:
   base=P(t).resolve();user=base/'user';codex=user/'.codex';personal=user/'.agents/skills/original';personal.mkdir(parents=True);(personal/'SKILL.md').write_text('original collection');codex.mkdir();cli=user/'terminal/bin/codex';cli.parent.mkdir(parents=True);cli.write_text('original-cli-bytes');cli.chmod(0o755);pair=base/'pair';pair.mkdir();binary=pair/'codex';binary.write_text('#!'+sys.executable+'\nimport os,pathlib,sys\np=pathlib.Path(sys.argv[0]).parent/"codex-code-mode-host"\nos.execv(str(p),[str(p)])\n');binary.chmod(0o755);host=pair/'codex-code-mode-host';host.write_text('#!/bin/sh\necho paired-launch-ok\n');host.chmod(0o755)
   args=argparse.Namespace(state=str(base/'state'),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='first',disable_mcp=[],disable_plugin=[],retire_personal=True,stage_only=False,bootstrap_cli=True,cli_path=str(cli))
   with patch('bootstrap.binary_pair',return_value=binary):i.install(args)
   self.assertEqual(subprocess.check_output([str(cli)],text=True).strip(),'paired-launch-ok');self.assertTrue(cli.with_name('codex-code-mode-host').is_symlink())
   # A second immutable release/run must not strand the first migration when
   # the one stable Terminal helper is invoked.
   args.run_id='second';args.retire_personal=False
   with patch('bootstrap.binary_pair',return_value=binary):i.install(args)
   config=codex/'config.toml';config.write_text(config.read_text()+'\n[later]\nkeep=true\n')
   subprocess.run([str(base/'state/rollback.sh')],capture_output=True,check=True)
   self.assertEqual(cli.read_text(),'original-cli-bytes');self.assertFalse(cli.with_name('codex-code-mode-host').exists());self.assertTrue(personal.exists());self.assertTrue(i.cm.tomllib.loads(config.read_text())['later']['keep'])
 def test_full_synthetic_profile_second_install_and_terminal_rollback(self):
  with tempfile.TemporaryDirectory() as t:
   base=P(t).resolve();user=base/'user';codex=user/'.codex';personal=user/'.agents/skills/old';personal.mkdir(parents=True);(personal/'SKILL.md').write_text('synthetic original skill bytes');built=codex/'skills/.system/builtin';built.mkdir(parents=True);(built/'SKILL.md').write_text('synthetic built-in');(codex/'config.toml').write_text('model="user-selected"\nmodel_reasoning_effort="high"\n[mcp_servers.legacy]\ncommand="old"\n[unrelated]\nkeep=1\n');(codex/'AGENTS.md').write_text('User safeguards remain.\n');state=base/'private';args=argparse.Namespace(state=str(state),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='test',disable_mcp=['legacy'],disable_plugin=['legacy@market'],retire_personal=True,stage_only=False)
   before=i.fingerprint(user);result=i.install(args);self.assertFalse(personal.exists());self.assertTrue((built/'SKILL.md').exists());journal=(state/'runs/test/journal.json').read_bytes();i.install(args);self.assertEqual(journal,(state/'runs/test/journal.json').read_bytes())
   report=json.loads(subprocess.check_output([str(user/'bin/nstack'),'doctor'],env=os.environ|{'NSTACK_STATE':str(state)},text=True));self.assertEqual(report['components'],262)
   # A later unrelated setting survives rollback from a standalone Terminal command.
   config=codex/'config.toml';config.write_text(config.read_text().replace('keep=1','keep=2'));subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True,text=True);self.assertTrue((personal/'SKILL.md').is_file());self.assertEqual((codex/'AGENTS.md').read_text(),'User safeguards remain.\n');self.assertEqual(i.cm.tomllib.loads(config.read_text())['unrelated']['keep'],2);self.assertTrue((state/'rollback.sh').is_file())
   # Restore then reapply in the same recorded run; retained originals are never clobbered.
   config.write_text(config.read_text().replace('keep=2','keep=1'));i.install(args);self.assertFalse(personal.exists());subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True);self.assertTrue(personal.exists())

class CompleteAddonPayload(unittest.TestCase):
 def test_every_checked_in_addon_and_integration_payload_is_portable(self):
  # Upstream methods rely on their complete scripts and legal notices, including
  # extensionless files. A successful install must not silently omit them.
  portable={str(rel) for file,rel in i.portable_files()}
  root=i.ROOT
  required={str(file.relative_to(root)) for folder in ['addons','integrations'] for file in (root/folder).rglob('*') if file.is_file() and '__pycache__' not in file.parts and not any(part.startswith('.') for part in file.relative_to(root).parts)}
  self.assertTrue(required)
  self.assertEqual(sorted(required-portable),[])

if __name__=='__main__':unittest.main()

class PolicyAndPreflightTests(unittest.TestCase):
 def test_stricter_policy_and_unknown_rollback_owner(self):
  with tempfile.TemporaryDirectory() as t:
   base=P(t).resolve();user=base/'user';codex=user/'.codex';codex.mkdir(parents=True);config=codex/'config.toml';config.write_text('sandbox_mode="read-only"\napproval_policy="never"\n');state=base/'state';args=argparse.Namespace(state=str(state),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='first',disable_mcp=[],disable_plugin=[],retire_personal=False,stage_only=False)
   i.install(args);data=i.cm.tomllib.loads(config.read_text());self.assertEqual(data['sandbox_mode'],'read-only');self.assertEqual(data['approval_policy'],'never')
   # A second recorded run is valid and keeps its predecessor's recovery helper.
   args.run_id='second';i.install(args);self.assertTrue((state/'runs/first/rollback.sh').exists());self.assertEqual((state/'rollback.sh').resolve(),state/'runs/second/rollback.sh')
   before=i.fingerprint(user);pointer=state/'rollback.sh';pointer.unlink();pointer.write_text('unrelated owner');args.run_id='third'
   with self.assertRaisesRegex(ValueError,'not owned'):i.install(args)
   self.assertEqual(i.fingerprint(user),before)

class PredictableFailureTests(unittest.TestCase):
 def test_readonly_originals_stage_before_retirement_and_restore_modes(self):
  with tempfile.TemporaryDirectory() as t:
   base=P(t).resolve();user=base/'user';codex=user/'.codex';personal=user/'.agents/skills/old';personal.mkdir(parents=True);(personal/'SKILL.md').write_text('retain');codex.mkdir();config=codex/'config.toml';config.write_text('model="chosen"\n');config.chmod(0o400);instructions=codex/'AGENTS.md';instructions.write_text('Preserve safeguards.\n');instructions.chmod(0o444)
   original={p:i.fingerprint(p) for p in [config,instructions]};args=argparse.Namespace(state=str(base/'state'),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='read-only',disable_mcp=[],disable_plugin=[],retire_personal=True,stage_only=False)
   i.install(args);self.assertFalse(personal.exists());subprocess.run([str(base/'state/rollback.sh')],capture_output=True,check=True)
   for p,f in original.items():self.assertEqual(i.fingerprint(p),f)
 def test_plan_race_and_unchecked_launchagent_fail_before_retirement(self):
  with tempfile.TemporaryDirectory() as t:
   base=P(t).resolve();user=base/'user';codex=user/'.codex';personal=user/'.agents/skills/old';personal.mkdir(parents=True);(personal/'SKILL.md').write_text('retain');codex.mkdir();profile=codex/'old.config.toml';profile.write_text('key=1\n')
   plan=base/'plan.json';plan.write_text(json.dumps({'schema':1,'user_home':str(user),'retire':[{'relative_path':'.codex/old.config.toml','expected':i.fingerprint(profile)}]}));args=argparse.Namespace(state=str(base/'state'),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='raced',disable_mcp=[],disable_plugin=[],retire_personal=True,stage_only=False,retirement_plan=str(plan));original=i.retirement_plan
   def race(*a):
    result=original(*a);profile.write_text('key=2\n');return result
   with patch.object(i,'retirement_plan',side_effect=race):
    with self.assertRaisesRegex(ValueError,'Concurrent change'):i.install(args)
   self.assertTrue(personal.exists());self.assertEqual(profile.read_text(),'key=2\n');self.assertFalse((codex/'config.toml').exists())
   job=user/'Library/LaunchAgents/com.example.old.plist';job.parent.mkdir(parents=True);job.write_bytes(plistlib.dumps({'Label':'com.example.old','ProgramArguments':['/usr/bin/true']}));plan.write_text(json.dumps({'schema':1,'user_home':str(user),'retire':[{'relative_path':'Library/LaunchAgents/com.example.old.plist','expected':i.fingerprint(job)}],'unloaded_launch_labels':[]}));args.run_id='unchecked'
   with self.assertRaisesRegex(ValueError,'Every LaunchAgent'):i.install(args)
   self.assertTrue(job.exists());self.assertTrue(personal.exists())
 def test_explicit_retirement_plan_repeat_and_rollback(self):
  with tempfile.TemporaryDirectory() as t:
   base=P(t).resolve();user=base/'user';codex=user/'.codex';codex.mkdir(parents=True);profile=codex/'old.config.toml';profile.write_text('[mcp_servers.legacy]\ncommand="old"\n');original=i.fingerprint(profile)
   plan=base/'plan.json';plan.write_text(json.dumps({'schema':1,'user_home':str(user),'retire':[{'relative_path':'.codex/old.config.toml','expected':original}],'unloaded_launch_labels':[]}))
   args=argparse.Namespace(state=str(base/'state'),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='planned',disable_mcp=[],disable_plugin=[],retire_personal=False,stage_only=False,retirement_plan=str(plan))
   i.install(args);self.assertFalse(profile.exists());journal=(base/'state/runs/planned/journal.json').read_bytes();i.install(args);self.assertEqual(journal,(base/'state/runs/planned/journal.json').read_bytes())
   subprocess.run([str(base/'state/rollback.sh')],capture_output=True,check=True);self.assertEqual(i.fingerprint(profile),original)
 def test_retirement_plan_rejects_foreign_path_and_changed_target_before_profile_mutation(self):
  for fault in ('path','changed'):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    base=P(t).resolve();user=base/'user';codex=user/'.codex';codex.mkdir(parents=True);profile=codex/'old.config.toml';profile.write_text('key=1\n');original=i.fingerprint(profile)
    row={'relative_path':'.codex/old.config.toml' if fault=='changed' else '.ssh/config','expected':original}
    plan=base/'plan.json';plan.write_text(json.dumps({'schema':1,'user_home':str(user),'retire':[row]}))
    if fault=='changed':profile.write_text('key=2\n')
    before=i.fingerprint(user);args=argparse.Namespace(state=str(base/'state'),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='bad-plan',disable_mcp=[],disable_plugin=[],retire_personal=False,stage_only=False,retirement_plan=str(plan))
    with self.assertRaises(ValueError):i.install(args)
    self.assertEqual(i.fingerprint(user),before)
 def test_invalid_guidance_and_directory_collision_preserve_profile(self):
  for fault in ('guidance','destination','linked-config'):
   with self.subTest(fault=fault),tempfile.TemporaryDirectory() as t:
    base=P(t).resolve();user=base/'user';codex=user/'.codex';personal=user/'.agents/skills/old';personal.mkdir(parents=True);(personal/'SKILL.md').write_text('Retain original');codex.mkdir();(codex/'config.toml').write_text('model="chosen"\n');(codex/'AGENTS.md').write_text('User guidance\n')
    if fault=='guidance':(codex/'AGENTS.md').write_text('<!-- nstack:start -->\ntruncated\n')
    if fault=='destination':(user/'bin/nstack').mkdir(parents=True)
    if fault=='linked-config':
     config=codex/'config.toml';target=user/'shared.toml';config.rename(target);config.symlink_to(target)
    before=i.fingerprint(user);args=argparse.Namespace(state=str(base/'state'),user_home=str(user),codex_home=str(codex),bin_dir=str(user/'bin'),run_id='preflight',disable_mcp=[],disable_plugin=[],retire_personal=True,stage_only=False)
    with self.assertRaises(ValueError):i.install(args)
    self.assertEqual(i.fingerprint(user),before)


class InterpreterLauncherTests(unittest.TestCase):
 def test_launcher_uses_installing_python_under_hostile_path_and_restores_prior_entries(self):
  for prior_kind in ('file','link'):
   with self.subTest(prior_kind=prior_kind),tempfile.TemporaryDirectory() as temporary:
    base=P(temporary).resolve();user=base/"user's home";codex=user/'.codex';codex.mkdir(parents=True)
    bin_dir=user/'bin tools';bin_dir.mkdir();entry=bin_dir/'nstack'
    original=base/'original.py';original.write_text('Original uncommitted launcher bytes.\n')
    if prior_kind=='link':entry.symlink_to(original)
    else:entry.write_text('Original uncommitted executable.\n');entry.chmod(0o751)
    prior=i.fingerprint(entry)
    state=base/'private state'
    args=argparse.Namespace(state=str(state),user_home=str(user),codex_home=str(codex),bin_dir=str(bin_dir),run_id='bound-python',disable_mcp=[],disable_plugin=[],retire_personal=False,stage_only=False)
    result=i.install(args);journal=state/'runs/bound-python/journal.json';journal_before=journal.read_bytes()
    self.assertFalse(entry.is_symlink());self.assertTrue(os.access(entry,os.X_OK))
    i.install(args);self.assertEqual(journal.read_bytes(),journal_before)
    hostile=base/'hostile-path';hostile.mkdir();fake=hostile/'python3'
    fake.write_text('#!/bin/sh\nprintf intercepted > "$NSTACK_TEST_MARKER"\nexit 97\n');fake.chmod(0o755)
    marker=base/'intercepted';env={'PATH':str(hostile),'HOME':str(user),'CODEX_HOME':str(codex),'NSTACK_STATE':str(state),'NSTACK_TEST_MARKER':str(marker)}
    legacy=base/'legacy-nstack';legacy.symlink_to(P(result['release'])/'nstack.py')
    failed=subprocess.run([str(legacy),'doctor'],env=env,capture_output=True)
    self.assertEqual(failed.returncode,97);self.assertTrue(marker.exists());marker.unlink()
    report=json.loads(subprocess.check_output([str(entry),'doctor'],env=env,text=True))
    self.assertEqual(report['python'],sys.version.split()[0]);self.assertEqual(report['components'],262)
    # This real CLI path imports config_merge/tomllib and writes only the owned
    # temporary project. A passing metadata-only doctor is insufficient.
    project=user/'project';(project/'.codex').mkdir(parents=True)
    config=project/'.codex/config.toml';config.write_text('user_note="retained"\n');project_before=i.fingerprint(config)
    subprocess.run([str(entry),'project-init',str(project)],env=env,capture_output=True,check=True)
    installed=i.cm.tomllib.loads(config.read_text())
    self.assertEqual(installed['mcp_servers']['nstack_project']['command'],str(P(sys.executable).absolute()))
    self.assertEqual(installed['user_note'],'retained')
    subprocess.run([str(entry),'project-remove',str(project)],env=env,capture_output=True,check=True)
    self.assertEqual(i.fingerprint(config),project_before);self.assertFalse(marker.exists())
    subprocess.run([result['rollback']],env=env,capture_output=True,check=True)
    self.assertEqual(i.fingerprint(entry),prior);self.assertFalse(marker.exists())

 def test_unsupported_python_stops_before_imports_or_profile_mutation(self):
  with tempfile.TemporaryDirectory() as temporary:
   base=P(temporary).resolve();user=base/'user';user.mkdir();state=base/'state'
   argv=[str(root/'install.py'),'install','--state',str(state),'--user-home',str(user),'--codex-home',str(user/'.codex'),'--bin-dir',str(user/'bin')]
   code='import runpy,sys; sys.version_info=(3,10,0); sys.argv='+repr(argv)+'; runpy.run_path('+repr(str(root/'install.py'))+',run_name="__main__")'
   result=subprocess.run([sys.executable,'-c',code],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0);self.assertIn('requires Python 3.11 or later',result.stderr)
   self.assertNotIn('tomllib',result.stderr);self.assertFalse(state.exists());self.assertEqual(list(user.iterdir()),[])
