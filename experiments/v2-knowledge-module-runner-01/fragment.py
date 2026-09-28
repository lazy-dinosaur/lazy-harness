"""Fragment generation with injected LLM transport.

The caller must use a fresh context, inherit no parent conversation, forbid writes,
and run from a neutral cwd without harness rules. This module does not enforce
process isolation; call_llm must provide it.
"""
import hashlib
from pathlib import Path

# The experiment's checker remains the single implementation of parse/check/repair.
from fragmenter.check_fragments import check, parse, repair_json

PROMPT = Path(__file__).parent / "fragmenter" / "prompt-v2.md"


def render_prompt(record_id, source_path):
    return PROMPT.read_text(encoding="utf-8").replace("{RECORD_ID}", str(record_id)).replace(
        "{SOURCE_PATH}", str(source_path))


def fragment_record(record_id, source_text, source_path, call_llm, max_retries=1):
    """Generate and validate fragments; call_llm(prompt) must run in a fresh context,
    without parent conversation or write access, from a neutral harness-rule-free cwd.
    Raw responses are represented by SHA-256 in attempts; caller retains raw bytes
    through its injected transport if raw retention beyond this invocation is needed.
    """
    if not isinstance(max_retries, int) or max_retries < 0:
        raise ValueError("max_retries must be a nonnegative integer")
    attempts = []
    fragments = []
    for _ in range(max_retries + 1):
        raw = call_llm(render_prompt(record_id, source_path))
        if not isinstance(raw, str):
            raise TypeError("call_llm must return a string")
        fixed, repaired = repair_json(raw)
        verdict = check(record_id, source_text, fixed)
        fragments = verdict.get("fragments", [])  # 줄 범위가 틀린 조각은 검사기가 이미 제외
        attempts.append({"raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                         "ok": verdict["ok"], "reasons": verdict["reasons"],
                         "warnings": verdict.get("warnings", []), "repaired": repaired})
        if verdict["ok"]:
            break
    return {"record_id": record_id, "fragments": fragments, "attempts": attempts, "ok": attempts[-1]["ok"]}
