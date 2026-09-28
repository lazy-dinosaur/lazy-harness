"""knowledge_brief: wide collection read by a cheap sub-agent (Luna) that returns only a four-view brief to the parent
(schema-delta '검색 전달 방식 확정', user 2026-09-28). The parent keeps reading source while this runs (async in the pi tool).

The wide document goes to a private temp file (mode 600) that the sub-agent reads with its read tool; the file is removed
as soon as the brief is written. The sub-agent is a headless `pi -p` run with only the read tool and no extensions.
"""
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import worker_tools

MODEL = os.environ.get("LH_BRIEF_MODEL", "openai-codex/gpt-6-luna:medium")
TIMEOUT = int(os.environ.get("LH_BRIEF_TIMEOUT", "300"))
PROMPT = """너는 지식 정리 담당이다. 파일을 쓰거나 고치지 않는다. 최종 응답은 정리본(markdown)만.

작업 AI 가 지금 이 일을 하려 한다: {QUESTION}
{CHANGE}
아래 파일에 이 일과 관련해 모은 지식 조각이 네 칸(이전 결정·이유 / 현재 구현 / 유지해야 할 것 / 기타) × 영역으로 있다.
파일: {FILE}

파일을 끝까지 읽고(길면 여러 번 나눠 읽는다) 작업 AI 가 이 일을 하기 전에 알아야 할 것을 정리한다.
- 먼저 '영역 목록' 에서 이 일에 해당하는 영역을 고른다(조각 수가 많다고 주제 영역인 것은 아니다).
- **고른 영역의 조각은 하나도 빼지 않고 반영한다**(조건·값·순서·식별자·경로 그대로, 요약하며 세부를 줄이지 않는다).
- 다른 영역의 조각은 이 일과 **직접** 관련될 때만 쓴다.
- 조각에 없는 내용은 쓰지 않는다. 각 줄 끝에 근거 [alias] 를 붙인다.

절(이 순서로, 내용이 없는 절은 생략):
## 이전 결정·이유 (기각한 안 포함)
## 현재 구현 (계약·코드 경로·흐름·시나리오)
## 유지해야 할 것 (제약·보호 테스트·단일 진실원)
## 충돌 후보 ('⚠ 충돌 후보' 표시 조각과, 하려는 변경과 부딪히는 내용)
## 기타
"""


LIMIT_RULE = ("- **정리본은 8,000자 안으로 쓴다.** 넘칠 것 같으면 '이전 결정·이유', '유지해야 할 것', '충돌 후보' 를 먼저 빠짐없이 쓰고,\n"
              "  '현재 구현'·'기타' 는 한 줄 요약 뒤 근거 [alias] 목록으로 줄인다(작업 AI 가 필요하면 knowledge_more 로 원문을 받는다).\n")


VERBATIM_RULE = "- 조각 문장의 조건·값·순서·동작(무엇을 제한·제외·비우는지 등)을 가능한 한 원문 그대로 옮기고, 여러 조각을 한 문장으로 뭉뚱그리지 않는다.\n"


def _prompt():
    """8,000-char rule on by default (scale-02 stability, 2026-09-28: same-setting runs vary 80.4~90.7%; the cap
    averaged 82.4% vs 84.5% without it — inside the range, -2.1%p — with ~30% smaller briefs). LH_BRIEF_LIMIT=0 turns it off."""
    p = PROMPT
    if os.environ.get("LH_BRIEF_VERBATIM") == "1":  # scale-02 diag experiment switch (R07: collected but dropped by the writer)
        p = p.replace("\n\n절(이 순서로", "\n" + VERBATIM_RULE + "\n절(이 순서로", 1)
    if os.environ.get("LH_BRIEF_LIMIT", "1") != "0":
        p = p.replace("\n\n절(이 순서로", "\n" + LIMIT_RULE + "\n절(이 순서로", 1)
    return p


def pi_runner(prompt, cwd):
    """Headless sub-agent: only the read tool, no extensions/skills/session. JSON event mode so the provider-reported
    usage/cost of every turn is summed. Returns (final text, cost_usd)."""
    import json as _json
    exe = shutil.which("pi") or "pi"
    model = os.environ.get("LH_BRIEF_MODEL", MODEL)
    r = subprocess.run([exe, "-p", "--mode", "json", "--model", model, "--tools", "read", "--no-extensions", "--no-skills",
                        "--no-session", prompt], cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT)
    text, cost = "", 0.0
    for line in r.stdout.splitlines():
        try:
            ev = _json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "turn_end":
            msg = ev.get("message") or {}
            cost += float(((msg.get("usage") or {}).get("cost") or {}).get("total") or 0)
            parts = [c.get("text", "") for c in msg.get("content") or [] if c.get("type") == "text"]
            if parts:
                text = "\n".join(parts).strip()
    if r.returncode != 0 or not text:
        raise RuntimeError("brief writer failed: " + (r.stderr or "empty output")[-300:])
    return text, round(cost, 6)


def brief(dsn, host, question, queries, ask, change=None, runner=pi_runner):
    t0 = time.time()
    doc, stats = worker_tools.collect_wide(dsn, host, question, queries, ask, change=change)
    t1 = time.time()
    d = Path(tempfile.mkdtemp(prefix="lh-brief-"))
    try:
        os.chmod(d, 0o700)
        f = d / "knowledge.md"
        f.write_text(doc)
        os.chmod(f, 0o600)
        got = runner(_prompt().replace("{QUESTION}", question.strip()).replace("{FILE}", str(f))
                     .replace("{CHANGE}", f"하려는 변경: {change.strip()}" if change else ""), str(d))
        text, cost = got if isinstance(got, tuple) else (got, None)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return {"brief": text, **stats, "collected_chars": len(doc), "brief_chars": len(text), "writer_cost_usd": cost,
            "collect_sec": round(t1 - t0, 1), "write_sec": round(time.time() - t1, 1)}
