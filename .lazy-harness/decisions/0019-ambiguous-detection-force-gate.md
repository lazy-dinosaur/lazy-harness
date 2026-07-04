# ADR 0019 — Ambiguous Detection → Force Gate Ask

- Status: Accepted
- Date: 2026-05-11
- Trigger: 사용자 catch — "이런 잘 모르겠는경우엔 gate 를 통해서 사람에게 물어보고 확정지을 수 있는거잔아 그지??"
- Discovered case: 5c-2 SDD detector 의 `Emr` 3글자 약어 — short noise filter 로 제외하면 false negative
- Related: ADR 0010 (Plan Status Hygiene), ADR 0011 (Verification Discipline), ADR 0018 (Cross-Layer Cascade)

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - a detector or classifier hits an ambiguous or low-confidence case
  - deciding whether to auto-apply, recommend, or stop for human confirmation
  - a term, length, layer, or alias classification is uncertain
- Must:
  - escalate ambiguous/low-confidence cases to a force gate with structured 3-5 options, a Recommended, and type-your-own
  - persist the user's decision so the same case is not re-asked
- Must not:
  - auto-decide or silently skip an ambiguous case via a simple length or whitelist filter
- Record completion:
  - ambiguous-case answers persist to ubiquitous-language, a forbidden list, or the decision log so detectors stop re-asking
- Related records:
  - `.lazy-harness/decisions/0038-requirements-first-change-gate.md`
  - `.lazy-harness/decisions/0010-plan-status-hygiene.md`
  - `.lazy-harness/decisions/0011-verification-discipline.md`
  - `.lazy-harness/decisions/0018-cross-layer-cascade.md`
  - `.lazy-harness/decisions/0020-tdd-cross-verify-gate-in-5d.md`
  - `.lazy-harness/ssot/rule-sources.md`

## Context

5c-2 SDD detector tuning 작업에서 발견:

```
ts-morph 검출: "Emr" (3글자)
- short noise (substring) 일 수도
- 약어 (EMR = Electronic Medical Record) 일 수도
- AI 가 확신 못 함
```

기존 detector 처리:
- 단순 길이 룰: 4글자 미만 제외 → false negative
- 또는 단순 substring 룰: PascalCase 합성어 아니면 제외 → false negative

→ **AI 가 단정 못 하는 경우, framework 가 자동 결정하면 안 됨**.

## Framework 안 기존 메커니즘 — Gate Strengths (Principle 1.6)

framework-contract.md 의 5 gate strength 가 이미 명시:

```
force         human confirmation required (DDD)
recommend     human review recommended (SDD / BDD)
auto+review   auto-applied, human review marker (TDD / SSOT / Regression)
auto          auto-applied, no human (Contract History / Traceability)
human-author  AI proposes, human writes (ADR / PRD)
```

그리고 Principle 1.7 — Risk Tier + Confidence:
```
confidence: high | medium | low
```

→ 이미 framework 안에 두 축 있음. 그러나 **두 축의 결합 룰** (어떤 confidence 면 어떤 gate?) 이 명시 안 됨.

## Decision

### Confidence × Gate 결합 룰

| Confidence | Gate | AI 행동 |
|---|---|---|
| **high** | auto+review | 자동 적용 + 사람 review 마커 |
| **medium** | recommend | 사람 review 권장 (warning, 강제 X) |
| **low** | **force** | **사람 confirmation 필수 — auto 적용 금지** |
| **ambiguous** (AI 가 confidence 도 못 매김) | **force + structured ask** | **A/B/C/D 옵션 ask 까지 가야 함** |

### Ambiguous 케이스 정의

다음 중 하나라도 해당:
1. 룰 매칭이 conflict (filter 룰로는 제외, 도메인 룰로는 포함)
2. Length / format edge case (3글자 약어 vs 2-3글자 noise)
3. 한 layer 인지 다른 layer 인지 불명확 (DDD vs SDD)
4. 새 term vs 기존 term alias 인지 모름

### Detector 의 의무

각 detector (5c-1~5c-5) 는:

1. **Confidence 정확히 매김** — high / medium / low / ambiguous 중 하나
2. **ambiguous 시 자동 처리 금지** — 단순 filter 로 제외 또는 등록 안 함
3. **Force gate ask 까지 progression** — Principle 17 의 구조화 옵션 (3~5 choice + Recommended + type-your-own)
4. **결정 영구 기록** — 사용자 답이 다음 detector 호출에서 같은 검출 재발 안 하게 (ubiquitous-language.xml 또는 forbidden list 또는 decision log)

### 예시 — Emr 케이스

