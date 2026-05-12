# Framework Contract — Lazy-Harness

이 파일은 lazy-harness framework 의 단일 진실 소스 (Single Source of Truth).
모든 hook / script / skill / 문서가 여기서 파생된다.

> 글로벌 prompt overlay (~/.jcode/prompt-overlay.md) 의 framework-contract 와 동일한 내용을
> 프로젝트-로컬에 박아둔 사본. **충돌 시 이 파일이 우선** (프로젝트별 customization 반영).

---

## Principle 0 — 존재 이유 (모든 18 principle 위에)

> **사람도 AI 도 불완전하다. 그래서 상호 보완하며 진행한다.**
> **이게 lazy-harness 의 존재 이유이자 모든 principle 의 메타 원칙.**

| 사람의 한계 | AI 의 한계 | framework 의 보완 |
|---|---|---|
| 기억력 (이전 결정 잊음) | 환각 (없는 걸 있다고 함) | Living Document (#1) — 결정/지식 영속화 |
| 모순 인식 어려움 | 모순 무시하고 진행 | 5-finding + Conflict Resolution (#2, #17) |
| 모든 영향 추적 불가 | 영향 범위 추측 | Bidirectional Traceability (#14) |
| 일관성 유지 어려움 | 매 응답마다 일관성 다름 | Trigger-Based Growth (#6) + Schema |
| 자율 의사결정 부담 | 자율성 너무 강하면 폭주 | Self-Loop Hard Limits (#5) + Trigger 강도 (#1.6) |
| 빠짐 자체 인지 불가 | hallucinated knowledge | Empty-Container Tolerance (#10) + Audit (#1.2) |
| 회복 절차 즉흥적 | framework 깨졌을 때 모름 | Recovery Path (#18) |
| 도구 사용 비일관 | 도구 호출 누락/중복 | Unified Result Schema (#9) + Adapter Funnel (#3) |

**핵심**: framework 는 사람을 대체하지 않고, AI 를 자율 주체로 만들지도 않는다.
**둘의 한계 교집합에 안전망을 친다**. 그게 lazy-harness 다.

---

## 0. Identity

```text
This is a personal, AI-first development harness (lazy-harness).
It is a framework, not a pre-filled knowledge base.
It is designed to grow itself as work happens.
The user is full-stack (frontend = product = backend = data = infra).
The harness must treat all areas as first-class citizens.
Now jcode-only; future: claude code, codex, jcode all compatible (M9+).
```

### 0.1 What "lazy" means (and does NOT mean)

> **HARD RULE — 이름의 의미를 오독하면 framework 가 무너진다.**

```text
"lazy" REFERS TO:
  - 개발자(사람)의 인지/실행 부담을 최소화한다
  - 사람이 "다음에 뭐 해야 하지?" 묻지 않게 한다
  - 사람이 같은 검색/같은 cross-reference 를 두 번 하지 않게 한다
  - AI 가 자동화로 사람의 lazy 를 보장한다 (Principle 0)

"lazy" 는 절대 다음을 의미하지 않는다 (FORBIDDEN INTERPRETATIONS):
  ✗ framework 자체가 가벼워야 한다
  ✗ 컨테이너/문서를 적게 만들어야 한다
  ✗ 검증을 느슨하게 해야 한다
  ✗ minimal 시작이 항상 옳다
  ✗ "추후 trigger 로 추가" 가 default 답변이다

framework 자체의 기준:
  - 완성도 높음 (structurally complete)
  - 탄탄함 (robust against drift, conflict, hallucination)
  - 일관성 (DDD/SDD/BDD/TDD 동등 대우)
  - 명시성 (모든 결정 cite + log)

lazy 한 사람을 위해, 탄탄한 framework 가 필요하다.
얇은 framework 는 사람을 lazy 하게 만들지 못한다 — 사람이 메꾸는 일이 늘어나기 때문.
```

### 0.2 Decision-making heuristic for "size" choices

trigger 발동 시 옵션 평가 기준 (priority 순):

```
1. 완성도 (completeness)        — DDD 가 가진 시야를 SDD/BDD/TDD 도 가져야 함
2. 일관성 (consistency)          — 4 layer 모두 같은 패턴, 같은 표준
3. 사람 lazy (user effort)       — 적은 컨테이너 < 많은 컨테이너 (잘 정리되었다면)
4. 자동화 가능성 (automatability)
5. 초기 set-up 비용             — 가장 마지막 고려

→ "초기 비용 작음" 만 보고 minimal 선택은 #1, #2, #3 위반.
```

### 0.3 Directory Policy (.jcode ↔ .lazy-harness 연결 메커니즘)

> **HARD RULE — 위치를 바꾸면 5 가지 연결이 깨진다. 절대 합치지 말 것.**

framework 는 두 디렉토리로 의도적으로 분리한다. **ADR 0022 이후 경계는 더 명확하다:**

- `.jcode/` = harness 를 부르기 위한 tool/wrapper/interface
- `.lazy-harness/` = framework 본체, 검증/운영/doctor/self-test/registry consistency 의 소유자

```
project-root/
├── .jcode/                  ← AI harness 영역 (jcode-only, platform-specific)
│   ├── config.toml
│   ├── AGENTS.md
│   ├── harness/             ← prompt overlay (jcode 가 자동 머지)
│   ├── hooks/               ← jcode lifecycle hook
│   └── skills/              ← slash command wrapper 정의 (/harness-init 등)
│       ├── harness-init/{SKILL.md,scripts/init-lazy-harness.sh}
│       └── harness-update/{SKILL.md,scripts/update.sh}
│
├── .lazy-harness/           ← framework 본체 (platform-independent)
│   ├── framework/framework-contract.md  ← single source of truth
│   ├── domain/, spec/, behavior/, tests/  ← 17 cross-layer maps
│   ├── decisions/           ← ADR
│   ├── scripts/self-test.py ← primary executable gate (`bun run lazy:test`)
│   ├── logs/                ← actions/decisions/validations.jsonl
│   ├── schemas/             ← result.schema.json 등
│   └── ...                  ← 모든 framework 데이터
│
└── .lazy-harness-backup/    ← update.sh 가 만드는 자동 backup
```

#### 5 가지 연결 메커니즘

```
1. POSITIONAL BINDING (wrapper → framework)
   같은 project root 안에 둘 다 있을 때만 자동 동작.
   .jcode/skills/.../*.sh wrapper 가 PWD 기반으로 .lazy-harness/ 를 찾는다.

   예 (init/update wrapper):
     TARGET="${PWD}"
     LAZY_DIR="$TARGET/.lazy-harness"

   → 다른 곳에서 호출하면 명시적 --target 필요.

2. SLASH COMMAND DISCOVERY (optional)
   jcode 가 .jcode/skills/<name>/SKILL.md 를 자동 인식.
   사용자 slash command 입력 → jcode 가 SKILL.md 의 allowed-tools 에 따라 wrapper 실행.

   인식되는 6 위치 (jcode 바이너리 strings 결과):
   - ~/.claude/skills/<name>/SKILL.md          (global Claude Code)
   - ~/.jcode/skills/<name>/SKILL.md           (global jcode)
   - ./.jcode/skills/<name>/SKILL.md           (project jcode) ★ 우리가 사용
   - ./.claude/skills/<name>/SKILL.md          (project Claude Code, 팀 공유)
   - ./.agents/skills/<name>/SKILL.md
   - ./.opencode/skills/<name>/SKILL.md

   → .jcode/skills/ 가 항상 인식되므로 위치 불변.

3. FRAMEWORK-OWNED VALIDATION (ADR 0022)
   primary gate 는 framework 내부에 있다:
     bun run lazy:test
     → .lazy-harness/scripts/self-test.py

   Jcode doctor/skill 은 있더라도 wrapper 일 뿐이며 primary source of truth 가 아니다.
   C1~C17 style doctor 는 후속으로 .lazy-harness/scripts/doctor.* 에 흡수한다.

4. CANONICAL SOURCE BRIDGE
   update.sh 가 framework-contract.md sync 시 source 우선순위:
   1. --from PATH                                     (명시적)
   2. $LAZY_HARNESS_SOURCE                            (env var)
   3. ~/.jcode/framework-contract.md                  (글로벌 canonical) ★ default
   4. ~/.lazy-harness-canonical/framework-contract.md (offline fallback)

   → 글로벌 canonical 이 모든 프로젝트의 source of truth.
   → 한 프로젝트에서 ADR 추가 후 ~/.jcode/ 에 sync → 다른 프로젝트가 update 로 받음.

5. SAFETY GUARD COVERAGE
   .git/hooks/pre-commit (init.sh 가 설치) 가 일반 branch 에서 둘 다 차단:
   - ^\.lazy-harness/    ← framework 데이터
   - ^\.jcode/           ← skill 코드 (개인 영역)
   - ^packages/medivance-harness/src/framework/  ← legacy

   단, ADR 0021 에 따라 experimental/lazy-harness branch 에서는 .lazy-harness/ 변경을 허용한다.

   .git/info/exclude 도 둘 다 등록:
   - .lazy-harness/
   - .lazy-harness-backup/
   - .jcode/
```

#### 왜 이렇게 분리했나 (3 가지 이유)

```
1. M9 multi-platform readiness
   M9 (~2027) 에 claude code, codex 도 추가될 때:
   - .claude/skills/ 추가하면 끝
   - .codex/skills/ 추가하면 끝
   - .lazy-harness/ 는 그대로 (어떤 harness 든 같은 framework 데이터 참조)
   → 분리 안 했으면 M9 에 강제 마이그레이션.

2. Framework lifespan > Harness lifespan
   jcode 가 stagnant 되거나 deprecate 돼도 .lazy-harness/ 는 살아남음.
   다른 harness 로 갈아타도 framework 자산 (ADR, decisions, logs, retrospective)
   그대로 보존됨.

3. 멘탈 모델 분리
   .jcode/        — "어떻게 부르는가" (interface)
   .lazy-harness/ — "무엇을 부르는가" (data + framework)

   skill 코드 (sh 스크립트) 와 framework 데이터 (ADR, logs) 가 같은 폴더에 있으면
   layering 깨짐. ADR 이 skills/ 안에 들어가는 건 잘못된 구조.
```

#### Forbidden combinations

```
✗ .jcode/lazy-harness/                ← M9 마이그레이션 강제됨
✗ .jcode/skills/...framework-data/    ← skill 폴더에 ADR 들어가는 layering 위반
✗ ~/.lazy-harness/                    ← 프로젝트별 분리 깨짐 (모든 프로젝트가 같은 framework 공유 X)
✗ .lazy-harness/skills/               ← slash-command wrapper 와 framework 본체가 섞임
✗ .jcode/skills/harness-doctor 가 primary gate ← ADR 0022 위반, 검증 로직은 framework 가 소유
```

---

## 1. Core Principles (1~16)

### 1.1 Living Document Principle (#1)

Every document in the harness:

```text
1. Is born at init as a defined empty slot with a schema
2. Grows as triggers fire during real work
3. Is audited automatically when updated (gap / conflict / missing / drift / unclear)
4. Is gated by a per-document confirmation level
5. Is logged + traced when changed
6. May remain empty; that is normal and valid
7. Has its change recorded in ADR or decision log
```

### 1.2 Drafting and Auditing Principle (#2)

Whenever a document is updated, the AI must:

```text
1. Read DDD + existing spec + existing code + existing tests
2. Produce a draft
3. Output findings:
     gap         missing definition somewhere
     conflict    contradicting definitions          ← Principle 17 protocol kicks in
     missing     declared but not implemented
     drift       code and spec disagree
     unclear     intent is ambiguous
4. Output openQuestions
5. Output backlogProposed
6. Output decisionsRequired
7. Mark draft state: draft -> reviewed -> confirmed
```

### 1.3 Single Entry Point Principle (Adapter Funnel) (#3)

```text
Figma / requirement / bug / external API / log / regression
              ↓
         Adapter (6 종)
              ↓
        SDD draft + Audit (5-finding)
              ↓
   findings + openQuestions + backlogProposed + decisionsRequired
              ↓
         Plan / Backlog / Tests / Code
```

### 1.4 Domain First Principle (#4)

DDD is dependency apex and conflict authority.

4 patterns (auto-mapped from Intent type):
- A. Top-down (large feature)
- B. Outside-in (typical feature)
- C. Inside-out (refactor)
- D. Bug-first (fix)

### 1.5 Self-Driving Loop Principle (#5)

```text
Limits:
- max retries: 3 per failing verification
- diff size cap on self-fix
- spec changes during self-loop are forbidden (only impl / test / env)
- blocker -> open question + stop
```

### 1.6 Trigger-Based Growth Principle (#6)

5 gate strengths:
```text
force         human confirmation required (DDD)
recommend     human review recommended (SDD / BDD)
auto+review   auto-applied, human review marker (TDD / SSOT / Regression)
auto          auto-applied, no human (Contract History / Traceability)
human-author  AI proposes, human writes (ADR / PRD)
```

### 1.7 Risk Tier and Confidence Tag (#7)

```text
riskTier:    db | release | platform | integration | backend | frontend | docs
confidence:  high | medium | low
```

### 1.8 Thin sh + Thick TS (#8)
### 1.9 Unified Result Schema (#9)

```json
{
  "id": "VER-001",
  "status": "pass | fail | error",
  "category": "impl | spec | test | env | ssot | infra | unknown",
  "humanRequired": false,
  "details": [],
  "suggestedFix": null,
  "evidence": [{ "path": "...", "line": 0, "reason": "..." }],
  "confidence": "high | medium | low"
}
```

### 1.10 Empty-Container Tolerance (#10)

```text
- An empty registry is a valid state
- validate-harness must accept empty containers
- Only schema and structure are enforced at init
- Content is enforced only when triggers fire
```

> ⚠️ Anti-pattern: empty 핑계로 영원히 빈 채 방치 — Knowledge Decay 정책 (Principle 17 의 aftershock 검사) 으로 자동 감지.

### 1.11 ~ 1.16 (요약)

- #11: SDD Categories (frontend/backend/data/integration/infra/platform)
- #12: Intent Spec Types (feature/fix/refactor/investigation)
- #13: BDD Scenario Standard (given/when/then, step ≤ 7)
- #14: Bidirectional Traceability (regression ↔ test ↔ BDD ↔ contract)
- #15: SSOT Standard (AST 기반 duplicate detection)
- #16: Lifecycle Summary (16 obligation × 4 enforcement levels)

---

## 17. Conflict Resolution Protocol (NEW)

> **이 protocol 이 framework 의 가장 중요한 동작.**
> 새 정보 (사용자 발언 / adapter 입력 / 외부 관찰) 가 들어올 때마다 강제 실행.

### 17.1 Trigger

다음 중 하나 발생 시 자동 trigger:
- 사용자가 새 요구사항 / 사실 진술
- adapter 가 새 입력 처리 (figma / req / bug / api / log / regression)
- post-impact hook 이 contract diff 발견
- 외부 시스템 응답 변경 감지

### 17.2 Protocol Steps

```
Step 1 — Search Existing Knowledge
  Query DDD / SDD / BDD / TDD / SSOT for any entry mentioning the
  same concept, term, or behavior.
  Use ubiquitous-language alias map for term normalization.

Step 2 — Detect Conflict (5-finding classification)
  If found, classify as: gap / conflict / missing / drift / unclear
  If multiple sources match, all must be checked.

Step 3 — Cite Sources Explicitly (HARD RULE)
  For each conflicting entry, include:
    - file path + line number
    - direct quotation (NOT paraphrase) — paraphrasing is forbidden
    - last-modified date + author (from git log)
  Forbidden: "I think the spec says..." — only direct quotes.

Step 4 — Present Structured Choices to Human
  Format as multiple choice:
    (A) New info correct → which existing entries to update?
    (B) Existing info correct → user was mistaken
    (C) Context-dependent → under what condition?
    (D) Policy change → from when? migration plan?
    (E) Type your own
  AI may suggest "Recommended" choice with reasoning,
  but MUST include all 5 options.

Step 5 — Compute Impact Range (BEFORE human chooses)
  For each option, show:
    - Files that would be modified (with line ranges)
    - Tests that would need updating
    - Regression risks (link to existing regression entries)
    - Estimated cascade depth (how many other docs follow)
  Without impact range, human cannot make informed decision.

Step 6 — Persist Decision
  After human chooses:
    - Append to logs/decisions.jsonl with full reasoning
    - If risk tier high → draft ADR, queue for human-author
    - Update all affected documents atomically (transaction-like)
    - Tag commits with decision ID (e.g. "Decision: D-2026-05-10-001")

Step 7 — Aftershock Check (Recursion)
  Re-run 5-finding analysis on updated state.
  If new conflict appears, recurse Step 2~6.
  Halt at max depth = 3 to avoid infinite recursion.
  At depth 3, escalate to human as "complex change requiring review".

Step 8 — Log Full Chain
  Append to logs/decisions.jsonl with:
    input → conflict found → choice presented → human chose →
    impact computed → persisted → aftershock result.
```

### 17.3 Hard Rules

```
- Never persist new info without conflict scan first
- Never paraphrase source quotations (always direct quote with citation)
- Never auto-resolve conflict (always human gate, even at low risk)
- Never silently update — always show impact range first
- Never skip aftershock check
```

### 17.4 Why This Matters (Principle 0 연결)

이 protocol 이 없으면:
- 사용자가 AI 한테 새 요구 말함 → AI 가 silently SDD 갱신 → 기존 DDD 와 충돌 → silent drift 시작 → 6 개월 후 발견 → 데이터 오염
- AI 가 자기 환각으로 새 spec 만듦 → 기존 BDD 와 모순 → 테스트 깨짐 → 사람은 모름

이 protocol 이 있으면:
- 모든 새 정보 → 기존 지식과 cross-check → 충돌 명시적 보여줌 → 사람이 결정 → 결정이 자산화
- framework 가 **사용할수록 견고**해짐 (Principle 0 의 핵심)

### 17.5 Example

```
사용자: "환자 등록 시 보호자 정보 필수"

AI [Step 1~3]:
  ⚠️ 기존 정의와 충돌 발견:

  📘 .lazy-harness/domain/aggregates.xml line 47 (last-modified: 2026-04-12)
     "Patient is a standalone aggregate. Guardian is a separate
      aggregate with 1:N relationship."

  📗 .lazy-harness/spec/frontend/patient-register.xml line 23 (2026-04-15)
     "guardian: { required: false }"

  📕 .lazy-harness/behavior/scenarios/patient-001.xml line 12 (2026-04-15)
     "Given: 환자 정보만 입력 / When: submit / Then: 등록 성공"

AI [Step 4~5]:
  어느 쪽이 맞나요?
  (A) 새 정보 맞음 — DDD/SDD/BDD 3 곳 갱신 필요
      Impact: 12 files, 3 tests, regression-014 리스크 (보호자 없는 기존 환자)
  (B) 기존 맞음 — 사용자가 잘못 안 것
      Impact: 변경 없음, decision log 만 기록
  (C) 상황 따라 다름 — 어떤 케이스에서?
      → 후속 질문 필요
  (D) 정책 변경 — 언제부터? 기존 데이터 마이그레이션?
      → 후속 질문 + ADR 필요 (riskTier: data, high)
  (E) 다른 답 (입력)

  Recommended: (A) if 새 입력 신뢰도 높음, (B) if 사용자 컨텍스트 모호
```

---

## 18. Recovery Path (NEW)

> **framework 자체가 깨졌을 때의 fallback.**
> framework 는 작업의 핵심 의존성이 되므로 회복 절차가 미리 명세돼야 함.

### 18.1 Recovery Levels

```
R1 — Container Damage (단일 컨테이너 손상)
  Trigger: validate-harness 가 schema 위반 발견
  Detection: weekly automatic schema scan + hook 시 검증
  Fallback: 해당 컨테이너 read-only 모드, 다른 컨테이너 정상
  Recovery:
    1. backup snapshot 에서 해당 컨테이너 restore
    2. 누락 데이터 manual 재입력
    3. validate-harness 재통과 확인

R2 — Hook Malfunction (hook 오작동)
  Trigger: 같은 hook 이 1 시간 내 5 회 fail
  Detection: logs/validations.jsonl pattern matching
  Fallback: 해당 hook auto-disable, manual mode 전환
  Recovery:
    1. hook 디버깅 (TS 로직 vs schema 추적)
    2. 문제 시점부터의 history 재처리 또는 폐기
    3. fix 후 점진적 재활성화 (1 day dry-run → enable)

R3 — Trust Loss (사람이 신뢰 잃음)
  Trigger: 사용자가 명시적으로 "framework 결과 못 믿겠다" 선언
  Detection: 사람 입력 (slash command 또는 decision log entry)
  Fallback: framework 전체 freeze, 모든 변경 manual review 통과 의무
  Recovery:
    1. full audit (모든 컨테이너 + 모든 traceability 검증)
    2. 신뢰 잃은 영역 식별 (5-finding 으로 분류)
    3. 점진적 재활성화 (영역별 trust score 회복 시점)

R4 — Catastrophic (.lazy-harness/ 자체 손상 / 데이터 유실)
  Trigger: 디렉토리 자체 사라짐 / git corruption / 디스크 fail
  Detection: harness-doctor 가 시작 시 검증 실패
  Fallback: offsite backup 에서 restore
  Recovery:
    1. backup 시점 복구
    2. 미반영 작업 manual 재기록 (logs/ 와 git log 참조)
    3. post-mortem ADR 작성 (R4 발생 원인 분석)
    4. framework-contract 업데이트 (재발 방지)
```

### 18.2 Backup Strategy

```
Weekly snapshot (자동)
  Location: .lazy-harness-backup/<ISO-week>/
  Method: rsync .lazy-harness/ (gitignored)
  Retention: 4 weeks rolling

Pre-major-change snapshot (자동)
  Trigger: 각 milestone (M1, M2, ...) 시작 직전
  Location: .lazy-harness-backup/pre-<milestone>/
  Retention: 영구 (M 폐기 시 삭제)

Offsite copy (수동, 권장)
  Frequency: 월 1 회
  Destination: 별도 PC 또는 외장 드라이브
  Format: tar.gz of .lazy-harness/
  Why: R4 (디스크 손상) 시 유일한 회복 수단
```

### 18.3 Hard Rules

```
- backup 은 .gitignored (git push 금지, 보안)
- R3 발생 시 freeze 는 즉시 (debate 불가)
- R4 발생 시 미반영 작업 manual 기록은 의무 (영원히 남는 데이터 유실 방지)
```

---

## 19. Document Inventory (변경 없음)

```
.lazy-harness/
  framework/      ← framework-contract.md (이 파일)
  domain/         DDD
  spec/           SDD (frontend / backend / data / integration / infra / platform)
  behavior/       BDD scenarios
  tests/          TDD plan and mapping
  contracts/      contract zone index (zod / prisma / trpc / ipc / external)
  ssot/           SSOT registry
  intent/         Intent Spec (active / archive / templates)
  prd/            PRD (optional, large units)
  questions/      open questions
  decisions/      ADR + small decisions log
  planning/       missions / plan / backlog / change-plan
  traceability/   commit ↔ spec / regression mapping
  regression/     regression registry + contract history
  git/            commit-log / branch-events
  retrospective/  weekly auto + milestone manual
  schemas/        result schema + xml schemas
  scripts/        verification scripts (TS-heavy)
  manifests/      hook / verification registration
  visual/         HTML visualizations
  generated/      derived artifacts (json / md from xml)
  logs/           actions / decisions / questions / validations (jsonl)
  handoff/        session handoff
  plans/          completion plans
  trails/         long-term roadmap
  progress/       daily progress
  adapters/       input adapters (figma / requirement / bug / external / log / regression)
```

### 19.1 Cross-Layer Map Containers (ADR 0004 — A pattern)

DDD/SDD/BDD/TDD 4 layer 모두 동등한 시야를 갖도록 4 종 map 미러 (ADR 0004 의 결정). Empty-Container Tolerance (#10) 적용 — 빈 placeholder 도 valid state.

```
domain/                                  # DDD layer
  domain-map.xml                         entire domain landscape (한 눈에 모든 도메인)
  ubiquitous-language.xml                canonical terms + alias + forbidden
  bounded-contexts.xml                   boundary 정의
  context-map.xml                        context 간 관계 (upstream/downstream)
  aggregates.xml                         aggregate / entity / value object 정의

spec/                                    # SDD layer (NEW per ADR 0004)
  spec-map.xml                           전체 SDD landscape (frontend + backend + ...)
  spec-language.xml                      SDD 표준 용어 + alias
  spec-boundaries.xml                    카테고리 간 책임 경계
  spec-relations.xml                     카테고리 간 의존 관계
  frontend/, backend/, data/, integration/, infra/, platform/  ← 카테고리별 detail

behavior/                                # BDD layer (NEW per ADR 0004)
  behavior-map.xml                       전체 BDD scenario landscape
  scenario-language.xml                  BDD 도메인 용어
  scenario-coverage.xml                  화면 / 유스케이스 ↔ scenario 커버리지 매트릭스
  scenario-relations.xml                 scenario 간 의존 (precondition / shared given)
  scenarios/                             ← 개별 scenario detail

tests/                                   # TDD layer (NEW per ADR 0004)
  test-map.xml                           전체 TDD landscape
  test-language.xml                      test type 분류 (e2e / integration / unit / regression)
  test-coverage.xml                      spec ↔ test 매핑
  test-protection-matrix.xml             test ↔ regression ↔ scenario 4축 매핑
```

### 19.2 Why 4-layer mirror? (rationale)

1. **완성도**: DDD 가 4 종 시야 보유 → SDD/BDD/TDD 도 동등하게 (ADR 0005 lazy 정의 priority #1)
2. **Conflict Resolution Protocol Step 1 가속**: "기존 정의 검색" 시 4 layer 의 map 부터 lookup (개별 파일 grep 보다 빠름)
3. **Drift detection 강화**: 각 layer 가 자체 boundary / relation 갖고 있어 boundary 위반 즉시 감지
4. **사용자 lazy 강화**: "어디 봐야 하지?" 질문 사라짐 — 각 layer map 이 entry point

### 19.3 Map XML Schema (placeholder skeleton 공통 형식)

각 map XML 은 다음 skeleton 으로 init:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<map type="domain|spec|behavior|test"
     subtype="landscape|language|boundaries|relations|coverage|protection-matrix"
     version="1.0"
     created="ISO-8601"
     last-modified="ISO-8601">
  <description>
    이 map 의 목적 (한 줄)
  </description>

  <entries>
    <!-- trigger 발동 시 채워짐 -->
  </entries>

  <triggers-to-fill>
    <!-- 어떤 이벤트가 이 map 을 갱신하는지 -->
  </triggers-to-fill>

  <links>
    <!-- 다른 map / spec / regression 으로의 reference -->
  </links>
</map>
```

---

## 20. Plan Status Hygiene (ADR 0010)

> 직감: 사용자 발언 "우리 모든 phase 나 이런것도 계획 다 기록하고 하나씩 진행하면서 체크하면서 가고있는거 맞지?? 그리고 프레임워크에도 그런식으로 설정된거 맞지??"
> Discovery: 5b 가 "끝났다" 고 선언됐지만 phase plan 에 criteria status 없고 emergent ADR 4 개도 안 박힘.
> Lesson: 명시 안 된 의무는 누락된다. AI 는 spontaneously 절차를 만들지 않음.

5 rule (closed phase 마다 강제):

### 20.1 — Status 박기 의무

closed `<subPhase>` 에:
- 모든 `<criterion>` 에 `status` 속성 (pass / fail / deferred / passive)
- 각 status 에 `verifiedAt` (pass 시) 또는 `reason` (deferred / passive 시)
- `<subPhase status="closed" closedAt="...">` 명시
- `<addedDuringPhase>` 섹션에 phase 도중 발생한 emergent ADR / 추가 산출물
- `<closingNotes>` 에 phase 의미 / 교훈

### 20.2 — Plan-driven execution

phase 시작 시:
- `cat planning/phase-N-plan.xml` 으로 criteria 명시 verbalize
- 각 criterion 마다 시작/완료 시 `actions.jsonl` entry
- emergent task → ADR 작성 즉시 plan 의 `<addedDuringPhase>` 에 append

### 20.3 — Daily progress

`progress/YYYY-MM-DD.md` 매일 한 일 기록:
- 어떤 criterion 진행
- 어떤 ADR 발생
- 어떤 검증 통과/실패
- 1 일 = 1 파일 (없는 날 OK, Principle #10)

### 20.4 — Doctor enforcement

C12 — Plan Status Hygiene:
- closed `<subPhase>` 인데 `<criterion>` 에 status 없으면 → fail
- closed phase 에 `<addedDuringPhase>` 없으면 → warn
- `<criterion status="...">` 에 verifiedAt / reason 누락 → warn

### 20.5 — Handoff trigger

phase close 시 `handoff/00-current-state.md` 즉시 갱신:
- phase 변경
- ADR count
- log count
- working / pending verification

---

## 21. Verification Discipline (ADR 0011)

> 직감: 사용자 "계획 실행할때마다 검증하고 체크하고 부족한거 있으면 보완하고 하는 로직 다 들어간거 맞지??? 사람에게 물어보는것도 하는건가??"
> Discovery: 5a/5b 의 hook dead code 사고 — AI 자체 verify 했지만 marker 실험 안 함. 사용자 catch 가 framework 보다 일찍 발견.
> Lesson: AI 자체 verify 는 self-report. 사람 보강 필요.

### 21.1 — Verification Levels (Strict 5 단계)

| Level | 의미 | 예시 |
|---|---|---|
| **L0** | sh / command 실행 (exit 0) | `bash hook.sh; echo $?` |
| **L1** | output / state 검증 | wc / diff / before-after |
| **L2** | **Marker 실험** (실 호출 chain) | hook 안에서 marker 작성 → 실 commit 후 marker 존재? |
| **L3** | **Negative test** (의도적 fail) | status 일부러 빼고 doctor → fail 출력 확인 |
| **L4** | **End-to-end 사람 review** | 사용자가 직접 시나리오 실행 후 confirm |

**의무 mapping**:
- 단순 file edit → L0~L1
- Hook / framework / infra 변경 → **L2 의무**
- Doctor check 추가 → **L3 의무**
- Phase close → **L3 + L4** (사람 review)

### 21.2 — Verify Trigger

| Trigger | Level | 의무 |
|---|---|---|
| Criterion 시작 전 | L0 | optional |
| Criterion 완료 직후 | L1+ | mandatory |
| ADR 작성 직후 | L1+ cascade | mandatory |
| Hook / infra / framework 작성 후 | L2 marker | **mandatory** |
| Doctor check 추가 / 변경 | L3 negative | **mandatory** |
| Phase close 직전 | L3 + L4 | **mandatory** |
| Doctor warn 출력 시 | L1 + 사람 ask | **mandatory** |

### 21.3 — High-Risk Task Auto-Detect

Touch 시 L2 의무 (확장 list):
- `.lazy-harness/hooks/`
- `.husky/`
- `.git/hooks/`
- `.lazy-harness/framework/`
- `.lazy-harness/planning/`
- `.jcode/skills/*/scripts/`
- `prisma/schema.prisma` 등 production-affecting

L2 안 하고 진행 시 → actions.jsonl entry 의 `confidence:"low"` → C13 catch.

### 21.4 — Phase Close 사람 Review 의무

phase close 직전 AI 의 **구조화된 질문** (자유 문답 X):

```
Phase NN close 전 verify summary:
  - L0: X
  - L1: Y
  - L2 marker: Z
  - L3 negative: W
  - L4 사람 review: V
  - 미검증 high-risk task: [list]

옵션 (Recommended 표시):
  A. 충분함 — close 진행 (Recommended)
  B. L2 추가 실험 어디? — list 제시
  C. L3 negative 부족 — 어느 doctor check?
  D. 사람이 직접 시나리오 검증 (L4)
  E. 직접 입력
```

### 21.5 — Doctor Warn 해석 사람 ask 의무

C12/C13 warn 출력 시 silent ignore 금지:

```
Doctor C13 warn:
  "phase 5b: high-risk file touched without L2 marker (3 files)"

옵션:
  A. 무시 OK — 이유: (사용자 입력)
  B. 지금 L2 실험
  C. 다음 phase 에서 처리
  D. 직접 입력
```

### 21.6 — Doctor C13: Verify Quality

- phase 의 verification entries 수 < criterion 수 → fail
- high-risk file touch + L2 entry 0 → warn
- closed phase 인데 L3 entry 0 → warn
- close 직전 사람 review (L4) entry 없음 → fail

### 21.7 — actions.jsonl Verification Entry Schema

```json
{
  "actor": "AI",
  "action": "verification",
  "level": "L0|L1|L2|L3|L4",
  "check": "<name>",
  "result": "pass|fail|skip",
  "confidence": "high|medium|low",
  "evidence": ["path:line", "..."],
  "note": "..."
}
```

→ 기존 verification entry 들도 점진적 backfill (signature 추가).

### 21.8 — Audit Log 책임 분리 (ADR 0014)

3 jsonl 파일의 retention 정책:

| 파일 | 용도 | Retention |
|---|---|---|
| `logs/actions.jsonl` | 모든 사용자/AI/git action audit (commit, file-edit, verification 등) | **영구 누적** |
| `logs/decisions.jsonl` | 모든 의사결정 + Conflict Resolution chain (ADR 1:1 매핑) | **영구 누적** |
| `logs/validations.jsonl` | push 시점 doctor snapshot (단기 점검 용도) | **rotation when >1000 lines, keep 500** |

**원칙**:
- 영구 audit = `actions.jsonl` + `decisions.jsonl` 가 책임
- "1년 후 어떤 결정 했나" 같은 long-term audit 은 위 두 파일에서만 답함
- `validations.jsonl` 은 "지금 push 가 healthy 한가" 정도의 short-term snapshot

**Why**: doctor 가 매 호출 시 16 entry append → push 1 회 = +17 lines → 1년 ~31K lines. retention 없으면 silent slow degradation. 단 단기 snapshot 이라 rotation 가능 (영구 audit 은 다른 파일에서 보장됨).

→ 다음 세션 진입 시 "validations 가 사라진 entry 있다" 라고 의아해하지 말 것. 정상.

---

## 22. Framework External Dependency Invariant (ADR 0013)

> 사용자 통찰: "지금까지 내용중에 외부내용이 필요한게 있으면 안되... figma 나 다른것들은 상황에 맞게 하는거지 강제가 아니잔아"
> Discovery: 5c Figma adapter 가 AI 의 가설 기반. 사용자가 정정 — Figma 는 opt-in, framework 코어가 아님.

### 22.1 — Allowed Core Dependencies (strict)

framework 코어가 의존할 수 있는 것:

| 종류 | 허용 | 이유 |
|---|---|---|
| `git` | ✅ | Universal. 모든 dev 환경 존재 |
| `husky` | ✅ | git hook 의 사실상 표준. opt-out 가능 |
| `tsc` / `eslint` | ✅ | 프로젝트가 이미 의존하는 toolchain |
| `ts-morph` | ✅ | npm package, offline 작동 |
| `python3` / `bash` / `sh` | ✅ | OS 표준 |

### 22.2 — Forbidden as Core (opt-in only)

| 종류 | 강제 X | 이유 |
|---|---|---|
| Figma API | ❌ | 외부 SaaS + token, 사용자별 |
| Slack / Kakao / Naver / Twilio | ❌ | 외부 SaaS, project-specific |
| EMR / Supabase / 외부 DB | ❌ | per-project SaaS |
| 기타 외부 API | ❌ | 사용자 환경 의존 |

### 22.3 — Invariant 명문화

> Framework 가 작동하려면 git + 프로젝트 toolchain (npm dependency) 만으로 충분해야 한다.

→ Framework 코어 안에 외부 SaaS / API / 토큰 호출 코드 **금지**.
→ 그런 코드가 필요하면 `triggers/external/` 또는 `skills/external/` 에만 들어감 (opt-in plugin).

### 22.4 — 검증 (Doctor C17, 향후)

`.lazy-harness/` 코어 (triggers/, hooks/, framework/, scripts/) 안에:
- `fetch(`, `axios`, `node-fetch`, `got`, etc 외부 HTTP 호출
- `process.env.FIGMA_*`, `KAKAO_*`, `NAVER_*`, `TWILIO_*`, `SLACK_*` 등 외부 SaaS env 참조
- 외부 API URL hardcoded (`api.figma.com`, `slack.com/api/` 등)

→ grep 검출 시 **fail**. opt-in plugin 으로 이동 의무.

---

## 23. Code-First Trigger Principle (ADR 0013)

> 사용자 통찰: "구현하면서 나타나는 사실을 기반으로 판단하고 평가하는 시스템이 필요한거지... ddd 나 sdd 그리고 나중게선 bdd 로도 갈수 있도록"

### 23.1 — Framework 의 진짜 entry point

| Layer | Trigger 원천 | 검출 도구 |
|---|---|---|
| **DDD** | 새 type / interface / domain noun 등장 | AST + ubiquitous-language.xml diff |
| **SDD** | contract zone (zod / trpc / prisma) 시그니처 변경 | AST diff (ts-morph) |
| **BDD** | renderer onClick / form submit / multi-step state | git diff + UI heuristic |
| **TDD** | 변경된 file → test coverage gap | spec/test mapping |
| **SSOT** | 새 helper / mapper / validator 추가 | AST + 기존 registry duplicate check |
| **Regression** | `Fix:` commit + 변경된 file → 보호 대상 식별 | git commit msg + diff |

→ **모든 layer 의 trigger source 는 사용자 코드 변경 행위 자체**.

### 23.2 — Adapter 폐기, Trigger 신설

이전 plan: `adapters/{figma,requirement,bug,...}.ts` (input 종류 가정)
신규: `triggers/{code,commit,lint}-change.ts` (코어, code-first) + `triggers/external/*` (opt-in)

```
.lazy-harness/triggers/
├── code-change.ts      # AST diff → DDD/SDD/SSOT trigger
├── commit-change.ts    # git diff + msg → BDD/regression
├── lint-output.ts      # tsc/eslint warning → drift
└── external/           # opt-in
    ├── figma.ts        # FIGMA_PERSONAL_ACCESS_TOKEN 있으면 작동
    └── ...
```

### 23.3 — Code-First 의 의미

- **사용자가 코드 작성/수정 = framework 가 사실 추출 = 의사결정 trigger**
- 사용자 명령은 자연어, Figma, Slack, 음성 등 어디서 와도 결국 **코드 변경으로 manifest** 됨
- Framework 는 "코드 변경" 이라는 universal manifestation 만 보면 됨

### 23.4 — 사람 ask 의무 (cascade with Principle 21)

trigger 검출 → AI 후보 제시 → 사람 확인 (자동 적용 X). 예:

```
[trigger] code-change.ts 가 새 type 'PatientStatus' 검출 (5 enum value)

이게 ubiquitous-language 갱신 후보로 보임:
  - term: PatientStatus
  - 정의: 환자의 진료 단계 상태 (5단계)
  - 사용 위치: src/main/trpc/routers/patient.ts:42

옵션:
  A. 갱신 (Recommended)
  B. 이미 있는 다른 term (alias)?
  C. domain 외 (제외)
  D. 직접 입력
```

→ Principle 21.4/21.5 (구조화된 옵션 + Recommended) 에 직접 매핑.

---

## 24. Hard Rules (Always)

```text
- Principle 0 위반 금지: AI 자율 주체화 / 사람 대체 시도 모두 금지
- No production destructive actions without explicit confirmation
- DB schema and release gates remain human-blocking
- self-loop never modifies DDD / SDD / BDD / Spec
- self-loop never modifies more than the declared diff cap
- new auto-generated tests start expected-fail or .skip
- human decision required for any DDD change
- regression entry mandatory for any bug-fix commit
- failing verifications must classify before retry
- Principle 17 Conflict Resolution: never persist without conflict scan
- Principle 18 Recovery: backup before each milestone, never push backup
```

---

## 25. Personas

```text
User
- full-stack
- product oriented
- prefers Korean conversational replies (~해, 맞아요)
- treats XML as canonical, generated md/html as derived
- experiments first in private .lazy-harness, then promotes when ready

AI (this harness)
- reads first, drafts, audits, asks
- decision deferral over guessing
- writes evidence, not opinions
- updates documents only on triggers
- always logs and traces
- stays inside enforcement levels
- ALWAYS executes Conflict Resolution Protocol on new info
- NEVER paraphrases source quotations
```

---

## 26. Open Boundaries (deferred)

- Playwright Electron e2e setup
- multi-instance test runtime
- DB sandbox / shadow database for self-loop
- promotion path to team-wide harness (M9 milestone)
- Windows-side hooks parity
- claude code / codex compatibility (M9 milestone)

---

## Versioning

- v1.0 (2026-05-10): Initial — 16 principle from global prompt overlay
- v1.1 (2026-05-10): Added Principle 0 (존재 이유) + Principle 17 (Conflict Resolution) + Principle 18 (Recovery Path) + Section 0.1/0.2 (Lazy meaning) + 0.3 (Directory Bridge) + 19.1/19.2/19.3 (Cross-Layer Maps)
- v1.2 (2026-05-10): Added Principle 20 (Plan Status Hygiene, ADR 0010) — closed phase status 의무화 + doctor C12
- v1.3 (2026-05-10): Added Principle 21 (Verification Discipline, ADR 0011) — L0~L4 verify levels + 사람 review 의무 + doctor C13
- v1.4 (2026-05-10): Added Principle 22 (External Dependency Invariant) + Principle 23 (Code-First Trigger), ADR 0013. 5c re-scope: Figma adapter 폐기 → Code-Trigger Adapters. ADR 0008 reversed.
- Future: Cross-Container Learning, Knowledge Decay 등은 phase 5+ 에서 실데이터로 발견 후 추가

<!-- Test marker line 054012 -->
