"""Real local discovery boundaries and missing-capability behavior."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "addons/01/scripts/capabilities.py"
spec = importlib.util.spec_from_file_location("adaptive_capabilities", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiscoveryTests(unittest.TestCase):
    def test_later_addon_description_runtime_and_no_irrelevant_or_private_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            entry = state / "native-releases/fixture/bundles/added/SKILL.md"
            entry.parent.mkdir(parents=True)
            entry.write_text("---\nname: added\ndescription: Render unusual local figures\n"
                             "disable-model-invocation: true\n---\nFull task guidance.\n")
            outside = state / "private/SKILL.md"
            outside.parent.mkdir()
            outside.write_text("---\ndescription: figure credential sentinel\n---\nsynthetic\n")
            escape = state / "native-releases/escape/SKILL.md"
            escape.parent.mkdir()
            escape.symlink_to(outside)
            rows = [{"name": "added", "skill_path": str(entry), "deployment": "on demand"},
                    {"name": "unsafe", "skill_path": str(outside)},
                    {"name": "escape", "skill_path": str(escape)},
                    {"name": "wrong-file", "skill_path": str(state / "native-releases/auth.json")}]
            (state / "native-skill-index.json").write_text(json.dumps(rows))
            (state / "native-tools").mkdir()
            (state / "native-tools/index.json").write_text(json.dumps([
                {"name": "figure-renderer", "version": "fixture", "binary": "/fixture/bin",
                 "checks": "Prior figure output checked", "apiKey": "never-emit-this"}]))
            result = module.search(state, ["figures", "figure"], 8)
            self.assertEqual({x["name"] for x in result["matches"]}, {"added", "figure-renderer"})
            self.assertTrue(next(x for x in result["matches"] if x["kind"] == "skill")["manual_only"])
            self.assertNotIn("never-emit-this", json.dumps(result))
            self.assertEqual(len(result["sources"]), 2)
            self.assertEqual(module.search(state, ["unrelated-objective"])["matches"], [])
            run = subprocess.run([sys.executable, str(SCRIPT), "--state", str(state),
                                  "--limit", "1", "figure"], capture_output=True, text=True, check=True)
            self.assertEqual(len(json.loads(run.stdout)["matches"]), 1)
            self.assertEqual(json.loads(run.stdout)["total_matches"], 2)

    def test_uninstalled_or_malformed_inventory_is_not_false_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.assertEqual(module.search(state, ["render"])["matches"], [])
            (state / "native-skill-index.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "array"):
                module.search(state, ["render"])
