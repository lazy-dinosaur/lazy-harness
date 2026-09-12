"""Guard-level regression; real initialized-host validation covers runtime behavior separately."""
import ast
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".lazy-harness/scripts/self-test.py"
spec = importlib.util.spec_from_file_location("scope_self_test", SCRIPT)
assert spec is not None and spec.loader is not None, "self-test module loader unavailable"
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
with patch.dict(os.environ, {"LAZY_HOST_ROOT": str(ROOT)}):
    spec.loader.exec_module(module)

STRATEGY = ROOT / ".lazy-harness/tests/test-strategy.xml"
README = ROOT / ".lazy-harness/generated/README.md"
CHECKS = {
    "check_bounded_validation_governor_cli": (STRATEGY, ("never after every micro-edit",)),
    "check_policy_machinery_v2": (README, (
        "policy-rulebook.md", "Canonical behavior policy semantics live in",
        "lazy policy render-rulebook --write", "Do not edit `policy-rulebook.md` as a source of truth",
    )),
}


class ReachedRuntime(BaseException):
    """Stop at the first external command; no claim of runtime functional coverage."""


class DocumentScopeTests(unittest.TestCase):
    def exercise(self, name, scope, replacements=None, absent=(), forbid_host_reads=False):
        replacements = replacements or {}
        real_read, real_exists = Path.read_text, Path.exists

        def read(path, *args, **kwargs):
            if forbid_host_reads and path in (STRATEGY, README):
                raise AssertionError("host-owned document was read: " + str(path))
            if path in absent:
                raise FileNotFoundError(str(path))
            if path in replacements:
                return replacements[path]
            return real_read(path, *args, **kwargs)

        def exists(path):
            return False if path in absent else real_exists(path)

        with patch.object(module, "ACTIVE_SCOPE", scope), \
                patch.object(Path, "read_text", read), patch.object(Path, "exists", exists), \
                patch.object(module.py_compile, "compile"), \
                patch.object(module.subprocess, "run", side_effect=ReachedRuntime), \
                patch.object(module.subprocess, "check_output", side_effect=ReachedRuntime):
            getattr(module, name)()

    def test_framework_valid_documents_reach_runtime(self):
        for name in CHECKS:
            with self.subTest(name=name), self.assertRaises(ReachedRuntime):
                self.exercise(name, "framework")

    def test_framework_rejects_every_missing_phrase(self):
        for name, (path, phrases) in CHECKS.items():
            for phrase in phrases:
                with self.subTest(name=name, phrase=phrase):
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
                        self.exercise(name, "framework", {path: path.read_text().replace(phrase, "REMOVED")})
                    self.assertIn(phrase, output.getvalue())

    def test_framework_missing_files_still_fail(self):
        for name, (path, _) in CHECKS.items():
            with self.subTest(name=name), contextlib.redirect_stdout(io.StringIO()), \
                    self.assertRaises((SystemExit, FileNotFoundError)):
                self.exercise(name, "framework", absent=(path,))

    def test_host_documents_are_not_framework_prose_inputs(self):
        for name, (path, _) in CHECKS.items():
            for text in ("", "<testStrategy>Use project-local tests.</testStrategy>", "# Local generated artifacts\n"):
                with self.subTest(name=name, text=text), self.assertRaises(ReachedRuntime):
                    self.exercise(name, "host", {path: text}, forbid_host_reads=True)
            with self.subTest(name=name, missing=True), self.assertRaises(ReachedRuntime):
                self.exercise(name, "host", absent=(path,), forbid_host_reads=True)

    def test_framework_managed_guards_remain_in_both_scopes(self):
        cases = (
            ("check_bounded_validation_governor_cli", ROOT / ".lazy-harness/AGENTS.md", "coherent mutation batch"),
            ("check_policy_machinery_v2", ROOT / ".lazy-harness/scripts/policy.ts", "requested.startsWith('.lazy-harness/generated/')"),
        )
        for name, path, phrase in cases:
            for scope in ("framework", "host"):
                with self.subTest(name=name, scope=scope), contextlib.redirect_stdout(io.StringIO()), \
                        self.assertRaises(SystemExit):
                    self.exercise(name, scope, {path: path.read_text().replace(phrase, "REMOVED")})

    def test_runtime_checks_keep_both_registration(self):
        tree = ast.parse(SCRIPT.read_text())
        pairs = {(node.elts[0].id, node.elts[1].value)
                 for node in ast.walk(tree) if isinstance(node, ast.Tuple) and len(node.elts) == 2
                 and isinstance(node.elts[0], ast.Name) and isinstance(node.elts[1], ast.Constant)}
        for name in CHECKS:
            self.assertIn((name, "BOTH"), pairs)


if __name__ == "__main__":
    unittest.main()
