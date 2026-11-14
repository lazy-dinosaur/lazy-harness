#!/usr/bin/env bash
# Shared by public install, update, and Pi/OMP package registration. Bash 3.2 compatible.
set -euo pipefail
SOURCE="${1:?source checkout required}"
DRY_RUN="${2:-}"
if [[ "$DRY_RUN" == "--dry-run" ]]; then
  printf '%s\n' '[dry-run] git submodule update --init --recursive vendor/lazy-harness-monitoring' '[dry-run] bun install --frozen-lockfile (source root)' '[dry-run] bun install --frozen-lockfile (vendor/lazy-harness-monitoring)'
  exit 0
fi
fail() {
  printf '%s\n' "lazy-harness dependency preparation failed: $1" 'Repair from the source checkout: git submodule update --init --recursive vendor/lazy-harness-monitoring, then bun install --frozen-lockfile at the root and inside the submodule. Check Git/Bun availability and network access, then retry lazy pi install.' >&2
  exit 1
}
command -v git >/dev/null 2>&1 || fail 'git is required (macOS: Xcode Command Line Tools)'
command -v bun >/dev/null 2>&1 || fail 'bun is required; see installation prerequisites in README.md'
git -C "$SOURCE" submodule update --init --recursive vendor/lazy-harness-monitoring || fail 'monitoring submodule initialization'
[[ -f "$SOURCE/vendor/lazy-harness-monitoring/package.json" ]] || fail 'monitoring checkout is empty'
(cd "$SOURCE" && bun install --frozen-lockfile) || fail 'root frozen install'
(cd "$SOURCE/vendor/lazy-harness-monitoring" && bun install --frozen-lockfile) || fail 'monitoring frozen install'
