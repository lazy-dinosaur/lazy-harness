# Current State (Honest Audit) — 2026-05-10 (5b CLOSED + Oracle/Sisyphus Audit)

이 파일은 **새 세션이 시작할 때 가장 먼저 읽어야 하는 파일**.

> 이전 버전 (5a 진입 직전 상태) 은 Section 9 에 archive 됨.

## ⚡ TL;DR for next session

| 항목 | 상태 |
|---|---|
| **Lazy-harness phase** | **5b CLOSED** + Oracle/Sisyphus audit hardening (2026-05-10) |
| **Working skills** | `harness-init` / `harness-doctor` / `harness-update` |
| **Working hooks (5b)** | `pre-commit-guard.sh` / `post-commit.sh` / `pre-push.sh` / `weekly-snapshot.sh` |
| **Husky integration** | ✅ `.husky/<3 hooks>` chain → `.lazy-harness/hooks/*.sh`, **commit b95dd3f7 medivance origin push 완료** (ADR 0009 enforced) |
| **Framework contract** | **v1.4**, **975 lines**, **23 principle sections** (incl. 21.8 audit log retention split) |
| **Cross-layer maps** | 17 XML placeholders |
| **ADRs** | **20** (0001~0020) |
| **Decisions logged** | **21** entries |
| **Actions logged** | **110+** entries (3 invalid → fixed by Oracle/Sisyphus) (3 invalid lines fixed by Oracle/Sisyphus audit) |
| **Doctor checks** | **C1~C16** (16 total) — 12 pass, 1 warn, 2 skip, 1 fail (C15 untracked) |
| **Skills manifest** | 11 skills declared |
| **Plan Status Hygiene** | ✅ Principle #20 — closed phase status 박음 + C12 자동 검증 |
| **Verification Discipline** | ✅ Principle #21 — L0~L4 + 사람 ask 4 시점 + C13 |
| **Daily progress** | ✅ `progress/2026-05-10.md` 작성 (첫 entry) |
| **AGENTS.md auto-injection** | ⚠ ADR 0007 — content **stale** (9 checks, `.git/hooks/` 표기, ADR 0006 까지만) |
| **R2 fallback** | ✅ `.hooks-disabled` lock |
| **fork bomb check** | ✅ 옛 verify-test-harness.sh 등 0 존재, 우리 hook timeout 5s 내 종료, no cycle |
| **git tracked under .lazy-harness/ + .jcode/** | 0 |
| **git tracked under .husky/<3 hooks>** | ✅ YES (commit `b95dd3f7` pushed, ADR 0009 enforced) |
| **Next phase** | 5c-3 BDD detector (자연어 분석 PRIMARY, code heuristic 보조) |
| **Pending verification** | (1) `/harness-init` jcode 노출, (2) 1주 실측 |

## 🎯 Principle 0 reminder

사람도 AI 도 불완전하다. 그래서 상호 보완하며 진행한다. **이게 모든 19 principle 위에 있는 메타 원칙.**

### 사람-AI 한계 매핑

| 사람의 한계 | AI 의 한계 | Framework 의 보완 |
|---|---|---|
| 기억력 (이전 결정 잊음) | 환각 (없는 걸 있다고 함) | Living Document (#1) — 결정/지식 영속화 |
| 모순 인식 어려움 | 모순 무시하고 진행 | 5-finding + Conflict Resolution (#17) |
| 모든 영향 추적 불가 | 영향 범위 추측 | Bidirectional Traceability (#14) |
| 일관성 유지 어려움 | 매 응답마다 일관성 다름 | Trigger-Based Growth (#6) + Schema |
| 자율적 의사결정 부담 | 자율성 너무 강하면 폭주 | Self-Loop Hard Limits (#5) |
| 빠짐 자체 인지 불가 | hallucinated knowledge | Empty-Container Tolerance (#10) + Audit (#1.2) |
| 새로운 정보의 영향 미예측 | 기존 spec 무시 새 spec 생성 | **Conflict Resolution Protocol (#17) — 직접 인용 강제** |
| 백업 안 함 | catastrophic 실수 | **Recovery Path (#18) — 자동 backup + auto-rollback** |
| 이름의 의미 오독 | 같은 단어 다른 뜻 사용 | **Section 0.1 — 정의 명시 (lazy 정의)** |

## 📁 File system reality

### Working skill scripts

```
.jcode/skills/harness-init/SKILL.md          (118 lines, YAML frontmatter)
.jcode/skills/harness-init/scripts/init-lazy-harness.sh   (524 lines, 30 containers + 17 maps + 2 schemas + safety guards)
.jcode/skills/harness-doctor/SKILL.md        (85 lines)
.jcode/skills/harness-doctor/scripts/doctor.sh            (410 lines, 9 check categories)
.jcode/skills/harness-update/SKILL.md        (103 lines)
.jcode/skills/harness-update/scripts/update.sh            (372 lines, dry-run/rollback/auto-rollback)
```

### Lazy-harness containers (40 directories under .lazy-harness/)

```
framework/  domain/  spec/{frontend,backend,data,integration,infra,platform}/  behavior/{scenarios}/
tests/  contracts/  ssot/  intent/{active,archive,templates}/  prd/  questions/  decisions/
planning/  traceability/  regression/  git/  retrospective/{metrics,cycles}/  schemas/
scripts/  manifests/  visual/  generated/  logs/  handoff/  plans/  trails/  progress/  adapters/  hooks/
```

### Core docs (alive)

| File | Purpose |
|---|---|
| `framework/framework-contract.md` | 975 lines — single source of truth for framework contract v1.4 (principles + hard rules/personas/open boundaries) |
| `handoff/00-current-state.md` | THIS file — what next session reads first |
| `trails/01-long-term-roadmap.xml` | M0~M10 milestones to 2027-05 |
| `planning/phase-5-plan.xml` | Phase 5a~5e success criteria |
| `retrospective/metrics/completeness-scorecard.xml` | tsq/DDD/BDD/C4/OTel comparison |
| `retrospective/cycles/5a-closing.md` | This phase's full retrospective |
| `decisions/0001-core-philosophy.md` | Principle 0 ADR |
| `decisions/0002-conflict-resolution-protocol.md` | Principle 17 ADR |
| `decisions/0003-recovery-path.md` | Principle 18 ADR |
| `decisions/0004-cross-layer-maps.md` | Cross-layer maps decision (D-001) |
| `decisions/0005-meaning-of-lazy.md` | Defines what "lazy" means (D-002) |
| `logs/decisions.jsonl` | 2 entries with full Step 1-8 Conflict Resolution trace |
| `logs/actions.jsonl` | 31 entries — full 5a phase action trace |
| `logs/validations.jsonl` | doctor result snapshots (Unified Result Schema) |

### Cross-layer maps (17 XML placeholders, all empty per Principle #10)

- DDD: domain-map / ubiquitous-language / bounded-contexts / context-map / aggregates
- SDD: spec-map / spec-language / spec-boundaries / spec-relations
- BDD: behavior-map / scenario-language / scenario-coverage / scenario-relations
- TDD: test-map / test-language / test-coverage / test-protection-matrix

### Schemas

- `schemas/result.schema.json` — Unified Result Schema (Principle #9)
- `schemas/decision.schema.json` — Decision Log entry (Principle #17)

### Visual

- `visual/roadmap.html` — dark-themed M0~M10 timeline (auto-opens in browser)

## 🚦 Safety state

```
✓ .lazy-harness/         in .git/info/exclude
✓ .lazy-harness-backup/  in .git/info/exclude (auto-added by update.sh)
✓ .jcode/                in .git/info/exclude
✓ packages/medivance-harness/src/framework/  in .git/info/exclude (legacy)
✓ .git/hooks/pre-commit  installed (lazy-harness + .jcode + framework guard)
✓ git ls-files | grep '^\.lazy-harness' = 0
```

## 🔮 What's NOT yet done (5b+)

### 5b: Lifecycle Hooks
- post-commit hook → logs/actions.jsonl auto-append
- post-impact hook → ts-morph AST diff → contract-history.xml
- pre-push hook → unified result schema output
- regression auto-registration on bug-fix commits
- weekly snapshot backup
- 1-week real-use measurement on medivance dev-ian

### 5c: Adapters
- adapters/figma.ts (FIGMA_PERSONAL_ACCESS_TOKEN)
- component tree → SDD draft auto-generation
- 5-finding classification output
- Conflict Resolution Protocol on real Figma input

### 5d: Self-Driving Loop
- questions/open.xml auto-update
- aftershock recursion (max depth 3)
- decisions/ auto-promotion to ADR

### 5e: TS Migration (Thin sh + Thick TS, Principle #8)
- Move heavy logic from sh to TS
- AST analysis (ts-morph)
- Cross-platform support (Windows ready)

### M3+: Recovery / Backup full automation
- Weekly automated backup
- Pre-milestone snapshot
- Offsite (cloud) backup

### M9: Multi-platform skill compatibility
- jcode-only NOW
- claude code + codex compatibility deferred

## 📋 What changed in 5a (vs the prior version of this handoff)

1. 3 working skills created (init / doctor / update)
2. 17 cross-layer maps added (was 0)
3. Section 0.1 / 0.2 / 19.1 / 19.2 / 19.3 added to framework-contract
4. ADR 0004 + 0005 added
5. Doctor C6 hardened (broken contract auto-detected)
6. Auto-rollback verified (Test 6)
7. logs/actions.jsonl established (31 entries)
8. logs/decisions.jsonl with 2 entries (D-001 / D-002)
9. retrospective/cycles/5a-closing.md written

## ⚠️ Things to remember next session

1. **`/harness-init` etc. should appear in jcode "Available Skills"** — if not, debug 5a-1 first
2. **Run `/harness-doctor` first** — it validates the entire framework state
3. **`~/.jcode/framework-contract.md` is the canonical source** — do `bun harness-update --dry-run` to see drift
4. **Pre-commit hook blocks `.lazy-harness/` and `.jcode/` staging** — this is intentional, not a bug
5. **Empty containers are valid** (Principle #10) — don't try to fill them without trigger
6. **"lazy" means developer effort minimization, NOT framework minimalism** (ADR 0005)
7. **Conflict Resolution Protocol fires automatically on new info** (Principle #17) — never silently update
8. **lazy-harness is private. NEVER push to medivance origin.**

---

## 9. Archive — Original handoff content (5a entry state)

이전 (5a 시작 직전) 의 handoff 내용은 [git history 또는 별도 archive 로 보관 — 이 시점에는 아직 없음].
주요 차이: 그 시점은 "framework 디렉토리 부재 발견 + 진실 기록 시작" 의 상태였고, 지금은 "5a 완료 + 5b 진입 준비" 상태.
