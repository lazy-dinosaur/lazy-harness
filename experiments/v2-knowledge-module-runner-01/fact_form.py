"""Fact form (schema-delta '지식 문장 형식 — 논리 뼈대는 영어 연산자, 잎은 한국어 완결 문장', 2026-09-30).

A fact is Korean leaf sentences joined by English operators:
  [IF cond [EVEN IF cond] THEN | BEFORE leaf THEN | AFTER leaf THEN] leaf [AND leaf ...] [EXCEPT WHEN cond] [BECAUSE reason]
  cond = leaf joined by AND / OR, parentheses allowed.
A leaf states one subject and one predicate; clause connectives (~하고, ~하며, ~이며, ~지만, ~거나, ~면, ~어도) inside a
leaf are rejected so the link is written as an operator. Negation stays inside the leaf (no NOT operator).
Measured in structure-01 pilot5: meaning kept 96% (random 100) and 96% (chat 172) vs 88% for slot assembly.
"""
import re

OPS = re.compile(r"\b(EVEN IF|EXCEPT WHEN|IF|THEN|AND|OR|BEFORE|AFTER|BECAUSE)\b")
GROUP_PAREN = re.compile(r"(?:(?<=\s)|^)\((?=\S)|(?<=\S)\)(?=\s|$)")
MEN_NOUNS = {"화면", "측면", "전면", "표면", "단면", "내면", "방면", "국면", "정면", "후면", "서면", "지면", "바닥면", "이면", "라면"}
CHAIN_END = ("하고", "되고", "이고", "않고", "있고", "없고", "았고", "었고", "했고", "됐고", "하며", "되며", "이며", "으며",
             "지만", "거나", "어도", "아도", "해도", "여도", "돼도")
GUIDE = ("연결은 영어 연산자로 쓴다: IF 조건 THEN 결과, A AND B, A OR B, EVEN IF, EXCEPT WHEN, BEFORE/AFTER … THEN, BECAUSE 이유. "
         "각 조각은 주어 하나와 서술 하나의 한국어 문장이고 부정은 문장 안에 둔다.")


# flow3 (2026-10-01): parents bypassed E_FORM with noun lists of actions ('X 판단과 Y 저장 및 Z 유지이다'), several facts in
# one sentence. An action noun followed by 과/와 or 및 is such a list; '-하여/-되어/-해서' chain two predicates.
ACTION_NOUN = ("저장", "거부", "판단", "유지", "확인", "제거", "검증", "검사", "절단", "사용", "생성", "수정", "갱신",
               "보장", "불변", "삭제", "추가", "변경", "처리", "적용", "차단", "허용", "정렬", "반환", "호출", "전달",
               "표시", "기록", "실행", "재시도", "무시", "자르기", "생략", "복구", "초기화", "보존", "대체", "반영")
NOMINALIZED = re.compile(r"(음|기)$")
CHAIN_PRED = ("하여", "되어", "해서", "돼서")
CHAIN_PRED_OK = ("위하여", "위해서", "대하여", "대해서", "의하여", "의해서", "통하여", "통해서")


def _action(stem):
    return stem.endswith(ACTION_NOUN) or (len(stem) >= 2 and NOMINALIZED.search(stem) is not None and stem not in ("마음", "처음", "다음"))


LIGHT_VERB = ("보장한다", "적용한다", "수행한다", "담당한다", "제공한다", "가진다", "갖는다", "한다", "이룬다")


