#!/usr/bin/env bash
# check-fix-regression.sh — Fix commit 후 regression 엔트리 검증
#
# 마지막 commit 이 Fix: 인데 regression/registry 미등록이면 deny

set -e

PAYLOAD="$1"  # 사용 안 함 (git 기반 검증)

# 마지막 commit 이 Fix: 타입인가
LAST_COMMIT=$(git log -1 --pretty=%s 2>/dev/null)
if ! echo "$LAST_COMMIT" | grep -qE "^Fix: "; then
  exit 0
fi

LAST_SHA=$(git rev-parse HEAD 2>/dev/null)

# regression/registry.jsonl 또는 candidates.jsonl 에 이 SHA 가 있나
REG_FILES=".lazy-harness/regression/registry.jsonl .lazy-harness/regression/candidates.jsonl"
FOUND=0
for f in $REG_FILES; do
  if [ -f "$f" ] && grep -q "\"sha\":\"$LAST_SHA\"" "$f" 2>/dev/null; then
    FOUND=1
    break
  fi
done

if [ "$FOUND" = "0" ]; then
  SHORT_SHA=$(echo "$LAST_SHA" | cut -c1-8)
  echo "STOP. .lazy-harness/regression/registry.jsonl 파일에 즉시 regression entry 등록하시오. 마지막 commit ($SHORT_SHA) 이 Fix: 타입. Edit tool 로 다음 JSON 줄을 registry.jsonl 끝에 append: {\"sha\":\"$LAST_SHA\",\"description\":\"<bug 설명>\",\"protectedBy\":[\"<test_path>\"],\"reproSteps\":\"<재현>\"}. 갱신 안 하면 다음 응답에서 동일 deny 반복됨."
fi

exit 0
