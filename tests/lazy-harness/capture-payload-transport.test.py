"""Real hook transport regressions: output, safety execution, UTF-8, cleanup."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class CapturePayloadTransport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="capture-transport-test-")
        self.root = Path(self.temp.name)
        self.hooks = self.root / ".lazy-harness/hooks/lifecycle"
        self.helpers = self.hooks / "helpers"
        self.helpers.mkdir(parents=True)
        (self.root / ".lazy-harness/scripts").mkdir()
        (self.root / "scratch").mkdir()
        for name in ("on-message-received.sh", "on-response-completed.sh", "helpers/check-analysis-discovery-capture.sh", "helpers/payload_transport.py"):
            shutil.copy2(ROOT / ".lazy-harness/hooks/lifecycle" / name, self.hooks / name)
        shutil.copy2(ROOT / ".lazy-harness/scripts/lifecycle-check.py", self.root / ".lazy-harness/scripts/lifecycle-check.py")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("LAZY_", "GIT_"))}
        self.env.update(LAZY_HOST_ROOT=str(self.root), LAZY_HOOK_TIMING="0", TMPDIR=str(self.root / "scratch"))

    def tearDown(self):
        self.temp.cleanup()

    def payload(self, size=180000):
        return {"source": "lazy-harness", "working_dir": str(self.root),
                "recent_tool_calls": [{"name": "write", "result_preview": "한" * size}],
                "tail": "끝-preserved",
                "capture_validation": {"schemaVersion": "1.0", "root": str(self.root), "epoch": 1,
                    "status": "pending", "reason": "transport fixture, not live receipt proof",
                    "semanticStatus": "llm-judgement-not-verified", "approvalStatus": "not-evaluated", "facts": []}}

    def run_hook(self, payload, mode="legacy"):
        result = subprocess.run(["bash", str(self.hooks / "on-response-completed.sh")],
            input=json.dumps(payload, ensure_ascii=False), text=True, capture_output=True,
            cwd=self.root, env={**self.env, "LAZY_RESPONSE_COMPLETED_ENGINE": mode}, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Argument list too long", result.stderr)
        self.assertEqual(list((self.root / "scratch").iterdir()), [], "owned payload files must be cleaned")
        return json.loads(result.stdout)

    def test_capture_survives_large_input_in_all_engines(self):
        for mode in ("legacy", "orchestrator", "compare"):
            with self.subTest(mode=mode):
                payload = self.payload()
                self.assertEqual(self.run_hook(payload, mode)["capture"], payload["capture_validation"])

    def test_large_input_executes_safety_helper_without_truncating_tail(self):
        helper = self.helpers / "check-layer-impact.sh"
        helper.write_text('''#!/usr/bin/env python3
import json, sys
from payload_transport import read_payload_text
p = json.loads(read_payload_text(sys.argv[1]))
assert len(p["recent_tool_calls"][0]["result_preview"]) == 180000
assert p["tail"] == "끝-preserved"
print("STOP safety-helper-ran")
''', encoding="utf-8")
        helper.chmod(0o700)
        for mode in ("legacy", "orchestrator", "compare"):
            with self.subTest(mode=mode):
                payload = self.payload()
                output = self.run_hook(payload, mode)
                self.assertEqual(output["inject"]["body"].strip(), "STOP safety-helper-ran")
                self.assertEqual(output["capture"], payload["capture_validation"])

    def test_large_capture_and_safety_output_do_not_use_environment_transport(self):
        helper = self.helpers / "check-layer-impact.sh"
        helper.write_text('#!/usr/bin/env python3\nprint("STOP " + "x" * 180000)\n', encoding="utf-8")
        helper.chmod(0o700)
        for mode in ("legacy", "orchestrator", "compare"):
            with self.subTest(mode=mode):
                payload = self.payload(10)
                payload["capture_validation"]["reason"] = "x" * 180000
                output = self.run_hook(payload, mode)
                self.assertEqual(output["inject"]["body"].strip(), "STOP " + "x" * 180000)
                self.assertEqual(output["capture"], payload["capture_validation"])

    def test_small_inline_transport_remains_compatible(self):
        helper = self.helpers / "check-layer-impact.sh"
        helper.write_text('#!/usr/bin/env python3\nimport json,sys\np=json.loads(sys.argv[1]); assert p["tail"] == "끝-preserved"\nprint("STOP inline-compatible")\n', encoding="utf-8")
        helper.chmod(0o700)
        self.assertEqual(self.run_hook(self.payload(10))["inject"]["body"].strip(), "STOP inline-compatible")

    def test_missing_capture_decoder_fails_instead_of_passing_empty_output(self):
        (self.helpers / "payload_transport.py").unlink()
        result = subprocess.run(["bash", str(self.hooks / "on-response-completed.sh")],
            input=json.dumps(self.payload()), text=True, capture_output=True,
            cwd=self.root, env=self.env, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list((self.root / "scratch").iterdir()), [])


    def test_message_temp_templates_generate_distinct_names(self):
        script = (self.hooks / "on-message-received.sh").read_text(encoding="utf-8")
        templates = re.findall(r'mktemp\s+"([^"]+)"', script)
        self.assertEqual(len(templates), 2, "cover primary and /tmp fallback templates")
        for template in templates:
            with self.subTest(template=template):
                expanded = template.replace("${TMPDIR:-/tmp}", self.env["TMPDIR"])
                names = []
                for _ in range(3):
                    result = subprocess.run(["mktemp", "-u", expanded],
                        text=True, capture_output=True, env=self.env, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    name = result.stdout.strip()
                    self.assertNotIn("XXXXXX", Path(name).name)
                    self.assertFalse(Path(name).exists(), "-u must not leave a test file")
                    names.append(name)
                self.assertEqual(len(set(names)), 3)

    def test_message_hooks_repeat_and_overlap_without_touching_old_tempfile(self):
        scratch = self.root / "scratch"
        sentinel = scratch / "lazy-harness-message.XXXXXX.json"
        sentinel.write_text("preserve-old-file", encoding="utf-8")

        def execute(index):
            payload = {"working_dir": str(self.root), "last_user_message": "tmp transport fixture",
                       "session_id": "tmp-fixture", "message_id": f"message-{index}"}
            return subprocess.run(["bash", str(self.hooks / "on-message-received.sh")],
                input=json.dumps(payload), text=True, capture_output=True, cwd=self.root,
                env={**self.env, "PYTHON_BIN": sys.executable}, timeout=15)

        results = [execute(index) for index in range(3)]
        with ThreadPoolExecutor(max_workers=6) as pool:
            results.extend(pool.map(execute, range(3, 15)))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["action"], "allow")
            self.assertTrue(output["inject"]["body"])
            self.assertNotIn("File exists", result.stderr)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve-old-file")
        self.assertEqual(list(scratch.iterdir()), [sentinel])

    def test_response_hooks_repeat_and_overlap_in_private_directories(self):
        scratch = self.root / "scratch"
        sentinel = scratch / "lazy-lifecycle-check.XXXXXX.json"
        sentinel.write_text("preserve-old-file", encoding="utf-8")
        payload = self.payload(10)

        def execute(mode):
            return subprocess.run(["bash", str(self.hooks / "on-response-completed.sh")],
                input=json.dumps(payload), text=True, capture_output=True, cwd=self.root,
                env={**self.env, "LAZY_RESPONSE_COMPLETED_ENGINE": mode}, timeout=30)

        modes = ["orchestrator", "compare"]
        results = [execute(mode) for mode in modes for _ in range(2)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            results.extend(pool.map(execute, modes * 4))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["capture"], payload["capture_validation"])
            self.assertNotIn("File exists", result.stderr)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve-old-file")
        self.assertEqual(list(scratch.iterdir()), [sentinel])

if __name__ == "__main__":
    unittest.main()
