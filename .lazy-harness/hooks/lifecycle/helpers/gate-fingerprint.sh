#!/usr/bin/env bash
# gate-fingerprint.sh — turn-level fingerprint suppression for option-gate helpers
#
# Public commands (sourced or invoked as subprocess):
#   gate_fingerprint_check  <helper_name> <fingerprint>      → exit 0 if already open
#                                                              this turn (caller should
#                                                              suppress), exit 1 if new
#   gate_fingerprint_record <helper_name> <fingerprint>      → mark open
#
# The state file `$LAZY_RUNTIME_ROOT/state/open-gates.json` is keyed by helper name +
# fingerprint and tied to the argv-passed message id. When the message id rolls
# over, all fingerprints from the previous turn are cleared. This provides a
# payload-schema-independent invariant: within a single turn each helper and
# fingerprint pair fires at most once.
# (= same message_id), each (helper, fingerprint) pair fires at most once.
#
# Contract:
#   - state file is best-effort. Any read/write failure exits 1 (treat as new).
#   - fingerprint should be deterministic for the same (input, intent) pair.
#   - caller must NOT rely on assistant_response for suppression.

set -euo pipefail

if [ -z "${LAZY_RUNTIME_ROOT:-}" ] && [ -f .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh ]; then
  # shellcheck disable=SC1091
  . .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh
  lazy_export_runtime_env "${LAZY_HOST_ROOT:-$(pwd)}" "{}"
fi

STATE_FILE="${LAZY_OPEN_GATES_FILE:-${LAZY_RUNTIME_ROOT:-.lazy-harness/.runtime}/state/open-gates.json}"

_gate_get_message_id() {
  # Prefer message id passed as 3rd argv, fall back to env, fall back to "unknown".
  if [ -n "${3:-}" ]; then
    printf '%s' "$3"
    return 0
  fi
  printf '%s' "unknown"
}

_gate_state_op() {
  local op="$1" helper="$2" fingerprint="$3" message_id="$4"
  STATE_FILE="$STATE_FILE" OP="$op" HELPER="$helper" FP="$fingerprint" MSG="$message_id" python3 <<'PY'
import json
import os
import sys
import time
from pathlib import Path

state_path = Path(os.environ['STATE_FILE'])
op = os.environ['OP']
helper = os.environ['HELPER']
fingerprint = os.environ['FP']
message_id = os.environ['MSG']
key = f"{helper}:{fingerprint}"

state = {"last_message_id": "", "open_fingerprints": {}}
if state_path.exists():
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        state = {"last_message_id": "", "open_fingerprints": {}}

# Clear fingerprints when message id rolls over.
if state.get("last_message_id") != message_id:
    state = {"last_message_id": message_id, "open_fingerprints": {}}

opens = state.setdefault("open_fingerprints", {})

if op == "check":
    if key in opens:
        sys.exit(0)  # already open this turn → caller should suppress
    sys.exit(1)  # new → caller should fire

if op == "record":
    opens[key] = {
        "first_seen_message_id": message_id,
        "first_seen_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    state["open_fingerprints"] = opens
    state["last_message_id"] = message_id
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.exit(0)

sys.exit(2)
PY
}

gate_fingerprint_check() {
  local helper="${1:-}" fingerprint="${2:-}" message_id
  message_id=$(_gate_get_message_id "$@")
  [ -z "$helper" ] || [ -z "$fingerprint" ] && return 1
  _gate_state_op check "$helper" "$fingerprint" "$message_id" && return 0
  return 1
}

gate_fingerprint_record() {
  local helper="${1:-}" fingerprint="${2:-}" message_id
  message_id=$(_gate_get_message_id "$@")
  [ -z "$helper" ] || [ -z "$fingerprint" ] && return 1
  _gate_state_op record "$helper" "$fingerprint" "$message_id" || return 1
  return 0
}

# Subprocess entry point: invoke directly with subcommand.
case "${1:-}" in
  check)
    shift
    gate_fingerprint_check "$@"
    exit $?
    ;;
  record)
    shift
    gate_fingerprint_record "$@"
    exit $?
    ;;
esac
