"""Korean rendering of fact forms: leaves kept, joints by rule, code-verified, labelled fallback."""
import fact_form
import fact_text


def ko(text):
    return fact_text.to_korean(fact_form.parse(text))


def test_condition_endings():
    e = fact_text.ending
    assert e("보관 위치가 없다", "면") == "보관 위치가 없으면"
    assert e("보관 위치가 비활성 상태다", "면") == "보관 위치가 비활성 상태이면"
    assert e("방이 열린다", "면") == "방이 열리면" and e("사용자가 저장 안 함을 고른다", "면") == "사용자가 저장 안 함을 고르면"
    assert e("사용자가 글을 읽는다", "면") == "사용자가 글을 읽으면"
    assert e("REST PAT가 실패한다", "더라도") == "REST PAT가 실패하더라도"
    assert e("캐시를 올렸다", "면") == "캐시를 올렸으면" and e("두 값이 같다", "면") == "두 값이 같으면"
    assert e("파일을 만든다", "면") == "파일을 만들면" and e("값이 길다", "면") == "값이 길면"
    assert e("버튼이 보이지 않는다", "면") == "버튼이 보이지 않으면"
    assert e("MCP가 정보를 제공할 수 있다", "면") == "MCP가 정보를 제공할 수 있으면"
    assert e("값이 크다", "면") == "값이 크면" and e("입력이 필요하다", "면") == "입력이 필요하면"
    assert e("끝내 noun", "면") is None


def test_rules_render_naturally_and_keep_leaves():
    t, how = ko("IF 보관 위치가 없다 OR 보관 위치가 비활성 상태다 THEN 첨부 파일은 고아 첨부로 분류된다 AND 첨부 파일은 목록에 보이지 않는다")
    assert how == "natural" and t == ("보관 위치가 없거나 보관 위치가 비활성 상태이면 첨부 파일은 고아 첨부로 분류된다. "
                                      "보관 위치가 없거나 보관 위치가 비활성 상태이면 첨부 파일은 목록에 보이지 않는다."), t
    t, how = ko("IF MCP가 정보를 제공할 수 있다 EVEN IF REST PAT가 실패한다 THEN 에이전트는 MCP를 활성 경로로 쓴다")
    assert how == "natural" and t == "REST PAT가 실패하더라도 MCP가 정보를 제공할 수 있으면 에이전트는 MCP를 활성 경로로 쓴다.", t
    t, how = ko("IF 사용자가 버튼을 누른다 THEN 창은 닫힌다 EXCEPT WHEN 관리자가 잠금을 걸었다")
    assert how == "natural" and t == "사용자가 버튼을 누르면 창은 닫힌다. 단, 관리자가 잠금을 걸었으면 예외다.", t
    t, how = ko("AFTER 캐시 크기를 2 GiB로 올렸다 THEN 빌드 시간이 약 40% 줄었다")
    assert how == "natural" and t == "캐시 크기를 2 GiB로 올렸다. 그 뒤 빌드 시간이 약 40% 줄었다.", t
    t, how = ko("ADR 0054는 개정된다 BECAUSE 분리가 독립 설계 경계다")
    assert how == "natural" and t == "ADR 0054는 개정된다. (이유: 분리가 독립 설계 경계다)", t
    assert ko("화면은 목록을 보여 준다.") == ("화면은 목록을 보여 준다.", "natural")


def test_unrenderable_falls_back_to_labelled_form():
    t, how = ko("IF (방이 열린다 OR 방이 포커스된다) AND 사용자가 있다 THEN A는 읽는다")
    assert how == "labelled" and t == "조건: (방이 열린다 또는 방이 포커스된다) 그리고 사용자가 있다 → 결과: A는 읽는다", t
    t, how = ko("IF 에이전트 설정 THEN 값은 1이다")  # condition leaf without a predicate
    assert how == "labelled" and "조건: 에이전트 설정" in t


def test_code_parentheses_stay_in_the_leaf():
    t, how = ko("확정 노드는 `10309:42169`(`스퀘어챗-그룹`)이다")
    assert (t, how) == ("확정 노드는 `10309:42169`(`스퀘어챗-그룹`)이다.", "natural")
    t, how = ko("장애는 `UPDATE x SET y = array_append(...) WHERE z` 문장에서 발생했다")
    assert "array_append(...)" in t and how == "natural", t
    t, how = ko("IF SquareChat의 전역 알림이 OFF다 THEN 일반 CHAT의 알림을 억제한다")
    assert (t, how) == ("SquareChat의 전역 알림이 OFF이면 일반 CHAT의 알림을 억제한다.", "natural")


def test_repeated_topic_and_before_read_naturally():
    t, how = ko("IF 사람은 부서에 들어온다 THEN 사람은 접근을 얻는다")
    assert (t, how) == ("사람은 부서에 들어오면 접근을 얻는다.", "natural"), t
    t, how = ko("IF 창은 숨겨져 있다 THEN 창은 알림을 보이지 않는다 AND 창은 소리를 낸다")
    assert (t, how) == ("창은 숨겨져 있으면 알림을 보이지 않는다. 창은 숨겨져 있으면 소리를 낸다.", "natural"), t
    t, how = ko("BEFORE `chat.markAsRead`는 읽음 상태를 갱신한다 THEN 행을 잠근다")
    assert (t, how) == ("먼저 행을 잠근다. 그다음 `chat.markAsRead`는 읽음 상태를 갱신한다.", "natural"), t


def test_mixed_and_or_without_condition_is_rejected_and_kept_whole():
    text = "factory는 순서를 유지한다 AND (factory는 교체된다 OR factory는 감싸진다)"
    assert any("섞지 않는다" in e for e in fact_form.check(text))
    assert fact_form.parse(text)["then"] == [text]  # nothing of the OR is lost
    assert fact_form.check("A는 된다 OR B는 된다") == []


def test_view_keeps_plain_facts_and_renders_operators():
    assert fact_text.view("화면은 목록을 보여 준다") == "화면은 목록을 보여 준다"
    assert fact_text.view("IF 보관 위치가 없다 THEN 첨부 파일은 7일 보관된다") == "보관 위치가 없으면 첨부 파일은 7일 보관된다."
    assert fact_text.view("ADR 0054는 개정된다 BECAUSE 분리가 경계다") == "ADR 0054는 개정된다. (이유: 분리가 경계다)"
