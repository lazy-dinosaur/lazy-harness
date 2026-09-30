"""Subject dictionary (schema-delta '주어는 기록할 때 맞추고 소화할 때 등록', 2026-09-30).

One dictionary per host. Record time only reads it: an existing subject (same entity by vector candidates + Jev)
replaces the written name in the fact. Digestion is the only writer: a name still new is re-checked against
subjects registered after the record was made, then registered. Thresholds from structure-01 contra02/03.
"""
import math
import re

import embed

COS_MIN = 0.83   # e5 candidate floor for the same-entity question
SAME_KEEP = 0.7  # Jev same-entity probability to reuse an existing name
TOP = 5
SAME_Q = ("items[{i}] 는 '새 이름 ||| 기존 이름' 이다(지식 문장의 주어). 두 이름이 같은 대상을 가리키는가? "
          "true: 표기·띄어쓰기·영문/한글·백틱 차이, 같은 대상에 붙인 '기능/화면/페이지/동작/함수' 같은 수식어 차이 "
          "(예: '예약관리'와 '예약관리 페이지', 'chat.markAsRead 함수'와 '`chat.markAsRead`'). "
          "false: 서로 다른 대상(형제 기능, 다른 파일, 다른 화면), 그리고 그 대상에 관한 문서·SDD·규칙·계약·테스트·변경·경로"
          "(예: '예약관리 SDD'는 '예약관리'와 다른 대상).")
NEW = ("new", "new_unchecked", "pending")


def norm(name):
    s = re.sub(r"[`'\"]", "", str(name or "")).strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower() if s.isascii() else s


def _vec(values):
    return "[" + ",".join(str(float(v)) for v in values) + "]"


def cos(u, v):
    d = math.sqrt(sum(a * a for a in u)) * math.sqrt(sum(b * b for b in v))
    return sum(a * b for a, b in zip(u, v)) / d if d else 0.0


def lookup(cur, host, name):
    cur.execute("""select s.subject_id::text, s.name from knowledge.subject_alias a
                   join knowledge.subject s on s.subject_id=a.subject_id
                   where a.host_id=%s and a.alias=%s""", (host, norm(name)))
    row = cur.fetchone()
    return {"subject_id": row[0], "name": row[1]} if row else None


def nearest(cur, host, vector, after=None, k=TOP):
    """Existing subjects whose name vector is within COS_MIN; after: only subjects registered later than this time."""
    v = _vec(vector)
    cur.execute("""select s.subject_id::text, s.name, 1 - (e.embedding operator(extensions.<=>) %s::extensions.vector)
                   from knowledge.subject s
                   join knowledge.subject_embedding e on e.subject_id=s.subject_id and e.model_id=%s
                   where s.host_id=%s and (%s::timestamptz is null or s.created_at > %s::timestamptz)
                   order by e.embedding operator(extensions.<=>) %s::extensions.vector limit %s""",
                (v, embed.MODEL_ID, host, after, after, v, k))
    return [{"subject_id": r[0], "name": r[1], "cos": float(r[2])} for r in cur.fetchall() if float(r[2]) >= COS_MIN]


def decide(name, cands, same):
    """same(state, texts, question) -> [probability]; returns the best candidate when Jev is sure enough."""
    if not cands or same is None:
        return None
    scores = same({}, [name + " ||| " + c["name"] for c in cands], SAME_Q)
    best, k = max(((float(s), k) for k, s in enumerate(scores)), default=(0.0, None))
    return cands[k] if k is not None and best >= SAME_KEEP else None


def rewrite(text, old, new):
    return text.replace(old, new, 1) if old and new and old != new and old in text else text


def add_alias(cur, host, alias, subject_id):
    cur.execute("""insert into knowledge.subject_alias(host_id,alias,subject_id) values (%s,%s,%s)
                   on conflict (host_id, alias) do nothing""", (host, norm(alias), subject_id))


def register(cur, host, name, vector=None):
    """Digestion only. Returns subject_id (existing when any spelling already maps to it)."""
    hit = lookup(cur, host, name)
    if hit:
        return hit["subject_id"]
    cur.execute("""insert into knowledge.subject(host_id,name) values (%s,%s)
                   on conflict (host_id,name) do update set name=excluded.name returning subject_id::text""", (host, name))
    sid = cur.fetchone()[0]
    add_alias(cur, host, name, sid)
    if vector is None:
        try:
            vector = embed.encode_queries([norm(name)])[0]
        except embed.EmbeddingUnavailable:
            vector = None
    if vector is not None:
        cur.execute("""insert into knowledge.subject_embedding(subject_id,model_id,embedding) values (%s,%s,%s::extensions.vector)
                       on conflict (subject_id,model_id) do update set embedding=excluded.embedding""",
                    (sid, embed.MODEL_ID, _vec(vector)))
    return sid


def resolver(connect, dsn, host, unit=None, same=None, embed_fn=None):
    """Record time (read only). resolve(name) -> (name_to_store, how); how in exact|alias|same_entity|pending|new|new_unchecked.
    pending = names still new in this work unit, so one unit uses one spelling."""
    efn = embed_fn or embed.encode_queries
    pending = {}
    if unit:
        with connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""select judgement_body from knowledge.ledger_entry where work_unit_id=%s
                           and state::text not in ('closed','expired','rejected_input') order by created_at""", (unit,))
            for (body,) in cur.fetchall():
                for f in body.get("facts", []):
                    if f.get("subject_new") and isinstance(f.get("subject"), str):
                        pending.setdefault(norm(f["subject"]), f["subject"])

    def resolve(name):
        with connect(dsn) as conn, conn.cursor() as cur:
            hit = lookup(cur, host, name)
        if hit:
            return hit["name"], ("exact" if hit["name"] == name else "alias")
        n = norm(name)
        if n in pending:
            return pending[n], "pending"
        if same is None:
            pending[n] = name
            return name, "new_unchecked"
        try:
            v = efn([n])[0]
        except embed.EmbeddingUnavailable:
            pending[n] = name
            return name, "new_unchecked"
        with connect(dsn) as conn, conn.cursor() as cur:
            cands = nearest(cur, host, v)
        if pending:  # Jev is called with no transaction open
            names = list(pending)
            cands += [{"subject_id": None, "name": pending[k], "cos": c}
                      for k, pv in zip(names, efn(names)) for c in [cos(v, pv)] if c >= COS_MIN]
        best = decide(name, cands, same)
        if best:
            return best["name"], ("same_entity" if best["subject_id"] else "pending")
        pending[n] = name
        return name, "new"
    return resolve
