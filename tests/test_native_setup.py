import argparse,json,pathlib,subprocess,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
import native_setup as native
import transaction
from transaction import fingerprint

class NativeSetup(unittest.TestCase):
 def setUp(self):
  saved=native.nstack.STATE;self.addCleanup(setattr,native.nstack,'STATE',saved)
 def args(self,home,state):
  return argparse.Namespace(home=str(home),state=str(state),only=['obsidian-markdown'],agent_reach=False,repository_docs=False,replace=True,vault=None)

 def fixture(self,base):
  source=base/'source';entry=source/'skills/entry';entry.mkdir(parents=True)
  (entry/'SKILL.md').write_text('---\nname: p011-obsidian-markdown\ndescription: fixture\n---\nRead [required support](../../support.md).\n')
  (source/'support.md').write_text('Required retained support.\n')
  (source/'LICENSE').write_text('MIT fixture\n')
  leaf=next(s for name,s in native.selection() if name=='obsidian-markdown')
  receipt={'content_sha256':'fixture','builder_sha256':'fixture','entry_dir':'skills/entry','files':{str(p.relative_to(source)):native.sha(p.read_bytes()) for p in source.rglob('*') if p.is_file()}}
  (source/'.nstack-release.json').write_text(json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False)+'\n')
  return source,leaf,receipt
 def test_complete_support_is_retained_but_only_the_selected_entry_is_exposed(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();source,leaf,r=self.fixture(base);state=base/'state'
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    release,index=native.prepare(state,[('obsidian-markdown',leaf)],[])
    entry=release/'skills/obsidian-markdown';self.assertEqual((entry/'../../support.md').resolve().read_text(),'Required retained support.\n')
    self.assertEqual(list((release/'skills').iterdir()),[entry]);self.assertIn('name: obsidian-markdown\n',(entry/'SKILL.md').read_text());self.assertTrue((release/'bundles/obsidian-markdown/UPSTREAM-RELEASE.json').is_file())
    bundle=release/'bundles/obsidian-markdown';bundle.chmod(0o755);(bundle/'NATIVE-MANIFEST.json').write_text('unexpected nested file')
    with self.assertRaisesRegex(ValueError,'release changed'):native.prepare(state,[('obsidian-markdown',leaf)],[])
 def test_addon_order_has_one_identity_and_identical_index_on_repeat(self):
  with tempfile.TemporaryDirectory() as temp:
   state=pathlib.Path(temp).resolve()/'state'
   first,index=native.prepare(state,[],['repository-docs','agent-reach'])
   before=fingerprint(first)
   second,repeated=native.prepare(state,[],['agent-reach','repository-docs'])
   self.assertEqual(first,second);self.assertEqual(index,repeated)
   self.assertEqual([r['name'] for r in index],['agent-reach','repository-docs'])
   self.assertEqual(fingerprint(second),before)
   self.assertEqual(json.loads((first/'NATIVE-MANIFEST.json').read_text())['inputs']['adaptation'],'full-bundle-natural-entry-v2')
 def test_addon_runtime_caches_do_not_change_deployable_inputs(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);source=root/'addons/fixture';source.mkdir(parents=True)
   (source/'SOURCE.json').write_text('{"license":"MIT"}');(source/'SKILL.md').write_text('fixture');(source/'LICENSE').write_text('MIT')
   with patch.object(native,'ROOT',root):
    before=native.addon_definition('fixture')['frozen_files']
    cache=source/'scripts/__pycache__';cache.mkdir(parents=True);(cache/'helper.cpython-314.pyc').write_bytes(b'local path-bearing cache')
    (source/'.DS_Store').write_bytes(b'local metadata')
    self.assertEqual(native.addon_definition('fixture')['frozen_files'],before)
 def test_exact_selection_excludes_conditional_and_reference_paths(self):
  rows=native.selection();self.assertEqual(len(rows),170);self.assertEqual(len({n for n,_ in rows}),170)
  for name,s in rows:
   self.assertIn(s['delivery'],['intact upstream leaf','narrow-patched leaf','native runtime/method adapter']);self.assertFalse(name.startswith(s['candidate_id'].lower()+'-'))
   self.assertEqual(native.nstack.component(s['candidate_id'])['deployment'],'on demand')
 def test_explicit_untangle_addition_preserves_base_repeat_and_rollback(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';home.mkdir();state=base/'state';source,leaf,r=self.fixture(base)
   args=self.args(home,state);args.untangle_codebase=True
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    result=native.apply(args);self.assertEqual(result['skills'],2)
    shared=home/'.agents/skills';self.assertEqual({p.name for p in shared.iterdir()},{'obsidian-markdown','untangle-codebase'})
    entry=shared/'untangle-codebase';provenance=json.loads((entry/'SOURCE.json').read_text())
    self.assertEqual(provenance['revision'],'f3cf47774975a7d9fca45730babf4ff7ad765ada')
    for name,receipt in provenance['upstream_files'].items():self.assertEqual(native.sha((entry/name).read_bytes()),receipt['sha256'])
    self.assertIn('disable-model-invocation: true\n',(entry/'SKILL.md').read_text())
    self.assertIn('allow_implicit_invocation: false\n',(entry/'agents/openai.yaml').read_text())
    before={p:fingerprint(p) for p in [shared,home/'.codex/AGENTS.md',state/'native-skill-index.json',pathlib.Path(result['run'])/'journal.json']}
    self.assertFalse(native.apply(args)['changed'])
    for p,value in before.items():self.assertEqual(fingerprint(p),value)
   subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True)
   self.assertFalse(shared.exists());self.assertFalse((home/'.codex/AGENTS.md').exists())
 def test_01_addition_preserves_selected_skill_dirty_original_and_manual_policy(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';home.mkdir();state=base/'state';source,leaf,r=self.fixture(base)
   legacy=home/'.agents/skills/01';legacy.mkdir(parents=True);(legacy/'SKILL.md').write_text('Original dirty01 bytes\n');original=fingerprint(legacy.parent)
   args=self.args(home,state);args.adaptive_routing=True
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    result=native.apply(args);shared=home/'.agents/skills';self.assertEqual({p.name for p in shared.iterdir()},{'obsidian-markdown','01'})
    entry=shared/'01';self.assertIn("name: '01'\n",(entry/'SKILL.md').read_text())
    self.assertIn('disable-model-invocation: true\n',(entry/'SKILL.md').read_text());self.assertIn('allow_implicit_invocation: false\n',(entry/'agents/openai.yaml').read_text())
    self.assertTrue((entry/'references/decisions.md').is_file());self.assertEqual((shared/'obsidian-markdown/../../support.md').resolve().read_text(),'Required retained support.\n')
    journal=pathlib.Path(result['run'])/'journal.json';before=journal.read_bytes();self.assertFalse(native.apply(args)['changed']);self.assertEqual(journal.read_bytes(),before)
   subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True);self.assertEqual(fingerprint(legacy.parent),original)
 def test_raea_and_01_keep_support_and_use_durable_recipe_without_installing_engine(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';home.mkdir();state=base/'state';source,leaf,r=self.fixture(base)
   args=self.args(home,state);args.adaptive_routing=True;args.raea=True
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    result=native.apply(args);shared=home/'.agents/skills'
    self.assertEqual({p.name for p in shared.iterdir()},{'obsidian-markdown','01','raea'})
    recipe=pathlib.Path(json.loads((shared/'raea/SOURCE.json').read_text())['runtime_recipe'])
    self.assertTrue(recipe.is_relative_to(state/'releases'));self.assertEqual(recipe.read_bytes(),(ROOT/'recipes/raea.py').read_bytes())
    self.assertTrue((shared/'01/scripts/capabilities.py').is_file());self.assertFalse((state/'native-tools/raea').exists())
    journal=pathlib.Path(result['run'])/'journal.json';old=journal.read_bytes()
    self.assertFalse(native.apply(args)['changed']);self.assertEqual(journal.read_bytes(),old)
   subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True)
   self.assertFalse(shared.exists())
 def test_repeat_and_terminal_rollback_preserve_original_dirty_bytes_and_new_data(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';state=base/'state';home.mkdir();source,leaf,r=self.fixture(base)
   old=home/'.agents/skills/old';old.mkdir(parents=True);(old/'SKILL.md').write_text('dirty original bytes\n')
   agents=home/'.codex/AGENTS.md';agents.parent.mkdir();agents.write_text('Unrelated user instructions.\n');old_root=fingerprint(old.parent);old_agents=fingerprint(agents)
   args=argparse.Namespace(home=str(home),state=str(state),only=['obsidian-markdown'],agent_reach=False,repository_docs=False,replace=True,vault=None)
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    result=native.apply(args);journal=pathlib.Path(result['run'])/'journal.json';before=journal.read_bytes();self.assertFalse(native.apply(args)['changed']);self.assertEqual(journal.read_bytes(),before)
   (home/'new-note.md').write_text('preserve after install\n');subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True)
   self.assertEqual(fingerprint(old.parent),old_root);self.assertEqual(fingerprint(agents),old_agents);self.assertEqual((home/'new-note.md').read_text(),'preserve after install\n');self.assertFalse((state/'rollback.sh').exists())
 def test_recovery_is_available_when_apply_is_interrupted_after_first_mutation(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';state=base/'state';home.mkdir();source,leaf,r=self.fixture(base)
   args=argparse.Namespace(home=str(home),state=str(state),only=['obsidian-markdown'],agent_reach=False,repository_docs=False,replace=False,vault=None)
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)),patch.object(native.Transaction,'replace_file',side_effect=RuntimeError('interrupted')):
    with self.assertRaisesRegex(RuntimeError,'interrupted'):native.apply(args)
   self.assertTrue((home/'.agents/skills').is_symlink());self.assertTrue((state/'rollback.sh').is_symlink())
   subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True);self.assertFalse((home/'.agents/skills').exists());self.assertFalse((state/'native-skill-index.json').exists())
 def test_rewritten_self_seal_and_writable_modes_do_not_authenticate_tampering(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();source,leaf,r=self.fixture(base);state=base/'state'
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    release,_=native.prepare(state,[('obsidian-markdown',leaf)],[]);skill=release/'bundles/obsidian-markdown/skills/entry/SKILL.md'
    skill.chmod(0o644)
    with self.assertRaisesRegex(ValueError,'release changed'):native.prepare(state,[('obsidian-markdown',leaf)],[])
    skill.write_text(skill.read_text()+'Unreviewed injected instruction.\n');skill.chmod(0o444)
    seal=release/'NATIVE-MANIFEST.json';data=json.loads(seal.read_text());data['files']=native.tree(release);seal.chmod(0o600);seal.write_text(json.dumps(data));seal.chmod(0o444)
    with self.assertRaisesRegex(ValueError,'release changed'):native.prepare(state,[('obsidian-markdown',leaf)],[])
 def test_linked_instruction_parent_is_rejected_before_switching_skills(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';state=base/'state';home.mkdir();source,leaf,r=self.fixture(base)
   old=home/'.agents/skills/old';old.mkdir(parents=True);(old/'SKILL.md').write_text('preserve original\n');before=fingerprint(old.parent)
   shared=base/'shared';shared.mkdir();(shared/'AGENTS.md').write_text('shared instructions\n');(home/'.codex').symlink_to(shared)
   args=argparse.Namespace(home=str(home),state=str(state),only=['obsidian-markdown'],agent_reach=False,repository_docs=False,replace=True,vault=None)
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    with self.assertRaisesRegex(ValueError,'Linked profile target parent'):native.apply(args)
   self.assertEqual(fingerprint(old.parent),before);self.assertEqual((shared/'AGENTS.md').read_text(),'shared instructions\n');self.assertFalse((state/'rollback.sh').exists())
 def test_concurrent_instruction_edit_is_preserved_before_profile_mutation(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';state=base/'state';home.mkdir();source,leaf,r=self.fixture(base)
   agents=home/'.codex/AGENTS.md';agents.parent.mkdir();agents.write_text('before\n')
   args=argparse.Namespace(home=str(home),state=str(state),only=['obsidian-markdown'],agent_reach=False,repository_docs=False,replace=False,vault=None)
   original=native.guidance
   def race(text,state,vault):
    result=original(text,state,vault);agents.write_text('concurrent user edit\n');return result
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)),patch.object(native,'guidance',side_effect=race):
    with self.assertRaisesRegex(ValueError,'Concurrent change'):native.apply(args)
   self.assertEqual(agents.read_text(),'concurrent user edit\n');self.assertFalse((home/'.agents/skills').exists());self.assertFalse((state/'rollback.sh').exists())
 def test_missing_owned_root_can_be_repaired_without_changing_original_rollback(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';home.mkdir();state=base/'state';source,leaf,r=self.fixture(base)
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    result=native.apply(self.args(home,state));journal=pathlib.Path(result['run'])/'journal.json';before=journal.read_bytes();root=home/'.agents/skills';root.unlink()
    repaired=native.apply(self.args(home,state));self.assertTrue(repaired['repaired_removed_entry']);self.assertEqual(journal.read_bytes(),before);self.assertTrue(root.is_symlink())
   subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True);self.assertFalse(root.exists())
 def test_atomic_directory_exchange_interruption_restores_dirty_original(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';home.mkdir();state=base/'state';source,leaf,r=self.fixture(base)
   old=home/'.agents/skills/old';old.mkdir(parents=True);(old/'dirty').write_text('original dirty bytes');before=fingerprint(old.parent);original=transaction.replace_entry
   def crash(source,target):
    original(source,target);raise RuntimeError('after exchange')
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)),patch.object(transaction,'replace_entry',side_effect=crash):
    with self.assertRaisesRegex(RuntimeError,'after exchange'):native.apply(self.args(home,state))
   subprocess.run([str(state/'rollback.sh')],check=True,capture_output=True);self.assertEqual(fingerprint(old.parent),before)
 def test_unwritable_instruction_parent_fails_before_root_switch(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';home.mkdir();state=base/'state';(home/'.codex').mkdir();(home/'.codex/AGENTS.md').write_text('keep')
   old=home/'.agents/skills/old';old.mkdir(parents=True);(old/'dirty').write_text('keep');before=fingerprint(old.parent)
   (home/'.codex').chmod(0o555)
   try:
    with self.assertRaisesRegex(ValueError,'not writable/searchable'):native.apply(self.args(home,state))
    self.assertEqual(fingerprint(old.parent),before);self.assertFalse((state/'rollback.sh').exists())
   finally:(home/'.codex').chmod(0o755)
 def test_interrupted_previous_pointer_replacement_is_retryable(self):
  with tempfile.TemporaryDirectory() as temp:
   base=pathlib.Path(temp).resolve();home=base/'home';home.mkdir();state=base/'state';source,leaf,r=self.fixture(base)
   previous=state/'runs/previous/rollback.sh';previous.parent.mkdir(parents=True);previous.write_text('#!/bin/sh\nexit 0\n');previous.chmod(0o700);(state/'rollback.sh').symlink_to(previous)
   with patch.object(native.nstack,'build',return_value=source),patch.object(native.nstack,'registered_release',return_value=(r,{},leaf)):
    result=native.apply(self.args(home,state))
   (state/'.native-rollback-previous').symlink_to(previous)
   native.rollback(result['run'],True);self.assertEqual((state/'rollback.sh').resolve(),previous)
 def test_upgrade_of_generated_block_removes_project_initialization_requirement(self):
  old=native.profile_install.guidance('User safeguard.\n');new=native.guidance(old,pathlib.Path('/state'),'/vault')
  self.assertIn('No project-init step is required.',new);self.assertNotIn('an authorized setup owner runs',new);self.assertIn('private local Git at /vault',new);self.assertTrue(new.startswith('User safeguard.'))
if __name__=='__main__':unittest.main()