```
검출: "Emr" (3글자, src/main/trpc/routers/emrRouter)

AI 분석:
- Length: 3글자 → short noise 후보
- Format: PascalCase 단일 단어 → 단일어 noun 후보
- Context: emrRouter 변수명 → tRPC procedure (SDD)
- ★ Confidence: ambiguous ★

Action:
→ force gate ask (auto 처리 금지)

Ask (Principle 17):
"5c-2 SDD detector: 'Emr' 검출. 다음 중 어느 것?
 A. EMR (Electronic Medical Record) 약어로 ubiquitous-language 등록 (Recommended)
 B. 다른 acronym 으로 등록 (어떤 풀네임?)
 C. 약어 아님, 직접 domain noun 으로 등록
 D. 진짜 noise, forbidden list 에 등록
 E. 다른 layer 로 routing (SSOT / 다른 detector)
 F. 직접 입력"

사용자 결정 → 영구 기록 → 다음 호출 시 재발 안 함
```

### 잘못된 패턴 (금지)

```
❌ if (name.length < 4) skip(); // 단순 filter 로 ambiguous 결정
❌ if (!seedNouns.includes(name)) skip(); // 화이트리스트만 봄
❌ auto-classify("Emr") = noise; // AI 가 단정
```

### 올바른 패턴 (필수)

```
✅ confidence = classify(name);
✅ if (confidence === 'ambiguous') return askForcedGate(...);
✅ if (confidence === 'low') return askWithRecommendation(...);
✅ if (confidence === 'medium') return suggestWithMarker(...);
✅ if (confidence === 'high') return autoApply(...);
```

## Why now

- 5c-2 의 Emr 케이스가 framework 안 첫 ambiguous 검증 사례
- 5c-3 (BDD), 5c-4 (SSOT) 진입 전에 일반 룰 명문화 안 하면 또 단순 filter 로 처리할 가능성
- Principle 0 (Human + AI complementarity) 의 본질 = "AI 가 모르면 사람 영역"

## Verification

- L0: ADR 작성됨
- L1: 5c-2 acronym tuning 시 ambiguous → force gate 패턴 적용 검증
- L2 marker: 5c-3/4/5 구현 시 confidence: 'ambiguous' 케이스 명시
- L3 negative: 일부러 Emr 같은 ambiguous case 만들고 detector 가 silent skip 안 하는지 검증
- L4 사람 review: 5c-2 tuning 완료 후 ask flow 시연

## Consequences

### Positive

- 사용자 catch 패턴이 framework 안 정식 메커니즘으로 흡수
- 5c-3/4/5 detector 가 일관된 ambiguous 처리 룰
- Principle 17 (structured ask) + Principle 1.6 (gate) + Principle 1.7 (confidence) 결합 완성
- false negative 사라짐 (AI 가 silent skip 안 함)

### Negative

- ask 횟수 증가 — 사용자 작업량 ↑
- 모든 detector 가 confidence: ambiguous 케이스 분류 로직 필요
- ask 의 reasoning 작성 비용 (Principle 17 의 구조화 옵션 정성껏)

### Mitigation

- ambiguous → 사용자 답 → 영구 기록 → 다음 호출 시 재발 안 함 (`alreadyAsked` registry)
- 사용자가 한 번 결정한 케이스는 자동 적용
- 누적된 답으로 detector 학습 가능 (예: "Emr 는 acronym" 답을 받았으면 다른 acronym 도 같은 패턴 ask)

## Related Future Work

- ADR 0020 (예정) — TDD cross-verify gate in 5d Interview Loop
- 5c-2 acronym tuning — Emr 케이스 force gate 적용
- ubiquitous-language.xml 안 acronym section 추가 (canonical + 풀네임)
- forbidden list registry (`/lazy-harness/domain/forbidden-terms.xml`?) — noise 영구 기록

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-option-gate-discipline.sh` — runtime guard that blocks tool execution or self-selected Recommended path after unresolved option gates.
  - `.lazy-harness/scripts/self-test.py` — option gate discipline fixture coverage.
  - `.lazy-harness/AGENTS.md` — active grammar for 3–5 option gates, Recommended marker, and type-your-own option.
  - `.lazy-harness/scripts/knowledge-intake.ts` — emits structured ask options for ambiguous knowledge candidates.
- Key symbols:
  - `check_option_gate_discipline_helper` (`self-test.py`) — validates plain gate pass, write/exec after gate block, self-selection block, and inferred-from-record pass.
  - `makeOptions` and `candidate` (`knowledge-intake.ts`) — build A/B/C/D/custom ask options for candidate classification.
- Flow:
  1. Ambiguous or unresolved decision presents a structured option gate.
  2. Option gate discipline helper detects if the same turn ran mutating tools or self-selected Recommended.
  3. Self-test protects that unresolved gates force a stop until user confirmation or record evidence exists.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` runs `check_option_gate_discipline_helper`.
  - Keep this map `needs-review` because the original detector-wide confidence taxonomy is broader than the implemented option-gate discipline helper and knowledge-intake ask surface.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0020-tdd-cross-verify-gate-in-5d.md`
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
- Machine index:
  - graph ids: `kg_adr0019_option_gate_discipline`, `kg_adr0019_knowledge_intake_ask`
  - generated index key: `pending`
