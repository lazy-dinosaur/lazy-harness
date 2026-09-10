"""Real CLI no-op and policy-link protection; changed graph history policy is pending."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CapabilityPreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="capability-preservation-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = self.root / ".lazy-harness/ssot/capabilities.json"
        self.graph = self.root / ".lazy-harness/knowledge/graph.jsonl"
        record = self.root / ".lazy-harness/ssot/fixture.md"
        record.parent.mkdir(parents=True)
        record.write_text("# Fixture\n")
        self.command = ["bun", str(ROOT / ".lazy-harness/scripts/capability.ts"), "add",
                        "--target", str(self.root), "--id", "fixture", "--kind", "checklist",
                        "--level", "recommend", "--source-record", ".lazy-harness/ssot/fixture.md",
                        "--applies-when", "fixture", "--description", "Fixture", "--owner", "host-project",
                        "--format=json"]
        self.assertEqual(self.add()["status"], "created")

    def add(self, *args):
        result = subprocess.run([*self.command, *args], cwd=self.root,
                                env={**os.environ, "LAZY_HOST_ROOT": str(self.root)},
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def snapshot(self):
        return [(p.read_bytes(), p.stat().st_mtime_ns) for p in (self.registry, self.graph)]

    def test_unchanged_is_byte_and_mtime_inert_including_history(self):
        with self.graph.open("a") as out:
            out.write(json.dumps({"id": "capability_fixture", "status": "superseded", "supersededBy": "other"}) + "\n")
        before = self.snapshot()
        self.assertEqual(self.add()["status"], "unchanged")
        self.assertEqual(self.snapshot(), before)

    def test_policy_links_survive_identical_add(self):
        data = json.loads(self.registry.read_text())
        data["capabilities"][0]["policyIds"] = ["host-policy"]
        self.registry.write_text(json.dumps(data))
        before = self.snapshot()
        result = self.add()
        self.assertEqual(result["capability"].get("policyIds"), ["host-policy"])
        self.assertEqual(result["status"], "unchanged")
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_does_not_rewrite_registry_or_graph(self):
        before = self.snapshot()
        self.assertEqual(self.add("--dry-run")["status"], "dry-run")
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
