"""Real record-index writer/map CLI regression for SPO and historical projections."""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
RECORD = ".lazy-harness/domain/fixture.md"


class RecordGraphProjectionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="record-graph-projection-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.rows = [
            {"id": "canonical", "subject": RECORD, "predicate": "implemented_by", "object": "src/current.ts", "status": "confirmed"},
            {"id": "reverse", "subject": "tests/current.test.ts", "predicate": "protected_by", "object": RECORD, "status": "confirmed"},
            {"id": "legacy", "source": RECORD, "relation": "implemented_by", "target": "src/legacy.ts"},
            {"id": "historical", "source": RECORD, "relation": "implemented_by", "target": "src/obsolete.ts", "status": "superseded", "supersededBy": "canonical"},
            {"id": "rejected", "subject": RECORD, "predicate": "implemented_by", "object": "src/rejected.ts", "status": "rejected"},
            {"id": "replacement", "subject": RECORD, "predicate": "implemented_by", "object": "src/replacement.ts", "status": "confirmed", "supersedes": ["historical"]},
            {"id": "unknown", "source": RECORD, "type": "implementation", "target": "src/unknown.ts", "status": "custom-state"},
            {"id": "structured", "subject": RECORD, "predicate": "defines_contract", "object": {"fields": ["a", "b"], "enabled": False}, "status": "needs-review"},
        ]
        self.write(RECORD, "# Fixture\n\n## Rule digest\n\n- Status: active\n- Layer: DDD\n- Scope: host-project\n- Applies when:\n  - exercising graph projection\n- Must:\n  - retain graph facts\n")
        self.graph = self.root / ".lazy-harness/knowledge/graph.jsonl"
        self.write(str(self.graph.relative_to(self.root)), "".join(json.dumps(row) + "\n" for row in self.rows))
        for file in ["src/current.ts", "tests/current.test.ts", "src/legacy.ts", "src/obsolete.ts", "src/rejected.ts", "src/replacement.ts", "src/unknown.ts"]:
            self.write(file, "export {}\n")
        self.original_graph = self.graph.read_bytes()
        self.index = self.cli("record-index", "--write", "--format=json")
        self.record = self.index["records"][0]

    def write(self, relative, text):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def cli(self, command, *args, json_output=True, expected_code=0) -> Any:
        env = {**os.environ, "LAZY_HOST_ROOT": str(self.root), "LAZY_RUNTIME_ROOT": str(self.root / "runtime"), "LAZY_SHARED_ROOT": str(self.root / "shared")}
        result = subprocess.run([str(ROOT / ".lazy-harness/bin/lazy"), command, *args], cwd=self.root, env=env, text=True, capture_output=True, timeout=30)
        artifact_root = os.environ.get("GRAPH_PROJECTION_ARTIFACTS")
        if artifact_root:
            dest = pathlib.Path(artifact_root) / self._testMethodName
            dest.mkdir(parents=True, exist_ok=True)
            name = f"{len(list(dest.iterdir())):02d}-{command}"
            (dest / (name + ".json")).write_text(json.dumps({"argv": [command, *args], "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, indent=2))
        self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)
        return json.loads(result.stdout) if json_output else result.stdout + result.stderr

    def map(self, query):
        return self.cli("map", query, "--format=json", "--limit=30")

    def test_canonical_writer_projection_and_both_endpoints(self):
        self.assertIn("canonical", self.record["graphIds"])
        self.assertIn("reverse", self.record["graphIds"])
        self.assertIn("src/current.ts", self.record["implementationHints"]["fileHints"])
        self.assertIn("tests/current.test.ts", self.record["implementationHints"]["testHints"])
        hints = {row["id"]: row for row in self.record["graphHints"]}
        self.assertEqual(hints["canonical"]["predicate"], "implemented_by")
        self.assertEqual(hints["structured"]["object"], self.rows[-1]["object"])

    def test_canonical_cli_drilldown_and_overview(self):
        mapped = self.map("canonical")
        row = next(row for row in mapped["graphRows"] if row["id"] == "canonical")
        self.assertEqual(row.get("subject"), RECORD)
        self.assertEqual(row.get("predicate"), "implemented_by")
        self.assertEqual(row.get("object"), "src/current.ts")
        self.assertIn(RECORD, mapped["drilldown"]["recordPaths"])
        self.assertIn("src/current.ts", mapped["drilldown"]["sourceFiles"])
        overview = self.cli("map", "--overview", "--format=json", "--limit=30")
        sample = next(row for row in overview["graph"]["sampleRows"] if row["id"] == "canonical")
        self.assertEqual(sample.get("status"), "confirmed")
        self.assertEqual(sample.get("predicate"), "implemented_by")

    def test_historical_state_remains_explicit_and_discoverable(self):
        hints = {row["id"]: row for row in self.record["graphHints"]}
        self.assertEqual(hints["historical"].get("status"), "superseded")
        mapped = self.map("historical")
        historical = next(row for row in mapped["graphRows"] if row["id"] == "historical")
        self.assertEqual(historical.get("status"), "superseded")
        self.assertEqual(historical.get("supersededBy"), "canonical")
        self.assertIn("src/obsolete.ts", mapped["drilldown"]["sourceFiles"])
        replacement = next(row for row in self.map("replacement")["graphRows"] if row["id"] == "replacement")
        self.assertEqual(replacement.get("supersedes"), ["historical"])
        text = self.cli("map", "historical", "--format=md", json_output=False)
        self.assertIn("status: `superseded`", text)
        self.assertIn("supersededBy: `canonical`", text)

    def test_retired_rows_do_not_contaminate_current_hints(self):
        hints = self.record["implementationHints"]["fileHints"]
        self.assertNotIn("src/obsolete.ts", hints)
        self.assertNotIn("src/rejected.ts", hints)
        self.assertIn("historical", self.record["graphIds"])
        self.assertIn("rejected", self.record["graphIds"])

    def test_legacy_and_unknown_status_behavior_is_preserved(self):
        self.assertIn("src/legacy.ts", self.record["implementationHints"]["fileHints"])
        self.assertIn("src/unknown.ts", self.record["implementationHints"]["fileHints"])
        row = next(row for row in self.map("legacy")["graphRows"] if row["id"] == "legacy")
        self.assertEqual(row["source"], RECORD)
        self.assertEqual(row["relation"], "implemented_by")
        self.assertEqual(row["target"], "src/legacy.ts")
        self.assertNotIn("status", row)

    def test_same_id_history_is_not_folded_or_deleted(self):
        active = {"id": "historical", "source": RECORD, "relation": "implemented_by", "target": "src/current.ts", "status": "confirmed"}
        self.graph.write_text(self.graph.read_text() + json.dumps(active) + "\n")
        rows = [row for row in self.map("historical")["graphRows"] if row["id"] == "historical"]
        self.assertEqual(len(rows), 2)
        self.assertEqual({row.get("status") for row in rows}, {"confirmed", "superseded"})

    def test_old_projection_cache_is_rebuilt(self):
        cache = self.root / ".lazy-harness/generated/record-index.json"
        old = json.loads(cache.read_text())
        old["source"].pop("graphProjection", None)
        old["records"][0]["graphIds"] = []
        cache.write_text(json.dumps(old))
        mapped = self.map(RECORD)
        self.assertFalse(mapped["source"]["recordIndexCache"]["used"])
        self.assertIn("canonical", mapped["records"][0]["graphIds"])

    def test_non_mutating_read_and_free_text_denial(self):
        cache = (self.root / ".lazy-harness/generated/record-index.json").read_bytes()
        self.map(RECORD)
        denied = self.cli("map", "please find graph", "--format=json", json_output=False, expected_code=1)
        self.assertIn("not free-form search text", denied)
        self.assertEqual(self.graph.read_bytes(), self.original_graph)
        self.assertEqual((self.root / ".lazy-harness/generated/record-index.json").read_bytes(), cache)


if __name__ == "__main__":
    unittest.main(verbosity=2)
