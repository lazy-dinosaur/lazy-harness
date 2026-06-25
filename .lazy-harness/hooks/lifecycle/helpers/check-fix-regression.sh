#!/usr/bin/env bash
# check-fix-regression.sh — Fix commit 후 regression 엔트리 검증
#
# 마지막 commit 이 Fix: 인데 regression/registry 미등록이면 deny

set -e

PAYLOAD="$1"  # 사용 안 함 (git 기반 검증)

# 마지막 commit 이 Fix: 타입인가
# lifecycle-check --sandbox 는 real host git history 를 복사하지 않는다.
# compare fidelity 를 위해 read-only git facts 를 env 로 전달하면 우선 사용한다.
LAST_COMMIT="${LAZY_LIFECYCLE_GIT_LAST_SUBJECT:-}"
if [ -z "$LAST_COMMIT" ]; then
  LAST_COMMIT=$(git log -1 --pretty=%s 2>/dev/null)
fi
if ! echo "$LAST_COMMIT" | grep -qE "^Fix: "; then
  exit 0
fi

LAST_SHA="${LAZY_LIFECYCLE_GIT_HEAD:-}"
if [ -z "$LAST_SHA" ]; then
  LAST_SHA=$(git rev-parse HEAD 2>/dev/null)
fi

# registry.jsonl 에 이 SHA 의 promoted regression entry 가 있나.
# JSON 파싱으로 sha 필드를 비교 — 공백/표기/인코딩 무관 (post-commit json.dumps 든 CLI 든 동일 인식).
# candidates.jsonl 의 auto-stub 은 만족 조건이 아님: 반드시 registry 로 승격해야 한다.
REG=".lazy-harness/regression/registry.jsonl"
FOUND=0
if [ -f "$REG" ] && LAZY_REG_SHA="$LAST_SHA" python3 - "$REG" <<'PY' 2>/dev/null
import os, sys, json
sha = os.environ.get("LAZY_REG_SHA", "")
try:
    fh = open(sys.argv[1], encoding="utf-8")
except OSError:
    sys.exit(1)
with fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        if str(row.get("sha", "")) == sha:
            sys.exit(0)
sys.exit(1)
PY
then
  FOUND=1
fi

if [ "$FOUND" = "0" ]; then
  SHORT_SHA=$(echo "$LAST_SHA" | cut -c1-8)
  echo "STOP. 마지막 commit ($SHORT_SHA) 이 Fix: 타입인데 .lazy-harness/regression/registry.jsonl 에 regression entry 가 없음. 검증된 CLI 로 등록하시오 (raw JSON 수동 append 금지): .lazy-harness/bin/lazy regression add --sha $LAST_SHA --description \"버그 설명\" --test 보호테스트경로 --repro \"재현 절차\". 등록 전까지 동일 STOP 반복."
fi

exit 0
