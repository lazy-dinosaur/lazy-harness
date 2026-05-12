#!/bin/bash
# Lazy-Harness pre-commit Layer Impact Gate (N1, observation mode)
#
# Triggered: husky chain via .husky/pre-commit
# Action: run scripts/layer-impact-gate.ts over the staged file set, append a
#         single Unified Result Schema entry to logs/validations.jsonl.
# Exit: always 0 at v0. Never blocks commit until host-pilot validates FP rate.
#
# ADR 0019 (ambiguous-detection force-gate) + Principle 0 (사람-AI 상호보완):
# until host-pilot data exists, route to logs only.

set +e

[ -f ".lazy-harness/.hooks-disabled" ] && exit 0
[ ! -f ".lazy-harness/scripts/layer-impact-gate.ts" ] && exit 0

# Collect staged files (added/modified/renamed). Deletions excluded — the gate's
# changeKind=deleted handler exists but contributes nothing actionable.
STAGED=$(git diff --cached --name-status --diff-filter=ACMR 2>/dev/null || true)
[ -z "$STAGED" ] && exit 0

CLI_ARGS=()
while IFS= read -r line; do
    [ -z "$line" ] && continue
    STATUS=$(printf '%s' "$line" | awk '{print $1}')
    if printf '%s' "$STATUS" | grep -q '^A'; then
        FLAG="--added"
        FILE=$(printf '%s' "$line" | awk '{print $2}')
    elif printf '%s' "$STATUS" | grep -q '^R'; then
        FLAG="--file"
        FILE=$(printf '%s' "$line" | awk '{print $3}')
    else
        FLAG="--file"
        FILE=$(printf '%s' "$line" | awk '{print $2}')
    fi
    [ -z "$FILE" ] && continue
    CLI_ARGS+=("$FLAG" "$FILE")
done <<EOF
$STAGED
EOF

[ "${#CLI_ARGS[@]}" -eq 0 ] && exit 0

CLI_ARGS+=("--source" "pre-commit" "--append-validation" "--format" "json")

if command -v bun >/dev/null 2>&1; then
    bun .lazy-harness/scripts/layer-impact-gate.ts "${CLI_ARGS[@]}" >/dev/null 2>&1 || true
fi

exit 0
