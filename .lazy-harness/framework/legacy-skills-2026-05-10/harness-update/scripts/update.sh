#!/usr/bin/env bash
# update.sh
# Sync framework-contract.md from canonical source.
# Auto-backup before apply. Auto-rollback if doctor fails.
#
# Spec: framework-contract Principle #18, Section 18.2
# Skill: .jcode/skills/harness-update/SKILL.md

set -uo pipefail

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

usage() {
  cat <<'USAGE'
Usage: update.sh [--from PATH] [--dry-run] [--rollback [DATE|--list]] [--target DIR] [--force]

Sync .lazy-harness/framework/framework-contract.md from canonical source.

Modes:
  (default)        apply update with auto-backup + auto-rollback on doctor fail
  --dry-run        show diff only, no changes (5a-6)
  --rollback       restore most recent backup (5a-7)
  --rollback DATE  restore specific backup (e.g. 2026-05-10T14-30-00)
  --rollback --list  list available backups

Source priority (when not --from):
  1. $LAZY_HARNESS_SOURCE env var
  2. ~/.jcode/framework-contract.md
  3. ~/.lazy-harness-canonical/framework-contract.md

Options:
  --from PATH      explicit source file
  --target DIR     project root (default: cwd)
  --force          continue even if doctor warns (NEVER skips backup)
  -h, --help       show help

Exit:
  0   success
  1   apply failed (rolled back)
  2   source missing or doctor fail
  3   rollback failed (HUMAN INTERVENTION REQUIRED)
USAGE
}

TARGET="${PWD}"
SOURCE=""
DRY_RUN=0
ROLLBACK=0
ROLLBACK_DATE=""
ROLLBACK_LIST=0
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) shift; SOURCE="${1:-}" ;;
    --dry-run) DRY_RUN=1 ;;
    --rollback)
      ROLLBACK=1
      # peek next arg
      if [[ $# -gt 1 ]]; then
        case "${2:-}" in
          --list) ROLLBACK_LIST=1; shift ;;
          --*|"") ;;
          *) ROLLBACK_DATE="$2"; shift ;;
        esac
      fi
      ;;
    --target) shift; TARGET="${1:-$PWD}" ;;
    --force) FORCE=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

TARGET=$(realpath -m "$TARGET")
LAZY_DIR="$TARGET/.lazy-harness"
CONTRACT="$LAZY_DIR/framework/framework-contract.md"
BACKUP_ROOT="$TARGET/.lazy-harness-backup"

if [[ ! -d "$LAZY_DIR" ]]; then
  echo "Error: .lazy-harness/ not found at $TARGET" >&2
  echo "Hint: run /harness-init first" >&2
  exit 2
fi

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

list_backups() {
  if [[ ! -d "$BACKUP_ROOT" ]]; then
    echo "(no backups)"
    return
  fi
  # Exclude safety snapshots (rollback-from-*) — those are recovery points, not normal backups
  find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d -printf "%f\n" \
    | grep -v '^rollback-from-' \
    | sort -r
}

list_safety_snapshots() {
  if [[ ! -d "$BACKUP_ROOT" ]]; then return; fi
  find "$BACKUP_ROOT" -maxdepth 1 -mindepth 1 -type d -printf "%f\n" \
    | grep '^rollback-from-' \
    | sort -r
}

get_doctor_path() {
  # Prefer same-project skill, then fallback
  local p1="$TARGET/.jcode/skills/harness-doctor/scripts/doctor.sh"
  local p2="$HOME/.jcode/skills/harness-doctor/scripts/doctor.sh"
  if [[ -x "$p1" ]]; then echo "$p1"
  elif [[ -x "$p2" ]]; then echo "$p2"
  else echo ""
  fi
}

run_doctor() {
  local doctor
  doctor=$(get_doctor_path)
  if [[ -z "$doctor" ]]; then
    echo "  ⚠ harness-doctor not found, skipping post-apply check" >&2
    return 0
  fi
  "$doctor" --target "$TARGET" >/dev/null 2>&1
}

# ─────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────

cat <<EOF

╭────────────────────────────────────────────╮
│ lazy-harness update                        │
│ target: $TARGET
╰────────────────────────────────────────────╯

