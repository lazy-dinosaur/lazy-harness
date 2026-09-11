#!/usr/bin/env bash
# Correction capture shares the LLM judgement + structural evidence contract.
# This is not execution approval; ADR 0038 and pre-action safeguards still apply.
# Keep the explicit helper entrypoint, but do not classify correction prose.
set -euo pipefail
exec bash "$(dirname "$0")/check-analysis-discovery-capture.sh" "${1:-}"
