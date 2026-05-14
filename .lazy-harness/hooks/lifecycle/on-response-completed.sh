#!/usr/bin/env bash
# on-response-completed.sh — lifecycle hook for jcode response.completed event
# Returns deny text when a lifecycle helper requires a human gate.

set +e

[ -f .lazy-harness/.hooks-disabled ] && exit 0

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] || [ ! -d "$REPO_ROOT/.lazy-harness" ] && exit 0
cd "$REPO_ROOT" || exit 0

PAYLOAD=$(cat || echo '{}')

for helper in \
  .lazy-harness/hooks/lifecycle/helpers/check-layer-impact.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-ssot-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-layer-completeness.sh \
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