EOF

# ─────────────────────────────────────────────
# Mode: --rollback --list
# ─────────────────────────────────────────────

if [[ "$ROLLBACK" == 1 ]] && [[ "$ROLLBACK_LIST" == 1 ]]; then
  echo "Available backups in $BACKUP_ROOT:"
  list_backups | while IFS= read -r b; do
    [[ -z "$b" ]] && continue
    meta="$BACKUP_ROOT/$b/.meta.json"
    if [[ -f "$meta" ]]; then
      printf "  %s  %s\n" "$b" "$(grep -oE '"source"\s*:\s*"[^"]*"' "$meta" 2>/dev/null | sed 's/.*: "//; s/"$//' | head -1)"
    else
      printf "  %s  (no meta)\n" "$b"
    fi
  done
  exit 0
fi

# ─────────────────────────────────────────────
# Mode: --rollback
# ─────────────────────────────────────────────

if [[ "$ROLLBACK" == 1 ]]; then
  if [[ -z "$ROLLBACK_DATE" ]]; then
    ROLLBACK_DATE=$(list_backups | head -1)
    if [[ -z "$ROLLBACK_DATE" ]]; then
      echo "Error: no backups available" >&2
      exit 3
    fi
    echo "→ rolling back to most recent: $ROLLBACK_DATE"
  else
    echo "→ rolling back to: $ROLLBACK_DATE"
  fi

  BACKUP_DIR="$BACKUP_ROOT/$ROLLBACK_DATE"
  BACKUP_FILE="$BACKUP_DIR/framework-contract.md"

  if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Error: backup not found: $BACKUP_FILE" >&2
    echo "Available:" >&2
    list_backups | sed 's/^/  /' >&2
    exit 3
  fi

  # Save current as safety-backup before rollback
  SAFETY_DATE="rollback-from-$(date -u +%Y%m%dT%H%M%SZ)"
  SAFETY_DIR="$BACKUP_ROOT/$SAFETY_DATE"
  mkdir -p "$SAFETY_DIR"
  if [[ -f "$CONTRACT" ]]; then
    cp "$CONTRACT" "$SAFETY_DIR/framework-contract.md"
    cat > "$SAFETY_DIR/.meta.json" <<EOF
{
  "type": "safety-pre-rollback",
  "rolling-back-to": "$ROLLBACK_DATE",
  "timestamp": "$(date -Iseconds)"
}
EOF
    echo "  ✓ safety snapshot: $SAFETY_DATE"
  fi

  # Apply rollback
  cp "$BACKUP_FILE" "$CONTRACT"
  echo "  ✓ restored: $CONTRACT"

  # Verify with doctor
  if run_doctor; then
    echo "  ✓ doctor passed after rollback"
    exit 0
  else
    echo "  ✗ doctor failed after rollback. Safety snapshot at $SAFETY_DIR" >&2
    exit 3
  fi
fi

# ─────────────────────────────────────────────
# Source resolution (apply or dry-run mode)
# ─────────────────────────────────────────────

if [[ -z "$SOURCE" ]]; then
  if [[ -n "${LAZY_HARNESS_SOURCE:-}" ]]; then
    SOURCE="$LAZY_HARNESS_SOURCE"
  elif [[ -f "$HOME/.jcode/framework-contract.md" ]]; then
    SOURCE="$HOME/.jcode/framework-contract.md"
  elif [[ -f "$HOME/.lazy-harness-canonical/framework-contract.md" ]]; then
    SOURCE="$HOME/.lazy-harness-canonical/framework-contract.md"
  else
    cat >&2 <<EOF
Error: no source found. Provide one of:
  --from PATH                                       (explicit)
  export LAZY_HARNESS_SOURCE=/path/to/contract.md   (env)
  ~/.jcode/framework-contract.md                    (global canonical)
  ~/.lazy-harness-canonical/framework-contract.md   (offline canonical)

Or seed canonical from current project:
  mkdir -p ~/.jcode && cp $CONTRACT ~/.jcode/framework-contract.md
EOF
    exit 2
  fi
fi

if [[ ! -f "$SOURCE" ]]; then
  echo "Error: source file does not exist: $SOURCE" >&2
  exit 2
fi

echo "Source: $SOURCE"
echo "Target: $CONTRACT"
echo ""

# ─────────────────────────────────────────────
# Diff preview
# ─────────────────────────────────────────────

if [[ ! -f "$CONTRACT" ]]; then
  echo "→ target framework-contract.md does not exist (first-time install)"
  if [[ "$DRY_RUN" == 1 ]]; then
    echo "[dry-run] would copy $SOURCE → $CONTRACT"
    wc -l "$SOURCE" | sed 's/^/  source: /'
    exit 0
  fi
else
  echo "Diff (source → target):"
  if diff -q "$SOURCE" "$CONTRACT" >/dev/null 2>&1; then
    echo "  (no changes — already in sync)"
    exit 0
  fi
  if command -v diff >/dev/null 2>&1; then
    diff -u "$CONTRACT" "$SOURCE" 2>/dev/null | head -60 | sed 's/^/  /'
    DIFF_LINES=$(diff "$CONTRACT" "$SOURCE" 2>/dev/null | wc -l)
    echo "  ... ($DIFF_LINES diff lines total)"
  fi
  echo ""

  if [[ "$DRY_RUN" == 1 ]]; then
    echo "[dry-run] would replace target with source. Use without --dry-run to apply."
    exit 0
  fi
fi

# ─────────────────────────────────────────────
# Backup before apply (Principle #18 R1)
# ─────────────────────────────────────────────

NOW=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR="$BACKUP_ROOT/$NOW"
mkdir -p "$BACKUP_DIR"

if [[ -f "$CONTRACT" ]]; then
  cp "$CONTRACT" "$BACKUP_DIR/framework-contract.md"
  echo "✓ backup: $BACKUP_DIR/framework-contract.md"
else
  echo "  (no existing target to backup)"
fi

# Add backup root to .git/info/exclude if not already
if git -C "$TARGET" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  EXCLUDE="$TARGET/.git/info/exclude"
  if ! grep -qxF '.lazy-harness-backup/' "$EXCLUDE" 2>/dev/null; then
    echo '.lazy-harness-backup/' >> "$EXCLUDE"
    echo "  ✓ added .lazy-harness-backup/ to .git/info/exclude"
  fi
fi

# ─────────────────────────────────────────────
# Apply
# ─────────────────────────────────────────────

cp "$SOURCE" "$CONTRACT"
echo "✓ applied: $CONTRACT"

# Write meta
cat > "$BACKUP_DIR/.meta.json" <<EOF
{
  "type": "pre-update-snapshot",
  "source": "$SOURCE",
  "target": "$CONTRACT",
  "timestamp": "$(date -Iseconds)",
  "applied_by": "harness-update"
}
EOF

# ─────────────────────────────────────────────
# Post-apply: run doctor (Principle #18 R1 verify)
# ─────────────────────────────────────────────

echo ""
echo "→ running harness-doctor..."

if run_doctor; then
  echo "✓ doctor passed. Update successful."

  # Trim old backups (keep last 5)
  if [[ -d "$BACKUP_ROOT" ]]; then
    KEPT=0
    list_backups | while IFS= read -r b; do
      KEPT=$((KEPT + 1))
      if [[ "$KEPT" -gt 5 ]]; then
        rm -rf "$BACKUP_ROOT/$b" 2>/dev/null
        echo "  ✓ trimmed old backup: $b"
      fi
    done
  fi

  exit 0
else
  echo "✗ doctor FAILED after apply." >&2
  if [[ "$FORCE" == 1 ]]; then
    echo "  --force given; keeping update despite failure." >&2
    echo "  Manual rollback: $0 --rollback $NOW" >&2
    exit 1
  fi
  echo "  → auto-rolling back from $BACKUP_DIR..." >&2

  if [[ -f "$BACKUP_DIR/framework-contract.md" ]]; then
    cp "$BACKUP_DIR/framework-contract.md" "$CONTRACT"
    echo "  ✓ rolled back" >&2
    exit 1
  else
    echo "  ✗ no backup to roll back to. CONTRACT MAY BE BROKEN." >&2
    echo "  HUMAN INTERVENTION REQUIRED" >&2
    exit 3
  fi
fi
