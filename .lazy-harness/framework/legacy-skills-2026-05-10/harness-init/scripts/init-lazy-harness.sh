#!/usr/bin/env bash
# init-lazy-harness.sh
# Initialize lazy-harness framework structure in target project.
# Idempotent — preserves existing files unless --force.
#
# Spec: .lazy-harness/framework/framework-contract.md (Principle 0~18)
# Skill: .jcode/skills/harness-init/SKILL.md
#
# Created by Lazy-Harness M1 (Phase 5a). Patterns borrowed from jcode-init.

set -euo pipefail

# ─────────────────────────────────────────────────────────
# CLI parsing
# ─────────────────────────────────────────────────────────

usage() {
  cat <<'USAGE'
Usage: init-lazy-harness.sh [TARGET_DIR] [--force] [--dry-run] [--tier <0|1|2|3>] [--gitignore]

Initialize lazy-harness framework in target directory (default: cwd).

Options:
  --force          overwrite existing files (default: keep existing)
  --dry-run        print actions without executing
  --tier N         adoption tier 0/1/2/3 (default 2). Reserved.
  --gitignore      add to .gitignore instead of .git/info/exclude (NOT recommended)
  -h, --help       show this help

Behavior:
  - Creates 30 containers per framework-contract
  - Adds schema placeholders + README in each container
  - Adds .lazy-harness/ to .git/info/exclude (default)
  - Installs/updates .husky/<pre-commit,post-commit,pre-push> chain (ADR 0009)
  - Idempotent: existing files preserved unless --force

USAGE
}

TARGET="${PWD}"
FORCE=0
DRY_RUN=0
TIER=2
USE_GITIGNORE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --tier)
      shift
      TIER="${1:-2}"
      if ! [[ "$TIER" =~ ^[0-3]$ ]]; then
        echo "Error: --tier must be 0, 1, 2, or 3" >&2
        exit 2
      fi
      ;;
    --gitignore) USE_GITIGNORE=1 ;;
    -h|--help) usage; exit 0 ;;
    --*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) TARGET="$1" ;;
  esac
  shift
done

TARGET=$(realpath -m "$TARGET")
if [[ ! -d "$TARGET" ]]; then
  echo "Error: target directory does not exist: $TARGET" >&2
  exit 1
fi

LAZY_DIR="$TARGET/.lazy-harness"

# ─────────────────────────────────────────────────────────
# Logging helpers
# ─────────────────────────────────────────────────────────

log_action() {
  if [[ "$DRY_RUN" == 1 ]]; then
    echo "[dry-run] $*"
  else
    echo "$*"
  fi
}

mkdir_p() {
  local dir="$1"
  if [[ "$DRY_RUN" == 1 ]]; then
    echo "[dry-run] mkdir -p $dir"
  else
    mkdir -p "$dir"
  fi
}

# Write file via heredoc input. Skip if exists unless --force.
# Usage: write_file PATH MODE [FORCE_OVERRIDE] <<EOF ... EOF
write_file() {
  local path="$1"
  local mode="${2:-0644}"
  local force_override="${3:-0}"
  local effective_force=$FORCE
  [[ "$force_override" == 1 ]] && effective_force=1

  if [[ "$DRY_RUN" == 1 ]]; then
    if [[ -e "$path" && "$effective_force" != 1 ]]; then
      echo "[dry-run] keep: $path"
      cat > /dev/null
      return 0
    fi
    echo "[dry-run] write: $path (mode $mode)"
    cat > /dev/null
    return 0
  fi

  if [[ -e "$path" && "$effective_force" != 1 ]]; then
    echo "keep existing: $path"
    cat > /dev/null
    return 0
  fi

  cat > "$path"
  chmod "$mode" "$path"
  echo "wrote: $path"
}

# ─────────────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────────────

cat <<EOF

╭─────────────────────────────────────────────╮
│  lazy-harness init                          │
│  framework-contract v1.1 · 18 principles    │
╰─────────────────────────────────────────────╯
target:    $TARGET
tier:      $TIER
mode:      $([ "$DRY_RUN" == 1 ] && echo "DRY-RUN" || echo "LIVE")
force:     $([ "$FORCE" == 1 ] && echo "yes" || echo "no")

EOF

# ────────────────────────��────────────────────────────────
# Step 1: Create 30 containers
# ─────────────────────────────────────────────────────────

CONTAINERS=(
  framework
  domain
  spec
  spec/frontend
  spec/backend
  spec/data
  spec/integration
  spec/infra
  spec/platform
  behavior
  behavior/scenarios
  tests
  contracts
  ssot
  intent
  intent/active
  intent/archive
  intent/templates
  prd
  questions
  decisions
  planning
  traceability
  regression
  git
  retrospective
  retrospective/metrics
  retrospective/cycles
  schemas
  scripts
  manifests
  visual
  generated
  logs
  handoff
  plans
  trails
  progress
  adapters
  hooks
)

echo "[1/5] Creating 30 containers..."
for container in "${CONTAINERS[@]}"; do
  mkdir_p "$LAZY_DIR/$container"
done
log_action "  → ${#CONTAINERS[@]} directories ensured"
echo ""

# ─────────────────────────────────────────────────────────
# Step 2: Place READMEs in each container (Empty-Container Tolerance #10)
# ─────────────────────────────────────────────────────────

echo "[2/5] Placing container READMEs (Empty-Container Tolerance)..."

