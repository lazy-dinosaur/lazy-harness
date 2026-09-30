"""Ledger protocol lines (schema-delta '원장 규약·스키마 0009'): one line = one change/observation of one key '대상/속성'.
lint + key registry (reuse nudges, no LLM) + storage + the mechanical relation of two records (conflict-01 D2 rules)."""
import difflib
import re

import dedup

KEY = re.compile(r"^[^/\s]+/[^/\s]+$")
KINDS = ("change", "observation")
SOURCES = ("user", "code", "doc", "worker")
SIMILAR = 0.6


def lint(lines):
    """[{code, where, detail}] for malformed lines; the tool returns them so the worker rewrites once."""
    errs = []
    if not isinstance(lines, list) or not lines:
        return [{"code": "E_LINES", "where": "lines", "detail": "nonempty lines required: one line = one key's change or observation"}]
    seen = set()
    for i, x in enumerate(lines):
        w = f"lines.{i}"
        if not isinstance(x, dict):
            errs.append({"code": "E_LINES", "where": w, "detail": "line must be an object"}); continue
        key = str(x.get("key", "")).strip()
        if not KEY.match(key):
            errs.append({"code": "E_KEY", "where": w + ".key", "detail": "key must be '대상/속성' (one slash, no spaces)"})
        elif key in seen:
            errs.append({"code": "E_KEY_TWICE", "where": w + ".key", "detail": "one key per record; merge the lines or split the record"})
        seen.add(key)
        new = str(x.get("new", "")).strip()
        if not new:
            errs.append({"code": "E_NEW", "where": w + ".new", "detail": "new value required (write only what you know)"})
        elif re.search(r"[,，;]| 그리고 | 및 ", new) and not re.fullmatch(r"[\d,]+\D*", new):
            errs.append({"code": "E_ONE_VALUE", "where": w + ".new", "detail": "one value per line; split into lines"})
        if x.get("kind") not in KINDS:
            errs.append({"code": "E_LINE_KIND", "where": w + ".kind", "detail": "kind must be change|observation"})
        if x.get("source") not in SOURCES:
            errs.append({"code": "E_LINE_SOURCE", "where": w + ".source", "detail": "source must be user|code|doc|worker"})
    return errs


def _norm(key):
    return dedup.normalize(key.replace("/", " "))


def similar_keys(key, known):
    """Existing keys that may name the same target: same subject part, or close spelling."""
    subject = key.split("/")[0]
    out = [k for k in known if k != key and (k.split("/")[0] == subject or
           difflib.SequenceMatcher(None, _norm(k), _norm(key)).ratio() >= SIMILAR)]
    return sorted(out, key=lambda k: -difflib.SequenceMatcher(None, _norm(k), _norm(key)).ratio())[:5]


def check_keys(cur, host, lines):
    """Unknown keys are refused once with similar existing keys; a line with new_key=true registers a new key."""
    cur.execute("select key from knowledge.fact_key where host_id=%s and status='active'", (host,))
    known = [r[0] for r in cur.fetchall()]
    errs = []
    for i, x in enumerate(lines):
        key = x["key"].strip()
        if key in known or x.get("new_key") is True:
            continue
        near = similar_keys(key, known)
        errs.append({"code": "E_KEY_UNKNOWN", "where": f"lines.{i}.key", "similar": near,
                     "detail": "unknown key. If it is one of `similar`, reuse that key; if it is really a new target, resend the line with new_key: true"})
    return errs


def store(cur, host, entry_id, facts):
    """Register new keys and write every fact's lines (append-only)."""
    for fi, fact in enumerate(facts):
        for li, x in enumerate(fact.get("lines") or []):
            key = x["key"].strip()
            cur.execute("""insert into knowledge.fact_key(host_id,key,description) values (%s,%s,%s)
                        on conflict (host_id,key) do nothing""", (host, key, str(x.get("new", ""))[:120]))
            cur.execute("""insert into knowledge.ledger_line(entry_id,fact_index,line_no,host_id,key,target_fragment_id,old_value,new_value,
                        kind,source,temporary,statement) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (entry_id, fi, li, host, key, x.get("target_ref") or fact.get("target_ref"), str(x.get("old") or ""),
                         str(x["new"]).strip(), x["kind"], x["source"], bool(x.get("temporary")), fact["fact"]))


def relation(earlier, new, fragment_of=lambda key: None):
    """conflict-01 D2 rules on two records' lines: merge | separate | replace | combine | conflict."""
    norm = lambda s: dedup.normalize(str(s or "")).replace(",", "")
    E = [x for x in earlier if not x.get("temporary")] or earlier
    ek, nk = {x["key"]: x for x in E}, {x["key"]: x for x in new}
    common = set(ek) & set(nk)
    if not common:
        same = {fragment_of(k) for k in ek} & {fragment_of(k) for k in nk} - {None}
        return "combine" if same else "separate"
    out = []
    for k in common:
        e, n = ek[k], nk[k]
        if norm(e["new"]) == norm(n["new"]):
            out.append("merge")
        elif n["kind"] == "change" and not (e["kind"] == "change" and n["kind"] == "observation"):
            out.append("replace")
        else:
            out.append("conflict")
    if set(ek) - common:
        return "separate"
    if "conflict" in out:
        return "conflict"
    return "replace" if "replace" in out else "merge"