def noun_list(leaf):
    """A '-하여' predicate chain, or actions listed as the predicate: after the subject, two or more action-noun joints
    ('판단과 … 저장 및 … 유지이다'), or one joint closed by a copula or a light verb ('저장과 … 불변을 보장한다').
    A list in the subject ('재시도와 coalescing은') or as the object of a real verb ('전달과 상태를 유지한다') is one fact."""
    toks = re.findall(r"[가-힣]+", leaf)
    for i, t in enumerate(toks):
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        if t.endswith(CHAIN_PRED) and not t.endswith(CHAIN_PRED_OK) and not nxt.startswith("있"):
            return t
    start = max([i + 1 for i, t in enumerate(toks) if (t.endswith(("은", "는")) and len(t) >= 2) or t in ("것이", "것은")] or [0])
    joints = []
    for i in range(start, len(toks)):
        t = toks[i]
        if t.endswith(("과", "와")) and len(t) >= 3 and _action(t[:-1]):
            joints.append(t)
        elif t == "및" and i > 0 and _action(toks[i - 1]):
            joints.append(toks[i - 1] + " 및")
    if not joints:
        return None
    last = toks[-1] if toks else ""
    if len(joints) >= 2 or last.endswith(("이다", "였다", "이었다")) or last in LIGHT_VERB or last.endswith(LIGHT_VERB[:6]):
        return joints[0]
    return None


def chain_token(leaf):
    """Clause connective inside a leaf, or None. Noun-modifying '~할 때' is allowed; conditions use IF."""
    for t in re.findall(r"[가-힣]+", leaf):
        if t.endswith(CHAIN_END):
            return t
        if t.endswith("면") and len(t) >= 2 and t not in MEN_NOUNS and not t.endswith("화면"):
            return t
    return None


def split(text):
    """-> list of (op or None, leaf text); parentheses are grouping only."""
    parts, pos, op = [], 0, None
    for m in OPS.finditer(text):
        parts.append((op, text[pos:m.start()]))
        op, pos = m.group(1), m.end()
    parts.append((op, text[pos:]))
    return [(o, GROUP_PAREN.sub(" ", s).strip().rstrip(".").strip()) for o, s in parts]


def check(text):
    """-> list of error details (empty = the fact follows the form)."""
    if not isinstance(text, str) or not text.strip():
        return ["fact 가 비어 있다"]
    errs = []
    groups = [t[1] for t in _tokens(text) if t[0] == "paren"]
    if groups.count("(") != groups.count(")"):
        errs.append("괄호가 짝이 맞지 않는다")
    parts = split(text)
    ops = [o for o, _ in parts if o]
    for k, (o, leaf) in enumerate(parts):
        if not leaf and not (k == 0 and ops and ops[0] in ("IF", "BEFORE", "AFTER")):
            errs.append(f"{o or '처음'} 뒤에 문장이 없다")
            continue
        if o == "BECAUSE" or not leaf:
            continue  # the reason is free text
        c = chain_token(leaf)
        if c:
            errs.append(f"'{leaf[:40]}' 안에 절을 잇는 '{c}' 가 있다. " + GUIDE)
            continue
        n = noun_list(leaf)
        if n:
            errs.append(f"'{leaf[:40]}' 은 동작을 '{n}' 로 나열해 사실 여러 개를 한 문장에 담았다. "
                        "동작마다 주어+동사 문장으로 쓰고 AND 로 잇거나 따로 기록한다. "
                        "예: 'X는 설명을 저장한다 AND X는 기존 설명을 유지한다'. " + GUIDE)
    head = ops[0] if ops else None
    if head in ("IF", "BEFORE", "AFTER") and parts[0][1]:
        errs.append(f"{head} 는 문장 맨 앞에 쓴다")
    if head in ("IF", "BEFORE", "AFTER") and "THEN" not in ops:
        errs.append(f"{head} 뒤에 THEN 결과가 없다")
    if "THEN" in ops and head not in ("IF", "BEFORE", "AFTER"):
        errs.append("THEN 은 IF/BEFORE/AFTER 뒤에만 쓴다")
    if ops.count("THEN") > 1 or ops.count("IF") > 1:
        errs.append("한 사실에는 IF … THEN 이 하나다. 결과가 다른 규칙은 따로 기록한다")
    if "EVEN IF" in ops and head != "IF":
        errs.append("EVEN IF 는 IF 조건 안에서만 쓴다")
    if "BECAUSE" in ops and ops.index("BECAUSE") != len(ops) - 1:
        errs.append("BECAUSE 는 맨 끝에 한 번 쓴다")
    if "THEN" in ops:
        then_at = ops.index("THEN")
        if any(o == "OR" for o in ops[then_at + 1:] if o not in ("EXCEPT WHEN",)) and "EXCEPT WHEN" not in ops[then_at + 1:]:
            errs.append("THEN 뒤 결과는 AND 로만 잇는다(또는은 조건에만)")
    plain_ops = [o for o in (ops[ops.index("THEN") + 1:] if "THEN" in ops else ops)
                 if o in ("AND", "OR")] if head not in ("IF", "BEFORE", "AFTER") else []
    if "AND" in plain_ops and "OR" in plain_ops:
        errs.append("조건 없는 사실에 AND 와 OR 를 섞지 않는다. 함께 성립하는 것과 둘 중 하나인 것을 따로 기록한다")
    return errs


