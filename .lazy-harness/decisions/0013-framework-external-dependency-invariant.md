# ADR 0013 — Framework External Dependency Invariant + 5c Re-scope

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: 사용자 발언 "지금까지 내용중에 외부내용이 필요한게 있으면 안되 husky 는 커밋을 통해 로그를 남기고 할 수 있으니까 그렇다 쳐도 말야 아 lint 까지는 가능하겠다 근데 뭐 figma 나 다른것들은 상황에 맞게 하는거지 강제가 아니잔아"

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - deciding whether framework core may depend on an external service, API, or SaaS
  - adding a trigger, adapter, or integration to framework core
  - a feature assumes a specific input channel (Figma, Slack, voice) as required
- Must:
  - keep framework core working with only git plus project toolchain, no required external SaaS
  - treat external API/DB/SaaS integrations as opt-in, project-specific plugins
  - derive triggers from code/commit/lint changes and user utterances, not channel-specific adapters
- Must not:
  - make framework core depend on or hardcode an external SaaS/network service
- Record completion:
  - new dependency or trigger decisions update this ADR and the external-dependency (C17) invariant guard
- Related records:
  - `.lazy-harness/decisions/0017-user-input-as-universal-trigger.md`
  - `.lazy-harness/decisions/0008-ast-contract-diff-deferred.md`

## Discovery

이전 plan 의 5c (Figma adapter) 가 **AI 의 가설 기반**이었음:
- "사용자가 Figma 설계 → 즉시 코드 cascade 하길 원할 것"
- "Figma 가 input 의 대표 사례"

사용자가 정정:
- 진짜 needs = **사용자가 코드 작성/수정/리뷰할 때 그 과정에서 사실 추출 → 의사결정 트리거**
- Figma 는 **상황별 opt-in**, framework 코어가 아님
- 명령 source 는 Figma 일 수도, 자연어일 수도, Slack 일 수도, 음성일 수도

→ Framework 가 input 종류를 가정하면 안 됨.

## Decision

### 22. Framework External Dependency Invariant (Principle 22 신설)

framework 코어가 의존할 수 있는 것 strict list:

| 종류 | 허용? | 이유 |
|---|---|---|
| `git` | ✅ Universal | 모든 dev 환경에 존재. commit / hook / diff |
| `husky` | ✅ npm 표준 | git hook 의 사실상 표준. opt-out 가능 |
| `tsc` / `eslint` | ✅ 프로젝트 dependency | 이미 프로젝트가 의존하는 toolchain |
| `ts-morph` (AST) | ✅ npm package | 프로젝트 dependency 로 추가. offline 작동 |
| `python3` | ✅ universal | linux/mac/windows 표준. JSON encoding 등 |
| `bash` / `sh` | ✅ universal | hook 실행 환경 |
| **Figma API** | ❌ 강제 X (opt-in) | 외부 SaaS + token. Figma 안 쓰는 user 차단 |
| **Slack / Kakao / Naver / Twilio** | ❌ 강제 X (opt-in) | 외부 SaaS, project-specific |
| **EMR connector / Supabase** | ❌ 강제 X (opt-in) | per-project SaaS |
| 기타 외부 API / DB / SaaS | ❌ 강제 X (opt-in) | 사용자 선택 |

**Invariant**:
> framework 가 작동하려면 git + 프로젝트 toolchain (npm dependency) 만으로 충분해야 한다.

**Rationale**:
- framework 가 외부 SaaS 에 의존하면 (1) 사용자 lock-in, (2) network 단절 시 lazy 도 멈춤, (3) project-specific 가정 강요.
- husky / lint / AST 까지는 "사용자가 어차피 쓰는 것" — framework 가 추가로 강요 안 함.

### 23. 5c Re-scope (Code-Trigger Adapters)

이전: `5c — Figma Adapter` (폐기)
신규: `5c — Code-Trigger Adapters`

```
.lazy-harness/triggers/
├── code-change.ts      # AST diff → DDD term / SDD contract / SSOT duplicate
├── commit-change.ts    # git diff + msg → BDD scenario / regression candidate
└── lint-output.ts      # tsc / eslint warning → drift candidate
```

→ **Universal trigger source = 사용자 발화 + 코드 변경**. external adapter 디렉토리 0.

| Sub-phase | 내용 | 외부 의존 |
|---|---|---|
| **5c-1** | git diff + AST → DDD term detector (ubiquitous-language 후보) | git + ts-morph |
| **5c-2** | AST contract diff → SDD trigger (옛 5b-2a 통합 — defer 해제) | ts-morph |
| **5c-3** | git diff + UI heuristic → BDD scenario 후보 | git + AST |
| **5c-4** | AST → SSOT duplicate detector | ts-morph |
| **5c-5** | lint/typecheck output → drift candidate | tsc/eslint |

### 사용자 발화도 trigger source (ADR 0017 로 명시화)

