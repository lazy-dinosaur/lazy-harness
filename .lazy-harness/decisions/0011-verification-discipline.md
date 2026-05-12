# ADR 0011 — Verification Discipline (Principle #21)

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: 사용자 발언 "계획 실행할때마다 검증하고 체크하고 부족한거 있으면 보완하고 하는 로직 다 들어간거 맞지???" + "사람에게 물어보는것도 하는건가??"

## Discovery

객관적 점검:

✅ 부분 들어가 있음:
- Self-Driving Loop (1.5): act → verify → fail → classify
- Drafting + Auditing (1.2): 5 finding 검출
- Conflict Resolution (17): 사람 의사결정
- Plan Status Hygiene (20): closed phase status
- 5b 진행 중 21 verification entry 작성됨

❌ 부족:
1. **"verify" 의 strict 정의 없음** — 어떤 건 sh 실행, 어떤 건 marker 실험. quality 차이 큼.
2. **High-risk task 의 verify 의무 명시 없음** — 5a/5b 의 dead code 가 증거 (hook 작성 후 marker 실험 안 함)
3. **AI 자체 verify quality 평가 불가능** — "내가 verify 했어" 자체가 self-report
4. **Phase close 직전 사람 review 의무 없음** — "이만하면 됐다" 가 AI 자체 판단으로 끝남
5. **Doctor warn 해석 시 사람 ask 의무 없음** — AI 가 silent ignore 가능

## Decision

**Principle #21 — Verification Discipline 추가**.

5 sub-rule:

### 21.1 — Verification Levels (Strict)

| Level | 의미 | 예시 |
|---|---|---|
| L0 | sh / command 실행 (exit 0) | `bash hook.sh; echo $?` |
| L1 | output / state 검증 | `wc -l logs.jsonl; before vs after diff` |
| L2 | **Marker 실험** (실 호출 chain 검증) | hook 안에서 marker 파일 작성 → commit 후 marker 존재? |
| L3 | **Negative test** (의도적 fail 시도) | status 일부러 빼고 doctor → fail 출력 확인 |
| L4 | **End-to-end 사람 review** | 사용자가 직접 시나리오 실행 후 confirm |

**의무 mapping**:

- 단순 file edit → L0~L1 충분
- Hook / framework / infra 변경 → **L2 의무** (5a/5b 의 dead code 사고 재발 방지)
- Doctor check 추가 / 변경 → **L3 의무** (negative test)
- Phase close → **L3 + 사람 confirm** (다음 21.4)

### 21.2 — Verify Trigger 명시

verify 가 일어나야 하는 시점:

| Trigger | Level | 의무 |
|---|---|---|
| Criterion 시작 전 | L0 (현재 baseline) | optional |
| Criterion 완료 직후 | L1+ | **mandatory** |
| ADR 작성 직후 | L1+ verify cascade | **mandatory** |
| Hook / infra 작성 후 | L2 marker 실험 | **mandatory** |
| Phase close 직전 | L3 + 사람 review | **mandatory** |
| Doctor warn 출력 시 | L1 (사실 확인) + 사람 ask | **mandatory** |

### 21.3 — High-Risk Task Auto-Detect

doctor / hook / framework / planning 파일 touch 시:
- AI 는 **L2 marker 실험 의무**
- L2 안 하면 verification entry 가 actions.jsonl 에 `confidence:"low"` 로 박힘
- 다음 phase close 시 doctor C13 가 catch

### 21.4 — Phase Close 사람 review 의무

phase close 직전 AI 가 사용자에게 **구조화된 질문**:

```
Phase NN close 전 verify summary:
  - L0 verifications: X 건
  - L1 verifications: Y 건
  - L2 marker experiments: Z 건
  - L3 negative tests: W 건
  - 미검증 high-risk task: [list]

옵션:
  A. 충분함 — close 진행 (Recommended)
  B. L2 추가 실험 필요 — 어디?
  C. L3 negative test 부족 — 어떤 doctor check?
  D. 사람이 직접 시나리오 검증 (L4)
  E. 직접 입력
```

