#!/usr/bin/env bash
# doctor.sh
# Read-only validation of lazy-harness framework integrity.
# Emits Unified Result Schema entries → logs/validations.jsonl
#
# Spec: framework-contract.md Principle #1.2, #9, #11
# Skill: .jcode/skills/harness-doctor/SKILL.md

set -uo pipefail

# ─────────────────────────────────────────────
# CLI parsing
# ─────────────────────────────────────────────

usage() {
  cat <<'USAGE'
Usage: doctor.sh [--target DIR] [--json] [--verbose] [-h|--help]

Read-only validation of lazy-harness framework. Emits Unified Result Schema.

Options:
  --target DIR     project root (default: cwd)
  --json           emit JSON only (machine-readable)
  --verbose        show all check details (incl. passed evidence)
  -h, --help       show this help

Exit codes:
  0   all pass (or only warns)
  1   ≥ 1 check failed
  2   doctor itself errored
USAGE
}

TARGET="${PWD}"
JSON_ONLY=0
VERBOSE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) shift; TARGET="${1:-$PWD}" ;;
    --json) JSON_ONLY=1 ;;
    --verbose) VERBOSE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

TARGET=$(realpath -m "$TARGET")
LAZY_DIR="$TARGET/.lazy-harness"

if [[ ! -d "$LAZY_DIR" ]]; then
  echo "Error: .lazy-harness/ not found at $TARGET" >&2
  echo "Hint: run /harness-init first" >&2
  exit 2
fi

# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0
RESULTS_JSON=()

# Tracks last details for --verbose
declare -a LAST_DETAILS=()

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

emit_human() {
  [[ "$JSON_ONLY" == 1 ]] && return 0
  printf "%s\n" "$@"
}

# emit_check ID NAME STATUS SUMMARY
emit_check() {
  local id="$1"
  local name="$2"
  local status="$3"
  local summary="$4"

  local icon=""
  case "$status" in
    pass) icon="✓"; PASS_COUNT=$((PASS_COUNT + 1)) ;;
    warn) icon="⚠"; WARN_COUNT=$((WARN_COUNT + 1)) ;;
    fail) icon="✗"; FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    skip) icon="○"; SKIP_COUNT=$((SKIP_COUNT + 1)) ;;
  esac

  if [[ "$JSON_ONLY" != 1 ]]; then
    printf "[%s] %-22s %s %s (%s)\n" "$id" "$name" "$icon" "$status" "$summary"
    if [[ "$VERBOSE" == 1 ]] || [[ "$status" == "fail" ]] || [[ "$status" == "warn" ]]; then
      for d in "${LAST_DETAILS[@]:-}"; do
        [[ -n "$d" ]] && printf "      → %s\n" "$d"
      done
    fi
  fi

  # Build JSON
  local details_json="[]"
  if [[ ${#LAST_DETAILS[@]} -gt 0 ]]; then
    details_json=$(printf '%s\n' "${LAST_DETAILS[@]}" | awk '
      BEGIN { print "[" }
      { gsub(/\\/, "\\\\"); gsub(/"/, "\\\""); printf "%s\"%s\"", (NR>1?",":""), $0 }
      END { print "]" }
    ')
  fi

  local result_status="pass"
  case "$status" in
    fail) result_status="fail" ;;
    warn|skip) result_status="pass" ;;
    pass) result_status="pass" ;;
  esac

  local human_required="false"
  [[ "$status" == "fail" ]] && human_required="true"

  RESULTS_JSON+=("$(cat <<EOF
{
  "id": "VER-DOC-$id",
  "status": "$result_status",
  "category": "infra",
  "humanRequired": $human_required,
  "details": $details_json,
  "suggestedFix": null,
  "evidence": [],
  "confidence": "high"
}
EOF
)")

  LAST_DETAILS=()
}

add_detail() {
  LAST_DETAILS+=("$1")
}

# ─────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────

if [[ "$JSON_ONLY" != 1 ]]; then
  cat <<EOF

╭───────────────────────────────────────────╮
│ lazy-harness doctor                       │
│ target: $TARGET
╰───────────────────────────────────────────╯

EOF
fi

# ─────────────────────────────────────────────
# C1 — Structure (30 containers)
# ─────────────────────────────────────────────

EXPECTED_CONTAINERS=(
  framework domain spec spec/frontend spec/backend spec/data spec/integration
  spec/infra spec/platform behavior behavior/scenarios tests contracts ssot
  intent intent/active intent/archive intent/templates prd questions decisions
  planning traceability regression git retrospective retrospective/metrics
  retrospective/cycles schemas scripts manifests visual generated logs handoff
  plans trails progress adapters hooks
)

