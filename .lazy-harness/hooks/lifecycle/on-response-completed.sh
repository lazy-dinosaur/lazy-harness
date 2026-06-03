#!/usr/bin/env bash
# on-response-completed.sh — lifecycle hook for jcode response.completed event
# Returns deny text when a lifecycle helper requires a human gate.

set +e

ROOT_CANDIDATE="${LAZY_HOST_ROOT:-}"
if [ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ]; then
  ROOT_CANDIDATE="$(git rev-parse --show-toplevel 2>/dev/null || true)"
fi
[ -z "$ROOT_CANDIDATE" ] || [ ! -d "$ROOT_CANDIDATE/.lazy-harness" ] && exit 0
cd "$ROOT_CANDIDATE" || exit 0

[ -f .lazy-harness/.hooks-disabled ] && exit 0

PAYLOAD=$(cat || echo '{}')

if [ -f .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh ]; then
  # shellcheck disable=SC1091
  . .lazy-harness/hooks/lifecycle/helpers/runtime-paths.sh
  lazy_export_runtime_env "$ROOT_CANDIDATE" "$PAYLOAD"
fi

TIMING_ENABLED="${LAZY_HOOK_TIMING:-1}"
if command -v lazy_log_file >/dev/null 2>&1; then
  TIMING_LOG="${LAZY_HOOK_TIMING_LOG:-$(lazy_log_file hook-timings.jsonl "$ROOT_CANDIDATE" "$PAYLOAD")}"
else
  TIMING_LOG="${LAZY_HOOK_TIMING_LOG:-.lazy-harness/.runtime/logs/hook-timings.jsonl}"
fi

now_ns() {
  date +%s%N 2>/dev/null || printf '0'
}

elapsed_ms() {
  START_NS="$1"
  END_NS="$2"
  if [ "$START_NS" -gt 0 ] 2>/dev/null && [ "$END_NS" -ge "$START_NS" ] 2>/dev/null; then
    printf '%s' $(( (END_NS - START_NS) / 1000000 ))
  else
    printf '0'
  fi
}

log_timing() {
  [ "$TIMING_ENABLED" = "0" ] && return 0
  COMPONENT="$1"
  START_NS="$2"
  END_NS="$3"
  EXIT_CODE="$4"
  OUTPUT_EMITTED="$5"
  DURATION_MS=$(elapsed_ms "$START_NS" "$END_NS")
  mkdir -p "$(dirname "$TIMING_LOG")" 2>/dev/null || true
  printf '{"ts":"%s","event":"response.completed","component":"%s","durationMs":%s,"exitCode":%s,"outputEmitted":%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || printf '')" \
    "$COMPONENT" \
    "$DURATION_MS" \
    "$EXIT_CODE" \
    "$OUTPUT_EMITTED" >> "$TIMING_LOG" 2>/dev/null || true
}

emit_inject() {
  HOOK_BODY="$1" python3 <<'PY'
import json
import os

print(json.dumps({
    "inject": {
        "body": os.environ.get("HOOK_BODY", ""),
        "format": "system_reminder",
    }
}, ensure_ascii=False))
PY
}

orchestrator_inject_json() {
  ORCHESTRATOR_RESULT_FILE="$1" python3 <<'PY'
import json
import os
import sys

path = os.environ.get("ORCHESTRATOR_RESULT_FILE")
try:
    with open(path, "r", encoding="utf-8") as fh:
        result = json.load(fh)
except Exception:
    raise SystemExit(2)
print(str(result.get("injectJson") or ""))
PY
}

write_compare_log() {
  [ -z "$ORCHESTRATOR_RESULT_FILE" ] && return 0
  [ ! -f "$ORCHESTRATOR_RESULT_FILE" ] && return 0
  if command -v lazy_log_file >/dev/null 2>&1; then
    COMPARE_LOG="${LAZY_RESPONSE_COMPLETED_COMPARE_LOG:-$(lazy_log_file lifecycle-compare.jsonl "$ROOT_CANDIDATE" "$PAYLOAD")}"
  else
    COMPARE_LOG="${LAZY_RESPONSE_COMPLETED_COMPARE_LOG:-.lazy-harness/.runtime/logs/lifecycle-compare.jsonl}"
  fi
  mkdir -p "$(dirname "$COMPARE_LOG")" 2>/dev/null || true
  ORCHESTRATOR_RESULT_FILE="$ORCHESTRATOR_RESULT_FILE" \
  ORCHESTRATOR_EXIT="$ORCHESTRATOR_EXIT" \
  LEGACY_BODY="$1" \
  LEGACY_HELPER="$2" \
  LIFECYCLE_ENGINE="$LIFECYCLE_ENGINE" \
  COMPARE_LOG="$COMPARE_LOG" \
  python3 <<'PY' >/dev/null 2>&1 || true
import hashlib
import json
import os
from datetime import datetime, timezone

def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]