→ **자유 문답 X. 구조화된 선택지 + type-your-own**.

### 21.5 — Doctor Warn 해석 사람 ask 의무

C12/C13 등 warn 출력 시:
- AI 가 silent ignore 금지
- 사용자에게:

```
Doctor C12 warn 출력:
  "5b: no <addedDuringPhase>"

옵션:
  A. 무시 OK — 5b 는 emergent 진짜 없었음
  B. 누락이므로 추가
  C. 잠시 defer (다음 phase 에서)
  D. 직접 입력
```

### 21.6 — Doctor C13: Verify Quality

새 doctor check:

```
C13 — Verify Quality
  - phase 의 verification entries 수 < criterion 수 → fail
  - high-risk file touch 했는데 L2 entry 없음 → warn
  - phase close 됐는데 L3 entry 0 → warn
  - close 직전 사람 review entry 없음 → fail
```

## Why this matters

> Principle 0: AI 자체 verify 는 self-report. 사람의 직감 catch 가 framework 보다 일찍 발견하는 패턴 = framework 약점.

5a/5b cascade 증거:
- ADR 0004 (Cross-layer maps): 사용자 catch
- ADR 0005 (Lazy meaning): 사용자 catch  
- ADR 0006 (Directory bridge): 사용자 catch
- ADR 0007 (AGENTS.md inject): 사용자 catch
- ADR 0009 (Husky integration + dead code): 사용자 catch
- ADR 0010 (Plan hygiene): 사용자 catch
- **ADR 0011 (Verification discipline): 사용자 catch** ← 지금

→ 6/7 ADR 이 사용자 catch. AI 가 한 ADR 은 0008 (5b-2 defer) 한 개 — 그것도 사용자 질문에 답한 결과.

이게 framework 의 약점인 동시에 framework 가 작동한다는 증거. 사용자 직감 → ADR → framework 강화 cascade. **단 사용자 의존도가 높음**. 21.4 + 21.5 가 사람 ask 자동화로 의존도 분산.

## Cascade

| 파일 | 변경 |
|---|---|
| `framework/framework-contract.md` | Principle 21 추가 (v1.2 → v1.3), 22/23/24 reorder |
| `harness-doctor` | C13 Verify Quality check 추가 |
| `actions.jsonl` schema | verification 에 `level` + `confidence` 필드 추가 |
| ADR cascade | 향후 모든 phase 에서 21.4 사람 review 의무 |

## Consequences

### Positive

- AI verify quality 자체 평가 불가능 → L0~L4 명시로 측정 가능
- High-risk task 의 dead code 사고 자동 catch
- 사용자 catch 의존도 분산 (자동 ask 가 사람 review trigger)
- C13 fail/warn 출력으로 phase 진실성 보장

### Negative

- 매 phase close 시 사람 ask 4~5 옵션 답해야 (작은 cost)
- L2 marker 실험 매번 수행 = 시간 +5분/task
- AI 가 21.4 ask 빠뜨리면 framework 무력 → C13 가 catch

### Risk

- AI 가 L0 entry 만 만들고 L2 라고 거짓 라벨 → framework 약점 (해결 어려움)
- 21.4 의 사람 답변 burden — too much friction → 사용자 회피 가능

→ Mitigation: 21.4 ask 는 phase 단위만 (criterion 단위 X). 작은 phase 는 1 분 내 응답 가능.

## References

- ADR 0005 (Lazy meaning): "암묵 → 명시"
- ADR 0009 (Husky integration): dead code 사고
- ADR 0010 (Plan hygiene): 명시 안 한 의무 누락 패턴 — 동일 lesson
- 사용자 발언 chain: "계획 실행할때마다 검증하고 체크" + "사람에게 물어보는것도 하는건가"
- Principle 0: 사람도 AI 도 불완전 → verify 도 사람 보강 필요
