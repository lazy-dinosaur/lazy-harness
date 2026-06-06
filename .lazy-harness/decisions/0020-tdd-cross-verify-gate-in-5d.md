# ADR 0020 — TDD Cross-Verify Gate in 5d (Interview Loop)

- Status: Accepted
- Date: 2026-05-11
- Trigger: ADR 0018 의 약속 — "TDD detector 는 5c 안 아닌 5d Interview Loop 의 cross-verify gate"
- Related: ADR 0018 (Cross-Layer Cascade), ADR 0019 (Ambiguous → Force Gate)

## Context

ADR 0018 에서 TDD 의 위치를 명확화:
- 4 detector (DDD/SDD/BDD/SSOT) = input/development phase
- TDD = output/verify phase (개발 완료 후)
- → **5c 의 detector 아닌, 5d Interview Loop 안의 cross-verify gate**

사용자 통찰:
> "tdd 의 경우엔 전부 다 개발이 완료 되고 나서 test 하면서 코드가 붙을꺼고 그 코드들이 ddd 나 다른 내용에 부합한지도 보면서 체크할꺼고 말야"

→ TDD 는 4 layer 가 모두 채워진 후 검증 게이트.

5d (Interview Loop) 의 본질:
- 양방향 conflict resolution
- 4 layer 가 서로 부합하는지 검증
- 사용자 ask 로 conflict 해소

TDD 는 5d 안에서 어떻게 동작할지 명문화 필요.

## Decision

### TDD Cross-Verify Gate 정의

**Fire 시점**: 4 detector 가 모두 채워진 후, AI 가 응답 stop 시도할 때
**Trigger**: `response.completed` hook 안 sync-guard 의 마지막 단계
**Mechanism**: 통합 검증 — test ↔ 4 layer 일관성

### 검증 항목 (5 cross-check)

| 검증 | 내용 |
|---|---|
| 1. **Test 존재** | src 코드 변경 시 매칭 *.test.ts / *.spec.ts / __tests__/ 존재? |
| 2. **Test ↔ BDD** | test name / structure 가 BDD scenario 의 step (given/when/then) 과 매칭? |
| 3. **Test ↔ DDD** | test 안 사용하는 type 이 ubiquitous-language.xml 안 term? |
| 4. **Test ↔ SDD** | test 가 검증하는 input/output 이 SDD contract (zod schema/trpc procedure) 와 일치? |
| 5. **Test ↔ SSOT** | test 가 호출하는 helper/mapper 가 SSOT registry 에 있나? |

### 검증 결과 → action

| 검증 통과 수 | Confidence | Gate | Action |
|---|---|---|---|
| 5/5 | high | auto+review | 정상 stop |
| 3-4/5 | medium | recommend | warn + suggest test 추가/수정 |
| 0-2/5 | low | **force gate** | deny + 구체적 missing list ask |
| Confused (한 layer 가 conflict) | ambiguous | force gate | structured ask (ADR 0019) |

### Example

```
시나리오: AI 가 PatientRiskProfile interface 추가 + DDD 등록 + SDD contract 추가 끝났다고 stop 시도

TDD Cross-Verify Gate fire:

1. Test 존재? 
   → src/main/services/__patient-risk.ts 에 매칭 test 파일 없음 ❌
2. Test ↔ BDD?
   → (test 없음, skip)
3. Test ↔ DDD?
   → (test 없음, skip)
4. Test ↔ SDD?
   → (test 없음, skip)
5. Test ↔ SSOT?
   → (test 없음, skip)

통과 0/5 → force gate

Deny reason:
"STOP. 5d TDD Cross-Verify Gate: 
 PatientRiskProfile 에 대응 test 파일 없음. 
 다음 중 어느 것?
 A. PatientRiskProfile.test.ts 작성 (Recommended) — BDD scenario X / DDD term Y / SDD contract Y 와 일치하는 test
 B. 의도적 refactor-only — Notes 에 명시
 C. 추후 작성 (today's PR 에서 제외) — regression entry 등록
 D. 직접 입력"
```

### Loop 방지 (ADR 0011 jcode loop guard 활용)

TDD gate 가 force gate 로 deny → 사용자 답 받음 → 다음 turn 에 reminder 주입.
사용자 답 영구 기록 → 같은 케이스 재발 안 함.
M11 Stage 3 loop guard (3회 연속 deny → suppress) 이 안전망.

### 5d Interview Loop 의 다른 부분과 관계

