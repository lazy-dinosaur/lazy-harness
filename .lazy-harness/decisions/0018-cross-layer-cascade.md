# ADR 0018 — Cross-Layer Cascade (4 Layer Detector 가 서로 catch)

- Status: Accepted
- Date: 2026-05-11
- Trigger: 사용자 catch — "이게 좀 되게 유기적으로 유동적으로 같이 들어가야해 중요한건 어떤걸 요구할때 ddd 와 sdd 맵이 만들어지는거겠지?? 긜고 그 스펙과 ddd 를 통해서 bdd 시나리오도 알수있고 그러면 이거로 빠진걸 알수도 있고 tdd 도 알수도 있고 아닌가??"
- Related: ADR 0013 (Code-First Trigger), ADR 0016 (Lifecycle Hook Strategy), ADR 0017 (User Input as Universal Trigger)

## Context

5c-1 (DDD detector) 완성 후 4 detector (DDD/SDD/BDD/SSOT) 의 관계를 어떻게 설계할지 논의 중 사용자 통찰:

> "한 layer 가 다른 layer 의 누락을 발견할 수 있다"

기존 5c 설계:
- 5c-1: DDD detector — 독립
- 5c-2: SDD detector — 독립
- 5c-3: BDD detector — 독립
- 5c-4: SSOT detector — 독립

→ **각 detector 가 isolated**. 한 detector 가 다른 layer 의 누락 못 봄.

## Decision

**4 layer detector 는 서로 cross-reference**. 한 layer 의 결과가 다른 layer 의 누락을 detect.

### Cross-reference 매트릭스

| 출발 layer | 검사 대상 | Cross-check 내용 |
|---|---|---|
| **DDD** detector 결과 | SDD spec | DDD term 이 SDD contract 안 type 으로 등장? |
| **DDD** detector 결과 | BDD scenario | DDD term 이 scenario 안 noun 으로 사용? |
| **SDD** detector 결과 | DDD ubiquitous-language | SDD contract type 이 DDD term 으로 등록됨? |
| **SDD** detector 결과 | BDD scenario | SDD endpoint 가 scenario verb 와 매칭? |
| **BDD** detector 결과 | DDD ubiquitous-language | scenario 의 noun 들이 DDD 안에 등록? |
| **BDD** detector 결과 | SDD contract | scenario 의 verb (then 자동완성 list) 가 SDD endpoint 와 매칭? |
| **SSOT** detector 결과 | 4 layer 전체 | helper 가 어느 domain context 에 속함? |

→ **유기적 cross-route**. 한 layer 누락이 자동 catch.

### 예시 cascade

```
사용자 발화: "환자 검색 자동완성 추가"

━━━ Phase 1: 발화 분석 (4 detector 병렬) ━━━

DDD detector (last_user_message + 새 type 검출):
  ✅ 'Patient' (이미 ubiquitous-language 안)
  ⚠ '자동완성' (새 term — 등록 후보)

SDD detector (contract zone):
  ✅ searchPatients(query) → Patient[] (이미 있음)
  ⚠ 'autocomplete' endpoint 없음 (BDD scenario 가 요구하면 후보)

BDD detector (자연어 flow 분석):
  scenario 후보:
    given 검색창 focus
    when 환자명 typing
    then 자동완성 list 보임

━━━ Phase 2: Cross-reference ★ 핵심 ★ ━━━

BDD ↔ SDD: scenario 의 'then 자동완성 list' → SDD endpoint 'autocomplete' 누락 발견
  → "SDD spec 에 autocomplete endpoint 추가 후보"

BDD ↔ DDD: scenario 의 '자동완성' → DDD ubiquitous-language 미등록 발견
  → "DDD term '자동완성' 등록 후보"

SDD ↔ DDD: SDD 'searchPatients' → DDD 'Patient' 정합 ✅

━━━ Phase 3: 통합 ask (사용자에게 한번에) ━━━

옵션:
A. '자동완성' DDD term 등록 + SDD endpoint 추가 + BDD scenario 등록 [전부]
B. DDD/SDD 만 등록 (BDD 는 나중에)
C. BDD scenario 만 등록 (DDD/SDD 는 implementation 시점에)
D. 직접 입력 / skip
```

### 5c criteria 재정의

