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
MEN_NOUNS = {"화면", "측면", "전면", "표면", "단면", "내면", "방면", "국면", "정면", "후면", "서면", "지면", "바닥면", "이면", "라면"}
CHAIN_END = ("하고", "되고", "이고", "않고", "있고", "없고", "았고", "었고", "했고", "됐고", "하며", "되며", "이며", "으며",
             "지만", "거나", "어도", "아도", "해도", "여도", "돼도")
GUIDE = ("연결은 영어 연산자로 쓴다: IF 조건 THEN 결과, A AND B, A OR B, EVEN IF, EXCEPT WHEN, BEFORE/AFTER … THEN, BECAUSE 이유. "
         "각 조각은 주어 하나와 서술 하나의 한국어 문장이고 부정은 문장 안에 둔다.")


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
    return [(o, re.sub(r"[()]", " ", s).strip().rstrip(".").strip()) for o, s in parts]


def check(text):
    """-> list of error details (empty = the fact follows the form)."""
    if not isinstance(text, str) or not text.strip():
        return ["fact 가 비어 있다"]
    errs = []
    if text.count("(") != text.count(")"):
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
    return errs


NEG = re.compile(r"(않|없|아니|금지|못하|못 )")
_TOK = re.compile(r"\b(EVEN IF|EXCEPT WHEN|IF|THEN|AND|OR|BEFORE|AFTER|BECAUSE)\b|([()])")


def _tokens(text):
    out, pos = [], 0
    for m in _TOK.finditer(text):
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
    then, join = [], None
    while i < len(toks):
        kind, val = toks[i]
        if kind == "op" and val == "EXCEPT WHEN":
            form["except"], i = _expr(toks, i + 1, ())
            continue
        if kind == "leaf":
            then.append(val)
        elif kind == "op" and val in ("AND", "OR") and form["kind"] == "plain":
            join = join or val
        i += 1
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
