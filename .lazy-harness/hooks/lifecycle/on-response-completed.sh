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

# ADR 0037 telemetry: collect one append-only route sample per response turn
# when Jcode provides last_user_message. This is silent and best-effort; it does
# not replace any gate or validation helper below.
if command -v bun >/dev/null 2>&1 && [ -f .lazy-harness/scripts/task-router.ts ]; then
  ROUTE_INPUT=$(PAYLOAD_JSON="$PAYLOAD" python3 <<'PY' 2>/dev/null || true
import json, os
try:
    payload = json.loads(os.environ.get('PAYLOAD_JSON', '{}'))
except Exception:
    raise SystemExit(0)
last = (payload.get('last_user_message') or '').strip()
mid = str(payload.get('message_id') or '')
if last:
    print(json.dumps({'message': last, 'message_id': mid}, ensure_ascii=False))
PY
)
  if [ -n "$ROUTE_INPUT" ]; then
    ROUTE_MESSAGE=$(printf '%s' "$ROUTE_INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("message", ""))' 2>/dev/null || true)
    ROUTE_MESSAGE_ID=$(printf '%s' "$ROUTE_INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("message_id", ""))' 2>/dev/null || true)
    if [ -n "$ROUTE_MESSAGE" ]; then
      LAZY_HOST_ROOT="$ROOT_CANDIDATE" bun .lazy-harness/scripts/task-router.ts --message "$ROUTE_MESSAGE" --format=json --log --message-id "$ROUTE_MESSAGE_ID" >/dev/null 2>&1 || true
    fi
  fi
fi

for helper in \
  .lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh \
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
  OUT=$("$helper" "$PAYLOAD" 2>/dev/null || true)
  [ -z "$OUT" ] && continue
  HOOK_BODY="$OUT" python3 <<'PY'
import json
import os

print(json.dumps({
    "inject": {
        "body": os.environ.get("HOOK_BODY", ""),
        "format": "system_reminder",
    }
}, ensure_ascii=False))
PY
  exit 0
done

exit 0
