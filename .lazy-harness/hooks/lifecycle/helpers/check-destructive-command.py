#!/usr/bin/env python3
"""check-destructive-command.py - deny obviously destructive shell commands.

Chained first in on-tool-execute-before.sh so the Pi/OMP `tool_call` bridge
denies destructive shell commands on both runtimes. Ported from the former
jcode-private `.jcode/hooks/check-bash.sh` (ADR 0050) so destructive-command
safety is runtime-agnostic rather than tied to a jcode-generated hook.

Emits a deny-reason string on stdout when blocked; silent + exit 0 otherwise.
Only inspects shell tool calls (normalized name `bash`); other tools pass
through so file payloads that merely contain these strings are not blocked.
"""
import json
import re
import sys

SHELL_TOOLS = {"bash", "sh", "shell", "command", "cmd", "terminal"}
BLOCKED = [
    (r"\brm\s+-rf\s+/(?:[\s\\\"\x27}\]]|$)", "Refusing rm -rf / (destructive root delete)"),
    (r"\bsudo\s+rm\s+-rf\s+/(?:[\s\\\"\x27}\]]|$)", "Refusing sudo rm -rf / (destructive root delete)"),
    (r"\bdd\b.*\bof=/dev/(sd|nvme|vd)", "Refusing raw disk overwrite (dd of=/dev/*)"),
    (r"\bmkfs(?:\.[a-z0-9]+)?\s+/dev/", "Refusing filesystem creation on block device (mkfs /dev/*)"),
]


def main() -> None:
    payload = sys.argv[1] if len(sys.argv) > 1 else ""
    if not payload.strip():
        try:
            payload = sys.stdin.read()
        except Exception:
            payload = ""
    try:
        data = json.loads(payload) if payload.strip() else {}
    except Exception:
        return
    if not isinstance(data, dict):
        return
    tool = data.get("tool") or {}
    if not isinstance(tool, dict):
        return
    if str(tool.get("name") or "").lower() not in SHELL_TOOLS:
        return
    args = tool.get("args") or {}
    if isinstance(args, dict):
        command = ""
        for key in ("command", "cmd", "text"):
            val = args.get(key)
            if isinstance(val, str) and val:
                command = val
                break
        if not command:
            command = json.dumps(args, ensure_ascii=False)
    else:
        command = str(args)
    for pattern, reason in BLOCKED:
        if re.search(pattern, command, re.IGNORECASE | re.DOTALL):
            print(reason)
            return


if __name__ == "__main__":
    main()