TDD gate 외 5d 의 다른 sub-task:
- 5d-1: Aftershock check (한 결정의 cascade)
- 5d-2: Follow-up question 자동 제시
- 5d-3: **TDD cross-verify gate (이 ADR)**
- 5d-4: User feedback → SDD revision loop

→ TDD gate 는 5d 의 1 sub-task. 5d 전체는 더 큼.

## Implementation

### 5d 진입 전 prerequisite

1. 5c-1~5c-5 모두 완료 (4 detector + cross-layer map)
2. ubiquitous-language.xml + SDD spec 파일들이 어느 정도 채워짐 (medivance 1회 시연 가능 수준)
3. Test framework 결정 (vitest? jest? 또는 medivance 의 기존 test 방식 그대로)

### 5d-3 (TDD gate) 구현 위치

```
.lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh
```

- `on-response-completed.sh` 에 등록 — 4 detector helper 다음에 마지막
- code-change.ts 에 `--layer tdd` 옵션 추가 또는 별도 `tdd-cross-verify.ts`

### Fixture

```
.lazy-harness/triggers/fixtures/__tdd-cross-verify.ts
```

- 의도적 missing test 케이스
- 검증: gate 가 deny 반환 + 구조화 ask

## Why now

- ADR 0018 에서 약속만 함 — 명문화 미루면 또 잊혀짐
- 5c 작업 진행 중 — 5d 진입 시 동일 패턴으로 cross-verify 적용 가능
- 사용자 통찰 영구 기록 (Principle 0 + ADR 0010)

## Verification

- L0: ADR 작성됨
- L2 marker: 5d 진입 시 이 ADR 의 5 cross-check 명세 그대로 적용
- L4 사람 review: 5d 시작 전 사용자 confirm

## Consequences

### Positive

- TDD 의 framework 안 위치 영구 명문화
- 사용자 통찰 ("test 가 4 layer 와 부합한지") 정확 반영
- 5c (input) vs 5d (verify) 분리 명확
- Force gate (ADR 0019) 패턴 일관 적용

### Negative

- 5d 작업량 증가 (5 cross-check 모두 구현)
- Test framework 명세 의존성
- 사용자 ask 빈도 ↑ (5/5 까지 못 가면 매번 force gate)

### Mitigation

- 5d 진입 시 medivance 의 현재 test 패턴 분석 후 cross-check 룰 조정
- 한 번 답한 케이스는 영구 기록 (ADR 0019)
- 점진 도입 — 처음엔 "test 존재" 만 검사, 나중 4 cross-check 추가

## Related Future Work

- 5c-1~5c-5 완료
- 5d-3 (이 ADR) 구현 시 fixture + 8 통과 조건 패턴 (5c-1/5c-2 와 동일)
- ubiquitous-language.xml / SDD spec 파일 구체화

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh` — response.completed helper that invokes TDD cross-verify and surfaces a force gate.
  - `.lazy-harness/scripts/tdd-cross-verify.ts` — source/test existence checker and question writer.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — lifecycle helper loop that runs the TDD helper.
  - `.lazy-harness/triggers/fixtures/tdd-cross-verify/` — fixture files for missing/covered test cases.
  - `.lazy-harness/scripts/self-test.py` — TDD cross-verify and lifecycle integration coverage.
- Key symbols:
  - `matchingTests`, `verifyFile`, `buildQuestion`, `persistQuestions` (`tdd-cross-verify.ts`) — implement missing-test force gate mechanics.
  - `check_tdd_cross_verify` and `check_lifecycle_hook_integration` (`self-test.py`) — protect CLI and lifecycle helper behavior.
- Flow:
  1. response.completed payload contains edited source files.
  2. `check-tdd-cross-verify.sh` extracts source paths and calls `tdd-cross-verify.ts`.
  3. Missing matching tests produce `forceGate=true` and XML questions with A/B/C/D choices.
  4. The lifecycle hook injects the first helper output as a system reminder.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` protects TDD cross-verify CLI, lifecycle helper output, queue persistence, and shadow parity.
  - Keep this map `needs-review` because current implementation covers source↔test existence, not all five original DDD/SDD/BDD/SSOT cross-check dimensions.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0019-ambiguous-detection-force-gate.md`
  - Fixtures: `.lazy-harness/triggers/fixtures/tdd-cross-verify/`
- Machine index:
  - graph ids: `kg_adr0020_tdd_cross_verify_source`, `kg_adr0020_tdd_cross_verify_tests`
  - generated index key: `pending`