NEG = re.compile(r"(않|없|아니|금지|못하|못 )")
# grouping parentheses stand free (space or edge outside); parentheses inside code such as array_append(...) or
# `a`(`b`) are leaf text (render-ko-01 found them split away)
_TOK = re.compile(r"\b(EVEN IF|EXCEPT WHEN|IF|THEN|AND|OR|BEFORE|AFTER|BECAUSE)\b|((?:(?<=\s)|^)\((?=\S)|(?<=\S)\)(?=\s|$))")
_TICK = re.compile(r"`[^`]*`")


def _tokens(text):
    out, pos = [], 0
    ticks = [(m.start(), m.end()) for m in _TICK.finditer(text)]
    for m in _TOK.finditer(text):
        if any(a <= m.start() < b for a, b in ticks):
            continue  # operators and parentheses inside `code` are text
        chunk = text[pos:m.start()].strip().rstrip(".").strip()
        if chunk:
            out.append(("leaf", chunk))
        out.append(("op", m.group(1)) if m.group(1) else ("paren", m.group(2)))
        pos = m.end()
    chunk = text[pos:].strip().rstrip(".").strip()
    if chunk:
        out.append(("leaf", chunk))
    return out


def _expr(toks, i, stops):
    """AND binds tighter than OR; parentheses group. -> (expr, next index)."""
    def atom(i):
        if i < len(toks) and toks[i] == ("paren", "("):
            e, i = _or(i + 1)
            if i < len(toks) and toks[i] == ("paren", ")"):
                i += 1
            return e, i
        if i < len(toks) and toks[i][0] == "leaf":
            return {"leaf": toks[i][1]}, i + 1
        return None, i

    def _and(i):
        args = []
        e, i = atom(i)
        if e:
            args.append(e)
        while i < len(toks) and toks[i] == ("op", "AND"):
            e, i = atom(i + 1)
            if e:
                args.append(e)
        return (args[0] if len(args) == 1 else {"op": "AND", "args": args}) if args else None, i

    def _or(i):
        args = []
        e, i = _and(i)
        if e:
            args.append(e)
        while i < len(toks) and toks[i] == ("op", "OR"):
            e, i = _and(i + 1)
            if e:
                args.append(e)
        return (args[0] if len(args) == 1 else {"op": "OR", "args": args}) if args else None, i
    return _or(i)


