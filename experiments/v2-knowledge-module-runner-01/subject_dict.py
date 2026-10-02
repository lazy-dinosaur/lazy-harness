"""Subject dictionary (schema-delta '주어는 기록할 때 맞추고 소화할 때 등록', 2026-09-30).

One dictionary per host. Record time only reads it: an existing subject replaces the written name in the fact.
Digestion is the only writer: a name still new is re-checked against subjects registered after the record was made,
then registered. Matching (structure-01 contra04, 2026-09-30): code first strips generic tails (화면/기능/페이지/함수/
동작/창) and matches exactly; otherwise e5 candidates on that core go to Jev with each subject's sentences as JSON
(name-only Jev: variants 4/8; tail + sentences: 8/8, document/test traps merged 0/6 in both).
"""
import json
import math
import re

import embed

COS_MIN = 0.83   # e5 candidate floor for the same-entity question
SAME_KEEP = 0.9  # Jev same-entity probability to reuse an existing name (flow3 r2: 0.7 merged 'domain describe' into '도메인 설명')
TOP = 5
# generic tails that do not change the entity; 테스트/SDD/문서/규칙 are NOT here (they name a different thing)
TAIL = re.compile(r"(?:\s*(?:화면|기능|페이지|함수|동작|창))+$")
SAME_Q = ("state.new 와 items[{i}] 는 지식 문장의 주어 두 개다. 각각 name 과 그 주어가 쓰인 문장(sentences)이 있다. "
          "문장 내용을 보고 두 name 이 같은 대상을 가리키는지 판단하라. "
          "true: 표기·띄어쓰기·영문/한글·백틱 차이, 같은 대상에 붙인 '기능/화면/페이지/동작/함수' 같은 수식어 차이. "
          "false: 서로 다른 대상(형제 기능, 다른 파일, 다른 화면), 그 대상에 관한 문서·SDD·규칙·계약·테스트·변경·경로.")
NEW = ("new", "new_unchecked", "pending")


def norm(name):
    s = re.sub(r"[`'\"]", "", str(name or "")).strip()
    s = re.sub(r"\s+", " ", s)
    return s.lower() if s.isascii() else s


def core(name):
    n = norm(name)
    c = TAIL.sub("", n).strip() or n
    return re.sub(r"[A-Z]+", lambda m: m.group(0).lower(), c)  # latin letters case-insensitive: 'CALL 화면' == 'CALL'


def _vec(values):
    return "[" + ",".join(str(float(v)) for v in values) + "]"


def cos(u, v):
    d = math.sqrt(sum(a * a for a in u)) * math.sqrt(sum(b * b for b in v))
    return sum(a * b for a, b in zip(u, v)) / d if d else 0.0


def lookup(cur, host, name):
    """Known spelling, or its core without a generic tail."""
    for key in dict.fromkeys((norm(name), core(name))):
        cur.execute("""select s.subject_id::text, s.name from knowledge.subject_alias a
                       join knowledge.subject s on s.subject_id=a.subject_id
                       where a.host_id=%s and a.alias=%s""", (host, key))
        row = cur.fetchone()
        if row:
            return {"subject_id": row[0], "name": row[1]}
    return None


def sentences(cur, subject_id, k=2):
    cur.execute("""select text from knowledge.fragment where subject_id=%s and active
                   order by updated_at desc limit %s""", (subject_id, k))
    return [r[0][:160] for r in cur.fetchall()]


def nearest(cur, host, vector, after=None, k=TOP):
    """Existing subjects whose core vector is within COS_MIN; after: only subjects registered later than this time."""
    v = _vec(vector)
    cur.execute("""select s.subject_id::text, s.name, 1 - (e.embedding operator(extensions.<=>) %s::extensions.vector)
                   from knowledge.subject s
                   join knowledge.subject_embedding e on e.subject_id=s.subject_id and e.model_id=%s
                   where s.host_id=%s and (%s::timestamptz is null or s.created_at > %s::timestamptz)
                   order by e.embedding operator(extensions.<=>) %s::extensions.vector limit %s""",
                (v, embed.MODEL_ID, host, after, after, v, k))
    out = [{"subject_id": r[0], "name": r[1], "cos": float(r[2])} for r in cur.fetchall() if float(r[2]) >= COS_MIN]
    for c in out:
        c["sentences"] = sentences(cur, c["subject_id"])
    return out


CODE_LIKE = re.compile(r"[A-Za-z_`./]")


def _compatible(a, b):
    """flow3 r2 (2026-10-01): never ask Jev to merge a name into one that contains it ('도메인 설명' / '도메인 설명 길이' are
    two things) or a code identifier into a Korean concept ('domain describe' / '도메인 설명')."""
    x, y = re.sub(r"\s+", "", core(a)), re.sub(r"\s+", "", core(b))
    if x != y and (x in y or y in x):
        return False
    return bool(CODE_LIKE.search(a)) == bool(CODE_LIKE.search(b))


def decide(name, cands, same, sentence=None):
    """same(state, texts, question) -> [probability]; Jev sees both subjects with their sentences (JSON)."""
    cands = [c for c in (cands or []) if _compatible(name, c["name"])]
    if not cands or same is None:
        return None
    state = {"new": {"name": name, "sentences": [sentence[:200]] if isinstance(sentence, str) and sentence else []}}
    items = [json.dumps({"name": c["name"], "sentences": c.get("sentences") or []}, ensure_ascii=False) for c in cands]
    scores = same(state, items, SAME_Q)
    best, k = max(((float(s), k) for k, s in enumerate(scores)), default=(0.0, None))
    return cands[k] if k is not None and best >= SAME_KEEP else None


