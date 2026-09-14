"""ADR 0026: installed generic guards must not load source-package parity fixtures."""
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".lazy-harness/scripts/self-test.py"
FIXTURE = ROOT / "packages/lazy-harness-pi/fixtures/reader-status-inspection.json"
CHECK = "check_read_debt_permit_generic_external_action"


def load(script, root, scope):
    with patch.dict(os.environ, {"LAZY_HOST_ROOT": str(root)}):
        namespace = runpy.run_path(str(script))
    check = namespace[CHECK]
    check.__globals__["ACTIVE_SCOPE"] = scope
    return check


class ReaderStatusFixtureScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="lazy-reader-status-scope-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = Path(cls.temp.name)
        cls.host = cls.base / "host"
        cls.host.mkdir()
        env = load(SCRIPT, ROOT, "framework").__globals__["env_without_lazy_runtime"]()
        subprocess.run(["git", "init", "-q"], cwd=cls.host, env=env, check=True)
        result = subprocess.run([
            "bun", str(ROOT / ".lazy-harness/scripts/lazy-init.ts"),
            "--from", str(ROOT), "--target", str(cls.host),
            "--skip-hooks", "--skip-agent-activation", "--quiet",
        ], cwd=ROOT, env=env, text=True, capture_output=True)
        if result.returncode:
            raise AssertionError("disposable host init failed:\n" + result.stdout + result.stderr)
        cls.worktree = cls.base / "worktree"
        subprocess.run(["git", "worktree", "add", "--orphan", "--quiet", str(cls.worktree)],
                       cwd=cls.host, env=env, check=True)
        (cls.worktree / ".lazy-harness").symlink_to(cls.host / ".lazy-harness", target_is_directory=True)

    def run_host(self, root, script):
        self.assertFalse((root / "packages").exists())
        check = load(script, root, "host")
        self.assertEqual(check.__globals__["ROOT"], root.resolve())
        real_read = Path.read_text

        def read(path, *args, **kwargs):
            if path.name == "reader-status-inspection.json":
                raise AssertionError("host attempted source-package fixture read: " + str(path))
            return real_read(path, *args, **kwargs)

        with patch.object(Path, "read_text", read), contextlib.redirect_stdout(io.StringIO()) as output:
            check()
        self.assertIn("read-debt generic external action guard ok", output.getvalue())

    def test_initialized_host_without_packages_executes_generic_guards(self):
        self.run_host(self.host, self.host / ".lazy-harness/scripts/self-test.py")

    def test_symlinked_worktree_honors_lazy_host_root(self):
        self.assertEqual((self.worktree / ".lazy-harness").resolve(), self.host / ".lazy-harness")
        self.run_host(self.worktree, self.worktree / ".lazy-harness/scripts/self-test.py")

    def test_source_script_with_explicit_host_root_does_not_fall_back_to_source_fixture(self):
        self.run_host(self.host, SCRIPT)

    def test_framework_executes_real_positive_and_negative_status_cases(self):
        fixture = json.loads(FIXTURE.read_text())
        self.assertTrue(any(case["allowed"] for case in fixture["cases"]))
        self.assertTrue(any(not case["allowed"] for case in fixture["cases"]))
        with contextlib.redirect_stdout(io.StringIO()):
            load(SCRIPT, ROOT, "framework")()

    def test_framework_missing_required_fixture_is_not_a_pass(self):
        # Explicit framework scope on an installed tree has no source fixture: fail, no fallback.
        with self.assertRaises(FileNotFoundError) as error:
            load(SCRIPT, self.host, "framework")()
        self.assertIn("reader-status-inspection.json", str(error.exception))

    def test_framework_rejects_inverted_positive_and_negative_status_expectations(self):
        real_read = Path.read_text
        for allowed in (True, False):
            fixture = json.loads(real_read(FIXTURE))
            case = next(case for case in fixture["cases"] if case["allowed"] is allowed)
            case["allowed"] = not allowed

            def read(path, *args, **kwargs):
                return json.dumps(fixture) if path == FIXTURE else real_read(path, *args, **kwargs)

            with self.subTest(allowed=allowed), patch.object(Path, "read_text", read), \
                    contextlib.redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit):
                load(SCRIPT, ROOT, "framework")()
            self.assertIn("Reader status fixture mismatch: " + case["id"], output.getvalue())

    def test_host_still_rejects_broken_generic_guard(self):
        check = load(SCRIPT, self.host, "host")
        real_run = subprocess.run

        def run(args, *positional, **kwargs):
            if len(args) > 1 and str(args[1]).endswith("check-read-debt-permit.py"):
                return subprocess.CompletedProcess(args, 0, "", "")
            return real_run(args, *positional, **kwargs)

        with patch.object(subprocess, "run", run), contextlib.redirect_stdout(io.StringIO()) as output, \
                self.assertRaises(SystemExit):
            check()
        self.assertIn("generic external action should be guarded", output.getvalue())

    def test_operative_registry_keeps_generic_both_and_regression_framework_only(self):
        tree = ast.parse(SCRIPT.read_text())
        pairs = {(node.elts[0].id, node.elts[1].value)
                 for node in ast.walk(tree) if isinstance(node, ast.Tuple) and len(node.elts) == 2
                 and isinstance(node.elts[0], ast.Name) and isinstance(node.elts[1], ast.Constant)}
        self.assertIn((CHECK, "BOTH"), pairs)
        self.assertIn(("check_reader_status_fixture_scope", "FRAMEWORK_ONLY"), pairs)


if __name__ == "__main__":
    unittest.main()
