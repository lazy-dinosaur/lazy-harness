#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def stable_hash(value: Any, length: int = 16) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8", errors="replace")).hexdigest()[:length]


def payload_session_id(payload: dict[str, Any] | None = None) -> str:
    payload = payload or {}
    for key in ("session_id", "sessionId"):
        value = payload.get(key)
        if value:
            return str(value)
    for key in ("LAZY_SESSION_ID", "JCODE_SESSION_ID", "JCODE_SESSION"):
        value = os.environ.get(key)
        if value:
            return value
    return ""


def session_key(payload: dict[str, Any] | None = None, session_id: str | None = None) -> str:
    raw = session_id or payload_session_id(payload)
    if not str(raw or "").strip():
        return "default"
    return f"session-{stable_hash(raw, 20)}"


def git_output(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def worktree_git_dir(root: Path) -> Path:
    out = git_output(root, "rev-parse", "--absolute-git-dir")
    if out:
        return Path(out).resolve()
    return root / ".lazy-harness" / ".gitless"


def git_common_dir(root: Path) -> Path:
    out = git_output(root, "rev-parse", "--git-common-dir")
    if not out:
        return worktree_git_dir(root)
    path = Path(out)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def runtime_root(root: Path, payload: dict[str, Any] | None = None, session_id: str | None = None) -> Path:
    explicit = os.environ.get("LAZY_RUNTIME_ROOT")
    if explicit:
        return Path(explicit).resolve()
    return worktree_git_dir(root) / "lazy-harness" / "runtime" / session_key(payload, session_id)


def shared_root(root: Path) -> Path:
    explicit = os.environ.get("LAZY_SHARED_ROOT")
    if explicit:
        return Path(explicit).resolve()
    return git_common_dir(root) / "lazy-harness" / "shared"


def runtime_state_path(root: Path, name: str, payload: dict[str, Any] | None = None, session_id: str | None = None) -> Path:
    return runtime_root(root, payload, session_id) / "state" / name


def runtime_log_path(root: Path, name: str, payload: dict[str, Any] | None = None, session_id: str | None = None) -> Path:
    return runtime_root(root, payload, session_id) / "logs" / name


def shared_path(root: Path, rel: str) -> Path:
    return shared_root(root) / rel


def append_jsonl_bounded(path: Path, row: dict[str, Any], keep: int = 200) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[str] = []
    if path.exists():
        existing = [line for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()][-(keep - 1):]
    existing.append(json.dumps(row, ensure_ascii=False, sort_keys=True))
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp.write_text("\n".join(existing) + "\n", encoding="utf-8")
    tmp.replace(path)


def stable_json(value: Any) -> str:
    if isinstance(value, list):
        return "[" + ",".join(stable_json(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            json.dumps(key, ensure_ascii=False) + ":" + stable_json(val)
            for key, val in sorted(value.items())
            if val is not None
        ) + "}"
    return json.dumps(value, ensure_ascii=False)


def _acquire_lock(lock_dir: Path, timeout_seconds: float = 5.0) -> None:
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    while True:
        try:
            lock_dir.mkdir()
            (lock_dir / "owner.json").write_text(json.dumps({"pid": os.getpid(), "startedAt": time.time()}) + "\n", encoding="utf-8")
            return
        except FileExistsError:
            if time.time() - started > timeout_seconds:
                raise TimeoutError(f"Timed out waiting for lazy-harness lock: {lock_dir}")
            time.sleep(0.05)


def _release_lock(lock_dir: Path) -> None:
    try:
        for child in lock_dir.iterdir():
            child.unlink(missing_ok=True)
        lock_dir.rmdir()
    except Exception:
        pass


def append_jsonl_stable(root: Path, path: Path, row: dict[str, Any], id_key: str = "id") -> str:
    lock_dir = shared_root(root) / "locks" / f"jsonl-{stable_hash(path, 24)}.lockdir"
    _acquire_lock(lock_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [line for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()] if path.exists() else []
        row_id = row.get(id_key)
        incoming = stable_json(row)
        for line in lines:
            try:
                existing = json.loads(line)
            except Exception:
                continue
            if stable_json(existing) == incoming:
                return "deduped-identical"
            if isinstance(row_id, str) and row_id:
                if isinstance(existing, dict) and existing.get(id_key) == row_id:
                    conflict = {
                        "id": f"conflict_{row_id}_{stable_hash(incoming, 12)}",
                        "event": "lazy-harness.jsonl-conflict",
                        "status": "conflict-recorded",
                        "detectedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "targetPath": str(path),
                        "idKey": id_key,
                        "conflictingId": row_id,
                        "existingHash": stable_hash(stable_json(existing)),
                        "incomingHash": stable_hash(incoming),
                        "incoming": row,
                    }
                    conflict_path = Path(str(path) + ".conflicts.jsonl")
                    with conflict_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(conflict, ensure_ascii=False, sort_keys=True) + "\n")
                    return "conflict-recorded"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return "appended"
    finally:
        _release_lock(lock_dir)


if __name__ == "__main__":
    import sys
    root = Path(os.environ.get("LAZY_HOST_ROOT") or os.getcwd()).resolve()
    payload: dict[str, Any] = {}
    if len(sys.argv) > 2 and sys.argv[2].strip():
        try:
            payload = json.loads(sys.argv[2])
        except Exception:
            payload = {}
    mode = sys.argv[1] if len(sys.argv) > 1 else "runtime-root"
    if mode == "runtime-root":
        print(runtime_root(root, payload))
    elif mode == "shared-root":
        print(shared_root(root))
    elif mode == "state-path":
        print(runtime_state_path(root, sys.argv[3] if len(sys.argv) > 3 else "state.json", payload))
    elif mode == "log-path":
        print(runtime_log_path(root, sys.argv[3] if len(sys.argv) > 3 else "log.jsonl", payload))
