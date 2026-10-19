"""Immutable admission boundary for an explicitly captured normal-poller cohort."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path


class ExecutionScopeError(ValueError):
    pass


_SCOPE_ISSUER = object()


class VerifiedScopeDependency:
    """Process-local dependency proof issued only from a protected CAS receipt."""
    __slots__ = ("parent", "child", "receipt_id", "source_fingerprint", "_issuer")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            raise AttributeError("verified scope dependencies are immutable")
        object.__setattr__(self, name, value)

    def __init__(self, parent, child, receipt_id, source_fingerprint, *, _issuer=None):
        if _issuer is not _SCOPE_ISSUER:
            raise ExecutionScopeError("scope dependencies require a protected receipt")
        self.parent, self.child = str(parent), str(child)
        self.receipt_id, self.source_fingerprint = str(receipt_id), str(source_fingerprint)
        self._issuer = _issuer

    @classmethod
    def _from_protected_receipt(cls, parent, child, receipt):
        if (not isinstance(receipt, dict) or receipt.get("status") not in {"applied", "existing"}
                or str(receipt.get("parent_id")) != str(parent)
                or str(receipt.get("child_id")) != str(child)
                or not receipt.get("receipt_id") or receipt.get("cas_verified") is not True):
            raise ExecutionScopeError("dependency receipt does not prove a current parent/child CAS")
        fingerprint = receipt.get("source_fingerprint")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64 or any(c not in "0123456789abcdef" for c in fingerprint):
            raise ExecutionScopeError("dependency receipt lacks a verified source fingerprint")
        return cls(parent, child, receipt["receipt_id"], fingerprint, _issuer=_SCOPE_ISSUER)


def _ids(values, name):
    if not isinstance(values, (list, tuple, set, frozenset)):
        raise ExecutionScopeError(f"{name} must be a nonempty collection")
    result = frozenset(str(value) for value in values)
    if not result or any(not value for value in result):
        raise ExecutionScopeError(f"{name} must be a nonempty collection")
    return result


@dataclass(frozen=True, repr=False)
class ExecutionScope:
    """Root allowlist plus explicitly verified parent->child dependencies.

    The scope is invocation state, not project configuration. Root membership is
    immutable; a child is admitted only with a caller-verified receipt binding it
    to an already admitted parent.
    """
    namespace: str
    dataset_fingerprint: str
    root_question_ids: frozenset
    root_fragment_ids: frozenset
    root_work_unit_ids: frozenset
    root_entry_ids: frozenset
    root_subject_ids: frozenset
    root_baseline_fingerprint: str
    source_manifest_fingerprint: str
    dependencies: tuple = ()
    question_fragment_pairs: tuple = ()
    question_fingerprints: tuple = ()
    version: str = "normal-poller-scope-v1"

    def __post_init__(self):
        if not isinstance(self.namespace, str) or not self.namespace.strip():
            raise ExecutionScopeError("execution scope namespace is required")
        for field in ("root_question_ids", "root_fragment_ids"):
            object.__setattr__(self, field, _ids(getattr(self, field), field))
        object.__setattr__(self, "root_subject_ids", frozenset(str(value) for value in self.root_subject_ids))
        for field in ("root_work_unit_ids", "root_entry_ids"):
            values = getattr(self, field)
            object.__setattr__(self, field, frozenset(str(value) for value in values))
        for field in ("dataset_fingerprint", "root_baseline_fingerprint", "source_manifest_fingerprint"):
            value = getattr(self, field)
            if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise ExecutionScopeError(f"{field} must be a SHA-256 fingerprint")
        normalized = []
        for item in self.dependencies:
            if not isinstance(item, VerifiedScopeDependency) or item._issuer is not _SCOPE_ISSUER:
                raise ExecutionScopeError("dependency must be an in-process protected-CAS receipt")
            parent, child = item.parent, item.child
            if parent not in self.root_question_ids | self.root_fragment_ids | self.root_work_unit_ids | self.root_entry_ids:
                raise ExecutionScopeError("dependency parent is outside root scope")
            if child in self.root_question_ids:
                raise ExecutionScopeError("dependency cannot redefine an existing root")
            normalized.append(item)
        object.__setattr__(self, "dependencies", tuple(normalized))
        pairs = []
        for question_id, fragment_ids in self.question_fragment_pairs:
            qid = str(question_id)
            pair = _ids(fragment_ids, "question fragment pair")
            if qid not in self.root_question_ids or not pair.issubset(self.root_fragment_ids):
                raise ExecutionScopeError("question dependency mapping exceeds root membership")
            pairs.append((qid, pair))
        if len({qid for qid, _ in pairs}) != len(pairs):
            raise ExecutionScopeError("duplicate question dependency mapping")
        object.__setattr__(self, "question_fragment_pairs", tuple(pairs))
        fingerprints = tuple((str(qid), str(digest)) for qid, digest in self.question_fingerprints)
        if any(qid not in self.root_question_ids or len(digest) != 64 or
               any(c not in "0123456789abcdef" for c in digest) for qid, digest in fingerprints):
            raise ExecutionScopeError("question fingerprint mapping exceeds root membership")
        if len({qid for qid, _ in fingerprints}) != len(fingerprints):
            raise ExecutionScopeError("duplicate question fingerprint mapping")
        object.__setattr__(self, "question_fingerprints", fingerprints)

    def __repr__(self):
        return (f"ExecutionScope(namespace={self.namespace!r}, version={self.version!r}, "
                f"roots={len(self.root_question_ids)})")

    @property
    def question_ids(self):
        return frozenset(qid for qid, _ in self.question_fragment_pairs)

    @property
    def blocked_root_question_ids(self):
        return self.root_question_ids - self.question_ids

    def admits_question(self, question_id):
        value = str(question_id)
        return value in self.root_question_ids or any(item.child == value for item in self.dependencies)

    def admits_fragment(self, fragment_id):
        value = str(fragment_id)
        return value in self.root_fragment_ids or any(item.child == value for item in self.dependencies)

    def admits_question_fragments(self, question_id, fragment_ids):
        qid = str(question_id)
        fragments = frozenset(map(str, fragment_ids))
        expected = dict(self.question_fragment_pairs).get(qid)
        # Descendants are not callback-admitted merely because a receipt-shaped edge
        # exists; a current per-question fragment mapping must also be captured.
        return qid in self.root_question_ids and expected is not None and fragments == expected

    def pair_for_question(self, question_id):
        """Return the validated immutable root-to-current FID pair, never selector text."""
        pair = dict(self.question_fragment_pairs).get(str(question_id))
        return tuple(sorted(pair)) if pair is not None else None

    def revalidate_current_question(self, dsn, question_id, host_id, fragment_ids):
        """Recheck the scoped root identity/linkage immediately before an effect."""
        qid = str(question_id)
        fragments = tuple(sorted(map(str, fragment_ids)))
        if host_id != self.namespace or not self.admits_question_fragments(qid, fragments):
            raise ExecutionScopeError("current question or fragment pair is outside the execution scope")
        expected = dict(self.question_fingerprints).get(qid)
        if expected is None:
            raise ExecutionScopeError("current question has no captured root fingerprint")
        import hashlib
        import json
        import store_pg
        with store_pg.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("""select e.host_id,q.reason from knowledge.confirmation_queue q
                join knowledge.ledger_entry e on e.entry_id=q.entry_id where q.confirmation_id=%s""", (question_id,))
            row = cur.fetchone()
        if not row or row[0] != self.namespace:
            raise ExecutionScopeError("current question is missing or crossed its approved namespace")
        reason = row[1]
        raw = reason if isinstance(reason, str) else json.dumps(reason, sort_keys=True)
        if hashlib.sha256(raw.encode()).hexdigest() != expected:
            raise ExecutionScopeError("current question linkage changed after scope creation")
        return True

    def admits_unit(self, unit_id):
        value = str(unit_id)
        return value in self.root_work_unit_ids or any(item.child == value for item in self.dependencies)

    def admits_entry(self, entry_id):
        value = str(entry_id)
        return value in self.root_entry_ids or any(item.child == value for item in self.dependencies)

    @classmethod
    def from_materialized_snapshot(cls, snapshot_path, ledger_path, *, namespace,
                                  dataset_fingerprint, source_manifest_fingerprint):
        """Load only a content-checked snapshot paired with its unchanged original ledger."""
        snapshot = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
        payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if (snapshot.get("version") != "normal-poller-lineage-v1" or snapshot.get("immutable") is not True
                or snapshot.get("snapshot_sha256") != digest
                or snapshot.get("original_ledger_sha256") != hashlib.sha256(Path(ledger_path).read_bytes()).hexdigest()
                or set(snapshot.get("root_question_ids", [])) != set(snapshot.get("question_fragment_pairs", {}))
                or set(snapshot.get("root_question_ids", [])) != set(snapshot.get("question_fingerprints", {}))):
            raise ExecutionScopeError("materialized lineage snapshot is invalid or detached from its original ledger")
        pairs = tuple((qid, frozenset(map(str, value))) for qid, value in snapshot["question_fragment_pairs"].items())
        fragments = frozenset(fid for _qid, pair in pairs for fid in pair)
        return cls(namespace, dataset_fingerprint, frozenset(snapshot["root_question_ids"]), fragments,
                   frozenset(), frozenset(), frozenset(), snapshot["baseline_fingerprint"],
                   source_manifest_fingerprint, question_fragment_pairs=pairs,
                   question_fingerprints=tuple(snapshot["question_fingerprints"].items()))

    @classmethod
    def from_pilot_ledger(cls, dsn, path, *, namespace,
                          source_manifest_fingerprint, expected_count=315):
        """Bind the existing retained cohort ledger to current pending DB identities.

        Candidate IDs are read from the approved ledger, never embedded in code.
        A database snapshot supplies each root's exact question, host and fragment
        dependencies; any missing, changed, or cross-namespace row fails closed.
        """
        from runtime_db import bind_runtime_db
        import store_pg

        ledger = json.loads(Path(path).read_text(encoding="utf-8"))
        cases = ledger.get("cases") if isinstance(ledger, dict) else None
        ledger_scope = ledger.get("scope", {}) if isinstance(ledger, dict) else {}
        if not isinstance(cases, list) or len(cases) != expected_count:
            raise ExecutionScopeError("approved cohort ledger is missing or has an unexpected size")
        if ledger_scope.get("host_id") != namespace:
            raise ExecutionScopeError("approved cohort namespace does not match runtime namespace")
        question_ids = [case.get("question_id") for case in cases if isinstance(case, dict)]
        if len(question_ids) != expected_count or len(set(question_ids)) != expected_count:
            raise ExecutionScopeError("approved cohort question identities are incomplete or duplicated")
        context = bind_runtime_db(dsn)
        with store_pg.connect(context.dsn) as conn, conn.cursor() as cur:
            conn.autocommit = False
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("""select q.confirmation_id,e.host_id,e.work_unit_id::text,e.entry_id::text,q.reason
                from knowledge.confirmation_queue q join knowledge.ledger_entry e on e.entry_id=q.entry_id
                where q.confirmation_id=any(%s::bigint[]) and e.host_id=%s
                order by q.confirmation_id""", (question_ids, namespace))
            rows = cur.fetchall()
        if len(rows) != expected_count or {row[0] for row in rows} != set(question_ids):
            raise ExecutionScopeError("approved cohort does not match current namespace question rows")
        fragments, subjects = set(), set()
        case_kinds = {str(case["question_id"]): case.get("kind") for case in cases}
        root_payload = []
        question_pairs = []
        question_fingerprints = []
        with store_pg.connect(context.dsn) as conn, conn.cursor() as cur:
            conn.autocommit = False
            cur.execute("SET TRANSACTION READ ONLY")
            for qid, host, unit_id, entry_id, reason in rows:
                if host != namespace:
                    raise ExecutionScopeError("cohort question crossed the approved namespace")
                try:
                    body = json.loads(reason) if isinstance(reason, str) else reason
                except (TypeError, ValueError):
                    raise ExecutionScopeError("cohort question linkage is invalid") from None
                pair = {str(body.get(key)) for key in ("id", "with_id") if body.get(key)}
                kind = case_kinds.get(str(qid))
                if not pair and kind == "canon_exception":
                    cur.execute("""select id::text from knowledge.fragment where host_id=%s and active
                        and ((alias=%s and text=%s) or (alias=%s and text=%s))""",
                        (namespace, body.get("alias"), body.get("text"), body.get("with"), body.get("with_text")))
                    pair.update(str(row[0]) for row in cur.fetchall())
                elif not pair and kind == "alias_conflict":
                    cur.execute("""select f.id::text from knowledge.fragment f
                        join knowledge.subject_alias a on a.host_id=f.host_id and a.source_fragment_id=f.id
                        where f.host_id=%s and f.active and a.alias=%s and a.subject_id=%s
                        union all
                        (select id::text from knowledge.fragment where host_id=%s and active and subject_id=%s
                         order by revision desc,id limit 1)
                        union all
                        (select id::text from knowledge.fragment where host_id=%s and active and subject_id=%s
                         order by revision desc,id limit 1)""",
                        (namespace, body.get("alias"), body.get("subject_id"), namespace,
                         body.get("subject_id"), namespace, body.get("other_id")))
                    pair.update(str(row[0]) for row in cur.fetchall())
                reason_fingerprint = hashlib.sha256((reason if isinstance(reason, str) else json.dumps(reason, sort_keys=True)).encode()).hexdigest()
                question_fingerprints.append((str(qid), reason_fingerprint))
                if len(pair) == 2:
                    fragments.update(pair)
                    question_pairs.append((str(qid), frozenset(pair)))
                # Incomplete/ambiguous lineage stays an admitted root identity but is
                # excluded from all model/writer selectors until its dependencies are proven.
                root_payload.append([int(qid), str(unit_id), str(entry_id), sorted(pair), reason_fingerprint])
        # A proof-derived snapshot is a distinct immutable sibling of the original
        # ledger. Never mutate that ledger or fall back to selector text once present.
        snapshot_path = Path(str(path) + ".lineage-snapshot.json")
        if snapshot_path.exists():
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            digest_payload = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
            digest = hashlib.sha256(json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if (snapshot.get("version") != "normal-poller-lineage-v1" or snapshot.get("immutable") is not True
                    or snapshot.get("snapshot_sha256") != digest
                    or snapshot.get("original_ledger_sha256") != hashlib.sha256(Path(path).read_bytes()).hexdigest()
                    or set(snapshot.get("root_question_ids", [])) != set(map(str, question_ids))
                    or set(snapshot.get("question_fragment_pairs", {})) != set(map(str, question_ids))
                    or set(snapshot.get("question_fingerprints", {})) != set(map(str, question_ids))):
                raise ExecutionScopeError("immutable lineage snapshot does not match original cohort ledger")
            pairs_by_qid = snapshot["question_fragment_pairs"]
            if any(not isinstance(pair, list) or len(pair) != 2 or len(set(pair)) != 2 for pair in pairs_by_qid.values()):
                raise ExecutionScopeError("immutable lineage snapshot contains an invalid root pair")
            question_pairs = [(qid, frozenset(map(str, pairs_by_qid[qid]))) for qid in map(str, question_ids)]
            question_fingerprints = list(snapshot["question_fingerprints"].items())
            fragments = {fid for _qid, pair in question_pairs for fid in pair}
            root_payload = [[int(qid), unit, entry, sorted(pair), fp]
                            for qid, unit, entry, _old_pair, fp in root_payload
                            for pair in [pairs_by_qid[str(qid)]]]
        if fragments:
            with store_pg.connect(context.dsn) as conn, conn.cursor() as cur:
                conn.autocommit = False
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute("select distinct subject_id::text from knowledge.fragment where host_id=%s and id=any(%s::uuid[]) and subject_id is not null",
                            (namespace, list(fragments)))
                subjects.update(row[0] for row in cur.fetchall())
        computed = hashlib.sha256(json.dumps(root_payload, separators=(",", ":"), sort_keys=True).encode()).hexdigest()
        dataset_fingerprint = hashlib.sha256(json.dumps(context.endpoint, separators=(",", ":")).encode()).hexdigest()
        return cls(namespace, dataset_fingerprint, frozenset(map(str, question_ids)), frozenset(fragments),
                   frozenset(), frozenset(), frozenset(subjects), computed, source_manifest_fingerprint,
                   question_fragment_pairs=tuple(question_pairs),
                   question_fingerprints=tuple(question_fingerprints))