path = os.environ.get("ORCHESTRATOR_RESULT_FILE") or ""
try:
    with open(path, "r", encoding="utf-8") as fh:
        orchestrator = json.load(fh)
except Exception as exc:
    orchestrator = {"ok": False, "parseError": str(exc)}

legacy_body = os.environ.get("LEGACY_BODY") or ""
orchestrator_body = str(orchestrator.get("firstOutput") or "")
entry = {
    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "event": "response.completed.compare",
    "engine": os.environ.get("LIFECYCLE_ENGINE") or "compare",
    "legacyOutputEmitted": bool(legacy_body.strip()),
    "orchestratorOutputEmitted": bool(orchestrator_body.strip()),
    "legacyHelper": os.environ.get("LEGACY_HELPER") or None,
    "orchestratorHelper": orchestrator.get("firstOutputHelper"),
    "legacyBodyBytes": len(legacy_body.encode("utf-8", errors="replace")),
    "orchestratorBodyBytes": len(orchestrator_body.encode("utf-8", errors="replace")),
    "legacyBodyHash": digest(legacy_body) if legacy_body else None,
    "orchestratorBodyHash": digest(orchestrator_body) if orchestrator_body else None,
    "bodyHashMatch": digest(legacy_body) == digest(orchestrator_body),
    "helperMatch": (os.environ.get("LEGACY_HELPER") or None) == orchestrator.get("firstOutputHelper"),
    "orchestratorExitCode": int(os.environ.get("ORCHESTRATOR_EXIT") or "0"),
    "orchestratorSandbox": bool(orchestrator.get("sandbox")),
}
with open(os.environ["COMPARE_LOG"], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
PY
}

run_orchestrator_check() {
  ORCHESTRATOR_MODE="$1"
  ORCHESTRATOR_RESULT_FILE=$(mktemp "${TMPDIR:-/tmp}/lazy-lifecycle-check.XXXXXX.json" 2>/dev/null || printf '/tmp/lazy-lifecycle-check.%s.json' "$$")
  ORCH_START_NS=$(now_ns)
  if [ "$ORCHESTRATOR_MODE" = "sandbox" ]; then
    printf '%s' "$PAYLOAD" | LAZY_HOST_ROOT="$ROOT_CANDIDATE" python3 .lazy-harness/scripts/lifecycle-check.py --root "$ROOT_CANDIDATE" --sandbox --format=json > "$ORCHESTRATOR_RESULT_FILE" 2>/dev/null
  else
    printf '%s' "$PAYLOAD" | LAZY_HOST_ROOT="$ROOT_CANDIDATE" python3 .lazy-harness/scripts/lifecycle-check.py --root "$ROOT_CANDIDATE" --format=json > "$ORCHESTRATOR_RESULT_FILE" 2>/dev/null
  fi
  ORCHESTRATOR_EXIT=$?
  ORCH_END_NS=$(now_ns)
  ORCH_OUTPUT=$(ORCHESTRATOR_RESULT_FILE="$ORCHESTRATOR_RESULT_FILE" python3 - <<'PY' 2>/dev/null || printf 'false'
import json
import os
try:
    with open(os.environ["ORCHESTRATOR_RESULT_FILE"], "r", encoding="utf-8") as fh:
        print("true" if json.load(fh).get("outputEmitted") else "false")
except Exception:
    print("false")
PY
)
  log_timing "lifecycle-orchestrator" "$ORCH_START_NS" "$ORCH_END_NS" "$ORCHESTRATOR_EXIT" "$ORCH_OUTPUT"
}

HOOK_START_NS=$(now_ns)
LIFECYCLE_ENGINE="${LAZY_RESPONSE_COMPLETED_ENGINE:-legacy}"
case "$LIFECYCLE_ENGINE" in
  legacy|orchestrator|compare) ;;
  *) LIFECYCLE_ENGINE="legacy" ;;
esac
ORCHESTRATOR_RESULT_FILE=""
ORCHESTRATOR_EXIT=0

