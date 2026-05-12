#!/usr/bin/env bash
# check-adr-sync.sh — recent_tool_calls 안 ADR 작성 detect → plan 갱신 검증
#
# Stdin arg: JSON payload (M11 Stage 5)
# Stdout: deny reason (or empty)

set -e

PAYLOAD="$1"
[ -z "$PAYLOAD" ] && exit 0

# recent_tool_calls 에서 ADR 파일 Write 가 있었나?
ADR_PATHS=$(echo "$PAYLOAD" | python3 -c "
import json, sys, re
try:
    p = json.load(sys.stdin)
    tc = p.get('recent_tool_calls', [])
    paths = []
    for t in tc:
        name = t.get('name', '')
        args = t.get('args_preview', '')
        if name in ('Write', 'Edit') and '.lazy-harness/decisions/' in args:
            m = re.search(r'\.lazy-harness/decisions/(\d{4})-[\w-]+\.md', args)
            if m:
                paths.append(m.group(1))
    print(','.join(set(paths)))
except Exception:
    pass
" 2>/dev/null)

[ -z "$ADR_PATHS" ] && exit 0

# 각 ADR 이 plan addedDuringPhase 에 있나
PLAN_FILE=".lazy-harness/planning/phase-5-plan.xml"
[ ! -f "$PLAN_FILE" ] && exit 0

MISSING=""
IFS=',' read -ra ADR_IDS <<< "$ADR_PATHS"
for adr in "${ADR_IDS[@]}"; do
  if ! grep -q "ADR $adr\|ADR-$adr\|0$adr" "$PLAN_FILE" 2>/dev/null; then
    MISSING="$MISSING $adr"
  fi
done

if [ -n "$MISSING" ]; then
  echo "STOP. .lazy-harness/planning/phase-5-plan.xml 파일을 즉시 갱신하시오. ADR$MISSING 작성됨, plan 의 <addedDuringPhase> 에 미등록. Edit tool 로 마지막 closed phase 의 <addedDuringPhase> 안에 '<note>ADR XXXX — <topic></note>' 형식으로 추가. 갱신 안 하면 다음 응답에서 동일 deny 반복됨. ADR 0010 (Plan Status Hygiene) 위반."
fi

exit 0
