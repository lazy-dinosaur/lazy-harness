#!/usr/bin/env python3
"""Enforce promoted host-owned command boundaries from typed policy records.

The shared hook receives the same normalized ``tool.name``/``tool.args`` shape
from Pi and OMP. This helper deliberately reads only explicit shell
tool input plus a promoted ``level=block`` policy.  It never classifies user or
assistant prose and stays silent for hosts without a matching command boundary.

Currently supported guard:

``git-worktree-promotion/v1``
    - deny raw ``git worktree add``;
    - deny creating/resetting a branch from a configured protected remote ref
      with ``git checkout -b/-B`` or ``git switch -c/-C``;
    - for a single-commit cherry-pick on a destination-labelled promotion
      branch, run the required read-only ``git merge-tree`` preflight before the
      mutating command is allowed.

The command semantics live in the host policy's ``runtime.commandBoundary``
configuration.  The implementation is runtime-neutral and project-name-free.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any


SHELL_TOOLS = {"bash", "sh", "shell", "command", "cmd", "terminal"}
CONTROL_CHERRY_PICK_FLAGS = {"--abort", "--continue", "--quit", "--skip"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
CHERRY_PICK_OPTIONS_WITH_VALUE = {"-m", "--mainline", "--strategy", "-X", "--strategy-option"}
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", re.DOTALL)
REDIRECTION_RE = re.compile(r"^\d*(?:<>|>>?|<<?|>&|<&|&>>?)(.*)$")


def parse_payload() -> dict[str, Any]:
    raw = sys.argv[1] if len(sys.argv) > 1 else ""
    if not raw.strip():
        try:
            raw = sys.stdin.read()
        except Exception:
            raw = ""
    try:
        value = json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def host_root(payload: dict[str, Any]) -> Path | None:
    candidates = [
        payload.get("working_dir"),
        payload.get("cwd"),
        os.environ.get("LAZY_HOST_ROOT"),
        os.getcwd(),
    ]
    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        root = Path(candidate).expanduser().resolve()
        if (root / ".lazy-harness" / "ssot" / "policies.json").is_file():
            return root
    return None


def shell_command(payload: dict[str, Any]) -> str:
    tool = payload.get("tool")
    if not isinstance(tool, dict) or str(tool.get("name") or "").lower() not in SHELL_TOOLS:
        return ""
    args = tool.get("args")
    if isinstance(args, dict):
        for key in ("command", "cmd", "text"):
            value = args.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return ""


def load_boundaries(root: Path) -> list[tuple[str, str, dict[str, Any]]]:
    try:
        registry = json.loads((root / ".lazy-harness" / "ssot" / "policies.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    policies = registry.get("policies") if isinstance(registry, dict) else None
    if not isinstance(policies, list):
        return []
    boundaries: list[tuple[str, str, dict[str, Any]]] = []
    for policy in policies:
        if not isinstance(policy, dict) or policy.get("level") != "block":
            continue
        policy_id = str(policy.get("id") or "")
        if not policy_id:
            continue
        runtime = policy.get("runtime")
        if not isinstance(runtime, dict) or runtime.get("blocks") is not True or runtime.get("mode") != "command-boundary":
            continue
        boundary = runtime.get("commandBoundary")
        if not isinstance(boundary, dict) or boundary.get("guard") != "git-worktree-promotion/v1":
            continue
        source = str(policy.get("sourceRecord") or ".lazy-harness/ssot/policies.json")
        boundaries.append((policy_id, source, boundary))
    return boundaries


def shell_segments(command: str) -> list[list[str]]:
    """Split top-level shell statements without treating redirection as control flow.

    ``shlex`` treats newlines as ordinary whitespace and punctuation tokenization
    can turn ``2>&1`` into a fake command/revision. Scan only top-level control
    separators here, preserve quoted text, then let ``shlex.split`` parse each
    statement independently.
    """
    raw_segments: list[str] = []
    current: list[str] = []
    quote = ""
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\" and quote != "'":
            current.append(char)
            escaped = True
            index += 1
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            index += 1
            continue
        previous = next((value for value in reversed(current) if not value.isspace()), "")
        is_control = char in {";", "\n", "|"} or (char == "&" and previous not in {">", "<"})
        if is_control:
            value = "".join(current).strip()
            if value:
                raw_segments.append(value)
            current = []
            while index + 1 < len(command) and command[index + 1] == char and char in {"&", "|", ";"}:
                index += 1
            index += 1
            continue
        current.append(char)
        index += 1
    value = "".join(current).strip()
    if value:
        raw_segments.append(value)

    segments: list[list[str]] = []
    for value in raw_segments:
        try:
            tokens = shlex.split(value, posix=True, comments=False)
        except Exception:
            continue
        if tokens:
            segments.append(tokens)
    return segments


def unwrap_command(tokens: list[str]) -> list[str]:
    index = 0
    while index < len(tokens) and ASSIGNMENT_RE.match(tokens[index]):
        index += 1
    if index < len(tokens) and tokens[index] == "env":
        index += 1
        while index < len(tokens) and (tokens[index].startswith("-") or ASSIGNMENT_RE.match(tokens[index])):
            index += 1
    while index < len(tokens) and Path(tokens[index]).name in {"command", "sudo"}:
        index += 1
        while index < len(tokens) and tokens[index].startswith("-"):
            index += 1
    return tokens[index:]


def resolve_cd(cwd: Path, tokens: list[str]) -> Path:
    unwrapped = unwrap_command(tokens)
    if not unwrapped or Path(unwrapped[0]).name != "cd" or len(unwrapped) < 2:
        return cwd
    target = Path(unwrapped[1]).expanduser()
    if not target.is_absolute():
        target = cwd / target
    try:
        return target.resolve()
    except Exception:
        return cwd


def git_invocation(cwd: Path, tokens: list[str]) -> tuple[Path, str, list[str]] | None:
    values = unwrap_command(tokens)
    if not values or Path(values[0]).name != "git":
        return None
    git_cwd = cwd
    index = 1
    while index < len(values):
        token = values[index]
        if token == "-C" and index + 1 < len(values):
            target = Path(values[index + 1]).expanduser()
            git_cwd = (target if target.is_absolute() else git_cwd / target).resolve()
            index += 2
            continue
        if token.startswith("-C") and token != "-C":
            target = Path(token[2:]).expanduser()
            git_cwd = (target if target.is_absolute() else git_cwd / target).resolve()
            index += 1
            continue
        if token in GIT_OPTIONS_WITH_VALUE and index + 1 < len(values):
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return git_cwd, token, values[index + 1 :]
    return None


def first_non_option(args: list[str]) -> str:
    for value in args:
        if not value.startswith("-"):
            return value
    return ""


def protected_ref(value: str, refs: list[str]) -> str | None:
    normalized = value.removeprefix("refs/remotes/")
    for ref in refs:
        if normalized == f"origin/{ref}":
            return ref
    return None


def branch_create_from_protected(subcommand: str, args: list[str], refs: list[str]) -> str | None:
    flags = {"checkout": {"-b", "-B"}, "switch": {"-c", "-C"}}.get(subcommand)
    if not flags:
        return None
    creates = any(value in flags or any(value.startswith(flag) and value != flag for flag in flags) for value in args)
    if not creates:
        return None
    for value in args:
        matched = protected_ref(value, refs)
        if matched:
            return matched
    return None


def run_git(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )


def current_branch(cwd: Path) -> str:
    result = run_git(cwd, ["symbolic-ref", "--quiet", "--short", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else ""


def nearest_protected_base(cwd: Path, refs: list[str]) -> str | None:
    choices: list[tuple[int, str]] = []
    for ref in refs:
        remote = f"origin/{ref}"
        if run_git(cwd, ["rev-parse", "--verify", "--quiet", remote]).returncode != 0:
            continue
        if run_git(cwd, ["merge-base", "--is-ancestor", remote, "HEAD"]).returncode != 0:
            continue
        ahead = run_git(cwd, ["rev-list", "--count", f"{remote}..HEAD"])
        if ahead.returncode == 0 and ahead.stdout.strip().isdigit():
            choices.append((int(ahead.stdout.strip()), ref))
    return min(choices)[1] if choices else None


def branch_mentions_target(branch: str, target: str) -> bool:
    return target in {part for part in re.split(r"[^A-Za-z0-9]+", branch) if part}


def cherry_pick_revisions(args: list[str]) -> tuple[list[str], int | None] | None:
    if any(flag in args for flag in CONTROL_CHERRY_PICK_FLAGS):
        return None
    revisions: list[str] = []
    mainline: int | None = None
    index = 0
    while index < len(args):
        value = args[index]
        if value in CHERRY_PICK_OPTIONS_WITH_VALUE:
            if index + 1 >= len(args):
                return (revisions, mainline)
            if value in {"-m", "--mainline"}:
                try:
                    mainline = int(args[index + 1])
                except ValueError:
                    mainline = None
            index += 2
            continue
        if value.startswith("--mainline="):
            try:
                mainline = int(value.split("=", 1)[1])
            except ValueError:
                mainline = None
            index += 1
            continue
        redirection = REDIRECTION_RE.match(value)
        if redirection:
            if not redirection.group(1) and index + 1 < len(args):
                index += 2
            else:
                index += 1
            continue
        if value.startswith("-"):
            index += 1
            continue
        revisions.append(value)
        index += 1
    return revisions, mainline


def preflight_cherry_pick(cwd: Path, args: list[str], refs: list[str]) -> str | None:
    parsed = cherry_pick_revisions(args)
    if parsed is None:
        return None
    revisions, mainline = parsed
    branch = current_branch(cwd)
    target = nearest_protected_base(cwd, refs)
    if not branch or not target or not branch_mentions_target(branch, target):
        return None
    if len(revisions) != 1 or any(".." in revision for revision in revisions):
        return "Promotion cherry-picks must be applied one commit at a time so each commit can be merge-tree preflighted."
    revision = revisions[0]
    commit = run_git(cwd, ["rev-parse", "--verify", f"{revision}^{{commit}}"])
    parent_suffix = f"^{mainline}" if mainline is not None else "^"
    parent = run_git(cwd, ["rev-parse", "--verify", f"{revision}{parent_suffix}"])
    if commit.returncode != 0 or parent.returncode != 0:
        return f"Cannot resolve cherry-pick commit and parent for merge-tree preflight: {revision}"
    check = run_git(
        cwd,
        [
            "merge-tree",
            "--write-tree",
            "--merge-base",
            parent.stdout.strip(),
            "HEAD",
            commit.stdout.strip(),
        ],
    )
    if check.returncode != 0:
        detail = (check.stderr or check.stdout).strip().splitlines()
        suffix = f" ({detail[0][:300]})" if detail else ""
        return f"Cherry-pick conflict preflight failed for {revision} onto {target}{suffix}"
    return None


def evaluate_boundary(root: Path, command: str, boundary: dict[str, Any]) -> str | None:
    refs = [str(value) for value in boundary.get("protectedRemoteRefs", []) if isinstance(value, str) and value]
    if not refs:
        return None
    cwd = root
    for segment in shell_segments(command):
        unwrapped = unwrap_command(segment)
        if unwrapped and Path(unwrapped[0]).name == "cd":
            cwd = resolve_cd(cwd, segment)
            continue
        invocation = git_invocation(cwd, segment)
        if not invocation:
            continue
        git_cwd, subcommand, args = invocation
        if boundary.get("blockRawGitWorktreeAdd") is True and subcommand == "worktree" and first_non_option(args) == "add":
            return "Raw `git worktree add` is forbidden; use the project worktree helper (`bun wt new ... --base <destination>`)."
        if boundary.get("blockProtectedRemoteRebranch") is True:
            target = branch_create_from_protected(subcommand, args, refs)
            if target:
                return (
                    f"Do not reuse the current worktree by creating/resetting a branch from origin/{target}; "
                    f"create a fresh destination worktree with `bun wt new <slug> --base {target}`."
                )
        if boundary.get("preflightPromotionCherryPick") is True and subcommand == "cherry-pick":
            reason = preflight_cherry_pick(git_cwd, args, refs)
            if reason:
                return reason
    return None


def main() -> None:
    payload = parse_payload()
    command = shell_command(payload)
    if not command:
        return
    root = host_root(payload)
    if root is None:
        return
    for policy_id, source, boundary in load_boundaries(root):
        reason = evaluate_boundary(root, command, boundary)
        if reason:
            print(f"[{policy_id}] {reason} Canonical rule: {source}")
            return


if __name__ == "__main__":
    main()
