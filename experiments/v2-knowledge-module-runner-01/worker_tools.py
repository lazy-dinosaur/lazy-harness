"""Worker-facing knowledge tools (spec/platform/v2-fragment-knowledge-store.md §13.3–13.4).

search      — 'what I need, nothing missing' (schema-delta 2026-09-28): paginated collection until no new relevant fragment,
              returns only the Jev-selected fragments in four views (decisions / implementation / keep / other) with an
              optional per-fragment conflict flag for a planned change, plus a 'more' index. more — rest of a domain/group.
fix_plan    — update flow: same collection -> Jev marks fragments that hold the old content -> fix list (+ identifier
              substitution proposal for renames). Plan persisted; worker answers every listed fragment.
fix_submit  — every listed alias must be answered; length guard; Jev re-check of rewritten text (still old -> returned
              for another fix); accepted updates go through the normal ledger record path (lint + Jev absorption +
              poller). deprecate (with why) goes the same way: Jev intent-deprecate check, then active=false (history kept).

Jev access is injected (`ask`) so tests run offline; production uses make_ask(config).
"""
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

import collect
import fact_text
import runner
import store_pg

STALE_Q = ("지식 조각 items[{i}] 를 본다. change 가 확정된 지금, 이 조각은 change.old 쪽 내용(이름·값·규칙)을 담고 있어서 "
           "고치거나 폐기해야 하는가? change.subject 와 다른 것을 말하는 조각, 바뀐 뒤에도 그대로 맞는 조각은 false.")
STILL_Q = ("조각 items[{i}] 는 change 를 반영하려고 고친 문장이다. 아직 change.old 쪽 이름·값·규칙이 남아 있어서 다시 고쳐야 하는가? "
           "change.new 가 들어갔고 old 내용이 없으면 false.")
THRESHOLD = 0.5
MAX_GROWTH = 1.6
CHUNK = 20


