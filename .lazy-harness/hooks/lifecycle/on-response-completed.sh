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
  .lazy-harness/hooks/lifecycle/helpers/check-ddd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-bdd-trigger.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-adr-sync.sh \
  .lazy-harness/hooks/lifecycle/helpers/check-handoff-stale.sh
 do
  [ -x "$helper" ] || continue
  OUT=$("$helper" "$PAYLOAD" 2>/dev/null || true)
  [ -z "$OUT" ] && continue
  printf '%s\n' "$OUT"
  exit 0
done

exit 0
