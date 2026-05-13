#!/usr/bin/env bash
set -euo pipefail

# lazy-harness public installer
#
# Generic, secret-free bootstrapper for host projects. It keeps a local source
# clone under ~/.cache/lazy-harness/source by default, then delegates the actual
# framework layout to .lazy-harness/scripts/lazy-init.ts.

REPO_URL="https://github.com/lazy-dinosaur/lazy-harness.git"
REF="main"
TARGET="$PWD"
SOURCE=""
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/lazy-harness/source"
FORCE=0
DRY_RUN=0
SKIP_HOOKS=0
INSTALL_JCODE=0
QUIET=0

usage() {
  cat <<'EOF'
lazy-harness installer

Usage:
  ./install.sh [options]
  curl -fsSL https://raw.githubusercontent.com/lazy-dinosaur/lazy-harness/main/install.sh | bash -s -- [options]

Options:
  --target <dir>     Host project root to install into. Default: current directory.
  --repo <url>       Framework git repository URL. Default: public lazy-harness repo.
  --ref <ref>        Branch, tag, or commit to install. Default: main.
  --source <dir>     Use an existing local lazy-harness source checkout instead of cloning.
  --cache-dir <dir>  Persistent clone location when --source is not supplied.
                     Default: ${XDG_CACHE_HOME:-$HOME/.cache}/lazy-harness/source
  --force            Pass --force to lazy-init for existing .lazy-harness/.
  --dry-run          Print planned actions without changing the target.
  --skip-hooks       Do not wire the host git pre-commit hook.
  --jcode            Also attempt to install tracked .jcode skills if present.
                     Default is off because public repo keeps private .jcode out.
  --quiet            Suppress per-file lazy-init logs.
  -h, --help         Show this help.

Requirements:
  - git
  - bun
  - target must already be a git repository

Examples:
  # Install into current git repo
  curl -fsSL https://raw.githubusercontent.com/lazy-dinosaur/lazy-harness/main/install.sh | bash

  # Dry-run install into another repo
  ./install.sh --target ../my-app --dry-run

  # Dogfood from a local framework checkout
  ./install.sh --target /path/to/host --source /home/lazydino/dev/lazy-harness --force
EOF
}

log() {
  if [[ "$QUIET" != "1" ]]; then
    printf '%s\n' "$*"
  fi
}

fail() {
  printf 'lazy-harness install error: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || fail "--target requires a value"
      TARGET="$2"
      shift 2
      ;;
    --repo)
      [[ $# -ge 2 ]] || fail "--repo requires a value"
      REPO_URL="$2"
      shift 2
      ;;
    --ref)
      [[ $# -ge 2 ]] || fail "--ref requires a value"
      REF="$2"
      shift 2
      ;;
    --source)
      [[ $# -ge 2 ]] || fail "--source requires a value"
      SOURCE="$2"
      shift 2
      ;;
    --cache-dir)
      [[ $# -ge 2 ]] || fail "--cache-dir requires a value"
      CACHE_DIR="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-hooks)
      SKIP_HOOKS=1
      shift
      ;;
    --jcode)
      INSTALL_JCODE=1
      shift
      ;;
    --quiet)
      QUIET=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

command -v git >/dev/null 2>&1 || fail "git is required"
command -v bun >/dev/null 2>&1 || fail "bun is required"

TARGET="$(cd "$TARGET" 2>/dev/null && pwd -P)" || fail "target does not exist: $TARGET"
[[ -e "$TARGET/.git" ]] || fail "target must be a git repository: $TARGET"

if [[ -n "$SOURCE" ]]; then
  SOURCE="$(cd "$SOURCE" 2>/dev/null && pwd -P)" || fail "source does not exist: $SOURCE"
  [[ -f "$SOURCE/.lazy-harness/scripts/lazy-init.ts" ]] || fail "source is not a lazy-harness checkout: $SOURCE"
else
  SOURCE="$CACHE_DIR"
  if [[ -d "$SOURCE/.git" ]]; then
    log "Updating cached lazy-harness source: $SOURCE"
    git -C "$SOURCE" remote set-url origin "$REPO_URL"
    git -C "$SOURCE" fetch origin --tags
  else
    log "Cloning lazy-harness source: $REPO_URL → $SOURCE"
    mkdir -p "$(dirname "$SOURCE")"
    git clone "$REPO_URL" "$SOURCE"
  fi

  if git -C "$SOURCE" show-ref --verify --quiet "refs/remotes/origin/$REF"; then
    git -C "$SOURCE" checkout -B "$REF" "origin/$REF" >/dev/null
  else
    git -C "$SOURCE" checkout "$REF" >/dev/null
  fi
fi

INIT_ARGS=("$SOURCE/.lazy-harness/scripts/lazy-init.ts" --target "$TARGET" --from "$SOURCE")
[[ "$FORCE" == "1" ]] && INIT_ARGS+=(--force)
[[ "$DRY_RUN" == "1" ]] && INIT_ARGS+=(--dry-run)
[[ "$SKIP_HOOKS" == "1" ]] && INIT_ARGS+=(--skip-hooks)
[[ "$INSTALL_JCODE" == "1" ]] || INIT_ARGS+=(--skip-jcode)
[[ "$QUIET" == "1" ]] && INIT_ARGS+=(--quiet)

log "Installing lazy-harness"
log "  source: $SOURCE"
log "  target: $TARGET"
log "  ref:    $(git -C "$SOURCE" rev-parse --short HEAD 2>/dev/null || printf unknown)"

bun "${INIT_ARGS[@]}"

if [[ "$DRY_RUN" != "1" ]]; then
  log ""
  log "Installed. Validate with:"
  log "  cd $TARGET"
  log "  python3 .lazy-harness/scripts/doctor.py --profile smoke"
  log "  python3 .lazy-harness/scripts/self-test.py --scope host"
fi