def plan_dir():
    d = Path(os.environ.get("LH_KNOWLEDGE_PLAN_DIR", Path.home() / ".cache" / "lh-knowledge" / "plans"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def make_ask(cfg, http=urlopen):
    """ask(state, texts, question) -> list[float]; one Jev request per CHUNK texts, two attempts each."""
    def ask(state, texts, question):
        scores = []
        for k in range(0, len(texts), CHUNK):
            chunk = texts[k:k + CHUNK]
            qs = {f"m{j}": {"type": "noul", "instructions": question.format(i=j),
                            "criteria": {"true": "예", "false": "아니오"}} for j in range(len(chunk))}
            body = {"model": cfg["jev_model"], "state": {**state, "items": [{"i": j, "text": t[:600]} for j, t in enumerate(chunk)]},
                    "questions": qs}
            data = None
            for _ in (1, 2):
                try:
                    req = Request(cfg["jev_base_url"].rstrip("/") + "/v1/systemone", data=json.dumps(body, ensure_ascii=False).encode(),
                                  headers={"Authorization": "Bearer " + cfg["jev_api_key"], "Content-Type": "application/json"}, method="POST")
                    with http(req, timeout=120) as resp:
                        data = json.load(resp)
                    if set(data.get("answers", {})) != set(qs):
                        raise ValueError("answer keys mismatch")
                    break
                except (OSError, ValueError, KeyError, TypeError):
                    data = None
                    time.sleep(1)
            if data is None:
                raise RuntimeError("Jev judgement failed after two attempts")
            scores += [float(data["answers"][f"m{j}"]["noul"]) for j in range(len(chunk))]
        return scores
    return ask


def _queries(queries):
    qs = [q.strip() for q in (queries or []) if isinstance(q, str) and q.strip()]
    if not 1 <= len(qs) <= 8:
        raise ValueError("queries: 1..8 nonempty strings required")
    return qs


NEED_Q = ("items[{i}] 의 지식 조각은 topic(지금 작업할 대상과 하려는 일)을 하려면 알아야 하는 내용인가? "
          "그 대상에 대한 이전 결정·이유·기각한 안, 현재 구현(계약·코드 경로·흐름), 유지해야 할 제약·보호 테스트·단일 진실원, "
          "부딪힐 수 있는 내용이면 예. 다른 기능의 내용이면 아니오.")
CONFLICT_Q = ("items[{i}] 는 저장된 지식 조각이다. change(하려는 변경)를 그대로 하면 이 조각의 결정·제약·동작과 부딪히거나 "
              "이 조각을 고쳐야 하는가? 변경과 무관하거나 변경 후에도 그대로 맞으면 아니오.")
# Four views of what an agent needs before changing something (user definition, schema-delta 2026-09-28).
VIEWS = (("decisions", "이전 결정·이유", ("decision", "rationale", "rejected")),
         ("implementation", "현재 구현", ("fact", "procedure")),
         ("keep", "유지해야 할 것", ("constraint",)),
         ("other", "기타", ("term", "question")))


def _page_judge(ask, topic, queries, question=None):
    rq = question or "items[{i}] 의 조각은 topic 을 이해하거나 topic 의 기능을 작업할 때 알아야 할 내용인가?"
    def judge(query, candidates):
        scores = ask({"topic": topic, "queries": queries}, [c["text"] for c in candidates], rq)
        return [{"relevant": s >= THRESHOLD, "novel": s >= THRESHOLD} for s in scores]
    return judge


def _collect(dsn, host, topic, queries, ask, question=None):
    res = collect.collect_topic(dsn, host, queries, judge=_page_judge(ask, topic, queries, question), variant="ctx-v1")
    _attach_domain(dsn, res["note"] + res["relevant"])
    return res["note"], res["relevant"]


def _attach_domain(dsn, frags):
    """search_hybrid/expand_group do not return domain/seq; read them so results can be grouped by domain."""
    ids = sorted({str(f["id"]) for f in frags if f.get("id")})
    if not ids:
        return
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("select id::text, domain, seq, kind::text from knowledge.fragment where id = any(%s::uuid[])", (ids,))
        found = {r[0]: r[1:] for r in cur.fetchall()}
    for f in frags:
        if str(f.get("id")) in found:
            f["domain"], f["seq"], f["kind"] = found[str(f["id"])]


# Layer notes are rebuilt at read time (spec §13.2); the agent writes them itself, never as a file.
LAYER_SECTIONS = {
    "domain": "용어 · 업무 규칙 · 불변 조건 · 기타",
    "spec": "목적 · 계약(입력·출력·규칙) · 구성 요소와 코드 경로 · 기타",
    "behavior": "시나리오(상황 → 동작 → 결과, 단계 번호) · 조건·예외 · 화면 반응 · 기타",
    "tests": "보호 대상 · 회귀 사례 · 테스트 경로와 보호 내용 · 기타",
    "decisions": "결정 · 이유 · 기각한 안 · 결과와 제약 · 기타",
    "ssot": "기준값·단일 진실원 · 소유자와 위치 · 지켜야 할 규칙 · 기타",
}
NOTE_RULES = (
    "- **주제 영역의 조각은 하나도 빼지 않고 모두 노트에 반영한다**(조건·값·순서·식별자·경로 그대로). 요약하거나 합치면서 세부를 줄이지 않는다.\n"
    "- 다른 영역의 조각은 주제와 **직접** 관련될 때만 쓴다. 비슷해 보여도 다른 기능의 규칙이면 넣지 않는다.\n"
    "- 조각에 없는 내용은 쓰지 않는다. 각 줄 끝에 근거 [alias] 를 붙인다.\n"
    "- 레이어에 맞는 절로 정리하되, 어느 절에도 딱 맞지 않는 내용도 '기타' 절에 남겨 버리지 않는다.\n")


def _domain_counts(frags):
    counts = {}
    for f in frags:
        d = f.get("domain") or "-"
        counts[d] = counts.get(d, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def _layer_guide(layer):
    return (f"\n# 레이어 노트 작성 안내 ({layer})\n\n"
            "먼저 문서 끝 '더 있음' 색인에서 **지금 작업 주제에 해당하는 영역**을 고른다(조각 수가 많다고 주제 영역인 것은 아니다). "
            "노트에 그 영역의 지식이 빠짐없이 필요하면 knowledge_more(domain) 로 나머지를 받은 뒤 쓴다.\n\n"
            f"{NOTE_RULES}\n절: {LAYER_SECTIONS[layer]}\n")


def _view(kind):
    for key, _label, kinds in VIEWS:
        if kind in kinds:
            return key
    return "other"


def _domain_rank(relevant):
    """Domains ordered by how many Jev-selected fragments they hold, ties by first discovery (scale-02 rank: ordering by
    total fragment count buried the asked-about domain inside large wide collections)."""
    score, first = {}, {}
    for i, f in enumerate(relevant):
        d = f.get("domain") or "-"
        score[d] = score.get(d, 0) + 1
        first.setdefault(d, i)
    return sorted(score, key=lambda d: (-score[d], first[d])), score


def _render(frags, flagged=frozenset(), rank=None):
    """Four views, each grouped by domain; conflict-flagged lines are marked. rank: domain order (most relevant first)."""
    lines = []
    for key, label, _kinds in VIEWS:
        part = [f for f in frags if _view(f.get("kind")) == key]
        if not part:
            continue
        lines += [f"## {label} ({len(part)})", ""]
        present = [d for d, _n in _domain_counts(part)]
        order = [d for d in (rank or []) if d in present] + [d for d in present if d not in (rank or [])]
        for d in order:
            lines.append(f"### 영역 {d}")
            for f in sorted((x for x in part if (x.get("domain") or "-") == d), key=lambda x: x.get("seq") or 0):
                mark = "⚠ 충돌 후보 " if str(f["id"]) in flagged else ""
                ref = f"{f['alias']}@{f['revision']}" if f.get("revision") else f["alias"]
                lines.append(f"- {mark}[{ref}] {fact_text.view(f['text'])}")  # stored operator form shown in Korean
            lines.append("")
    return lines


def _more_index(dsn, host, frags):
    """How much of each touched domain/group was not returned (for knowledge_more)."""
    have = {str(f["id"]) for f in frags}
    domains = sorted({f.get("domain") for f in frags if f.get("domain")})
    groups = sorted({f.get("group_id") for f in frags if f.get("group_id")})
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select domain, array_agg(id::text) from knowledge.fragment
                       where host_id=%s and active and domain = any(%s) group by domain""", (host, domains))
        dom = {d: [i for i in ids if i not in have] for d, ids in cur.fetchall()}
        cur.execute("""select group_id, array_agg(id::text) from knowledge.fragment
                       where host_id=%s and active and group_id = any(%s) group by group_id""", (host, groups))
        grp = {g: [i for i in ids if i not in have] for g, ids in cur.fetchall()}
    return ({d: len(v) for d, v in dom.items() if v}, {g: len(v) for g, v in grp.items() if v})


DOMAIN_EXPAND_MIN, DOMAIN_EXPAND_SHARE = 3, 0.25
DOMAIN_EXPAND_CAP = int(os.environ.get("LH_DOMAIN_EXPAND_CAP", "150"))  # scale-02 stability: 150 + length cap adopted (93.1% was an outlier run)


def _expand_domains(dsn, host, note, relevant):
    """Wide collection (G1 round3): a domain holding at least max(3, 25%) of the judge-selected fragments is the
    working area, so all of its active fragments are added — no Jev call, one DB query."""
    counts = dict(_domain_counts(relevant))
    total = sum(counts.values())
    picked = [d for d, n in counts.items() if d != "-" and n >= max(DOMAIN_EXPAND_MIN, DOMAIN_EXPAND_SHARE * total)]
    if not picked:
        return note
    have = {str(f["id"]) for f in note}
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("""select id::text as id, alias, domain, seq, kind::text as kind, text, group_id, revision from knowledge.fragment
                       where host_id=%s and active and domain = any(%s) order by domain, seq""", (host, picked))
        cols = [c[0] for c in cur.description]
        extra = [dict(zip(cols, r)) for r in cur.fetchall() if r[0] not in have]
    return note + extra[:DOMAIN_EXPAND_CAP]


def collect_wide(dsn, host, question, queries, ask, change=None):
    """Wide collection for knowledge_brief (schema-delta '검색 전달 방식 확정'): Jev-selected fragments + group siblings +
    working-domain expansion, rendered in the four views. Returns (document, stats). Read by the brief writer, not the parent."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question required")
    qs = _queries(queries)
    if question.strip() not in qs:
        qs = qs + [question.strip()]
    note, relevant = _collect(dsn, host, question, qs, ask, NEED_Q)
    wide = _expand_domains(dsn, host, note, relevant)
    flagged = set()
    if change and relevant:
        scores = ask({"change": str(change).strip()}, [f["text"] for f in relevant], CONFLICT_Q)
        flagged = {str(f["id"]) for f, s in zip(relevant, scores) if s >= THRESHOLD}
    counts = _domain_counts(wide)
    lines = [f"# 모은 지식: {question.strip()}", "", "영역 목록: " + ", ".join(f"{d}({n})" for d, n in counts), ""]
    lines += _render(wide, flagged)  # scale-02 rank (relevance-ordered domains) tried and not adopted: R07 1.0/12
    return "\n".join(lines) + "\n", {"relevant": len(relevant), "collected": len(wide), "conflicts": len(flagged)}


def search_dir():
    d = Path(os.environ.get("LH_KNOWLEDGE_SEARCH_DIR", Path.home() / ".cache" / "lh-knowledge" / "searches"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def search(dsn, host, question, queries, ask, layer=None, change=None):
    """What the agent needs for its task, nothing missing, nothing more: collection keeps paging until no new relevant
    fragment; only Jev-selected fragments are returned, in four views; `change` flags fragments it would conflict with;
    the 'more' index says what else exists in the touched domains/groups (knowledge_more)."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question required")
    if layer is not None and layer not in LAYER_SECTIONS:
        raise ValueError("layer must be one of " + "|".join(LAYER_SECTIONS))
    qs = _queries(queries)
    if question.strip() not in qs:
        qs = qs + [question.strip()]  # the question itself is also a query (layer-02 round3)
    note, relevant = _collect(dsn, host, question, qs, ask, NEED_Q)
    # Group siblings come along (layer-03 round2): fragments split from one decision/flow lose meaning apart.
    returned = note
    flagged = set()
    if change and relevant:
        if not isinstance(change, str) or not change.strip():
            raise ValueError("change must be a short description of the planned change")
        scores = ask({"change": change.strip()}, [f["text"] for f in relevant], CONFLICT_Q)
        flagged = {str(f["id"]) for f, s in zip(relevant, scores) if s >= THRESHOLD}
    more_d, more_g = _more_index(dsn, host, returned)
    search_id = uuid4().hex[:12]
    (search_dir() / f"{search_id}.json").write_text(json.dumps(
        {"host_id": host, "question": question, "returned": [str(f["id"]) for f in returned]}))
    lines = [f"# 필요한 지식: {question.strip()}", ""] + _render(returned, flagged)
    if more_d or more_g:
        lines += ["## 더 있음 (knowledge_more 로 받음)", ""]
        lines += [f"- 영역 {d}: {n}개 더" for d, n in sorted(more_d.items(), key=lambda kv: -kv[1])]
        lines += [f"- 묶음 {g}: {n}개 더" for g, n in sorted(more_g.items(), key=lambda kv: -kv[1])[:20]]
        lines += ["", f"search_id: {search_id} (knowledge_more 에 쓴다)", ""]
    document = "\n".join(lines) + "\n"
    if layer:
        document += _layer_guide(layer)
    return {"search_id": search_id, "document": document, "relevant": len(relevant), "returned": len(returned), "conflicts": len(flagged),
            "more": {"domains": more_d, "groups": more_g}}


def more(dsn, search_id, domain=None, group=None):
    """Rest of a domain or group touched by a search (fragments not yet returned in this search), same four views."""
    p = search_dir() / f"{search_id}.json"
    if not p.exists():
        raise ValueError("unknown search_id")
    st = json.loads(p.read_text())
    if bool(domain) == bool(group):
        raise ValueError("give exactly one of domain or group")
    col, val = ("domain", domain) if domain else ("group_id", group)
    with store_pg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(f"""select id::text as id, alias, domain, seq, kind::text as kind, text, group_id, revision from knowledge.fragment
                        where host_id=%s and active and {col}=%s and not (id::text = any(%s)) order by seq""",
                    (st["host_id"], val, st["returned"]))
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    st["returned"] += [r["id"] for r in rows]
    p.write_text(json.dumps(st))
    head = f"# 더 받은 지식: {'영역 ' + domain if domain else '묶음 ' + group} ({len(rows)})"
    return {"search_id": search_id, "count": len(rows), "document": "\n".join([head, ""] + _render(rows)) + "\n"}


def _change(change):
    if not isinstance(change, dict):
        raise ValueError("change object required")
    for k in ("subject", "old", "new", "instruction", "user_quote"):
        if not isinstance(change.get(k), str) or not change[k].strip():
            raise ValueError(f"change.{k} required")
    if change.get("type", "semantic") not in ("rename", "semantic"):
        raise ValueError("change.type must be rename|semantic")
    fq = change.get("forms_quote")
    if fq is not None and (not isinstance(fq, str) or not fq.strip()):
        raise ValueError("change.forms_quote must be a nonempty string when given")
    if fq and runner.QUESTION_TAIL.search(fq.strip()):
        # The ledger only checks that SOME user_utterance is a non-question, so a question here would slip through.
        raise ValueError("change.forms_quote is a question; ask the user and quote their confirming answer")
    out = {k: change[k] for k in ("subject", "old", "new", "instruction", "user_quote")} | {"type": change.get("type", "semantic")}
    if fq:
        out["forms_quote"] = fq
    return out


def _new_form_confirmed(ch):
    """The exact new wording must appear in a user utterance, or rewrites using it fail the ledger's E_CLAIM_QUOTE."""
    return ch["new"] in ch["user_quote"] or ch["new"] in ch.get("forms_quote", "")


def _ident(old):
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(old) + r"(?![A-Za-z0-9_])")


def fix_plan(dsn, host, change, queries, ask):
    ch = _change(change)
    qs = _queries(queries)
    note, _ = _collect(dsn, host, ch["subject"] + " — " + ch["instruction"], qs, ask)
    state = {"change": {k: ch[k] for k in ("subject", "old", "new", "instruction")}}
    scores = ask(state, [f["text"] for f in note], STALE_Q) if note else []
    items = []
    pat = _ident(ch["old"]) if ch["type"] == "rename" else None
    for f, s in zip(note, scores):
        if s < THRESHOLD:
            continue
        item = {"alias": f["alias"], "id": str(f["id"]), "text": f["text"], "revision": f.get("revision")}
        if pat is not None and pat.search(f["text"]):
            item["proposed_text"] = pat.sub(ch["new"], f["text"])
        items.append(item)
    plan_id = str(uuid4())
    plan = {"plan_id": plan_id, "host_id": host, "change": ch, "items": items, "collected": len(note), "created_at": time.time()}
    (plan_dir() / f"{plan_id}.json").write_text(json.dumps(plan, ensure_ascii=False))
    needs = None
    if not _new_form_confirmed(ch):
        needs = {"reason": "change.new does not appear verbatim in the user's confirmation; rewrites that use it will be rejected by the ledger",
                 "ask_user": f"변경 후 표기를 그대로 `{ch['new']}` 로 쓰면 될까요? (확정 답을 forms_quote 로 넣어 fix_plan 을 다시 부르세요)"}
    return {"plan_id": plan_id, "collected": len(note), "items": items, "needs_confirmation": needs,
            "instruction": "Answer EVERY item exactly once with action update (full corrected text; change only the old part; "
                           "use proposed_text when present), deprecate (with why: why it is no longer valid), or keep (with why)."}


def _load_plan(plan_id):
    if not isinstance(plan_id, str) or not re.fullmatch(r"[0-9a-f-]{36}", plan_id):
        raise ValueError("invalid plan_id")
    p = plan_dir() / f"{plan_id}.json"
    if not p.exists():
        raise ValueError("unknown plan_id")
    return json.loads(p.read_text())


MAX_CODE_REFS = 4


def _added_lines(cwd):
    """[(repo-relative path, new line number, text)] added in the working tree vs HEAD (tracked files)."""
    if not cwd:
        return []
    try:
        top = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        if top.returncode:
            return []
        diff = subprocess.run(["git", "-C", top.stdout.strip(), "diff", "-U0", "--no-color", "HEAD"],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return []
    out, path, line = [], None, 0
    for raw in diff.stdout.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            line = int(m.group(1)) if m else 0
        elif raw.startswith("+") and path:
            out.append((path, line, raw[1:]))
            line += 1
    return out


def _code_refs(ch, text, added):
    """Changed code that shows the confirmed new value (live-01/audit-01: without it digestion judged 'claim broader than
    evidence' because only the user's words and the old fragment backed file/function claims). Lines carrying the new
    value, preferring files the rewritten text names; nothing when the code does not show the change (stays in review)."""
    new = str(ch.get("new") or "").strip()
    if not new or not added:
        return []
    # code rarely carries the prose form of the value ('1000자' -> '[:1000]'): match the whole new value or its
    # code-like tokens (numbers, identifiers) that the old value did not have
    old_tokens = set(re.findall(r"[A-Za-z0-9_.]+", str(ch.get("old") or "")))
    needles = {new} | {t for t in re.findall(r"[A-Za-z0-9_.]+", new) if t not in old_tokens and (len(t) > 1 or t.isdigit())}
    hits = [(p, n, t) for p, n, t in added if t.strip() and any(x in t for x in needles)]
    named = [h for h in hits if Path(h[0]).name in text or Path(h[0]).stem in text]
    picked, seen = [], set()
    for p, n, t in named + [h for h in hits if not h[0].split("/")[-1].startswith("test_")] + hits:
        if (p, n) in seen or len(picked) >= MAX_CODE_REFS:
            continue
        seen.add((p, n))
        picked.append({"type": "code_test", "locator": f"{p}:{n}", "quote": t.strip()[:300]})
    return picked


def _update_fact(ch, item, text, code_refs=()):
    refs = [{"type": "user_utterance", "locator": "change/user_quote", "quote": ch["user_quote"]},
            {"type": "official_doc", "locator": f"fragment/{item['alias']}", "quote": item["text"]}, *code_refs]
    if ch.get("forms_quote"):
        refs.insert(1, {"type": "user_utterance", "locator": "change/forms_quote", "quote": ch["forms_quote"]})
    return {"operation": "update", "kind": "fact", "subject": text.split()[0] if text.split() else ch["subject"],
            "fact": text, "target_ref": item["id"], "evidence_source": "user_confirmed",
            "reason": f"사용자가 확정한 변경({ch['subject']}: {ch['old']} → {ch['new']})을 이 조각에 반영한다.",
            "evidence_refs": refs, **({"expected_revision": item["revision"]} if item.get("revision") else {})}


def _deprecate_fact(ch, item, why):
    refs = [{"type": "user_utterance", "locator": "change/user_quote", "quote": ch["user_quote"]},
            {"type": "official_doc", "locator": f"fragment/{item['alias']}", "quote": item["text"]}]
    subject = ch["subject"]
    return {"operation": "deprecate", "kind": "fact", "subject": subject,
            "fact": f"{subject} 변경으로 [{item['alias']}] 는 더 이상 유효하지 않다: {why.strip()}",
            "target_ref": item["id"], "evidence_source": "user_confirmed",
            "reason": f"사용자가 확정한 변경({subject}: {ch['old']} → {ch['new']})으로 이 조각을 폐기한다.",
            "evidence_refs": refs}


def fix_submit(dsn, plan_id, answers, ask, record, *, partition_key, work_unit_id=None, cwd=None, precheck=None):
    """record(data) is knowledge_cli.record bound to dsn; accepted updates become ordinary update facts.
    precheck(fact) -> list of {code, detail}: the ledger's own lint, run before record so rejected rewrites come
    back as retry (with the reason) instead of being reported as accepted and then refused by the ledger."""
    plan = _load_plan(plan_id)
    ch = plan["change"]
    items = {it["alias"]: it for it in plan["items"]}
    got = {}
    errors = []
    for i, a in enumerate(answers if isinstance(answers, list) else []):
        if not isinstance(a, dict) or a.get("alias") not in items:
            errors.append({"code": "E_ALIAS", "where": f"answers.{i}", "detail": "alias not in this plan"})
            continue
        if a.get("action") not in ("update", "deprecate", "keep"):
            errors.append({"code": "E_ACTION", "where": f"answers.{i}", "detail": "action must be update|deprecate|keep"})
            continue
        if a["action"] == "update" and (not isinstance(a.get("text"), str) or not a["text"].strip()):
            errors.append({"code": "E_TEXT", "where": f"answers.{i}", "detail": "update needs full corrected text"})
            continue
        if a["action"] == "deprecate" and (not isinstance(a.get("why"), str) or not a["why"].strip()):
            errors.append({"code": "E_WHY", "where": f"answers.{i}", "detail": "deprecate needs why (why this fragment is no longer valid)"})
            continue
        got[a["alias"]] = a
    missing = [al for al in items if al not in got]
    if missing:
        errors.append({"code": "E_MISSING", "where": "answers", "detail": f"every plan item needs an answer; missing {len(missing)}",
                       "aliases": missing})
    if errors:
        return {"ok": False, "errors": errors}
    ups = [al for al, a in got.items() if a["action"] == "update"]
    retry, accepted = [], []
    for al in ups:
        new_text, old_text = got[al]["text"], items[al]["text"]
        if new_text.strip() == old_text.strip():
            retry.append({"alias": al, "reason": "unchanged text", "text": old_text})
        elif len(new_text) > MAX_GROWTH * max(1, len(old_text)):
            retry.append({"alias": al, "reason": "text grew too much; change only the old part", "text": old_text})
        else:
            accepted.append(al)
    if accepted:
        state = {"change": {k: ch[k] for k in ("subject", "old", "new", "instruction")}}
        scores = ask(state, [got[al]["text"] for al in accepted], STILL_Q)
        still = {al for al, s in zip(accepted, scores) if s >= THRESHOLD}
        retry += [{"alias": al, "reason": "old content still present", "text": items[al]["text"], "previous_attempt": got[al]["text"]}
                  for al in accepted if al in still]
        accepted = [al for al in accepted if al not in still]
    added = _added_lines(cwd) if accepted else []
    code = {al: _code_refs(ch, got[al]["text"], added) for al in accepted}
    if accepted and precheck is not None:
        passed = []
        for al in accepted:
            errs = precheck(_update_fact(ch, items[al], got[al]["text"], code[al]))
            if errs:
                idents = [e["detail"].replace(" absent from evidence_quote", "") for e in errs if e.get("code") == "E_CLAIM_QUOTE"]
                reason = (f"identifier not in the confirmed change or the original fragment: {', '.join(idents)} — "
                          "use only names that appear in change.user_quote or the original text" if idents
                          else "ledger lint: " + ", ".join(sorted({e.get('code', '?') for e in errs})))
                retry.append({"alias": al, "reason": reason, "text": items[al]["text"], "previous_attempt": got[al]["text"],
                              "lint": sorted({e.get("code", "?") for e in errs})})
            else:
                passed.append(al)
        accepted = passed
    deps = [al for al, a in got.items() if a["action"] == "deprecate"]
    if deps and precheck is not None:
        ok = []
        for al in deps:
            errs = precheck(_deprecate_fact(ch, items[al], got[al]["why"]))
            if errs:
                retry.append({"alias": al, "reason": "ledger lint: " + ", ".join(sorted({e.get('code', '?') for e in errs})),
                              "text": items[al]["text"], "lint": sorted({e.get("code", "?") for e in errs})})
            else:
                ok.append(al)
        deps = ok
    recorded = None
    facts = ([_update_fact(ch, items[al], got[al]["text"], code[al]) for al in accepted] +
             [_deprecate_fact(ch, items[al], got[al]["why"]) for al in deps])
    if facts:
        recorded = record({"partition_key": partition_key, "host_id": plan["host_id"], "facts": facts,
                           "work_unit_id": work_unit_id, "cwd": cwd, "atomic": True})
    return {"ok": True, "plan_id": plan_id, "accepted": accepted, "deprecated": deps, "retry": retry, "recorded": recorded,
            "kept": [al for al, a in got.items() if a["action"] == "keep"]}
