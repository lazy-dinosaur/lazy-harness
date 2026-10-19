"""Merge guards shared by the G4 clean-up (write-01 round_merge2 / round_clause / round_guard, the most balanced
result: detail loss 1.1%, new-knowledge loss 0). A merged sentence replaces two fragments only if BOTH guards pass.
  code_missing(a, b, merged): identifiers, paths, numbers, negations, camelCase/PascalCase/CONST and lint identifiers
                              present in a source but absent from the merged sentence
  clauses(text): split a sentence into condition-sized parts (parentheses/backticks protected) for the Jev clause check
"""
import re

import runner

IDENT_RE = re.compile(r"`[^`]+`|(?<![\w/.-])(?:[\w.-]+/)+[A-Za-z0-9_.-]*[A-Za-z0-9_]|\b\d+(?:[.,]\d+)?\s*(?:분|초|시간|일|개|%|px|ms|MB|GB)?")
NEG_RE = re.compile(r"않|금지|없|말고|말아|못하|제외|거부")
# Python \b treats Hangul as word chars, so '…Number는' has no boundary: delimit by ASCII alnum/_ instead.
CAMEL = re.compile(r"(?<![A-Za-z0-9_])(?:[a-z]+[A-Z][A-Za-z0-9]*|[A-Z][a-z0-9]+[A-Z][A-Za-z0-9]*|[A-Z0-9]+_[A-Z0-9_]+)(?![A-Za-z0-9_])")
CLAUSE_Q = ("items[{i}] 는 원문 문장의 한 부분이다. 이 부분의 내용(조건·값·대상·식별자·부정)이 merged 문장에 같은 뜻으로 들어 있는가? "
            "표현이 달라도 뜻이 같으면 true. 빠졌거나 뜻이 바뀌었으면 false.")
SPLIT = re.compile(r"(?<=[.!?。;])\s+|,\s+|(?<=며)\s+|(?<=고),?\s+|(?<=지만)\s+|(?<=면서)\s+|(?<=거나)\s+")


def code_missing(a, b, merged):
    merged = merged or ""
    miss = set()
    for src in (a or "", b or ""):
        for tok in IDENT_RE.findall(src):
            t = tok.strip()
            if t and t.strip("`") not in merged:
                miss.add(t)
        for t in set(runner.claim_identifiers(src)) | set(CAMEL.findall(src)):
            if t not in merged:
                miss.add(t)
    if any(NEG_RE.search(s or "") for s in (a, b)) and not NEG_RE.search(merged):
        miss.add("(부정 표현: …하지 않는다/금지/없다)")
    return sorted(miss)


def clauses(text):
    out = []
    safe = re.sub(r"\([^)]*\)|`[^`]*`", lambda m: m.group(0).replace(",", "\u0001").replace(" ", "\u0002"), text or "")
    for part in SPLIT.split(safe):
        p = (part or "").replace("\u0001", ",").replace("\u0002", " ").strip(" ,;")
        if not p:
            continue
        if len(p) < 4 and out:
            out[-1] += " " + p
        else:
            out.append(p)
    return out or [text]


def clause_missing(ask, a, b, merged):
    """Clauses of the two sources that Jev does not find (same meaning) in the merged sentence."""
    cl = clauses(a) + clauses(b)
    scores = ask({"merged": merged}, cl, CLAUSE_Q)
    return [c for c, s in zip(cl, scores) if s < 0.5]
