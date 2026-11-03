#!/usr/bin/env python3
"""Real isolated Git/init regressions; never commit or push the live checkout."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ("pre-commit-guard.sh", "pre-push.sh", "post-commit.sh")


class GitHookRetirement(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lazy-git-hooks-retired-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(("GIT_", "LAZY_"))}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null",
                        GIT_AUTHOR_NAME="Hook fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                        GIT_COMMITTER_NAME="Hook fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        self.host = self.base / "host"
        self.host.mkdir()
        self.run_cmd(self.host, "git", "init", "-q")
        self.source = self.base / "source"
        lazy = self.source / ".lazy-harness"
        (lazy / "manifests").mkdir(parents=True)
        self.manifest = {"version": "1.0", "categories": {
            key: {"items": []} for key in ("A", "B", "C")}, "postInit": {"actions": []}}
        self.write_manifest()

    def run_cmd(self, cwd, *command):
        result = subprocess.run(command, cwd=cwd, env=self.env, text=True,
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def write_manifest(self):
        (self.source / ".lazy-harness/manifests/init-categories.json").write_text(
            json.dumps(self.manifest), encoding="utf-8")

    def init(self, host=None, *flags):
        return self.run_cmd(self.base, "bun", str(ROOT / ".lazy-harness/scripts/lazy-init.ts"),
                            "--target", str(host or self.host), "--from", str(self.source),
                            "--skip-agent-activation", "--quiet", *flags)

    @staticmethod
    def snapshot(directory):
        return {str(path.relative_to(directory)): (path.read_bytes(), path.stat().st_mode)
                for path in directory.rglob("*") if path.is_file()}

    def test_fresh_and_repeated_init_do_not_install_hooks(self):
        hooks = self.host / ".git/hooks"
        before = self.snapshot(hooks)
        self.init()
        self.init(None, "--force")
        self.init(None, "--force", "--skip-hooks")
        self.assertEqual(self.snapshot(hooks), before)
        manifest = json.loads((ROOT / ".lazy-harness/manifests/init-categories.json").read_text())
        self.assertNotIn("pre-commit-hook", [a["kind"] for a in manifest["postInit"]["actions"]])

    def test_user_hooks_custom_path_and_old_manifest_are_preserved(self):
        hooks = self.host / ".git/hooks"
        custom = self.host / ".custom-hooks"
        custom.mkdir()
        for directory in (hooks, custom):
            for name in ("pre-commit", "post-commit", "pre-push"):
                path = directory / name
                path.write_text("#!/bin/sh\n# user-owned fixture\nexit 17\n")
                path.chmod(0o755)
        self.run_cmd(self.host, "git", "config", "core.hooksPath", ".custom-hooks")
        self.manifest["postInit"]["actions"] = [{"kind": "pre-commit-hook", "description": "old manifest"}]
        self.write_manifest()
        before = (self.snapshot(hooks), self.snapshot(custom))
        self.init()
        self.init(None, "--force")
        self.assertEqual((self.snapshot(hooks), self.snapshot(custom)), before)
        self.assertEqual(self.run_cmd(self.host, "git", "config", "--get", "core.hooksPath").stdout.strip(),
                         ".custom-hooks")

    def test_linked_worktree_init_does_not_write_hooks(self):
        self.run_cmd(self.host, "git", "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", "fixture")
        worktree = self.base / "worktree"
        self.run_cmd(self.host, "git", "worktree", "add", "-qb", "fixture-worktree", str(worktree))
        gitdir = Path(self.run_cmd(worktree, "git", "rev-parse", "--absolute-git-dir").stdout.strip())
        before = self.snapshot(self.host / ".git/hooks")
        self.init(worktree)
        self.init(worktree, "--force")
        self.assertEqual(self.snapshot(self.host / ".git/hooks"), before)
        self.assertFalse((gitdir / "hooks").exists())

    def test_old_delegates_allow_real_commit_push_without_validation(self):
        lazy = self.host / ".lazy-harness"
        (lazy / "hooks").mkdir(parents=True)
        (lazy / "bin").mkdir()
        marker = self.host / "unexpected-validation"
        runner = lazy / "bin/lazy"
        runner.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 42\n')
        runner.chmod(0o755)
        for name in HOOKS:
            shutil.copy2(ROOT / ".lazy-harness/hooks" / name, lazy / "hooks" / name)
        for name, delegate in (("pre-commit", HOOKS[0]), ("pre-push", HOOKS[1]), ("post-commit", HOOKS[2])):
            hook = self.host / ".git/hooks" / name
            hook.write_text(f'#!/bin/sh\n.lazy-harness/hooks/{delegate} "$@"\n')
            hook.chmod(0o755)
        lock = self.host / ".git/lazy-harness/locks/git-action.lockdir"
        lock.mkdir(parents=True)
        (lock / "owner.json").write_text('{"pid":1,"action":"fixture"}\n')
        self.run_cmd(self.host, "git", "add", ".lazy-harness")
        self.run_cmd(self.host, "git", "-c", "commit.gpgsign=false", "commit", "-qm", "Fix: fixture")
        remote = self.base / "remote.git"
        self.run_cmd(self.base, "git", "init", "--bare", "-q", str(remote))
        self.run_cmd(self.host, "git", "remote", "add", "origin", str(remote))
        self.run_cmd(self.host, "git", "push", "-q", "origin", "HEAD:refs/heads/fixture")
        self.assertFalse(marker.exists())
        self.assertFalse((lazy / "logs").exists())
        self.assertFalse((lazy / "regression").exists())
        self.assertTrue((lock / "owner.json").exists())
        self.assertEqual(self.run_cmd(self.host, "git", "rev-parse", "HEAD").stdout,
                         self.run_cmd(self.base, "git", "--git-dir", str(remote), "rev-parse", "refs/heads/fixture").stdout)


if __name__ == "__main__":
    unittest.main()