# Phase 1 conservative fast-path.
# Only skip helpers that are provably write-only, and only when the payload has
# a valid recent_tool_calls list whose tools are all known read-only helpers.
# Unknown payload/tool shape falls back to the full helper set.
FASTPATH_SKIP_HELPERS=$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys

READ_ONLY = {
    "read", "Read",
    "grep", "Grep",
    "agentgrep", "glob", "Glob", "ls", "LS",
    "webfetch", "websearch",
    "mcp__filesystem__read_text_file", "mcp__filesystem__read_file", "mcp__filesystem__read_multiple_files",
    "mcp__filesystem__list_directory", "mcp__filesystem__list_directory_with_sizes", "mcp__filesystem__directory_tree",
    "mcp__filesystem__search_files", "mcp__filesystem__get_file_info",
}
WRITE_ONLY_HELPERS = [
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh",
    ".lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh",
]

try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)
if not isinstance(payload, dict) or "recent_tool_calls" not in payload:
    raise SystemExit(0)
calls = payload.get("recent_tool_calls")
if not isinstance(calls, list):
    raise SystemExit(0)
for call in calls:
    if not isinstance(call, dict):
        raise SystemExit(0)
    name = str(call.get("name") or "")
    if name not in READ_ONLY:
        raise SystemExit(0)
print("\n".join(WRITE_ONLY_HELPERS))
' 2>/dev/null || true)

should_skip_helper() {
  CANDIDATE="$1"
  [ -z "$FASTPATH_SKIP_HELPERS" ] && return 1
  printf '%s\n' "$FASTPATH_SKIP_HELPERS" | grep -Fx -- "$CANDIDATE" >/dev/null 2>&1
}

# ADR 0037 telemetry: collect one append-only route sample per response turn
# when Jcode provides last_user_message. This is silent and best-effort; it does
# not replace any gate or validation helper below.
if command -v bun >/dev/null 2>&1 && [ -f .lazy-harness/scripts/task-router.ts ]; then
  ROUTE_START_NS=$(now_ns)
  ROUTE_EXIT=0
  ROUTE_OUTPUT=false
  ROUTE_INPUT=$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)
last = ""
for key in ("last_user_message", "lastUserMessage", "last_user_input", "lastUserInput", "user_message", "userMessage"):
    value = payload.get(key)
    if isinstance(value, str) and value.strip():
        last = value.strip()
        break
mid = str(payload.get("message_id") or "")
if last:
    print(json.dumps({"message": last, "message_id": mid}, ensure_ascii=False))