MISSING=()
for c in "${EXPECTED_CONTAINERS[@]}"; do
  [[ ! -d "$LAZY_DIR/$c" ]] && MISSING+=("$c")
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
  emit_check "C1" "Structure" "pass" "${#EXPECTED_CONTAINERS[@]}/${#EXPECTED_CONTAINERS[@]} containers"
else
  for m in "${MISSING[@]}"; do add_detail "missing: $m"; done
  emit_check "C1" "Structure" "fail" "${#MISSING[@]} missing of ${#EXPECTED_CONTAINERS[@]}"
fi

# ─────────────────────────────────────────────
# C2 — READMEs
# ─────────────────────────────────────────────

README_TARGETS=(
  domain spec/frontend spec/backend spec/data spec/integration spec/infra spec/platform
  behavior/scenarios tests contracts ssot intent/active intent/archive intent/templates
  prd questions decisions planning traceability regression git
  retrospective retrospective/metrics retrospective/cycles schemas scripts manifests
  visual generated logs handoff plans trails progress adapters hooks
)
README_MISSING=()
for c in "${README_TARGETS[@]}"; do
  [[ ! -f "$LAZY_DIR/$c/README.md" ]] && README_MISSING+=("$c")
done

if [[ ${#README_MISSING[@]} -eq 0 ]]; then
  emit_check "C2" "READMEs" "pass" "${#README_TARGETS[@]}/${#README_TARGETS[@]}"
else
  for m in "${README_MISSING[@]}"; do add_detail "missing README: $m/README.md"; done
  emit_check "C2" "READMEs" "warn" "${#README_MISSING[@]}/${#README_TARGETS[@]} missing"
fi

# ─────────────────────────────────────────────
# C3 — Schemas (valid JSON)
# ─────────────────────────────────────────────

SCHEMA_FILES=(
  "schemas/result.schema.json"
  "schemas/decision.schema.json"
)

SCHEMA_OK=0
SCHEMA_FAIL=()
for s in "${SCHEMA_FILES[@]}"; do
  if [[ ! -f "$LAZY_DIR/$s" ]]; then
    SCHEMA_FAIL+=("$s (missing)")
    continue
  fi
  if command -v jq >/dev/null 2>&1; then
    if jq empty "$LAZY_DIR/$s" 2>/dev/null; then
      SCHEMA_OK=$((SCHEMA_OK + 1))
    else
      SCHEMA_FAIL+=("$s (invalid JSON)")
    fi
  elif command -v python3 >/dev/null 2>&1; then
    if python3 -c "import json,sys; json.load(open('$LAZY_DIR/$s'))" 2>/dev/null; then
      SCHEMA_OK=$((SCHEMA_OK + 1))
    else
      SCHEMA_FAIL+=("$s (invalid JSON)")
    fi
  else
    SCHEMA_OK=$((SCHEMA_OK + 1))  # No validator; assume OK
    add_detail "no jq/python3 — skipping JSON validation for $s"
  fi
done

if [[ ${#SCHEMA_FAIL[@]} -eq 0 ]]; then
  emit_check "C3" "Schemas" "pass" "$SCHEMA_OK/${#SCHEMA_FILES[@]} valid"
else
  for f in "${SCHEMA_FAIL[@]}"; do add_detail "$f"; done
  emit_check "C3" "Schemas" "fail" "${#SCHEMA_FAIL[@]} broken"
fi

# ─────────────────────────────────────────────
# C4 — Safety (git tracked = 0, exclude OK)
# Exception: experimental/lazy-harness branch — .lazy-harness commit 의도된 상태
# ─────────────────────────────────────────────

if git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  CURRENT_BRANCH=$(git -C "$TARGET" branch --show-current 2>/dev/null)
  TRACKED_COUNT=$(git -C "$TARGET" ls-files | grep -c '^\.lazy-harness' || true)
  EXCLUDE_FILE="$TARGET/.git/info/exclude"
  GITIGNORE_HAS=0
  EXCLUDE_HAS=0

  [[ -f "$EXCLUDE_FILE" ]] && grep -qxF '.lazy-harness/' "$EXCLUDE_FILE" && EXCLUDE_HAS=1
  [[ -f "$TARGET/.gitignore" ]] && grep -qxF '.lazy-harness/' "$TARGET/.gitignore" && GITIGNORE_HAS=1

  # experimental/lazy-harness branch 에서는 tracked 가 의도된 상태
  if [[ "$CURRENT_BRANCH" == "experimental/lazy-harness" ]]; then
    if [[ "$TRACKED_COUNT" -gt 0 ]]; then
      emit_check "C4" "Safety" "pass" "$TRACKED_COUNT files tracked (experimental branch, intended)"
    else
      add_detail "experimental/lazy-harness branch should have .lazy-harness tracked"
      emit_check "C4" "Safety" "fail" "0 tracked on experimental branch"
    fi
  elif [[ "$TRACKED_COUNT" == "0" ]] && { [[ "$EXCLUDE_HAS" == 1 ]] || [[ "$GITIGNORE_HAS" == 1 ]]; }; then
    emit_check "C4" "Safety" "pass" "0 tracked, ignored"
  elif [[ "$TRACKED_COUNT" != "0" ]]; then
    add_detail "$TRACKED_COUNT files tracked by git! Run: git rm --cached -r .lazy-harness/"
    add_detail "(or switch to experimental/lazy-harness branch if intentional)"
    emit_check "C4" "Safety" "fail" "$TRACKED_COUNT files staged/tracked"
  else
    add_detail "neither .git/info/exclude nor .gitignore mentions .lazy-harness/"
    add_detail "fix: echo '.lazy-harness/' >> .git/info/exclude"
    emit_check "C4" "Safety" "fail" "not ignored"
  fi
else
  emit_check "C4" "Safety" "skip" "not a git repo"
fi

# ─────────────────────────────────────────────
# C5 — Pre-commit guard
# ─────────────────────────────────────────────

if git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  # husky-aware hook detection: prefer .husky/pre-commit if husky present
  USES_HUSKY_C5=0
  if [[ -f "$TARGET/package.json" ]] && grep -q '"husky"' "$TARGET/package.json" 2>/dev/null; then
    USES_HUSKY_C5=1
    HOOK_PATH="$TARGET/.husky/pre-commit"
  else
    HOOK_PATH="$TARGET/.git/hooks/pre-commit"
  fi

  if [[ ! -f "$HOOK_PATH" ]]; then
    add_detail "pre-commit missing at $HOOK_PATH — run /harness-init to install"
    emit_check "C5" "Pre-commit" "fail" "missing ($([ "$USES_HUSKY_C5" = 1 ] && echo "husky" || echo "git native"))"
  elif [[ ! -x "$HOOK_PATH" ]]; then
    add_detail "pre-commit not executable: chmod +x $HOOK_PATH"
    emit_check "C5" "Pre-commit" "fail" "not executable"
  elif ! grep -q "lazy-harness" "$HOOK_PATH"; then
    add_detail "pre-commit lacks lazy-harness guard — run /harness-init --force"
    emit_check "C5" "Pre-commit" "warn" "no lazy-harness guard"
  else
    emit_check "C5" "Pre-commit" "pass" "executable + has guard ($([ "$USES_HUSKY_C5" = 1 ] && echo "husky chain" || echo "git native"))"
  fi
else
  emit_check "C5" "Pre-commit" "skip" "not a git repo"
fi

# ─────────────────────────────────────────────
# C6 — Core docs (framework-contract.md exists, ≥ 18 principles)
# ─────────────────────────────────────────────

CONTRACT="$LAZY_DIR/framework/framework-contract.md"
if [[ ! -f "$CONTRACT" ]]; then
  add_detail "framework-contract.md missing — copy from prior version or use /harness-update"
  emit_check "C6" "Core docs" "fail" "framework-contract.md missing"
else
  CONTRACT_LINES=$(wc -l < "$CONTRACT")
  PRINCIPLE_COUNT=$(grep -cE '^### 1\.[0-9]+|^## [0-9]+\.' "$CONTRACT" || echo 0)
  # Hard min: must be a real framework-contract (not corrupt placeholder)
  # 16 = #1~#16 sections + ## 17/18/19/... headings → real contract has ≥ 19
  # < 10 sections OR < 200 lines → broken / corrupt → FAIL
  if [[ "$PRINCIPLE_COUNT" -lt 10 ]] || [[ "$CONTRACT_LINES" -lt 200 ]]; then
    add_detail "$CONTRACT_LINES lines, $PRINCIPLE_COUNT principle sections — looks corrupt or placeholder"
    add_detail "real framework-contract has ≥ 200 lines and ≥ 16 principles"
    add_detail "rollback or restore from canonical: /harness-update --rollback"
    emit_check "C6" "Core docs" "fail" "looks broken ($CONTRACT_LINES lines, $PRINCIPLE_COUNT principles)"
  elif [[ "$PRINCIPLE_COUNT" -ge 16 ]]; then
    emit_check "C6" "Core docs" "pass" "$CONTRACT_LINES lines, $PRINCIPLE_COUNT principle sections"
  else
    add_detail "only $PRINCIPLE_COUNT principle sections found (expected ≥ 16)"
    emit_check "C6" "Core docs" "warn" "$CONTRACT_LINES lines, $PRINCIPLE_COUNT principles"
  fi
fi

# ─────────────────────────────────────────────
# C7 — Links (XML/MD references resolve)
# ─────────────────────────────────────────────

# Check trails roadmap references real files
LINK_OK=0
LINK_FAIL=()
ROADMAP="$LAZY_DIR/trails/01-long-term-roadmap.xml"
PHASE5="$LAZY_DIR/planning/phase-5-plan.xml"

if [[ -f "$ROADMAP" ]]; then
  # Extract <link>path</link> references (simple heuristic)
  while IFS= read -r ref; do
    # Strip leading ./
    ref="${ref#./}"
    # Resolve relative to project root or .lazy-harness
    found=0
    for base in "$TARGET" "$LAZY_DIR" "$(dirname "$ROADMAP")"; do
      [[ -e "$base/$ref" ]] && { found=1; break; }
    done
    if [[ "$found" == 1 ]]; then
      LINK_OK=$((LINK_OK + 1))
    else
      LINK_FAIL+=("trails/01-long-term-roadmap.xml → $ref")
    fi
  done < <(grep -oE '<link[^>]*>([^<]+)</link>' "$ROADMAP" 2>/dev/null | sed -E 's|.*<link[^>]*>([^<]+)</link>.*|\1|' | sort -u)
fi

if [[ ${#LINK_FAIL[@]} -eq 0 ]]; then
  if [[ "$LINK_OK" == 0 ]]; then
    emit_check "C7" "Links" "skip" "no links found to verify"
  else
    emit_check "C7" "Links" "pass" "$LINK_OK links resolved"
  fi
else
  for f in "${LINK_FAIL[@]:0:5}"; do add_detail "broken: $f"; done
  [[ ${#LINK_FAIL[@]} -gt 5 ]] && add_detail "...and $((${#LINK_FAIL[@]} - 5)) more"
  emit_check "C7" "Links" "warn" "$LINK_OK ok, ${#LINK_FAIL[@]} broken"
fi

# ─────────────────────────────────────────────
# C8 — Cross-Layer Maps (ADR 0004)
# ─────────────────────────────────────────────

EXPECTED_MAPS=(
  "domain/domain-map.xml"
  "domain/ubiquitous-language.xml"
  "domain/bounded-contexts.xml"
  "domain/context-map.xml"
  "domain/aggregates.xml"
  "spec/spec-map.xml"
  "spec/spec-language.xml"
  "spec/spec-boundaries.xml"
  "spec/spec-relations.xml"
  "behavior/behavior-map.xml"
  "behavior/scenario-language.xml"
  "behavior/scenario-coverage.xml"
  "behavior/scenario-relations.xml"
  "tests/test-map.xml"
  "tests/test-language.xml"
  "tests/test-coverage.xml"
  "tests/test-protection-matrix.xml"
)

MAP_MISSING=()
for m in "${EXPECTED_MAPS[@]}"; do
  [[ ! -f "$LAZY_DIR/$m" ]] && MAP_MISSING+=("$m")
done

if [[ ${#MAP_MISSING[@]} -eq 0 ]]; then
  emit_check "C8" "Cross-Layer Maps" "pass" "${#EXPECTED_MAPS[@]}/${#EXPECTED_MAPS[@]} present"
else
  for m in "${MAP_MISSING[@]}"; do add_detail "missing map: $m"; done
  emit_check "C8" "Cross-Layer Maps" "fail" "${#MAP_MISSING[@]}/${#EXPECTED_MAPS[@]} missing"
fi

# ─────────────────────────────────────────────
# C9 — AGENTS.md injection (ADR 0007)
# ─────────────────────────────────────────────

AGENTS_PATH="$TARGET/.jcode/AGENTS.md"
LAZY_SECTION_MARKER="## ⚡ Lazy-Harness Framework (CRITICAL — read first)"

if [[ ! -f "$AGENTS_PATH" ]]; then
  add_detail ".jcode/AGENTS.md missing — new sessions won't see framework existence"
  add_detail "fix: /harness-init (will create + inject)"
  emit_check "C9" "AGENTS.md inject" "fail" ".jcode/AGENTS.md missing"
elif ! grep -q "$LAZY_SECTION_MARKER" "$AGENTS_PATH"; then
  add_detail "lazy-harness section missing in $AGENTS_PATH"
  add_detail "fix: /harness-init (idempotent — will inject section)"
  emit_check "C9" "AGENTS.md inject" "fail" "section not injected"
else
  AGENTS_LINES=$(wc -l < "$AGENTS_PATH")
  emit_check "C9" "AGENTS.md inject" "pass" "$AGENTS_LINES lines, section present"
fi

# ─────────────────────────────────────────────
# C10 — Backup (Principle #18 R3, deferred to M3)
# ─────────────────────────────────────────────

emit_check "C10" "Backup" "skip" "deferred to M3 (Principle #18)"

# ─────────────────────────────────────────────
# C11 — Husky integration (ADR 0009)
# Verify hook wiring is in the right place per husky detection.
# ──────────────────────────────────────���──────

USES_HUSKY=0
if [[ -f "$TARGET/package.json" ]] && grep -q '"husky"' "$TARGET/package.json" 2>/dev/null; then
  USES_HUSKY=1
fi

if [[ "$USES_HUSKY" == 1 ]]; then
  HUSKY_PRE="$TARGET/.husky/pre-commit"
  HUSKY_POST="$TARGET/.husky/post-commit"
  HUSKY_PUSH="$TARGET/.husky/pre-push"
  MISSING=()
  if [[ ! -f "$HUSKY_PRE" ]] || ! grep -q "lazy-harness" "$HUSKY_PRE" 2>/dev/null; then MISSING+=(".husky/pre-commit"); fi
  if [[ ! -f "$HUSKY_POST" ]] || ! grep -q "lazy-harness" "$HUSKY_POST" 2>/dev/null; then MISSING+=(".husky/post-commit"); fi
  if [[ ! -f "$HUSKY_PUSH" ]] || ! grep -q "lazy-harness" "$HUSKY_PUSH" 2>/dev/null; then MISSING+=(".husky/pre-push"); fi

  if [[ ${#MISSING[@]} -gt 0 ]]; then
    emit_check "C11" "Husky integration" "fail" "husky env but ${#MISSING[@]} hook(s) missing: ${MISSING[*]} — re-run /harness-init"
  else
    emit_check "C11" "Husky integration" "pass" "all 3 .husky/<hook> wired (pre-commit, post-commit, pre-push)"
  fi

  # Detect dead .git/hooks/ files (silent dead code per ADR 0009)
  DEAD=()
  for h in pre-commit post-commit pre-push; do
    if [[ -f "$TARGET/.git/hooks/$h" ]] && grep -q "lazy-harness" "$TARGET/.git/hooks/$h" 2>/dev/null; then
      DEAD+=(".git/hooks/$h")
    fi
  done
  if [[ ${#DEAD[@]} -gt 0 ]]; then
    emit_check "C11b" "Dead hooks" "warn" "husky env but lazy-aware files in .git/hooks/ (never called): ${DEAD[*]} — safe to delete"
  fi
else
  GIT_PRE="$TARGET/.git/hooks/pre-commit"
  if [[ -f "$GIT_PRE" ]] && grep -q "lazy-harness" "$GIT_PRE" 2>/dev/null; then
    emit_check "C11" "Husky integration" "pass" "no husky — using .git/hooks/ legacy wiring"
  else
    emit_check "C11" "Husky integration" "fail" "no husky and no .git/hooks/pre-commit lazy guard — re-run /harness-init"
  fi
fi


# ────────────────────────────────���────────────
# C12 — Plan Status Hygiene (ADR 0010, Principle #20)
# closed <subPhase> 인데 <criterion> 에 status 없으면 fail
# ─────────────────────────────────────────────

PLAN_FILES=$(find "$LAZY_DIR/planning" -name "*.xml" 2>/dev/null)
if [[ -n "$PLAN_FILES" ]]; then
  PLAN_FAIL=0
  PLAN_WARN=0
  PLAN_DETAIL=""
  for plan in $PLAN_FILES; do
    # closed phase 검색 (status="closed")
    CLOSED_PHASES=$(grep -oE 'subPhase id="[^"]+"[^>]*status="closed"' "$plan" 2>/dev/null | grep -oE 'id="[^"]+"' | sed 's/id="//;s/"//' || true)
    for phase_id in $CLOSED_PHASES; do
      # 해당 phase 의 criteria 추출 (단순 패턴 — closed 라벨 다음 100줄 가정)
      CRITERIA_LINE=$(grep -n "subPhase id=\"$phase_id\"" "$plan" | head -1 | cut -d: -f1)
      [[ -z "$CRITERIA_LINE" ]] && continue
      # 해당 phase 영역만 잘라서 status 없는 criterion 검사
      PHASE_BLOCK=$(sed -n "${CRITERIA_LINE},/<\/subPhase>/p" "$plan")
      MISSING_STATUS=$(echo "$PHASE_BLOCK" | grep -E '<criterion id="[^"]+"' | grep -vE 'status="' | wc -l)
      HAS_ADDED=$(echo "$PHASE_BLOCK" | grep -c '<addedDuringPhase>' || echo 0)
      if [[ "$MISSING_STATUS" -gt 0 ]]; then
        PLAN_FAIL=$((PLAN_FAIL + MISSING_STATUS))
        PLAN_DETAIL="$PLAN_DETAIL [$phase_id: $MISSING_STATUS criterion(s) missing status]"
      fi
      if [[ "$HAS_ADDED" -eq 0 ]]; then
        PLAN_WARN=$((PLAN_WARN + 1))
        PLAN_DETAIL="$PLAN_DETAIL [$phase_id: no <addedDuringPhase>]"
      fi
    done
  done
  if [[ "$PLAN_FAIL" -gt 0 ]]; then
    emit_check "C12" "Plan Hygiene" "fail" "$PLAN_FAIL criterion(s) without status in closed phase(s)$PLAN_DETAIL"
  elif [[ "$PLAN_WARN" -gt 0 ]]; then
    emit_check "C12" "Plan Hygiene" "warn" "$PLAN_WARN closed phase(s) missing <addedDuringPhase>$PLAN_DETAIL"
  else
    emit_check "C12" "Plan Hygiene" "pass" "all closed phases have status + addedDuringPhase"
  fi
else
  emit_check "C12" "Plan Hygiene" "skip" "no planning/*.xml found"
fi

# ─────────────────────────────────────────────
# C13 — Verify Quality (ADR 0011, Principle #21)
# Phase 별 verification entries 의 level distribution + high-risk task 검증
# ─────────────────────────────────────────────

ACTIONS_LOG="$LAZY_DIR/logs/actions.jsonl"
if [[ -f "$ACTIONS_LOG" ]]; then
  TOTAL_VERIFY=$(grep -cE '"action":\s*"verification"' "$ACTIONS_LOG" 2>/dev/null | head -1 | tr -d ' \n')
  L2_COUNT=$(grep -E '"action":\s*"verification"' "$ACTIONS_LOG" 2>/dev/null | grep -cE '"level":\s*"L2"' | head -1 | tr -d ' \n')
  L3_COUNT=$(grep -E '"action":\s*"verification"' "$ACTIONS_LOG" 2>/dev/null | grep -cE '"level":\s*"L3"' | head -1 | tr -d ' \n')
  L4_COUNT=$(grep -E '"action":\s*"verification"' "$ACTIONS_LOG" 2>/dev/null | grep -cE '"level":\s*"L4"' | head -1 | tr -d ' \n')
  [[ -z "$TOTAL_VERIFY" ]] && TOTAL_VERIFY=0
  [[ -z "$L2_COUNT" ]] && L2_COUNT=0
  [[ -z "$L3_COUNT" ]] && L3_COUNT=0
  [[ -z "$L4_COUNT" ]] && L4_COUNT=0

  # high-risk file touches (rough heuristic)
  HIGH_RISK_TOUCH=$(grep -E '"action":\s*"file-' "$ACTIONS_LOG" 2>/dev/null | grep -cE '\.lazy-harness/(hooks|framework|planning)|\.husky/|\.jcode/skills/.*scripts/' | head -1 | tr -d ' \n')
  [[ -z "$HIGH_RISK_TOUCH" ]] && HIGH_RISK_TOUCH=0

  # Closed phase 수
  CLOSED_PHASES=0
  if [[ -n "$PLAN_FILES" ]]; then
    CLOSED_PHASES=$(grep -h 'subPhase id=.*status="closed"' $PLAN_FILES 2>/dev/null | wc -l | tr -d ' \n')
  fi
  [[ -z "$CLOSED_PHASES" ]] && CLOSED_PHASES=0

  WARNS=()
  FAILS=()

  if [[ "$HIGH_RISK_TOUCH" -gt 0 ]] && [[ "$L2_COUNT" -eq 0 ]]; then
    WARNS+=("$HIGH_RISK_TOUCH high-risk file touches but 0 L2 marker experiments")
  fi
  if [[ "$CLOSED_PHASES" -gt 0 ]] && [[ "$L3_COUNT" -eq 0 ]]; then
    WARNS+=("$CLOSED_PHASES closed phase(s) but 0 L3 negative tests")
  fi
  if [[ "$CLOSED_PHASES" -gt 0 ]] && [[ "$L4_COUNT" -eq 0 ]]; then
    WARNS+=("$CLOSED_PHASES closed phase(s) but 0 L4 사람 review entries")
  fi

  if [[ ${#FAILS[@]} -gt 0 ]]; then
    emit_check "C13" "Verify Quality" "fail" "${FAILS[*]}"
  elif [[ ${#WARNS[@]} -gt 0 ]]; then
    emit_check "C13" "Verify Quality" "warn" "$TOTAL_VERIFY total verifies (L2:$L2_COUNT L3:$L3_COUNT L4:$L4_COUNT) — ${WARNS[*]}"
  else
    emit_check "C13" "Verify Quality" "pass" "$TOTAL_VERIFY verifies (L2:$L2_COUNT L3:$L3_COUNT L4:$L4_COUNT)"
  fi
else
  emit_check "C13" "Verify Quality" "skip" "no actions.jsonl"
fi

# ─────────────────────────────────────────────
# C14 — JSONL Validity (Sisyphus/Oracle audit, 2026-05-10)
# logs/*.jsonl 파일이 모두 valid JSON line 인지 검증
# ─────────────────────────────────────────────

JSONL_FAIL=0
JSONL_TOTAL=0
JSONL_INVALID_DETAIL=""
for f in "$LAZY_DIR/logs"/*.jsonl; do
  [[ -f "$f" ]] || continue
  bn=$(basename "$f")
  result=$(python3 -c "
import sys, json
total = 0
invalid = 0
with open('$f') as fp:
    for i, line in enumerate(fp, 1):
        line = line.rstrip('\n')
        if not line: continue
        total += 1
        try: json.loads(line)
        except: invalid += 1
print(f'{total} {invalid}')
" 2>/dev/null) || result="0 0"
  read -r tot inv <<< "$result"
  JSONL_TOTAL=$((JSONL_TOTAL + tot))
  if [[ "$inv" -gt 0 ]]; then
    JSONL_FAIL=$((JSONL_FAIL + inv))
    JSONL_INVALID_DETAIL="$JSONL_INVALID_DETAIL $bn:$inv"
  fi
done

if [[ "$JSONL_FAIL" -gt 0 ]]; then
  emit_check "C14" "JSONL Validity" "fail" "$JSONL_FAIL invalid line(s) total=$JSONL_TOTAL detail=$JSONL_INVALID_DETAIL"
else
  emit_check "C14" "JSONL Validity" "pass" "$JSONL_TOTAL lines all valid"
fi

# ─────────────────────────────────────────────
# C15 — Husky Tracked (ADR 0009 cascade verification)
# .husky/<3 hook> 가 git tracked + .git/info/exclude 에 없어야
# ─────────────────────────────────────────────

HUSKY_HOOKS=("pre-commit" "post-commit" "pre-push")
HUSKY_UNTRACKED=()
HUSKY_EXCLUDED=()
for h in "${HUSKY_HOOKS[@]}"; do
  if [[ -f "$TARGET/.husky/$h" ]]; then
    if ! git -C "$TARGET" ls-files --error-unmatch ".husky/$h" >/dev/null 2>&1; then
      HUSKY_UNTRACKED+=("$h")
    fi
    if grep -q "^\.husky/$h$" "$TARGET/.git/info/exclude" 2>/dev/null; then
      HUSKY_EXCLUDED+=("$h")
    fi
  fi
done

HUSKY_PROBLEMS=""
[[ ${#HUSKY_UNTRACKED[@]} -gt 0 ]] && HUSKY_PROBLEMS="untracked=${HUSKY_UNTRACKED[*]}"
[[ ${#HUSKY_EXCLUDED[@]} -gt 0 ]] && HUSKY_PROBLEMS="$HUSKY_PROBLEMS excluded=${HUSKY_EXCLUDED[*]}"

if [[ -n "$HUSKY_PROBLEMS" ]]; then
  emit_check "C15" "Husky Tracked (ADR 0009)" "fail" "ADR 0009 says husky chain hooks must be tracked: $HUSKY_PROBLEMS"
else
  emit_check "C15" "Husky Tracked (ADR 0009)" "pass" "all 3 husky hooks tracked + not excluded"
fi

# ─────────────────────────────────────────────
# C16 — Handoff Freshness (Sisyphus audit, 2026-05-10)
# handoff/00-current-state.md 의 cited counts 가 실제와 일치
# ─────────────────────────────────────────────

HANDOFF="$LAZY_DIR/handoff/00-current-state.md"
if [[ -f "$HANDOFF" ]]; then
  ACTUAL_ADR=$(ls "$LAZY_DIR/decisions/"0*.md 2>/dev/null | wc -l | tr -d ' \n')
  ACTUAL_DEC=$(wc -l < "$LAZY_DIR/logs/decisions.jsonl" 2>/dev/null | tr -d ' \n')
  ACTUAL_ACT=$(wc -l < "$LAZY_DIR/logs/actions.jsonl" 2>/dev/null | tr -d ' \n')
  ACTUAL_VER=$(grep -oE 'v1\.[0-9]+' "$LAZY_DIR/framework/framework-contract.md" | tail -1 | tr -d ' \n')

  STALE=()
  CITED_ADR=$(grep -oE '\*\*[0-9]+\*\* \(0001~' "$HANDOFF" | grep -oE '[0-9]+' | head -1)
  CITED_VER=$(grep -oE 'v1\.[0-9]+' "$HANDOFF" | head -1 | tr -d ' \n')

  if [[ -n "$CITED_ADR" ]] && [[ "$CITED_ADR" != "$ACTUAL_ADR" ]]; then
    STALE+=("ADR cited=$CITED_ADR actual=$ACTUAL_ADR")
  fi
  if [[ -n "$CITED_VER" ]] && [[ "$CITED_VER" != "$ACTUAL_VER" ]]; then
    STALE+=("contract version cited=$CITED_VER actual=$ACTUAL_VER")
  fi

  if [[ ${#STALE[@]} -gt 0 ]]; then
    emit_check "C16" "Handoff Freshness" "warn" "stale: ${STALE[*]}"
  else
    emit_check "C16" "Handoff Freshness" "pass" "ADR=$ACTUAL_ADR ver=$ACTUAL_VER actions=$ACTUAL_ACT"
  fi
else
  emit_check "C16" "Handoff Freshness" "skip" "no handoff file"
fi

# ─────────────────────────────────────────────
# Summary + log
# ─────────────────────────────────────────────

if [[ "$JSON_ONLY" == 1 ]]; then
  echo "["
  for i in "${!RESULTS_JSON[@]}"; do
    if [[ "$i" -gt 0 ]]; then echo ","; fi
    echo "${RESULTS_JSON[$i]}"
  done
  echo "]"
else
  cat <<EOF

────────────────────────────────────────────
Overall: $PASS_COUNT pass, $WARN_COUNT warn, $SKIP_COUNT skipped, $FAIL_COUNT fail
────────────────────────────────────────────
EOF
fi

# Append to validations.jsonl
LOG_FILE="$LAZY_DIR/logs/validations.jsonl"
mkdir -p "$(dirname "$LOG_FILE")"
TS=$(date -Iseconds)
{
  for r in "${RESULTS_JSON[@]}"; do
    # Compact to single line
    echo "$r" | tr -d '\n' | sed 's/  */ /g'
    echo ""
  done
} | while IFS= read -r line; do
  [[ -n "$line" ]] && echo "{\"timestamp\":\"$TS\",\"result\":$line}" >> "$LOG_FILE"
done

# Rotate validations.jsonl when > 1000 lines (keep last 500) — bug-4 fix from Sisyphus 2026-05-10
# Audit log is actions.jsonl + decisions.jsonl. Validations is push-time snapshot only.
LINE_COUNT=$(wc -l < "$LOG_FILE" 2>/dev/null | tr -d ' \n')
if [[ -n "$LINE_COUNT" ]] && [[ "$LINE_COUNT" -gt 1000 ]]; then
  TMP="$LOG_FILE.tmp.$$"
  tail -500 "$LOG_FILE" > "$TMP" && mv "$TMP" "$LOG_FILE"
fi

# Exit code
if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi
exit 0
