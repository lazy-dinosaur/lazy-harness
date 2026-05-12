#!/usr/bin/env bash
# check-handoff-stale.sh — handoff 안 stale 표기 detect
#
# Detects:
# - "pending ADR XXXX" 표기인데 해당 ADR 가 closed (file 존재) 상태
# - "framework v1.X N lines" 의 N 이 실제와 다름

set -e

PAYLOAD="$1"  # 사용 안 함 (file 기반 검증)

HANDOFF=".lazy-harness/handoff/00-current-state.md"
[ ! -f "$HANDOFF" ] && exit 0

# Pattern 1: pending ADR XXXX 가 stale?
STALE_PENDING=$(grep -oE "pending ADR [0-9]{4}" "$HANDOFF" 2>/dev/null | sort -u | head -3)
if [ -n "$STALE_PENDING" ]; then
  for line in $STALE_PENDING; do
    ADR_NUM=$(echo "$line" | grep -oE "[0-9]{4}")
    if [ -n "$ADR_NUM" ]; then
      ADR_FILE=$(ls .lazy-harness/decisions/"$ADR_NUM"-*.md 2>/dev/null | head -1)
      if [ -f "$ADR_FILE" ]; then
        # ADR exists → not pending → handoff stale
        echo "STOP. handoff/00-current-state.md 파일을 즉시 갱신하시오. 'pending ADR $ADR_NUM' 표기 발견. ADR $ADR_NUM 는 이미 closed ($ADR_FILE). Edit tool 로 그 줄에서 'pending' 제거하고 status 를 closed 표기로 변경. 갱신 안 하면 다음 응답에서 동일 deny 반복됨. ADR 0015 위반."
        exit 0
      fi
    fi
  done
fi

# Pattern 2: framework v1.X N lines 의 N 검증 — 모든 N 후보 검사
ACTUAL=$(wc -l < .lazy-harness/framework/framework-contract.md 2>/dev/null | tr -d ' ')
if [ -n "$ACTUAL" ]; then
  # handoff 안 framework / Framework 키워드 줄에서 "N lines" 추출
  FW_LINES=$(grep -iE "framework" .lazy-harness/handoff/00-current-state.md 2>/dev/null | grep -oE "[0-9]+ lines" | grep -oE "[0-9]+" | sort -u)
  STALE_NUMS=""
  for n in $FW_LINES; do
    DIFF=$((ACTUAL - n))
    if [ "${DIFF#-}" -gt 5 ]; then
      STALE_NUMS="$STALE_NUMS $n"
    fi
  done
  if [ -n "$STALE_NUMS" ]; then
    STALE_NUMS=$(echo "$STALE_NUMS" | sed 's/^ //')
    echo "STOP. handoff/00-current-state.md 의 'framework contract' 라인 수가 stale. 발견된 stale 값: [$STALE_NUMS]. 실제: $ACTUAL. 즉시 Edit tool 로 handoff 안 stale 값들을 \"$ACTUAL lines\" 로 일괄 교체. 갱신 안 하면 다음 응답에서 동일 deny 반복됨."
    exit 0
  fi
fi

exit 0