PARTICLES = (("으로", "로"), ("은", "는"), ("이", "가"), ("을", "를"), ("과", "와"))


def _jong(word):
    w = re.sub(r"[`'\"\s)]+$", "", word)
    ch = w[-1:] if w else ""
    if not ch:
        return False
    o = ord(ch) - 0xAC00
    if 0 <= o < 11172:
        return o % 28 != 0
    if ch.isdigit():
        return ch in "013678"
    return ch.lower() in "lmn" or w.lower().endswith("ng")


def _particle(new, p):
    for a, b in PARTICLES:
        if p in (a, b):
            if a == "으로":
                return "로" if (not _jong(new) or new.rstrip("`").endswith(("ㄹ", "l", "L"))) else "으로"
            return a if _jong(new) else b
    return p


def rewrite(text, old, new):
    """Replace the subject where it stands as a word (whole name, any particle fixed for the new name). An occurrence that
    already reads as the longer new name is left alone: '도메인 설명 길이는' would become '도메인 설명 길이 길이는' (flow3 r2)."""
    if not old or not new or old == new or old not in text:
        return text
    pat = re.compile(r"(?<![0-9A-Za-z가-힣_])" + re.escape(old) +
                     r"(으로|로|은|는|이|가|을|를|과|와|에서|에게|에|의|도|만|부터|까지|보다|처럼)?(?![0-9A-Za-z가-힣_])")
    def one(m):
        if len(new) > len(old) and text.startswith(new, m.start()):
            return m.group(0)
        return new + (_particle(new, m.group(1)) if m.group(1) else "")
    return pat.sub(one, text)


def add_alias(cur, host, alias, subject_id):
    for key in dict.fromkeys((norm(alias), core(alias))):
        cur.execute("""insert into knowledge.subject_alias(host_id,alias,subject_id) values (%s,%s,%s)
                       on conflict (host_id, alias) do nothing""", (host, key, subject_id))


def register(cur, host, name, vector=None, allow_embed=True):
    """Digestion only. Returns subject_id (existing when any spelling already maps to it). allow_embed=False inside the
    digestion transaction: no embedding service call there (astra big review r2); store_pg.embed_unit fills it after."""
    hit = lookup(cur, host, name)
    if hit:
        return hit["subject_id"]
    cur.execute("""insert into knowledge.subject(host_id,name) values (%s,%s)
                   on conflict (host_id,name) do update set name=excluded.name returning subject_id::text""", (host, name))
    sid = cur.fetchone()[0]
    add_alias(cur, host, name, sid)
    if vector is None and allow_embed:
        try:
            vector = embed.encode_queries([core(name)])[0]
        except embed.EmbeddingUnavailable:
            vector = None
    if vector is not None:
        cur.execute("""insert into knowledge.subject_embedding(subject_id,model_id,embedding) values (%s,%s,%s::extensions.vector)
                       on conflict (subject_id,model_id) do update set embedding=excluded.embedding""",
                    (sid, embed.MODEL_ID, _vec(vector)))
    return sid


def resolver(connect, dsn, host, unit=None, same=None, embed_fn=None):
    """Record time (read only). resolve(name, sentence) -> (name_to_store, how);
    how in exact|alias|same_entity|pending|new|new_unchecked. pending = names still new in this work unit."""
    efn = embed_fn or embed.encode_queries
    pending = {}  # core -> (name, sentence)
    if unit:
        with connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""select judgement_body from knowledge.ledger_entry where work_unit_id=%s
                           and state::text not in ('closed','expired','rejected_input') order by created_at""", (unit,))
            for (body,) in cur.fetchall():
                for f in body.get("facts", []):
                    if f.get("subject_new") and isinstance(f.get("subject"), str):
                        pending.setdefault(core(f["subject"]), (f["subject"], f.get("fact", "")))

    def resolve(name, sentence=None):
        with connect(dsn) as conn, conn.cursor() as cur:
            hit = lookup(cur, host, name)
        if hit:
            return hit["name"], ("exact" if hit["name"] == name else "alias")
        c = core(name)
        if c in pending:
            return pending[c][0], "pending"
        if same is None:
            pending[c] = (name, sentence or "")
            return name, "new_unchecked"
        try:
            v = efn([c])[0]
        except embed.EmbeddingUnavailable:
            pending[c] = (name, sentence or "")
            return name, "new_unchecked"
        with connect(dsn) as conn, conn.cursor() as cur:
            cands = nearest(cur, host, v)
        if pending:  # Jev is called with no transaction open
            keys = list(pending)
            cands += [{"subject_id": None, "name": pending[k][0], "sentences": [pending[k][1][:160]], "cos": cc}
                      for k, pv in zip(keys, efn(keys)) for cc in [cos(v, pv)] if cc >= COS_MIN]
        best = decide(name, cands, same, sentence)
        if best:
            return best["name"], ("same_entity" if best["subject_id"] else "pending")
        pending[c] = (name, sentence or "")
        return name, "new"
    return resolve