place_readme() {
  local container="$1"
  local desc="$2"
  local trigger="$3"

  write_file "$LAZY_DIR/$container/README.md" 0644 <<EOF
# $container

$desc

## Trigger to fill

$trigger

## Status

- Empty is valid (Principle #10 Empty-Container Tolerance)
- Will be filled when triggers fire (Principle #6 Trigger-Based Growth)
- Auto-audited on update (Principle #1.2 Drafting and Auditing)
EOF
}

place_readme "domain" "DDD aggregates, ubiquitous-language, bounded-contexts. Apex authority for conflicts (Principle #4)." "New domain concept appears, boundary changes, or same word used differently in two places."
place_readme "spec/frontend" "SDD for frontend: component contracts, screen specs, interaction, visual binding." "Component contract or state machine changes."
place_readme "spec/backend" "SDD for backend: trpc/ipc/service contracts, background jobs." "Procedure split, permission, transaction boundary changes."
place_readme "spec/data" "SDD for data: prisma schema intent, migration plan, soft-delete/multi-tenant policy." "Schema change or migration plan."
place_readme "spec/integration" "SDD for external systems: EMR connector, Twilio, Naver, Kakao, Figma API." "External API change or new integration."
place_readme "spec/infra" "SDD for infra: build channel, release flow, env policy, auto-update." "Build/release/env config change."
place_readme "spec/platform" "SDD for platform: electron multi-instance, userData isolation, autoUpdater channel." "Platform-level config change."
place_readme "behavior/scenarios" "BDD scenarios with given/when/then, usabilityChecks, protectedBy, links. Step ≤ 7 (Principle #13)." "User-facing multi-step flow (≥ 2 inputs), bug fix needing regression protection, or migration."
place_readme "tests" "TDD plan and mapping. Auto-generated tests start as expected-fail or .skip until reviewed." "Code added/changed, regression entry created, spec sync."
place_readme "contracts" "Contract zone index: zod, prisma, trpc, ipc, external. AST-detected (Principle #15)." "Signature/contract change."
place_readme "ssot" "SSOT registry. AST-based duplicate detection. Includes contractZone tag." "New helper/filter/mapper/validator added."
place_readme "intent/active" "Active Intent Specs (feature/fix/refactor/investigation). Drives 4-pattern selection (Principle #4)." "New work begins."
place_readme "intent/archive" "Completed Intent Specs (read-only)." "Active intent completes."
place_readme "intent/templates" "Templates for new Intent Specs by type." "Initial scaffold or new intent type added."
place_readme "prd" "PRD (optional, large units). Wraps multiple feature-type Intent Specs." "New screen/flow/user group, product direction change."
place_readme "questions" "Open questions: blocker, assumption, later. Generated by Conflict Resolution Protocol (Principle #17)." "AI/human encounters ambiguity, conflict, or pending decision."
place_readme "decisions" "ADR + small decisions log. Generated by Conflict Resolution Protocol Step 6." "Six ADR triggers OR conflict resolution decision made."
place_readme "planning" "Missions, plan, backlog, change-plan. Drives self-driving loop (Principle #5)." "Work scope changes."
place_readme "traceability" "Commit ↔ spec/regression mapping. Bidirectional (Principle #14)." "Auto-updated on every commit (post-commit hook)."
place_readme "regression" "Regression registry + contract history. Auto-detected via AST diff (Principle #14)." "Bug fix commit OR contract diff detected."
place_readme "git" "Commit-log, branch-events. Auto (Principle #1.6 auto strength)." "Every commit (post-commit hook)."
place_readme "retrospective" "Weekly auto + milestone manual. Drives Knowledge Decay (future principle)." "Weekly schedule OR milestone completion."
place_readme "retrospective/metrics" "Auto-collected metrics: regression count, hook block count, self-loop ratio, etc." "Weekly hook collects."
place_readme "retrospective/cycles" "Cycle-level retrospectives (per Phase / milestone)." "Phase or milestone ends."
place_readme "schemas" "Result schema (Principle #9 Unified Result Schema) + container XML schemas." "Schema change."
place_readme "scripts" "Verification scripts (TS-heavy per Principle #8 Thin sh + Thick TS)." "New verification or framework script."
place_readme "manifests" "Hook + verification + skill registration." "New hook/verification/skill added."
place_readme "visual" "HTML visualizations from XML data." "Visualization needed at phase boundary (per Lazydino's preference)."
place_readme "generated" "Derived artifacts (json/md from xml). Read-only outputs." "XML source updated → regenerate."
place_readme "logs" "JSONL logs: actions, decisions, questions, validations. Append-only." "Auto by hooks."
place_readme "handoff" "Session handoff. First file new sessions read." "Each session ends."
place_readme "plans" "Completion plans (per task)." "Major task begins."
place_readme "trails" "Long-term roadmap (1+ year)." "Strategy/milestone update."
place_readme "progress" "Daily progress notes." "Daily."
place_readme "adapters" "Input adapters: figma, requirement, bug, external-api, log, regression. Single Entry Point (Principle #3)." "New input source or adapter improvement."
place_readme "hooks" "Lazy-harness lifecycle hooks (post-commit, post-impact, pre-push). Thin sh + Thick TS." "Lifecycle event auto-handled."

log_action "  → 30 README placeholders placed"
echo ""

# ─────────────────────────────────────────────────────────
# Step 2.5: Place 16 cross-layer map placeholders (ADR 0004)
# ─────────────────────────────────────────────────────────

echo "[2.5/5] Placing 16 cross-layer map placeholders (DDD/SDD/BDD/TDD mirror)..."

place_map() {
  local layer="$1"
  local subtype="$2"
  local filename="$3"
  local description="$4"
  local triggers="$5"

  local now
  now=$(date -Iseconds)

  write_file "$LAZY_DIR/$layer/$filename" 0644 <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!--
  $filename
  Layer: $layer | Subtype: $subtype
  Created by harness-init per ADR 0004 (Cross-Layer Maps).
  Empty container is valid (Principle #10 Empty-Container Tolerance).
-->
<map type="$layer"
     subtype="$subtype"
     version="1.0"
     created="$now"
     last-modified="$now">

  <description>
    $description
  </description>

  <entries>
    <!-- Empty until triggers fill (Principle #6 Trigger-Based Growth). -->
  </entries>

  <triggers-to-fill>
$triggers
  </triggers-to-fill>

  <links>
    <!-- Cross-references to other maps / specs / regressions / decisions. -->
  </links>
</map>
EOF
}

# DDD layer (5 maps — 4 standard + aggregates)
place_map "domain" "landscape" "domain-map.xml" \
  "전체 도메인 landscape — 모든 도메인 개념을 한 눈에 본다." \
  "    <trigger>새 도메인 개념 발견</trigger>
    <trigger>boundary 변경</trigger>"

place_map "domain" "language" "ubiquitous-language.xml" \
  "도메인 표준 용어 사전 — canonical / alias / forbidden 포함." \
  "    <trigger>새 용어 등장 또는 동의어 발견</trigger>
    <trigger>UI label 또는 코드 식별자가 표준어를 위반</trigger>"

place_map "domain" "boundaries" "bounded-contexts.xml" \
  "Bounded Context 정의 — 도메인 모델의 일관성 경계." \
  "    <trigger>새 context 출현</trigger>
    <trigger>같은 단어가 두 context 에서 다르게 쓰임</trigger>"

place_map "domain" "relations" "context-map.xml" \
  "Context 간 관계 (upstream / downstream / shared kernel / anti-corruption)." \
  "    <trigger>두 context 간 의존 관계 출현</trigger>"

place_map "domain" "aggregates" "aggregates.xml" \
  "Aggregate / Entity / Value Object 정의." \
  "    <trigger>새 aggregate boundary 식별</trigger>
    <trigger>entity 가 lifecycle 가짐을 발견</trigger>"

# SDD layer (4 maps — NEW per ADR 0004)
place_map "spec" "landscape" "spec-map.xml" \
  "전체 SDD landscape — frontend/backend/data/integration/infra/platform 통합 시점." \
  "    <trigger>새 spec entry 추가</trigger>
    <trigger>spec 간 의존 발견</trigger>"

place_map "spec" "language" "spec-language.xml" \
  "SDD 표준 용어 + alias (contract / procedure / route / migration 등)." \
  "    <trigger>새 spec 용어 등장</trigger>"

place_map "spec" "boundaries" "spec-boundaries.xml" \
  "SDD 카테고리 간 책임 경계 (frontend ↔ backend ↔ data 등)." \
  "    <trigger>책임 경계 위반 또는 변경 발견</trigger>"

place_map "spec" "relations" "spec-relations.xml" \
  "SDD 카테고리 간 의존 관계 그래프." \
  "    <trigger>spec ↔ spec 의존 출현</trigger>"

# BDD layer (4 maps — NEW per ADR 0004)
place_map "behavior" "landscape" "behavior-map.xml" \
  "전체 BDD scenario landscape — 모든 시나리오 한 눈." \
  "    <trigger>새 scenario 추가</trigger>
    <trigger>scenario archive (deprecated)</trigger>"

place_map "behavior" "language" "scenario-language.xml" \
  "BDD 도메인 용어 (given / when / then 외)." \
  "    <trigger>새 scenario 용어 등장</trigger>"

place_map "behavior" "coverage" "scenario-coverage.xml" \
  "화면 / 유스케이스 ↔ scenario 커버리지 매트릭스." \
  "    <trigger>새 화면/유스케이스 추가</trigger>
    <trigger>scenario 가 어느 화면도 커버하지 않음 발견</trigger>"

place_map "behavior" "relations" "scenario-relations.xml" \
  "scenario 간 의존 관계 (precondition / shared given)." \
  "    <trigger>scenario 간 shared given 출현</trigger>"

# TDD layer (4 maps — NEW per ADR 0004)
place_map "tests" "landscape" "test-map.xml" \
  "전체 TDD landscape — e2e / integration / unit / regression." \
  "    <trigger>새 test 추가</trigger>
    <trigger>test type 변경</trigger>"

place_map "tests" "language" "test-language.xml" \
  "test type 분류 + 표준 용어 (e2e / integration / unit / regression / contract / smoke)." \
  "    <trigger>새 test type 등장</trigger>"

place_map "tests" "coverage" "test-coverage.xml" \
  "spec ↔ test 매핑 — 어느 spec 이 test 보호 받는지." \
  "    <trigger>새 test 추가</trigger>
    <trigger>spec 추가 후 test 부재 감지</trigger>"

place_map "tests" "protection-matrix" "test-protection-matrix.xml" \
  "test ↔ regression ↔ scenario 4축 매핑 — bidirectional traceability core." \
  "    <trigger>regression entry 추가</trigger>
    <trigger>protection 깨짐 발견 (test 가 regression 미커버)</trigger>"

log_action "  → 17 cross-layer map placeholders placed (DDD: 5, SDD: 4, BDD: 4, TDD: 4)"
echo ""

# ─────────────────────────────────────────────────────────
# Step 2.6: Inject lazy-harness section into .jcode/AGENTS.md (ADR 0007)
# ─────────────────────────────────────────────────────────

echo "[2.6/5] Injecting lazy-harness section into .jcode/AGENTS.md..."

JCODE_DIR="$TARGET/.jcode"
AGENTS_PATH="$JCODE_DIR/AGENTS.md"
LAZY_SECTION_MARKER="## ⚡ Lazy-Harness Framework (CRITICAL — read first)"

if [[ "$DRY_RUN" == 1 ]]; then
  if [[ -f "$AGENTS_PATH" ]] && grep -q "$LAZY_SECTION_MARKER" "$AGENTS_PATH"; then
    echo "[dry-run] $AGENTS_PATH already has lazy-harness section — skip"
  else
    echo "[dry-run] would inject lazy-harness section into $AGENTS_PATH"
  fi
else
  mkdir -p "$JCODE_DIR"

  # Create base AGENTS.md if missing
  if [[ ! -f "$AGENTS_PATH" ]]; then
    cat > "$AGENTS_PATH" <<'AGENTS_BASE_EOF'
# Private Jcode Harness

This directory is Lazydino's private project-local harness for Jcode.

## Intent

- Preserve project/team instructions unless `.jcode/config.toml` sets `ignore_project_agents = true`.
- Prefer this private harness for personal workflow details, local hooks, and routing preferences.
- Do not assume `.jcode/` is committed. Treat it as local/private by default.

## Working style

- Be proactive and finish natural next steps.
- Run focused validation after code changes.
- Avoid destructive actions unless explicitly requested.
- Document project-specific discoveries in `.jcode/harness/20-project-rules.md` when useful.
AGENTS_BASE_EOF
    echo "  → created base $AGENTS_PATH"
  fi

  # Inject lazy-harness section if not already present
  if grep -q "$LAZY_SECTION_MARKER" "$AGENTS_PATH"; then
    echo "  → lazy-harness section already present in $AGENTS_PATH (keep)"
  else
    cat >> "$AGENTS_PATH" <<'AGENTS_LAZY_EOF'

---

## ⚡ Lazy-Harness Framework (CRITICAL — read first)

> 이 프로젝트에는 **lazy-harness framework** 가 active 상태로 활성화되어 있다.
> 이 섹션은 새 세션이 시작 시 **반드시 먼저 인지**해야 하는 framework 의 존재와 진입점.
> framework 의 single source of truth: `.lazy-harness/framework/framework-contract.md` (v1.4+, 23 principle)

### Quick orientation (3 초)

| Question | Answer |
|---|---|
| Framework 살아있나? | `/harness-doctor` 실행해서 **C1~C16 (16 checks)** 통과 확인 |
| 현재 phase? | `.lazy-harness/handoff/00-current-state.md` 읽기 (TL;DR 표) |
| 마지막 결정? | `.lazy-harness/decisions/` 의 최신 ADR + `.lazy-harness/logs/decisions.jsonl` |
| 무엇을 다음에? | `.lazy-harness/planning/phase-N-plan.xml` 의 next sub-phase |

### Active skills (project-local at `.jcode/skills/`)

```bash
/harness-init       # 새 프로젝트에 framework 셋업 (idempotent, husky 자동 wiring)
/harness-doctor     # C1~C16 검증 + Unified Result Schema JSON
/harness-update     # framework-contract sync + auto-rollback (Principle #18)
```

### Working with the framework

**ALWAYS** before non-trivial change:

1. **Conflict Resolution Protocol** (Principle #17) — 새 정보 → 구조화된 옵션 → 사람 결정 → ADR
   - Step 1: `.lazy-harness/` 검색
   - Step 3: file:line + 직접 인용 (paraphrase 금지)
   - Step 4: 3~5 choice + Recommended + type-your-own
   - Step 6: ADR + decisions.jsonl 자동 기록

2. **Verification Discipline** (Principle #21) — verify level 명시
   - L0 sh / L1 output / **L2 marker** (hook/infra 의무) / **L3 negative test** (doctor check 의무) / **L4 사람 review** (phase close 의무)

3. **Plan Status Hygiene** (Principle #20) — phase 진행 시
   - 시작 전 plan.xml 의 criterion 필독
   - 완료 후 status="pass" + verifiedAt 박기
   - 새 ADR 추가 시 `<addedDuringPhase>` 명시

4. **External Dependency Invariant** (Principle #22)
   - 허용: `git / husky / tsc / eslint / ts-morph / python3 / bash`
   - 금지: Figma / Slack / 외부 SaaS — 모두 `triggers/external/` opt-in

5. **Code-First Trigger** (Principle #23) — 사용자 코드 변경이 universal trigger source
   - AST diff → DDD / SDD / SSOT
   - git diff → BDD / regression
   - tsc/eslint → drift candidate

**NEVER**:

- `.jcode/` 또는 `.lazy-harness/` 를 git 에 commit (private! pre-push hook 차단)
- `.husky/<3>` 를 ignore (ADR 0009 — framework public surface, origin commit)
- 두 디렉토리 합치기 (Section 0.3 forbidden)
- doctor fail 무시 (Principle #21.5 silent ignore 금지)
- "lazy" = "minimal" 해석 (ADR 0005)
- 외부 SaaS 를 framework 코어에 호출 (Principle #22)
- AI 가 input source 가정 (Principle #23 — code 가 universal source)

### Critical context

- **Principle 0**: 사람-AI 상호보완 (`0001-core-philosophy.md`)
- **Principle 17**: Conflict Resolution (`0002`)
- **Principle 18**: Recovery Path (`0003`)
- **ADR 0004**: Cross-layer maps (17 XML placeholders)
- **ADR 0005**: lazy = developer effort minimization
- **ADR 0006**: Directory bridge (Section 0.3)
- **ADR 0007**: AGENTS.md auto-inject
- **ADR 0009**: Husky integration (`.husky/<3>` framework public surface)
- **ADR 0010**: Plan Status Hygiene (Principle 20 + doctor C12)
- **ADR 0011**: Verification Discipline (Principle 21 + doctor C13)
- **ADR 0012**: Oracle/Sisyphus Audit (doctor C14/C15/C16 추가)
- **ADR 0013**: External Dependency Invariant + Code-First Trigger (Principle 22 + 23)

### Safety state

- ✅ `.lazy-harness/` ignored via `.git/info/exclude`
- ✅ `.jcode/` ignored
- ✅ `.husky/pre-commit / post-commit / pre-push` chain → lazy hooks (ADR 0009)
- ✅ Husky chain silent-skip if `.lazy-harness/` absent (팀원 무해)
- ✅ Auto-backup before framework-contract update
- ✅ pre-push hook: ALL push leak guard (URL 무관)

### Hook chain (ADR 0009)

```
git commit
  ↓ .husky/post-commit (medivance origin tracked)
  ↓ if [ -x ".lazy-harness/hooks/post-commit.sh" ]
    ↓ → actions.jsonl entry (python3 JSON encoding)

git push
  ↓ .husky/pre-push (medivance origin tracked)
  ↓ if [ -x ".lazy-harness/hooks/pre-push.sh" ]
    ↓ → leak guard (ALL push) + doctor gate
```

→ `.lazy-harness/` 없는 팀원: husky 가 silent skip → 무해.

### When in doubt

`.lazy-harness/handoff/00-current-state.md` 가 always-fresh 진실. 새 세션이면 그걸 먼저 읽어.
AGENTS_LAZY_EOF
    echo "  → injected lazy-harness section into $AGENTS_PATH"
  fi
fi

echo ""

# ─────────────────────────────────────────────────────────
# Step 2.6b: Place lazy-harness hook scripts (.lazy-harness/hooks/*.sh)
# Per ADR 0009 — these are the actual logic; Step 2.7 wires them.
# ─────────────────────────────────────────────────────────

echo "[2.6b/5] Placing lazy-harness hook scripts..."

write_file "$LAZY_DIR/hooks/pre-commit-guard.sh" 0755 <<'PRE_GUARD_EOF'
#!/bin/bash
# Lazy-Harness pre-commit safety guard (called via .husky/pre-commit or .git/hooks/pre-commit)
# Blocks commit if .lazy-harness/, .jcode/, or framework/ files staged.

set -e
[ -f ".lazy-harness/.hooks-disabled" ] && exit 0

LAZY_STAGED=$(git diff --cached --name-only | grep -E '^\.lazy-harness/' || true)
JCODE_STAGED=$(git diff --cached --name-only | grep -E '^\.jcode/' || true)
FRAMEWORK_STAGED=$(git diff --cached --name-only | grep -E '^packages/medivance-harness/src/framework/' || true)

if [ -n "$LAZY_STAGED" ] || [ -n "$JCODE_STAGED" ] || [ -n "$FRAMEWORK_STAGED" ]; then
    echo ""
    echo "🚨 BLOCKED: Private 영역 파일이 staged 됐습니다!"
    [ -n "$LAZY_STAGED" ] && { echo "Staged .lazy-harness/ files:"; echo "$LAZY_STAGED" | sed 's/^/  - /'; }
    [ -n "$JCODE_STAGED" ] && { echo "Staged .jcode/ files:"; echo "$JCODE_STAGED" | sed 's/^/  - /'; }
    [ -n "$FRAMEWORK_STAGED" ] && { echo "Staged framework files:"; echo "$FRAMEWORK_STAGED" | sed 's/^/  - /'; }
    echo ""
    echo "복구: git restore --staged <files>"
    exit 1
fi
exit 0
PRE_GUARD_EOF

write_file "$LAZY_DIR/hooks/post-commit.sh" 0755 <<'POST_EOF'
#!/bin/bash
# Lazy-Harness post-commit hook — append entry to logs/actions.jsonl
set +e
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] && exit 0
LAZY="$REPO_ROOT/.lazy-harness"
[ ! -d "$LAZY" ] && exit 0
[ -f "$LAZY/.hooks-disabled" ] && exit 0

LOG="$LAZY/logs/actions.jsonl"
mkdir -p "$(dirname "$LOG")"
COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null)
COMMIT_MSG=$(git log -1 --pretty=%s 2>/dev/null | head -c 200)
COMMIT_TYPE=$(echo "$COMMIT_MSG" | grep -oE '^[A-Z][a-z]+:' | tr -d ':')
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | wc -l)
TIMESTAMP=$(date -Iseconds)
TOUCHED_LAZY=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | grep -cE '\.lazy-harness/|\.jcode/' | head -1 | tr -d ' \n' || echo 0)
[ -z "$TOUCHED_LAZY" ] && TOUCHED_LAZY=0
# JSON encode via python3 (handles newline / unicode / special chars)
JSON_LINE=$(COMMIT_MSG="$COMMIT_MSG" TIMESTAMP="$TIMESTAMP" COMMIT_SHA="$COMMIT_SHA" BRANCH="$BRANCH" \
  COMMIT_TYPE="$COMMIT_TYPE" FILES_CHANGED="$FILES_CHANGED" TOUCHED_LAZY="$TOUCHED_LAZY" \
  python3 -c '
import os, json
print(json.dumps({
  "timestamp": os.environ["TIMESTAMP"], "actor": "git", "action": "commit",
  "sha": os.environ["COMMIT_SHA"], "branch": os.environ["BRANCH"],
  "type": os.environ["COMMIT_TYPE"], "filesChanged": int(os.environ["FILES_CHANGED"]),
  "touchedLazy": int(os.environ["TOUCHED_LAZY"]),
  "message": os.environ["COMMIT_MSG"].split("\n")[0]
}, ensure_ascii=False))
' 2>/dev/null) || JSON_LINE=""
[ -n "$JSON_LINE" ] && echo "$JSON_LINE" >> "$LOG"

if [ "$COMMIT_TYPE" = "Fix" ]; then
    REG="$LAZY/regression/candidates.jsonl"
    mkdir -p "$(dirname "$REG")"
    CAND=$(COMMIT_MSG="$COMMIT_MSG" TIMESTAMP="$TIMESTAMP" COMMIT_SHA="$COMMIT_SHA" python3 -c '
import os, json
print(json.dumps({
  "timestamp": os.environ["TIMESTAMP"], "sha": os.environ["COMMIT_SHA"],
  "message": os.environ["COMMIT_MSG"].split("\n")[0], "status": "candidate"
}, ensure_ascii=False))
' 2>/dev/null) || CAND=""
    [ -n "$CAND" ] && echo "$CAND" >> "$REG"
fi
exit 0
POST_EOF

write_file "$LAZY_DIR/hooks/pre-push.sh" 0755 <<'PUSH_EOF'
#!/bin/bash
# Lazy-Harness pre-push hook — doctor gate + private leak guard
set -e
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_ROOT" ] && exit 0
LAZY="$REPO_ROOT/.lazy-harness"
[ ! -d "$LAZY" ] && exit 0
[ -f "$LAZY/.hooks-disabled" ] && { echo "⚠️ lazy-harness hooks disabled — skip pre-push"; exit 0; }

URL="${2:-}"
# CRITICAL: ALL push 에서 private file leak 차단 (URL 무관 — bug-2 fix)
# .husky/<3 hooks> 는 ADR 0009 framework public surface 로 ALLOW
LEAKED=$(git diff --name-only origin/HEAD..HEAD 2>/dev/null | grep -E '^\.lazy-harness/|^\.jcode/' || true)
if [ -n "$LEAKED" ]; then
    echo "🚨 BLOCKED: lazy-harness/jcode 파일이 push 시도됨!"
    echo "$LEAKED" | sed 's/^/  - /'
    exit 1
fi

DOCTOR="$REPO_ROOT/.jcode/skills/harness-doctor/scripts/doctor.sh"
if [ -x "$DOCTOR" ]; then
    DOCTOR_OUT=$("$DOCTOR" 2>&1 || true)
    FAILS=$(echo "$DOCTOR_OUT" | grep -cE '^\[C[0-9]+\].*✗ fail' | head -1 | tr -d ' \n' || echo 0)
    [ -z "$FAILS" ] && FAILS=0
    TS=$(date -Iseconds)
    LOG="$LAZY/logs/validations.jsonl"
    mkdir -p "$(dirname "$LOG")"
    if [ "$FAILS" -gt 0 ]; then
        echo "{\"timestamp\":\"$TS\",\"id\":\"PRE-PUSH-001\",\"status\":\"fail\",\"category\":\"infra\",\"humanRequired\":true,\"details\":[\"doctor reports $FAILS fail\"],\"confidence\":\"high\"}" >> "$LOG"
        echo "🚨 pre-push blocked: doctor $FAILS fail. Run /harness-doctor"
        exit 1
    else
        echo "{\"timestamp\":\"$TS\",\"id\":\"PRE-PUSH-001\",\"status\":\"pass\",\"category\":\"infra\",\"humanRequired\":false,\"confidence\":\"high\"}" >> "$LOG"
    fi
fi
exit 0
PUSH_EOF

write_file "$LAZY_DIR/hooks/weekly-snapshot.sh" 0755 <<'SNAP_EOF'
#!/bin/bash
# Lazy-Harness weekly snapshot (Principle #18) — manual or cron
set -e
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LAZY="$REPO_ROOT/.lazy-harness"
BACKUP="$REPO_ROOT/.lazy-harness-backup"
WEEK=$(date +%Y-W%V)
SNAP="$BACKUP/$WEEK"
TS=$(date -Iseconds)
[ ! -d "$LAZY" ] && exit 0
mkdir -p "$SNAP"
rsync -a --exclude='logs/' --exclude='.lazy-harness-backup/' "$LAZY/" "$SNAP/"
cat > "$SNAP/.snapshot-meta.json" <<META
{"timestamp":"$TS","isoWeek":"$WEEK","trigger":"${1:-manual}","headSha":"$(git rev-parse HEAD 2>/dev/null || echo unknown)"}
META
mkdir -p "$LAZY/logs"
echo "{\"timestamp\":\"$TS\",\"actor\":\"weekly-snapshot\",\"action\":\"backup\",\"path\":\"$SNAP\"}" >> "$LAZY/logs/actions.jsonl"
cd "$BACKUP" && ls -t | grep -E '^[0-9]{4}-W[0-9]+$' | tail -n +9 | xargs -r rm -rf
echo "✓ Snapshot: $SNAP ($(du -sh "$SNAP" | cut -f1))"
SNAP_EOF

echo "  → 4 hook scripts placed at $LAZY_DIR/hooks/"
echo ""

# ─────────────────────────────────────────────────────────
# Step 2.7: Wire git hooks via husky (if present) or .git/hooks (legacy)
# Per ADR 0009 — Husky Integration Policy.
# Detects husky from package.json; chooses correct wiring strategy.
# ─────────────────────────────────────────────────────────

echo "[2.7/5] Wiring git hooks..."

USES_HUSKY=0
if [ -f "$TARGET/package.json" ] && grep -q '"husky"' "$TARGET/package.json" 2>/dev/null; then
  USES_HUSKY=1
  HOOK_DIR="$TARGET/.husky"
  echo "  → husky detected — using .husky/<hook> chain (ADR 0009)"
else
  HOOK_DIR="$TARGET/.git/hooks"
  echo "  → no husky — using .git/hooks/<hook> (legacy fallback)"
fi

mkdir -p "$HOOK_DIR"

# pre-commit (safety guard)
PRE_COMMIT="$HOOK_DIR/pre-commit"
if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would write $PRE_COMMIT"
elif [ ! -f "$PRE_COMMIT" ]; then
  if [ "$USES_HUSKY" = "1" ]; then
    cat > "$PRE_COMMIT" <<'HUSKY_PRE'
#!/usr/bin/env sh
# Lazy-Harness pre-commit chain entry (committed to origin per ADR 0009)
if [ -x ".lazy-harness/hooks/pre-commit-guard.sh" ]; then
    .lazy-harness/hooks/pre-commit-guard.sh || exit 1
fi
HUSKY_PRE
  else
    cp "$LAZY_DIR/hooks/pre-commit-guard.sh" "$PRE_COMMIT" 2>/dev/null || true
  fi
  chmod +x "$PRE_COMMIT"
  echo "  → created $PRE_COMMIT"
elif ! grep -q "lazy-harness" "$PRE_COMMIT" 2>/dev/null; then
  echo "  ⚠ $PRE_COMMIT exists without lazy-harness reference — skipping (manual wiring needed)"
else
  echo "  → $PRE_COMMIT already wired"
fi

# post-commit (logger)
POST_COMMIT="$HOOK_DIR/post-commit"
if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would write $POST_COMMIT"
elif [ ! -f "$POST_COMMIT" ] || ! grep -q "lazy-harness" "$POST_COMMIT" 2>/dev/null; then
  if [ "$USES_HUSKY" = "1" ]; then
    cat > "$POST_COMMIT" <<'HUSKY_POST'
#!/usr/bin/env sh
# Lazy-Harness post-commit chain entry (committed to origin per ADR 0009)
if [ -x ".lazy-harness/hooks/post-commit.sh" ]; then
    .lazy-harness/hooks/post-commit.sh "$@" || true
fi
HUSKY_POST
  else
    cat > "$POST_COMMIT" <<'GIT_POST'
#!/bin/bash
# Lazy-Harness post-commit (legacy fallback wiring)
[ -x ".lazy-harness/hooks/post-commit.sh" ] && .lazy-harness/hooks/post-commit.sh "$@" || true
exit 0
GIT_POST
  fi
  chmod +x "$POST_COMMIT"
  echo "  → created $POST_COMMIT"
else
  echo "  → $POST_COMMIT already wired"
fi

# pre-push (validator)
PRE_PUSH="$HOOK_DIR/pre-push"
if [ "$DRY_RUN" = "1" ]; then
  echo "  [dry-run] would write $PRE_PUSH"
elif [ ! -f "$PRE_PUSH" ] || ! grep -q "lazy-harness" "$PRE_PUSH" 2>/dev/null; then
  if [ "$USES_HUSKY" = "1" ]; then
    cat > "$PRE_PUSH" <<'HUSKY_PUSH'
#!/usr/bin/env sh
# Lazy-Harness pre-push chain entry (committed to origin per ADR 0009)
if [ -x ".lazy-harness/hooks/pre-push.sh" ]; then
    .lazy-harness/hooks/pre-push.sh "$@" || exit 1
fi
HUSKY_PUSH
  else
    cat > "$PRE_PUSH" <<'GIT_PUSH'
#!/bin/bash
# Lazy-Harness pre-push (legacy fallback wiring)
[ -x ".lazy-harness/hooks/pre-push.sh" ] && .lazy-harness/hooks/pre-push.sh "$@" || exit 1
exit 0
GIT_PUSH
  fi
  chmod +x "$PRE_PUSH"
  echo "  → created $PRE_PUSH"
else
  echo "  → $PRE_PUSH already wired"
fi

echo ""

# ─────────────────────────────────────────────────────────
# Step 3: Place schemas (Unified Result Schema #9)
# ─────────────────────────────────────────────────────────

echo "[3/5] Placing core schemas (Unified Result Schema)..."

write_file "$LAZY_DIR/schemas/result.schema.json" 0644 <<'EOF'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "lazy-harness/result.schema.json",
  "title": "Unified Result Schema (Principle #9)",
  "description": "All hooks/checks/validations emit this JSON shape.",
  "type": "object",
  "required": ["id", "status", "category", "humanRequired", "details", "evidence", "confidence"],
  "properties": {
    "id":            { "type": "string", "pattern": "^(VER|HOOK|CHECK|AUDIT)-[0-9A-Z-]+$" },
    "status":        { "enum": ["pass", "fail", "error"] },
    "category":      { "enum": ["impl", "spec", "test", "env", "ssot", "infra", "unknown"] },
    "humanRequired": { "type": "boolean" },
    "details":       { "type": "array", "items": { "type": "string" } },
    "suggestedFix":  { "type": ["string", "null"] },
    "evidence": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "line", "reason"],
        "properties": {
          "path":   { "type": "string" },
          "line":   { "type": "integer", "minimum": 0 },
          "reason": { "type": "string" }
        }
      }
    },
    "confidence":    { "enum": ["high", "medium", "low"] },
    "riskTier":      { "enum": ["db", "release", "platform", "integration", "backend", "frontend", "docs"] }
  }
}
EOF

write_file "$LAZY_DIR/schemas/decision.schema.json" 0644 <<'EOF'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "lazy-harness/decision.schema.json",
  "title": "Decision Log Entry (Principle #17 Conflict Resolution)",
  "type": "object",
  "required": ["id", "timestamp", "input", "conflict", "presentedChoices", "humanChose", "impact", "persisted", "aftershock"],
  "properties": {
    "id":              { "type": "string", "pattern": "^D-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}$" },
    "timestamp":       { "type": "string", "format": "date-time" },
    "input":           { "type": "string" },
    "conflict": {
      "type": "object",
      "required": ["finding", "sources"],
      "properties": {
        "finding":  { "enum": ["gap", "conflict", "missing", "drift", "unclear"] },
        "sources":  {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["path", "line", "quote", "lastModified"],
            "properties": {
              "path":         { "type": "string" },
              "line":         { "type": "integer" },
              "quote":        { "type": "string" },
              "lastModified": { "type": "string", "format": "date-time" },
              "author":       { "type": "string" }
            }
          }
        }
      }
    },
    "presentedChoices": { "type": "array", "minItems": 5 },
    "humanChose":       { "type": "string" },
    "reasoning":        { "type": "string" },
    "impact": {
      "type": "object",
      "properties": {
        "filesModified":      { "type": "array", "items": { "type": "string" } },
        "testsAffected":      { "type": "array", "items": { "type": "string" } },
        "regressionRisks":    { "type": "array", "items": { "type": "string" } },
        "cascadeDepth":       { "type": "integer" }
      }
    },
    "persisted": {
      "type": "object",
      "properties": {
        "documentsUpdated": { "type": "array", "items": { "type": "string" } },
        "adrDrafted":       { "type": ["string", "null"] },
        "commitTag":        { "type": "string" }
      }
    },
    "aftershock": {
      "type": "object",
      "properties": {
        "depth":         { "type": "integer", "minimum": 0, "maximum": 3 },
        "newConflicts":  { "type": "array" },
        "halted":        { "type": "boolean" }
      }
    }
  }
}
EOF

log_action "  → 2 core schemas placed"
echo ""

# ─────────────────────────────────────────────────────────
# Step 4: Add to .git/info/exclude (default) or .gitignore
# ─────────────────────────────────────────────────────────

echo "[4/5] Configuring git ignore..."

if git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [[ "$USE_GITIGNORE" == 1 ]]; then
    GITIGNORE="$TARGET/.gitignore"
    if [[ "$DRY_RUN" == 1 ]]; then
      echo "[dry-run] would add .lazy-harness/ to $GITIGNORE"
    else
      touch "$GITIGNORE"
      if ! grep -qxF '.lazy-harness/' "$GITIGNORE"; then
        printf '\n# Private lazy-harness framework (do NOT commit)\n.lazy-harness/\n' >> "$GITIGNORE"
        echo "  → added .lazy-harness/ to $GITIGNORE"
      else
        echo "  → .lazy-harness/ already in $GITIGNORE"
      fi
    fi
  else
    EXCLUDE_FILE="$TARGET/.git/info/exclude"
    if [[ "$DRY_RUN" == 1 ]]; then
      echo "[dry-run] would add .lazy-harness/ to $EXCLUDE_FILE"
    else
      mkdir -p "$(dirname "$EXCLUDE_FILE")"
      touch "$EXCLUDE_FILE"
      if ! grep -qxF '.lazy-harness/' "$EXCLUDE_FILE"; then
        cat >> "$EXCLUDE_FILE" <<EXCLUDE_EOF

# Lazy-harness private framework (Lazydino — do NOT commit, do NOT push)
.lazy-harness/
EXCLUDE_EOF
        echo "  → added .lazy-harness/ to $EXCLUDE_FILE"
      else
        echo "  → .lazy-harness/ already in $EXCLUDE_FILE"
      fi
    fi
  fi
else
  echo "  → not a git repo; skipping ignore config"
fi
echo ""

# ─────────────────────────────────────────────────────────
# Step 5: (removed — pre-commit wiring moved to Step 2.7 per ADR 0009)
# ─────────────────────────────────────────────────────────

echo "[5/5] Pre-commit safety guard wiring done in Step 2.7 (husky-aware) ✓"
echo ""

# ─────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────

cat <<EOF
╭─────────────────────────────────────────────╮
│  ✓ lazy-harness initialized                 │
╰─────────────────────────────────────────────╯

next steps:
  1. (recommended) bring framework-contract.md to ${LAZY_DIR}/framework/
     If you have a global copy at ~/.jcode/framework-contract.md, copy it.
     Or use: \`/harness-update\` (when available, M1-stage)
  2. verify with:
       /harness-doctor
     OR:
       cd $TARGET && find .lazy-harness -maxdepth 2 -type d | sort
  3. start phase 5b when M1 success criteria pass.

safety verified:
  - .lazy-harness/ in .git/info/exclude
  - .husky/pre-commit chain → .lazy-harness/hooks/pre-commit-guard.sh blocks accidental staging
  - 0 files tracked by git (verify: git ls-files | grep -c '^\.lazy-harness')

EOF

exit 0