def parse(text):
    """Operator string -> form {kind, if?, even_if?, then[], join?, except?, anchor?, because?}. Total: text that does
    not follow the form becomes one plain leaf (check() is what rejects it at record time)."""
    body, because = text, None
    m = re.search(r"\bBECAUSE\b", text)
    if m:
        body, because = text[:m.start()], text[m.end():].strip().rstrip(".").strip() or None
    toks = _tokens(body)
    form = {"kind": "plain"}
    i = 0
    if toks and toks[0] == ("op", "IF"):
        form["kind"] = "if"
        form["if"], i = _expr(toks, 1, ())
        if i < len(toks) and toks[i] == ("op", "EVEN IF"):
            form["even_if"], i = _expr(toks, i + 1, ())
        if i < len(toks) and toks[i] == ("op", "THEN"):
            i += 1
    elif toks and toks[0] in (("op", "BEFORE"), ("op", "AFTER")):
        form["kind"] = toks[0][1].lower()
        form["anchor"] = toks[1][1] if len(toks) > 1 and toks[1][0] == "leaf" else ""
        i = 3 if len(toks) > 2 and toks[2] == ("op", "THEN") else 2
    then, join, mixed = [], None, False
    while i < len(toks):
        kind, val = toks[i]
        if kind == "op" and val == "EXCEPT WHEN":
            form["except"], i = _expr(toks, i + 1, ())
            continue
        if kind == "leaf":
            then.append(val)
        elif kind == "op" and val in ("AND", "OR") and form["kind"] == "plain":
            if join and join != val:
                mixed = True  # 'A AND (B OR C)': results cannot be a flat list without losing the OR
            join = join or val
        i += 1
    if mixed:  # legacy text that check() now rejects: keep it whole so no OR is lost
        then = [body.strip().rstrip(".").strip()]
        join = None
    form["then"] = then or [text.strip().rstrip(".").strip() or text]
    if join == "OR" and len(then) > 1:
        form["join"] = "OR"
    if because:
        form["because"] = because
    for k in ("if", "even_if", "except"):
        if k in form and not form[k]:
            del form[k]
    if form["kind"] == "if" and "if" not in form:
        form = {"kind": "plain", "then": form["then"], **({"because": because} if because else {})}
    if form["kind"] in ("before", "after") and not form.get("anchor"):
        form = {"kind": "plain", "then": form["then"], **({"because": because} if because else {})}
    return form


def _expr_leaves(e):
    if not e:
        return []
    if "leaf" in e:
        return [e["leaf"]]
    return [x for a in e.get("args", []) for x in _expr_leaves(a)]


def leaves(form):
    """-> [{role, text, polarity}] in a stable order (ord = index)."""
    out = []
    for role in ("if", "even_if"):
        out += [{"role": role, "text": t} for t in _expr_leaves(form.get(role))]
    if form.get("anchor"):
        out.append({"role": "anchor", "text": form["anchor"]})
    out += [{"role": "then", "text": t} for t in form.get("then", [])]
    out += [{"role": "except", "text": t} for t in _expr_leaves(form.get("except"))]
    for leaf in out:
        leaf["polarity"] = "neg" if NEG.search(leaf["text"]) else "pos"
    return out


def condition_key(form):
    """Comparable condition of a fact: two facts can contradict only under the same condition (or none)."""
    import json
    return json.dumps({k: form.get(k) for k in ("kind", "if", "even_if", "anchor", "except") if form.get(k)},
                      ensure_ascii=False, sort_keys=True)


def unconditional(form):
    """A plain fact holds always: it can contradict a rule under any condition."""
    return (form or {}).get("kind", "plain") == "plain" and not (form or {}).get("except")


def expr_text(e, top=True):
    if not e:
        return ""
    if "leaf" in e:
        return e["leaf"]
    body = f" {e['op']} ".join(expr_text(a, False) for a in e.get("args", []))
    return body if top else "(" + body + ")"


def display(form, leaf):
    """One result leaf with its condition, as the judge reads it."""
    form = form or {}
    head = ""
    if form.get("kind") == "if":
        head = "IF " + expr_text(form.get("if")) + (" EVEN IF " + expr_text(form["even_if"]) if form.get("even_if") else "")
    elif form.get("kind") in ("before", "after"):
        head = form["kind"].upper() + " " + form.get("anchor", "")
    out = (head + " THEN " if head else "") + leaf
    if form.get("except"):
        out += " EXCEPT WHEN " + expr_text(form["except"])
    return out


def comparable(a, b):
    """Two facts can contradict only under the same condition, or when either holds always."""
    return unconditional(a) or unconditional(b) or condition_key(a) == condition_key(b)