' 2>/dev/null || true)
  if [ -n "$ROUTE_INPUT" ]; then
 	ROUTE_MESSAGE=$(printf '%s' "$ROUTE_INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("message", ""))' 2>/dev/null || true)
	ROUTE_MESSAGE_ID=$(printf '%s' "$ROUTE_INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("message_id", ""))' 2>/dev/null || true)
		if [ -n "$ROUTE_MESSAGE" ]; then
		  ROUTE_CHANGED_FILES=$( (git diff --name-only; git diff --cached --name-only) 2>/dev/null | awk 'NF' | sort -u | head -200 | paste -sd, - )
		  if [ -n "$ROUTE_CHANGED_FILES" ]; then
		    LAZY_HOST_ROOT="$ROOT_CANDIDATE" bun .lazy-harness/scripts/task-router.ts --message "$ROUTE_MESSAGE" --format=json --log --message-id "$ROUTE_MESSAGE_ID" --changed-files "$ROUTE_CHANGED_FILES" >/dev/null 2>&1 || ROUTE_EXIT=$?
		  else
		    LAZY_HOST_ROOT="$ROOT_CANDIDATE" bun .lazy-harness/scripts/task-router.ts --message "$ROUTE_MESSAGE" --format=json --log --message-id "$ROUTE_MESSAGE_ID" >/dev/null 2>&1 || ROUTE_EXIT=$?
		  fi
		fi
  else
    # Non-canonical diagnostics only. Do not store raw payload values or messages.
    printf '%s' "$PAYLOAD" | LAZY_HOST_ROOT="$ROOT_CANDIDATE" python3 -c '
import hashlib, json, os, sys
from datetime import datetime, timezone
try:
    payload = json.load(sys.stdin)
except Exception:
    payload = {}
keys = sorted(payload.keys()) if isinstance(payload, dict) else []
aliases = ["last_user_message", "lastUserMessage", "last_user_input", "lastUserInput", "user_message", "userMessage"]
mid = str(payload.get("message_id") or "") if isinstance(payload, dict) else ""
entry = {
    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "status": "no-route-message",
    "payloadBytes": len(json.dumps(payload, ensure_ascii=False)) if isinstance(payload, dict) else 0,
    "keys": keys,
    "messageIdHash": hashlib.sha256(mid.encode()).hexdigest()[:16] if mid else None,
    "messageAliasesPresent": [k for k in aliases if isinstance(payload.get(k), str) and payload.get(k).strip()] if isinstance(payload, dict) else [],
}
root = os.environ.get("LAZY_HOST_ROOT") or os.getcwd()
shared_root = os.environ.get("LAZY_SHARED_ROOT") or os.path.join(root, ".lazy-harness", ".shared")
path = os.path.join(shared_root, "logs", "route-telemetry-debug.jsonl")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
	' >/dev/null 2>&1 || true
	  fi
  ROUTE_END_NS=$(now_ns)
  log_timing "route-telemetry" "$ROUTE_START_NS" "$ROUTE_END_NS" "$ROUTE_EXIT" "$ROUTE_OUTPUT"
fi

if [ "$LIFECYCLE_ENGINE" = "orchestrator" ] && [ -f .lazy-harness/scripts/lifecycle-check.py ]; then
  run_orchestrator_check "live"
  if [ "$ORCHESTRATOR_EXIT" -eq 0 ]; then
    ORCH_INJECT=$(orchestrator_inject_json "$ORCHESTRATOR_RESULT_FILE")
    ORCH_PARSE_EXIT=$?
    if [ "$ORCH_PARSE_EXIT" -eq 0 ]; then
      HOOK_END_NS=$(now_ns)
      if [ -n "$ORCH_INJECT" ]; then
        printf '%s\n' "$ORCH_INJECT"
        log_timing "hook-total" "$HOOK_START_NS" "$HOOK_END_NS" 0 true
      else
        log_timing "hook-total" "$HOOK_START_NS" "$HOOK_END_NS" 0 false
      fi
      rm -f "$ORCHESTRATOR_RESULT_FILE" 2>/dev/null || true
      exit 0
    fi
  fi
  # Safe rollback path: any orchestrator failure falls back to the legacy helper loop.
fi

if [ "$LIFECYCLE_ENGINE" = "compare" ] && [ -f .lazy-harness/scripts/lifecycle-check.py ]; then
  run_orchestrator_check "sandbox"
fi

for helper in \
  .lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-user-correction-capture.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py \
  .lazy-harness/hooks/lifecycle/helpers/check-record-decision-shadow.py \
  .lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-record-before-session-history.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-lazy-cli-entrypoint.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-aftershock-reanalysis.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-adr-sync.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-handoff-stale.sh
 do
  [ -x "$helper" ] || continue
  if should_skip_helper "$helper"; then
    continue
  fi
  HELPER_START_NS=$(now_ns)
  OUT=$("$helper" "$PAYLOAD" 2>/dev/null)
  HELPER_EXIT=$?
  HELPER_END_NS=$(now_ns)
  if [ -z "$OUT" ]; then
    log_timing "$helper" "$HELPER_START_NS" "$HELPER_END_NS" "$HELPER_EXIT" false
    continue
  fi
  log_timing "$helper" "$HELPER_START_NS" "$HELPER_END_NS" "$HELPER_EXIT" true
  [ "$LIFECYCLE_ENGINE" = "compare" ] && write_compare_log "$OUT" "$helper"
  emit_inject "$OUT"
  HOOK_END_NS=$(now_ns)
  log_timing "hook-total" "$HOOK_START_NS" "$HOOK_END_NS" 0 true
  [ -n "$ORCHESTRATOR_RESULT_FILE" ] && rm -f "$ORCHESTRATOR_RESULT_FILE" 2>/dev/null || true
  exit 0
done

HOOK_END_NS=$(now_ns)
[ "$LIFECYCLE_ENGINE" = "compare" ] && write_compare_log "" ""
log_timing "hook-total" "$HOOK_START_NS" "$HOOK_END_NS" 0 false
[ -n "$ORCHESTRATOR_RESULT_FILE" ] && rm -f "$ORCHESTRATOR_RESULT_FILE" 2>/dev/null || true

exit 0