| Sub-criterion | 내용 |
|---|---|
| 5c-1 | DDD detector (완료) |
| **5c-2** | **SDD detector + DDD reference check** (DDD term 이 SDD type 으로 사용?) |
| **5c-3** | **BDD detector** (last_user_message 자연어 우선 + 코드 UI heuristic 보조) **+ DDD/SDD reference check** |
| 5c-4 | SSOT detector |
| **5c-5 (신규)** | **Cross-layer consistency map** — 4 detector 결과 통합, gap detect (BDD ↔ SDD missing endpoint 등) |
| 5c-6 | lint drift (옛 5c-5) |
| 5c-7 | 구조화 옵션 (옛 5c-6) |
| 5c-8 | E2E 시연 — 4 detector + cross-ref (옛 5c-7) |
| 5c-9 | Doctor C17 (옛 5c-8) |

### TDD 의 위치

TDD detector 는 **5c 안에 없음**. 이유:

- 사용자 통찰: "tdd 의 경우엔 전부 다 개발이 완료 되고 나서 test 하면서 코드가 붙을꺼고"
- TDD = output phase (verify gate), 다른 detector = input/development phase
- BDD scenario / DDD term / SDD contract 가 모두 채워진 후 → test 가 그것들과 일치 검증

→ **TDD 는 5d Interview Loop 안의 cross-verify gate** 로 위치. ADR 0019 (예정) 에서 명문화.

### BDD trigger 의 주된 source

기존: 코드 안 UI heuristic (onClick / form submit / multi-step state)
신규: **사용자 발화 (`last_user_message`) 의 자연어 flow 분석이 PRIMARY**

이유:
- BDD scenario 의 raw material 은 자연어 요구사항
- 코드 heuristic 은 추측 (false positive 높음)
- 사용자가 "의사가 ~ 하면 ~ 보임" 같은 표현 → 직접 given/when/then draft

→ 5c-3 의 명세 갱신: PRIMARY = 자연어, SECONDARY = 코드 heuristic.

### 2026-05-21 amendment — raw BDD 후보는 ask 가 아니라 candidate capture

BDD trigger 가 발견하는 raw scenario / cross-ref gap 은 제품 코드 변경 승인이나 canonical record mutation 이 아니다. 따라서 response.completed hook 에서 반복 STOP / A-B-C-D option gate 로 사용자 흐름을 막지 않는다. Hook 은 BDD 후보를 `.lazy-harness/knowledge/candidates.jsonl` 에 dedupe 저장하고 조용히 종료한다. `behavior/`, `domain/`, `spec/` 로 승격하는 작업은 별도 사용자 확인을 받은 뒤 수행한다.

## Why now

1. 사용자 통찰이 framework 의 **Principle 1.4 (Domain First) 의 본질** 을 더 강하게 표현 — DDD 가 apex 라는 건 다른 layer 도 DDD 참조해야 한다는 의미. cross-reference 가 그 메커니즘.
2. 4 detector 가 isolated 면 framework self-correcting 의 **50% 가치** (각 detector 의 단편 정보만). cross-ref 가 있어야 100%.
3. 5c-2 진입 전에 명문화 안 하면 또 isolated detector 됨.

## Verification

- L0: ADR 작성됨
- L1: 5c criteria 재정의 (plan 갱신)
- L2 marker: 5c-2/3/4/5 구현 시 각 detector 의 결과가 다른 layer reference 검사 코드 포함
- L3 negative: 한 layer 에 missing 만들고 다른 layer detector 가 catch 하는지 검증
- L4 사람 review: 5c-5 cross-layer map 구현 후 사용자에게 시연

## Consequences

### Positive

- Framework self-correcting 진정한 의미 — 한 layer 누락이 다른 layer 가 catch
- 사용자 통찰 ("유기적 유동적 cascade") 정확 반영
- TDD 의 위치 명확 (5c 안 아닌 5d gate)
- 통합 ask — 사용자가 한 결정으로 4 layer 갱신 가능

### Negative

- 5c 작업량 증가 — 각 detector 가 다른 layer reference 검사 코드 추가
- Cross-ref map (5c-5) 신규 — 4 detector 결과 통합 로직
- BDD detector 의 자연어 분석 난이도 ↑ (LLM 없이 heuristic + structural ask 로 어디까지 가능?)

### Risk

- BDD 자연어 분석이 unreliable 하면 framework 의 일관성 약화
- → 5c-3 구현 시 NLP 정확도 측정 + fallback "사용자가 직접 입력" 옵션 강화

## Related Future Work

- ADR 0019 (예정) — TDD gate in 5d Interview Loop (cross-verify)
- 5c-5 Cross-layer consistency map 설계 spec
- 5c-3 BDD detector 자연어 분석 구체화
