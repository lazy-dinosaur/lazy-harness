"""Harness base rules that need semantic judgment (schema-delta '기본 규칙 정의 — 하네스 특성',
'답변 끝 통합 판정 — 하네스 규칙은 하드코딩', 2026-09-29).

Hard-coded here: not stored in the DB, not changeable by the rule tools, not part of the project rule block.
Judged at answer end together with the project rules in one Jev request; receipts carry origin='harness'.
Code-certain harness rules are enforced directly by code and listed in CODE_ENFORCED only so rule creation can
check that a project rule does not weaken them."""

SEMANTIC = (
    {"id": "H-1", "when": "요청의 범위 해석에 따라 코드·지식 결과가 크게 갈리거나 큰 변경을 할 때",
     "must": "진행 전에 사용자에게 묻고, 큰 변경은 계획을 보여 주고 승인받는다",
     "unless": "사소한 선택(이름·순서 등)이거나 사용자가 이미 범위를 정한 경우", "level": "must",
     "why": "묻지 않고 범위를 정하면 되돌리는 비용이 큼(실사용 ensure 사례)"},
)

CODE_ENFORCED = (
    {"id": "H-c1", "when": "항상", "must": "프로젝트 폴더 밖(다른 프로젝트·상위 폴더)을 일반 도구로 읽거나 뒤지지 않는다(밖은 소화 전용 도구로만)"},
    {"id": "H-c2", "when": "검수 대기 사실을 승인할 때", "must": "그 사실을 보여 준 뒤의 사용자 답만 근거로 쓴다(완료 문장 재사용 금지)"},
    {"id": "H-c3", "when": "항상", "must": "지침은 lazy-harness 만 따른다(팀 AGENTS.md 는 지침이 아님, 우리 스킬만 사용)"},
)


def rules():
    """Semantic harness rules for the answer-end judgment (origin='harness')."""
    return [dict(r, origin="harness") for r in SEMANTIC]


def for_review():
    """All harness rules a new project rule must not weaken (creation review)."""
    return [dict(r) for r in SEMANTIC + CODE_ENFORCED]
