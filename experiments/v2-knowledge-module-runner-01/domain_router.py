"""Domain routing for digestion (schema-delta: domain tags, routing decided 2026-09-27).

The worker writes a rough domain name in partition_key. Digestion routes each add:
  1. proposed name is an active domain (after following merges) -> use it, no Jev call
  2. no active domains yet -> create the proposed name
  3. otherwise Jev choice over active domains (+ 'none'):
       top is an existing domain            -> that domain
       top is 'none' and p(none) >= NEW_MIN -> create the proposed name
       ambiguous                            -> the best existing domain (avoid scattering names)
Jev cannot write names, so a new domain always takes the worker's proposed name.
"""
import json
import re

NEW_MIN = 0.7
ROUTE_MIN = 0.6  # route_unit: join an existing domain only when Jev is at least this sure; otherwise create
SAME_MIN = 0.8  # G5: before creating, a one-to-one 'same area?' check against the closest existing domains
CONFIRM_TOP = 2
SAME_Q = ("items[{i}] 는 이미 있는 영역(도메인)이다. facts 의 작업이 속한 영역과 같은 영역인가? "
          "이름이 달라도 같은 기능·업무 영역이면 예, 관련은 있지만 다른 기능·업무면 아니오.")


def norm(name):
    return re.sub(r"\s+", " ", (name or "").strip())


def load(cur, host):
    """{domain: row} for the host, rows have description/status/merged_into."""
    cur.execute("select domain, description, status, merged_into from knowledge.domain_type where host_id=%s", (host,))
    return {r[0]: {"description": r[1], "status": r[2], "merged_into": r[3]} for r in cur.fetchall()}


def resolve(domains, name):
    """Follow merged_into to the surviving domain (cycle-safe)."""
    seen = set()
    while name in domains and domains[name]["merged_into"] and name not in seen:
        seen.add(name)
        name = domains[name]["merged_into"]
    return name


def route(domains, proposed, fact_text, choose):
    """Return (domain, how). choose(fact_text, options:{key: description}) -> {key: probability}."""
    proposed = norm(proposed)
    active = {d: v for d, v in domains.items() if v["status"] == "active"}
    if proposed:
        r = resolve(domains, proposed)
        if r in active:
            return r, "exact"
    if not active:
        return proposed, "new"
    names = sorted(active)
    options = {f"d{i}": f"{n}: {active[n]['description'] or n}" for i, n in enumerate(names)}
    options["none"] = "위 어느 영역에도 속하지 않는다(새 영역)"
    probs = choose(fact_text, options)
    best = max((k for k in probs if k != "none"), key=lambda k: probs.get(k, 0.0), default=None)
    top = max(probs, key=probs.get) if probs else None
    if top == "none" and probs["none"] >= NEW_MIN and proposed:
        return proposed, "new"
    if best is not None:
        return names[int(best[1:])], "routed"
    return (proposed or names[0]), "new" if proposed else "routed"


def route_unit(domains, proposed, facts, choose, confirm=None):
    """Route a whole work unit (all its add facts) to ONE domain. Return (domain, how).
    A fragment has exactly one domain (2026-09-28: related-domain lists were tried and dropped — auto links were
    39% wrong and cross-domain knowledge was 0/42; knowledge shared by two domains is handled with merge).
    domain-01: fact-by-fact routing sent 31 records away from the worker's (correct) name because the first
    ambiguous fact joined an existing domain. Here ambiguity creates the worker's name; scattered names are
    fixed later with merge."""
    proposed = norm(proposed)
    active = {d: v for d, v in domains.items() if v["status"] == "active"}
    if proposed:
        r = resolve(domains, proposed)
        if r in active:
            return r, "exact"
    if not active:
        return (proposed or "general"), "new"
    text = "\n".join(f"- {f[:200]}" for f in facts[:8])
    names = sorted(active)
    options = {f"d{i}": f"{n}: {active[n]['description'] or n}" for i, n in enumerate(names)}
    options["none"] = "위 어느 영역에도 속하지 않는다(새 영역)"
    probs = choose(text, options)
    top = max(probs, key=probs.get) if probs else None
    if top and top != "none" and probs[top] >= ROUTE_MIN:
        return names[int(top[1:])], "routed"
    # G5 (user 2026-09-28): stop scattering at creation — before making a new domain, ask one-to-one about the
    # closest existing ones (a pairwise question is sharper than the multi-choice); confirm(text, [option text]) -> scores.
    if confirm is not None:
        near = sorted((k for k in probs if k != "none"), key=lambda k: -probs[k])[:CONFIRM_TOP]
        if near:
            scores = confirm(text, [options[k] for k in near])
            best = max(range(len(near)), key=lambda i: scores[i])
            if scores[best] >= SAME_MIN:
                return names[int(near[best][1:])], "confirmed"
    return (proposed or names[0]), ("new" if proposed else "routed")


def make_confirm(cfg):
    """Jev one-to-one 'same area?' check for route_unit (noul per candidate domain)."""
    import worker_tools
    ask = worker_tools.make_ask(cfg)
    return lambda facts_text, candidates: ask({"facts": facts_text}, candidates, SAME_Q)


def ensure(cur, host, domain, description):
    cur.execute("""insert into knowledge.domain_type(host_id, domain, description) values (%s,%s,%s)
                on conflict (host_id, domain) do nothing""", (host, domain, (description or "")[:200]))


def make_choose(cfg, http=None):
    """Jev choice judge: which domain does this fact belong to."""
    import capture_audit
    judge = capture_audit.make_judge(cfg, **({"http": http} if http else {}))
    def choose(fact_text, options):
        a = judge({"fact": fact_text}, [fact_text], "items[{i}] 의 지식은 어느 영역(기능·업무 부분)에 속하는가?", options)[0]
        p = a.get("probabilities") or {}
        return {k: float(p.get(k, 1.0 if a.get("choice") == k else 0.0)) for k in options}
    return choose


# --- management (knowledge_cli domain) ---
def list_domains(cur, host):
    ds = load(cur, host)
    cur.execute("select domain, count(*) from knowledge.fragment where host_id=%s and active group by domain", (host,))
    counts = dict(cur.fetchall())
    return [{"domain": d, **v, "fragments": counts.get(d, 0)} for d, v in sorted(ds.items())]


def fragments(cur, host, domain):
    """Active fragments of `domain` and of every domain merged into it."""
    ds = load(cur, host)
    target = resolve(ds, domain)
    names = [d for d in ds if resolve(ds, d) == target] or [target]
    cur.execute("""select id::text, alias, domain, text from knowledge.fragment
                   where host_id=%s and active and domain = any(%s)
                   order by domain, seq""", (host, names))
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def merge(cur, host, src, dst):
    ds = load(cur, host)
    if src not in ds or dst not in ds or src == dst:
        raise ValueError("unknown or identical domain")
    if resolve(ds, dst) == src:
        raise ValueError("merge would create a cycle")
    cur.execute("""update knowledge.domain_type set status='retired', merged_into=%s, updated_at=now()
                where host_id=%s and domain=%s""", (dst, host, src))


def retire(cur, host, domain):
    cur.execute("""update knowledge.domain_type set status='retired', updated_at=now()
                where host_id=%s and domain=%s and merged_into is null""", (host, domain))
    if cur.rowcount != 1:
        raise ValueError("unknown domain")
