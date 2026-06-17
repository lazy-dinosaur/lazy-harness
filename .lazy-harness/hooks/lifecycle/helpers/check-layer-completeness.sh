#!/usr/bin/env bash
# check-layer-completeness.sh — prevent TDD/regression-only record completion
#
# If an agent writes a TDD/regression record, it must also document the cross-layer
# impact check in the same turn. Either update SDD/BDD/SSOT/DDD records or add a
# `Layer completeness` section to the TDD record that explicitly mentions all four.

set -euo pipefail

PAYLOAD="${1:-}"
[ -z "$PAYLOAD" ] && exit 0

python3 - "$PAYLOAD" <<'PY'
import json
import pathlib
import re
import sys

payload_text = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    payload = json.loads(payload_text)
except Exception:
    raise SystemExit(0)

allowed = {
    "Write",
    "Edit",
    "MultiEdit",
    "write",
    "edit",
    "multiedit",
    "mcp__filesystem__write_file",
    "mcp__filesystem__edit_file",
}
pattern = re.compile(r"""\.lazy-harness/(?:domain|spec|behavior|tests|decisions|ssot|regression)/[^\s"',)}]+\.(?:md|jsonl|xml|json)""")
paths: list[str] = []
for call in payload.get("recent_tool_calls", []):
    if not isinstance(call, dict) or str(call.get("name", "")) not in allowed:
        continue
    for match in pattern.finditer(str(call.get("args_preview", ""))):
        paths.append(match.group(0))

files = list(dict.fromkeys(path for path in paths if path))
if not files:
    raise SystemExit(0)

touched_tdd = False
touched_other_layer = False
for file in files:
    if file == ".lazy-harness/tests/test-strategy.xml":
        continue
    if (
        file.startswith(".lazy-harness/tests/") and file.endswith(".md")
    ) or file.startswith(".lazy-harness/regression/"):
        touched_tdd = True
    elif file.startswith((
        ".lazy-harness/spec/",
        ".lazy-harness/behavior/",
        ".lazy-harness/ssot/",
        ".lazy-harness/domain/",
    )):
        touched_other_layer = True

if not touched_tdd or touched_other_layer:
    raise SystemExit(0)

missing: list[str] = []
for file in files:
    if file.startswith(".lazy-harness/tests/") and file.endswith(".md"):
        path = pathlib.Path(file)
        if not path.exists():
            missing.append(file)
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not all(token in text for token in ("Layer completeness", "SDD", "BDD", "SSOT", "DDD")):
            missing.append(file)
    elif file.startswith(".lazy-harness/regression/"):
        missing.append(file)

if not missing:
    raise SystemExit(0)

print("STOP. Layer completeness gate: TDD/regression record 만 쓰고 SDD/BDD/SSOT/DDD 영향 판단이 빠졌습니다.\n")
print("누락 후보:")
for file in missing:
    print(f"  - {file}")
print("\n해야 할 일:")
print("  A. 관련 SDD/BDD/SSOT/DDD record 를 같은 turn 에 추가/갱신 (Recommended)")
print("  B. TDD record 에 Layer completeness 섹션을 추가하고 SDD/BDD/SSOT/DDD 각각 영향 없음/있음 판단 기록")
print("  C. layer 가 애매하면 사용자에게 옵션 게이트로 확인")
print("  D. 직접 입력 / skip 사유를 .lazy-harness/logs/skipped.jsonl 에 기록")
print("\n규칙: AGENTS §2.4 Layer completeness gate. TDD 만 추가하고 끝내면 안 됩니다.")
raise SystemExit(0)
PY