사용자가 "Figma 의 이 화면 만들어줘" / "처방전에 환자명 추가" / "@figma.com/.../xyz 참고" 같이 자연어로 줘도 `response.completed` hook 의 `last_user_message` payload + `recent_tool_calls` (WebFetch/Read 등) 안으로 자연스럽게 잡힘. **별도 external adapter 디렉토리 불필요**.

### 5b-2a → 5c-2 elevate

이전 ADR 0008 결정 ("ts-morph 1주 측정 후 채택") **reverse**:
- Reason: 사용자 통찰로 needs 명확. AST 가 5c 의 prerequisite. 1주 측정 안 기다려도 됨.
- 새 status: `5b-2a` closed-redirected, `5c-2` 가 후속.

### 옛 adapters/ directory

이전 plan: `adapters/{figma,requirement,bug,external-api,log,regression}.ts` (강제)
신규: 폐기. `triggers/{code,commit,lint}-change.ts` (코어) 만. external 디렉토리 없음.

기존 `.lazy-harness/adapters/README.md` → `triggers/README.md` 로 rename + 내용 갱신 (다음 cascade 작업).

## Cascade

| 파일 | 변경 |
|---|---|
| `framework/framework-contract.md` | Principle 22 (External Dependency Invariant) + Principle 23 (Code-First Trigger) 추가, v1.3 → v1.4 |
| `planning/phase-5-plan.xml` | 5c 재작성, 5b-2a closed-redirected, 5c-1~5c-5 (코어) + 5c-6~5c-8 (시연/Doctor) |
| `.lazy-harness/adapters/` | rename → `.lazy-harness/triggers/` (다음 phase 시작 시) |
| `decisions/0008-ast-contract-diff-deferred.md` | Status: Reversed by ADR 0013 추가 |
| `manifests/skills.xml` | Figma adapter skill 제거 |
| Doctor | C17 (5c-8) — external SaaS reference grep |

## Consequences

### Positive
- Framework 가 진짜로 portable (어떤 프로젝트에 init 해도 작동)
- 5c 의 진짜 needs 명확 (사용자 코드 변경 = 모든 layer trigger 의 source)
- AST 채택 즉시 — DDD/SDD/BDD 모두 즉시 시작 가능
- Opt-in 외부 어댑터는 framework 외 plugin pattern 으로 자연스럽게

### Negative
- 5c scope 가 커짐 (5 sub-phase)
- ts-morph 학습 필요 (1주 측정 단계 skip)
- 옛 ADR 0008 reverse → cascade 정리 필요

### Risk
- AST analyzer 가 false positive 많으면 사용자 fatigue
- "DDD term 후보" 검출이 noise 되면 사용자 ignore
- **Mitigation**: 21.4 (사람 ask 의무) + 21.5 (silent ignore 금지) 가 이미 framework 에 있음. 후보 제시 + 사람 확인 의무.

## Why this matters

> Principle 0 의 "사람-AI 상호보완" 의 진짜 적용:
> AI 가 가정한 input source (Figma) 가 사용자 needs 와 mismatch 였음.
> 사용자가 catch 함 (또 catch 패턴 9/9).
> Framework 가 이 정정을 invariant 로 박음 = 다음 가설 등장 시에도 같은 catch 가능.

핵심 깨달음:
- Framework 는 **사용자가 코드를 작성하면서 발생하는 사실** 만 입력으로 받음
- 외부 SaaS / API 는 **상황별 opt-in** 으로 분리
- Code-First 가 framework 의 진짜 entry point

## References

- ADR 0008 (AST contract diff deferred) — 이 결정으로 reversed
- 사용자 통찰: "구현하면서 나타나는 사실을 기반으로 판단하고 평가하는 시스템"
- Principle 0 (사람-AI 상호보완)
- Principle 1.6 (Trigger-Based Growth) — 이번에 trigger source 가 명확화
- Principle 1.8 (Thin sh + Thick TS) — 5c 부터 ts-morph 본격 활용

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/doctor.py` — C17 external dependency invariant scanner.
  - `.lazy-harness/scripts/self-test.py` — negative fixture for forbidden external SaaS call.
  - `.lazy-harness/triggers/code-change.ts` and trigger source files — code-first trigger implementation.
- Key symbols:
  - `check_external_dependency_invariant` (`doctor.py`) — scans active code for forbidden external SaaS/network patterns.
  - `check_doctor_c17_negative` (`self-test.py`) — validates C17 fails on a negative fixture.
- Flow:
  1. Framework core external dependency invariant is enforced by doctor D06/C17 against active code roots.
  2. Self-test injects a forbidden fixture and verifies doctor fails for the right reason.
  3. Code-trigger direction is represented by `.lazy-harness/triggers/`.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` protects C17 negative fixture and runtime host/product hardcoding guard.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0017-user-input-as-universal-trigger.md`
- Machine index:
  - graph ids: `kg_adr0013_external_dependency_doctor`, `kg_adr0013_c17_negative_test`
  - generated index key: `pending`
