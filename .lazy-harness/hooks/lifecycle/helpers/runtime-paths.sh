#!/usr/bin/env bash
# runtime-paths.sh — resolve per-session/worktree runtime state and shared bus roots.
# Source this file from lifecycle hooks after resolving LAZY_HOST_ROOT.

lazy_runtime_root() {
  local root="${1:-${LAZY_HOST_ROOT:-$(pwd)}}"
  local payload="${2:-}"
  LAZY_HOST_ROOT="$root" python3 "$root/.lazy-harness/hooks/lifecycle/helpers/runtime_paths.py" runtime-root "$payload" 2>/dev/null || true
}

lazy_shared_root() {
  local root="${1:-${LAZY_HOST_ROOT:-$(pwd)}}"
  LAZY_HOST_ROOT="$root" python3 "$root/.lazy-harness/hooks/lifecycle/helpers/runtime_paths.py" shared-root 2>/dev/null || true
}

lazy_export_runtime_env() {
  local root="${1:-${LAZY_HOST_ROOT:-$(pwd)}}"
  local payload="${2:-}"
  if [ -z "${LAZY_RUNTIME_ROOT:-}" ]; then
    local runtime
    runtime=$(lazy_runtime_root "$root" "$payload")
    [ -n "$runtime" ] && export LAZY_RUNTIME_ROOT="$runtime"
  fi
  if [ -z "${LAZY_SHARED_ROOT:-}" ]; then
    local shared
    shared=$(lazy_shared_root "$root")
    [ -n "$shared" ] && export LAZY_SHARED_ROOT="$shared"
  fi
}

lazy_state_file() {
  local name="$1"
  local root="${2:-${LAZY_HOST_ROOT:-$(pwd)}}"
  local payload="${3:-}"
  local runtime="${LAZY_RUNTIME_ROOT:-$(lazy_runtime_root "$root" "$payload")}" 
  printf '%s/state/%s' "$runtime" "$name"
}

lazy_log_file() {
  local name="$1"
  local root="${2:-${LAZY_HOST_ROOT:-$(pwd)}}"
  local payload="${3:-}"
  local runtime="${LAZY_RUNTIME_ROOT:-$(lazy_runtime_root "$root" "$payload")}" 
  printf '%s/logs/%s' "$runtime" "$name"
}
