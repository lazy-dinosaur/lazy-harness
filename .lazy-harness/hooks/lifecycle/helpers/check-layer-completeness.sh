#!/usr/bin/env bash
# check-layer-completeness.sh — prevent TDD/regression-only record completion
#
# If an agent writes a TDD/regression record, it must also document the cross-layer
# impact check in the same turn. Update another layer only for an independent semantic
# delta; otherwise add a `Layer completeness` section naming all four as no delta.

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

def is_tdd_markdown(file: str) -> bool:
    return (
        file != ".lazy-harness/tests/test-strategy.xml"
        and file.endswith(".md")
        and (
            file.startswith(".lazy-harness/tests/")
            or file.startswith(".lazy-harness/regression/")
        )
    )

tdd_markdown_files = [file for file in files if is_tdd_markdown(file)]
regression_data_files = [
    file
    for file in files
    if file.startswith(".lazy-harness/regression/") and not file.endswith(".md")
]
if not tdd_markdown_files and not regression_data_files:
    raise SystemExit(0)

missing: list[str] = []
for file in tdd_markdown_files:
    path = pathlib.Path(file)
    if not path.exists():
        missing.append(file)
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    has_matrix = "Layer completeness" in text and all(
        re.search(rf"(?mi)^\s*[-*]\s*{layer}\s*:\s*\S.*$", text)
        for layer in ("SDD", "BDD", "SSOT", "DDD")
    )
    if not has_matrix:
        missing.append(file)

if regression_data_files and not tdd_markdown_files:
    missing.extend(regression_data_files)

if not missing:
    raise SystemExit(0)

print("STOP. Layer completeness gate: TDD/regression record 의 SDD/BDD/SSOT/DDD 명시적 판단 matrix 가 빠졌습니다.\n")
print("누락 후보:")
for file in missing:
    print(f"  - {file}")
print("\n해야 할 일:")
print("  A. TDD record 에 `- SDD: ...` / BDD / SSOT / DDD 네 개의 명시적 판단을 추가 (Recommended)")
print("  B. 독립적으로 바뀐 invariant 가 있으면 그 layer 의 primary record 도 갱신·cross-link; 없으면 no independent delta/영향 없음 기록")
print("  C. layer 가 애매하면 사용자에게 옵션 게이트로 확인")
print("  D. 직접 입력 / skip 사유를 .lazy-harness/logs/skipped.jsonl 에 기록")
print("\n규칙: AGENTS §2.4 Primary canonical record + Layer completeness gate. 후보/관련성만으로 여러 layer 에 같은 내용을 복제하면 안 됩니다.")
raise SystemExit(0)
PY
