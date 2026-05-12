#!/usr/bin/env bash
# check-layer-impact.sh — N1 Layer Impact Completion Gate (v0 observation mode)
#
# Input:  response.completed payload as argv[1]
# Output: empty (observation mode never blocks at v0)
# Side effect: appends a single layer-impact-result.schema.json line to
#              .lazy-harness/logs/validations.jsonl when the payload references
#              code/file writes inside triggerable scopes.
#
# v0 contract: do NOT block, even when missingLayers is non-empty. We are
# collecting false-positive data via fixtures + (later) host-pilot before
# promoting the gate to a force-gate. ADR 0019 ambiguous-detection rule plus
# Principle 0 (사람-AI 상호보완): until verified, route to logs only.
#
# Promotion path (future):
#   1. host-pilot collects N≥3 real-change samples → measure FP rate
#   2. flip --strict on for production hooks
#   3. switch this helper to emit deny text when humanRequired=true

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

GATE_TS=".lazy-harness/scripts/layer-impact-gate.ts"
[ ! -f "$GATE_TS" ] && exit 0

# Extract changed file paths from the payload. Mirror the regex used by
# check-ddd-trigger.sh so the two helpers agree on what counts as a write.
FILES=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json
import os
import re

try:
    payload = json.loads(os.environ.get("PAYLOAD_JSON", "{}"))
except Exception:
    raise SystemExit(0)

paths = []
allowed_names = {
    "Write",
    "Edit",
    "MultiEdit",
    "write",
    "edit",
    "multiedit",
    "mcp__filesystem__write_file",
    "mcp__filesystem__edit_file",
}
# N1 is wider than DDD: we consider ANY source/record path the user touched.
# Production source, test files, AND .lazy-harness/ record files all count
# because N1 measures the joint impact set.
pattern = re.compile(r"(?:src/[^\s\"'`,)}]+|\.lazy-harness/[^\s\"'`,)}]+)\.(?:ts|tsx|js|jsx|mts|cts|xml|json|md)")

for call in payload.get("recent_tool_calls", []):
    name = str(call.get("name", ""))
    args = str(call.get("args_preview", ""))
    if name not in allowed_names:
        continue
    for match in pattern.finditer(args):
        paths.append(match.group(0))

# de-dup preserving order
print("\n".join(dict.fromkeys(paths)))
PY
)

[ -z "$FILES" ] && exit 0

# Build --file args. We mark every path as modified at v0 — the payload does
# not distinguish added/modified reliably.
CLI_ARGS=()
while IFS= read -r file; do
  [ -z "$file" ] && continue
  CLI_ARGS+=("--file" "$file")
done <<EOF
$FILES
EOF

[ "${#CLI_ARGS[@]}" -eq 0 ] && exit 0

CLI_ARGS+=("--source" "response-completed" "--append-validation" "--format" "json")

# Run the gate. Never let a gate failure trigger this helper to block — the
# gate already exits 0 in non-strict mode, but we additionally swallow stderr.
GATE_OUT=$(bun "$GATE_TS" "${CLI_ARGS[@]}" 2>/dev/null || true)
[ -z "$GATE_OUT" ] && exit 0

# v0: observation only. Never emit deny text.
# (Future strict mode would parse $GATE_OUT and emit a structured ask here.)
exit 0
