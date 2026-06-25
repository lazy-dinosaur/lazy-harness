# ADR 0014 — Validations.jsonl Retention Policy (Sisyphus bug-4 fix)

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: Sisyphus audit bug-4 — `validations.jsonl` 무한 누적 (push 1회 = +17 lines, retention 정책 없음)

## Rule digest

- Status: needs-review
- Layer: ADR
- Scope: framework-global
- Applies when:
  - a log or JSONL file grows unbounded and needs a retention/rotation policy
  - deciding which audit logs are permanent versus ephemeral snapshots
  - diagnosing slow grep or heavy doctor runs caused by log bloat
- Must:
  - keep permanent audit in actions.jsonl plus decisions.jsonl; treat validations.jsonl as a short-term snapshot
  - bound ephemeral snapshot logs with rotation (cap roughly 1000 lines, keep recent ~500)
- Must not:
  - rely on validations.jsonl for long-term audit history
- Record completion:
  - retention/rotation changes update this ADR; current rotation behavior is superseded and needs review
- Related records:
  - `.lazy-harness/decisions/0012-oracle-sisyphus-audit-cascade.md`
  - `.lazy-harness/decisions/0011-verification-discipline.md`

## Discovery

doctor 가 16 check 출력 → 매 호출 시 16 entry append. pre-push hook 이 매 push 마다 doctor 호출 + 자체 1 entry. 즉:

```
push 1회 = doctor 1 run = +17 lines
하루 push 5회 = +85 lines/day
1년 = ~31,000 lines
```

8 분 사이 측정: 516 lines (32 doctor runs). 결국 grep 느려짐 + doctor 자체 무거워짐 + JSONL 분석 노이즈.

**Audit log 책임 분리** 점검:
- `actions.jsonl` — 사용자 작업 audit trail (영구)
- `decisions.jsonl` — 의사결정 audit (영구, ADR 와 1:1)
- `validations.jsonl` — push 시점 snapshot (단기, 최근 audit 만 의미)

→ validations 는 **단기 snapshot 용도**라 retention OK. 영구 audit 은 actions + decisions 가 책임.

## Decision

`doctor.sh` 의 validations.jsonl append 직후 rotation 추가:

```bash
LINE_COUNT=$(wc -l < "$LOG_FILE" 2>/dev/null | tr -d ' \n')
if [[ -n "$LINE_COUNT" ]] && [[ "$LINE_COUNT" -gt 1000 ]]; then
  TMP="$LOG_FILE.tmp.$$"
  tail -500 "$LOG_FILE" > "$TMP" && mv "$TMP" "$LOG_FILE"
fi
```

**Threshold**: 1000 lines (~60 push runs)
**Keep**: 500 lines (최근 ~30 push runs)
**Trigger**: doctor 매 호출 시 자동 (pre-push 가 doctor 호출하므로 push 시점에도 적용)

## 검증

- L3 negative test: 1100 line padding → doctor 실행 → 500 line 으로 truncate ✓
- JSONL validity 유지 ✓
- 1000 미만 시 정상 누적 (rotation 안 발동) ✓
- 16+1 = 17 entry per doctor run 정상 ✓

## Cascade

| 파일 | 변경 |
|---|---|
| `doctor.sh:706` | rotation 코드 추가 (8 lines) |
| `init.sh` | doctor.sh 는 init 이 emit 안 함 (skill dir 별도). 무관. |
| Audit log split | 영구 audit = actions + decisions, 단기 snapshot = validations 명시 |

## Consequences

### Positive
- 무한 누적 문제 해결
- doctor / grep / JSONL 분석 성능 안정 (1000 line 상한)
- audit log 책임 분리 명시

### Negative
- 30 push 이전 validations 는 사라짐 (영구 audit 필요 시 actions 사용)
- rotation 발동 시 ms 단위 IO (무시 가능)

### Risk
- 만약 누군가 validations 만 보고 long-term audit 한다면 문제. 사용 안 하므로 OK.

## References

- Sisyphus session: bug-4 발견
- ADR 0011 (Verification Discipline) — validations 는 verification entry 의 sample sink
- 사용자: "버그 먼저 잡고가야하는거 아닌가??"

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/hooks/pre-push.sh` — current validation hook references validations log but intentionally avoids success writes.
  - `.lazy-harness/scripts/doctor.py` — parses validations.jsonl if present.
  - `.lazy-harness/framework/legacy-skills-2026-05-10/harness-doctor/scripts/doctor.sh` — historical implementation target for rotation.
- Key symbols:
  - `check_jsonl_parse` (`doctor.py`) — parses validations JSONL.
  - `RESULT_LOG` (`pre-push.sh`) — current validation log path.
- Flow:
  1. ADR 0014 targeted legacy `doctor.sh` rotation.
  2. Current active `doctor.py` does not append/rotate validations.jsonl, and pre-push success intentionally does not write tracked validations.
  3. Keep needs-review; current behavior appears superseded rather than directly implemented.
- Tests / protection:
  - No current self-test verifies validations rotation.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0012-oracle-sisyphus-audit-cascade.md`
- Machine index:
  - graph ids: `kg_adr0014_validations_rotation_legacy`, `kg_adr0014_current_validations_parse_only`
  - generated index key: `pending`
