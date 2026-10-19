"""Regression for changed-file collection; never changes the real Git ignore config."""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / ".lazy-harness/scripts/lazy-check.py"


class ChangedCollectionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lazy-check-collection-")
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True)

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())

    def check(self, *args):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--format=json", "--no-diff-check", *args],
            cwd=self.root, env={**os.environ, "LAZY_HOST_ROOT": str(self.root)},
            text=True, capture_output=True, check=False,
        )
        return result.returncode, json.loads(result.stdout)

    def test_untracked_dependencies_excluded_but_authored_names_preserved(self):
        self.put("node_modules/pkg/tsconfig.json", "{// JSONC\n}")
        self.put("packages/app/node_modules/pkg/image.png", b"\x00\xff")
        self.put("node_modules-notes/source.json", "{}")
        self.put(" spaced name.json", "{}")
        self.put("line\nbreak.json", "{}")
        code, result = self.check()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["files"], [" spaced name.json", "line\nbreak.json", "node_modules-notes/source.json"])
        self.assertTrue(any("node_modules" in note for note in result["notes"]))

    def test_staged_dependency_is_not_silently_excluded(self):
        name = "packages/app/node_modules/owned.json"
        self.put(name, "invalid")
        subprocess.run(["git", "add", "--", name], cwd=self.root, check=True)
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertIn(name, result["files"])
        self.assertTrue(any(error["check"] == "json-parse" for error in result["errors"]))

    def test_explicit_dependency_still_checked(self):
        name = "node_modules/owned.json"
        self.put(name, "invalid")
        code, result = self.check("--files", name)
        self.assertEqual(code, 1)
        self.assertEqual(result["mode"], "explicit")
        self.assertEqual(result["files"], [name])

    def test_authored_invalid_json_and_binary_nul_still_fail(self):
        self.put("source.json", "invalid")
        self.put("source.ts", b"\x00")
        code, result = self.check()
        self.assertEqual(code, 1)
        self.assertEqual({error["check"] for error in result["errors"]}, {"json-parse", "binary-nul"})


if __name__ == "__main__":
    unittest.main()
