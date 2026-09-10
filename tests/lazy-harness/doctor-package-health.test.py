"""Isolated D07 regression: real harmless commands, no generate execution.

Run directly with Python; fixture and subprocess output stay under TMPDIR.
The semantic fixture uses the actual typecheck:bun command (D07's historical
typecheck:node alias), replacing only its source glob with one isolated file.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("doctor", ROOT / ".lazy-harness/scripts/doctor.py")
assert SPEC is not None and SPEC.loader is not None
doctor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = doctor
SPEC.loader.exec_module(doctor)


class PackageHealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="doctor-health-", dir=os.environ.get("TMPDIR", ROOT))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "package.json").write_text('{}')
        self.root_patch = patch.object(doctor, "ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def result(self, text="", code=1, pkg=None):
        if pkg is not None:
            (self.root / "package.json").write_text(json.dumps(pkg))
        completed = subprocess.CompletedProcess([], code, text, "")
        with patch.object(doctor, "run_typecheck_node", return_value=completed) as checker, patch.object(
            doctor, "run_generate_remediation", create=True,
            return_value=subprocess.CompletedProcess([], 0, "", "")
        ) as generate:
            result = doctor.check_package_health()
        return result, checker, generate

    def test_success(self):
        result, checker, generate = self.result(code=0)
        self.assertEqual(result.status, "ok")
        self.assertEqual(checker.call_count, 1)
        generate.assert_not_called()

    def test_environment_diagnostic(self):
        result, _, generate = self.result("error TS2688: Cannot find type definition file for 'node'.")
        self.assertEqual(result.status, "warn")
        generate.assert_not_called()

    def test_semantic_failure(self):
        result, _, _ = self.result("error TS2322: Type 'string' is not assignable to type 'number'.")
        self.assertEqual(result.status, "fail")

    def test_unknown_ts_failure(self):
        result, _, _ = self.result("error TS9999: Unrecognized diagnostic.")
        self.assertEqual(result.status, "fail")

    def test_mixed_failure_is_not_environment_only(self):
        result, _, _ = self.result("error TS2688: Cannot find type definition file for 'node'.\nerror TS2322: Type 'string' is not assignable to type 'number'.")
        self.assertEqual(result.status, "fail")

    def test_plain_nonzero_build(self):
        completed = subprocess.run(["bun", "build", "missing-entry.ts", "--target=bun"], cwd=self.root, text=True, capture_output=True, check=False)
        self.assertNotEqual(completed.returncode, 0)
        with patch.object(doctor, "run_typecheck_node", return_value=completed):
            result = doctor.check_package_health()
        self.assertEqual(result.status, "fail", result)
        self.assertTrue(result.details)

    def test_empty_nonzero_fails(self):
        result, _, _ = self.result(code=7)
        self.assertEqual(result.status, "fail")
        self.assertTrue(result.details)

    def test_existing_generate_retry_contract_is_preserved(self):
        # The script is inert fixture data; even baseline remediation is mocked.
        pkg = {"scripts": {"generate": "echo harmless-fixture"}}
        result, checker, generate = self.result("error TS2322: Type 'string' is not assignable to type 'number'.", pkg=pkg)
        self.assertEqual(result.status, "fail")
        generate.assert_called_once_with(["bun", "run", "generate"])
        self.assertEqual(checker.call_count, 2)

    def test_existing_prisma_retry_contract_is_preserved_without_execution(self):
        pkg = {"dependencies": {"@prisma/client": "latest"}}
        result, checker, generate = self.result('error TS2305: Module "@prisma/client" has no exported member Example', pkg=pkg)
        self.assertEqual(result.status, "fail")
        generate.assert_called_once_with(["bun", "x", "prisma", "generate"])
        self.assertEqual(checker.call_count, 2)

    def test_missing_bun_and_timeout_remain_environment_warnings(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired("typecheck:node", 120)):
            with self.subTest(error=type(error).__name__), patch.object(doctor, "run_typecheck_node", side_effect=error):
                self.assertEqual(doctor.check_package_health().status, "warn")

    def test_typecheck_command_rejects_semantic_error_bundling_accepts(self):
        compiler_package = ROOT / "node_modules/typescript/package.json"
        self.assertTrue(compiler_package.is_file(), "run bun install --frozen-lockfile --ignore-scripts first")
        compiler = (compiler_package.parent / json.loads(compiler_package.read_text())["bin"]["tsc"]).resolve()
        self.assertTrue(compiler.is_file() and compiler.is_relative_to(ROOT / "node_modules"))
        scripts = json.loads((ROOT / "package.json").read_text())["scripts"]
        self.assertEqual(scripts["typecheck:node"], "bun run typecheck:bun")
        argv = shlex.split(scripts["typecheck:bun"])
        self.assertEqual(argv[0], "bun")
        self.assertEqual((ROOT / argv[1]).resolve(), compiler, "fixture must use the project compiler")
        argv[1] = str(compiler)
        argv[argv.index(".lazy-harness/scripts/*.ts")] = "index.ts"
        argv += ["--typeRoots", str(ROOT / "node_modules/@types")]
        script = shlex.join(argv)
        runtimes: dict[str, str] = {}
        for name in ("bun", "sh"):
            executable = shutil.which(name)
            assert executable is not None, f"{name} runtime prerequisite missing"
            runtimes[name] = str(Path(executable).resolve())
        # Only test-owned wrappers enter PATH, never a runtime's containing directory.
        local_bin = self.root / "bin"
        local_bin.mkdir()
        for name, executable in runtimes.items():
            wrapper = local_bin / name
            wrapper.write_text(f'#!{runtimes["sh"]}\nexec {shlex.quote(executable)} "$@"\n')
            wrapper.chmod(0o755)
        external_bin = self.root / "external-global-bin"
        external_bin.mkdir()
        marker = self.root / "decoy-invoked"
        decoy = external_bin / "tsc"
        decoy.write_text(f'#!{runtimes["sh"]}\nprintf invoked > {shlex.quote(str(marker))}\nexit 97\n')
        decoy.chmod(0o755)
        decoy_probe = subprocess.run([str(decoy)], capture_output=True, text=True)
        self.assertEqual(decoy_probe.returncode, 97)
        self.assertTrue(marker.is_file(), "decoy must really be executable")
        marker.unlink()
        (self.root / "package.json").write_text(json.dumps({"scripts": {
            "typecheck:node": scripts["typecheck:node"], "typecheck:bun": script,
        }}))
        for mode, path in (("absent", str(local_bin)), ("decoy", os.pathsep.join([str(external_bin), str(local_bin)]))):
            with self.subTest(global_tsc=mode), patch.dict(os.environ, {"PATH": path}):
                self.assertEqual(shutil.which("tsc"), None if mode == "absent" else str(decoy))
                (self.root / "index.ts").write_text('export const count: number = "semantic-error";\n')
                bundle = subprocess.run(["bun", "build", "index.ts", "--target=bun", "--outdir", str(self.root / "bundle")], cwd=self.root, capture_output=True, text=True)
                self.assertEqual(bundle.returncode, 0, bundle.stderr)
                invalid = doctor.run_typecheck_node()
                print(json.dumps({"fixture": "semantic-invalid", "globalTsc": mode, "path": path, "runtimes": runtimes, "command": script, "bundleExit": bundle.returncode, "typecheckExit": invalid.returncode, "stdout": invalid.stdout, "stderr": invalid.stderr}), flush=True)
                self.assertNotEqual(invalid.returncode, 0, "bundling is not semantic typechecking")
                self.assertIn("TS2322", invalid.stdout + invalid.stderr)
                (self.root / "index.ts").write_text('export const count: number = 1;\n')
                valid = doctor.run_typecheck_node()
                print(json.dumps({"fixture": "semantic-valid", "globalTsc": mode, "command": script, "typecheckExit": valid.returncode, "stdout": valid.stdout, "stderr": valid.stderr}), flush=True)
                self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
                self.assertFalse(marker.exists(), "project-local compiler must ignore PATH tsc")


if __name__ == "__main__":
    started = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PackageHealthTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped), "seconds": round(time.monotonic() - started, 3)}), flush=True)
    sys.exit(not result.wasSuccessful())
