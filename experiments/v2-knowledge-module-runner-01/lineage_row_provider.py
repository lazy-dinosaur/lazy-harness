"""Scoped PostgreSQL row projection for immutable 315-root lineage materialization.

No model, poller, writer, or general namespace scan is imported. One bound connection
runs one read-only transaction; selectors come only from the approved root ledger.
"""
from __future__ import annotations

import hashlib
import json

import store_pg


class RowProviderError(ValueError):
    pass


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _refs_digest(source):
    refs = (source or {}).get("evidence_refs", [])
    return hashlib.sha256(json.dumps(refs, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def _claim_digest(text):
    return _digest(text)


def _is_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _refs_list_digest(refs):
    return hashlib.sha256(json.dumps(refs or [], sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def _legacy_replacement_refs_proof(evidence, source_fp):
    """Return a versioned derived POST-refs proof for legacy PRE-digest receipts.

    The legacy writer persisted the proposal/old reference digest in
    source_correction_receipt.source_refs_digest.  This helper does not trust the
    current row or membership alone: it accepts only an existing verifier payload
    whose replacement refs, source recovery fingerprint, frozen-import source
    contexts and typed supported judgement all agree with the receipt source.
    """
    if not isinstance(evidence, dict) or not _is_sha(source_fp):
        return None
    recovery = evidence.get("source_recovery") or {}
    refs = recovery.get("replacement_refs")
    if not isinstance(refs, list) or not refs:
        return None
    if recovery.get("replacement_fingerprint") != source_fp:
        return None
    judgement = evidence.get("semantic_judgement") or {}
    probability = (judgement.get("probabilities") or {}).get(judgement.get("choice"))
    if probability is None:
        probability = judgement.get("choice_probability")
    if (judgement.get("choice") != "supported" or isinstance(probability, bool)
            or not isinstance(probability, (int, float)) or probability < 0.9):
        return None
    contexts = evidence.get("source_contexts") or []
    if not isinstance(contexts, list) or not contexts:
        return None
    manifests = {c.get("manifest_sha256") for c in contexts if c.get("origin") == "frozen-import"}
    if len(manifests) != 1 or not _is_sha(next(iter(manifests))):
        return None
    context_keys = {(c.get("locator"), c.get("quote"), c.get("type")) for c in contexts}
    ref_keys = {(r.get("locator"), r.get("quote"), r.get("type")) for r in refs if isinstance(r, dict)}
    if len(ref_keys) != len(refs) or not ref_keys.issubset(context_keys):
        return None
    digest = _refs_list_digest(refs)
    return {"version": "legacy-source-correction-post-refs-v1",
            "source_refs_fingerprint": digest,
            "replacement_refs_fingerprint": digest,
            "source_fingerprint": source_fp,
            "manifest_sha256": next(iter(manifests)),
            "typed_verification": {"choice": judgement.get("choice"), "probability": probability}}


def _question_fingerprint(reason):
    # Match ExecutionScope.from_pilot_ledger's existing root-reason fingerprint exactly.
    raw = reason if isinstance(reason, str) else json.dumps(reason, sort_keys=True)
    return _digest(raw)


def _selector_sides(case, reason):
    """Read exact selector fields used by the confirmation reason; never invent them."""
    body = _json(reason)
    if not isinstance(body, dict):
        raise RowProviderError("question reason is not a structured selector")
    kind = case.get("kind")
    if kind == "canon_contradiction":
        candidates = ((body.get("id"), body.get("text")), (body.get("with_id"), body.get("with_text")))
        aliases = ((body.get("alias"), body.get("text")), (body.get("with"), body.get("with_text")))
    elif kind == "canon_exception":
        candidates = ((body.get("id"), body.get("text")), (body.get("with_id"), body.get("with_text")))
        aliases = ((body.get("alias"), body.get("text")), (body.get("with"), body.get("with_text")))
    elif kind == "alias_conflict":
        # Normal alias resolution is subject-rooted: declared alias source fragment,
        # falling back to the subject's latest active fragment; other subject likewise.
        subjects = ((body.get("subject_id"), body.get("alias")), (body.get("other_id"), None))
        if all(subject and (alias is None or isinstance(alias, str)) for subject, alias in subjects):
            return [{"fragment_id": None, "alias": alias, "declared_root_alias": alias,
                     "claim": None, "subject_id": str(subject), "resolve_alias_root": True}
                    for subject, alias in subjects]
        candidates = ((body.get("fragment_id"), body.get("text")), (body.get("other_fragment_id"), body.get("other_text")))
        aliases = ((body.get("alias"), body.get("text")), (body.get("other_alias"), body.get("other_text")))
    else:
        raise RowProviderError("baseline case kind is unsupported")
    selectors = []
    for (fid, claim), (alias, alias_claim) in zip(candidates, aliases):
        selector = {"fragment_id": str(fid) if fid else None,
                    "alias": alias if isinstance(alias, str) else None,
                    "claim": claim if isinstance(claim, str) else alias_claim if isinstance(alias_claim, str) else None}
        if not selector["fragment_id"] and not selector.get("resolve_alias_root") and (not selector["alias"] or selector["claim"] is None):
            raise RowProviderError("question lacks an exact fragment identity or alias-and-claim selector")
        selectors.append(selector)
    return selectors


class PostgresLineageRowProvider:
    """Materializer adapter. ``connect`` is injectable for fake row-mapping integration tests."""
    def __init__(self, dsn, ledger, *, namespace, connect=None,
                 ledger_path=None, approved_ledger_sha256=None):
        self.dsn = dsn
        self.ledger = ledger
        self.namespace = namespace
        self.ledger_path = ledger_path
        self.approved_ledger_sha256 = approved_ledger_sha256
        self._connect = connect or store_pg.connect
        self._rows = None
        self.metadata_repair_rows = []
        self.current_pair_probe = None
        self.metrics = {"root_rows": 0, "selector_sides": 0, "history_rows": 0,
                        "cas_receipts": 0, "direct_dependencies": 0, "cas_descendants": 0,
                        "blocked": 0, "statements": 0}

    def load(self, proof):
        cases = self.ledger.get("cases") if isinstance(self.ledger, dict) else None
        if not isinstance(cases, list) or len(cases) != 315:
            raise RowProviderError("approved original 315-root ledger required")
        if self.ledger_path is not None:
            from pathlib import Path
            if (not isinstance(self.approved_ledger_sha256, str) or len(self.approved_ledger_sha256) != 64
                    or hashlib.sha256(Path(self.ledger_path).read_bytes()).hexdigest() != self.approved_ledger_sha256):
                raise RowProviderError("original baseline ledger fingerprint mismatch")
            if json.loads(Path(self.ledger_path).read_text(encoding="utf-8")) != self.ledger:
                raise RowProviderError("loaded ledger differs from approved immutable input")
        if proof.get("read_only") is not True or proof.get("database", {}).get("original_baseline_roots") != 315:
            raise RowProviderError("read-only proof is not bound to the 315-root baseline")
        qids = [int(case["question_id"]) for case in cases]
        if len(set(qids)) != 315:
            raise RowProviderError("root ledger has duplicate question IDs")
        roots = {}
        # The provider opens exactly one connection and keeps all reads in one transaction.
        with self._connect(self.dsn) as conn, conn.cursor() as cur:
            conn.autocommit = False
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("select current_database(),current_user")
            self.metrics["statements"] += 1
            if cur.fetchone() != ("postgres", "supabase_admin"):
                raise RowProviderError("database identity does not match the approved retained target")
            cur.execute("select host_id from knowledge.host where host_id=%s", (self.namespace,))
            self.metrics["statements"] += 1
            if cur.fetchone() != (self.namespace,):
                raise RowProviderError("exact namespace row missing")
            cur.execute("""select q.confirmation_id,e.host_id,q.status::text,q.reason,e.entry_id::text,
                                  e.work_unit_id::text
                           from knowledge.confirmation_queue q
                           join knowledge.ledger_entry e on e.entry_id=q.entry_id
                           where q.confirmation_id=any(%s::bigint[]) and e.host_id=%s
                           order by q.confirmation_id""", (qids, self.namespace))
            self.metrics["statements"] += 1
            queue = {int(r[0]): r for r in cur.fetchall()}
            if set(queue) != set(qids) or any(row[1] != self.namespace for row in queue.values()):
                raise RowProviderError("root question rows are missing or crossed namespace")
            for case in cases:
                qid = int(case["question_id"])
                question = queue[qid]
                try:
                    selectors = _selector_sides(case, question[3])
                except RowProviderError as exc:
                    sides = [self._blocked({}, f"selector_mapping:{str(exc)}") for _ in range(2)]
                    roots[str(qid)] = {"question_id": str(qid), "root_fingerprint": _question_fingerprint(question[3]),
                        "current_question": {"question_id": str(qid), "host_id": question[1], "status": question[2],
                            "entry_id": question[4], "work_unit_id": question[5],
                            "root_fingerprint": _question_fingerprint(question[3])},
                        "sides": sides, "status": question[2], "entry_id": question[4], "work_unit_id": question[5],
                        "admission": "blocked", "blocked_reasons": [side["blocked_reason"] for side in sides]}
                    self.metrics["root_rows"] += 1
                    self.metrics["blocked"] += 1
                    continue
                sides = []
                for selector in selectors:
                    self.metrics["selector_sides"] += 1
                    if selector.get("resolve_alias_root"):
                        if selector.get("alias") is not None:
                            cur.execute("""select f.id::text,f.host_id,f.alias,f.text,f.revision,f.active,f.source
                                from knowledge.subject_alias a join knowledge.fragment f
                                  on f.id=a.source_fragment_id and f.host_id=a.host_id
                                where a.host_id=%s and a.alias=%s and a.subject_id=%s and f.active""",
                                (self.namespace, selector["alias"], selector["subject_id"]))
                            self.metrics["statements"] += 1
                            direct_rows = cur.fetchall()
                            if not direct_rows:
                                cur.execute("""select id::text,host_id,alias,text,revision,active,source
                                    from knowledge.fragment where host_id=%s and subject_id=%s and active
                                    order by revision desc,id limit 1""",
                                    (self.namespace, selector["subject_id"]))
                                self.metrics["statements"] += 1
                                direct_rows = cur.fetchall()
                        else:
                            cur.execute("""select id::text,host_id,alias,text,revision,active,source
                                from knowledge.fragment where host_id=%s and subject_id=%s and active
                                order by revision desc,id limit 1""",
                                (self.namespace, selector["subject_id"]))
                            self.metrics["statements"] += 1
                            direct_rows = cur.fetchall()
                        if len(direct_rows) != 1:
                            sides.append(self._blocked(selector, "missing_or_ambiguous_alias_root"))
                            continue
                        # The reason alias selects a subject-root binding; it is not the
                        # storage alias of the resolved fragment. Preserve it separately.
                        selector = {**selector, "fragment_id": direct_rows[0][0],
                                    "claim": direct_rows[0][3], "resolved_alias": direct_rows[0][2],
                                    "resolved_host_id": direct_rows[0][1],
                                    "resolved_subject_id": selector["subject_id"]}
                    if selector["fragment_id"]:
                        cur.execute("""select id::text,host_id,alias,text,revision,active,source,subject_id::text
                                       from knowledge.fragment where id=%s::uuid and host_id=%s""", 
                                    (selector["fragment_id"], self.namespace))
                    else:
                        cur.execute("""select id::text,host_id,alias,text,revision,active,source,subject_id::text
                                       from knowledge.fragment where host_id=%s and alias=%s and text=%s
                                       order by id""",  (self.namespace, selector["alias"], selector["claim"]))
                    self.metrics["statements"] += 1
                    direct_rows = cur.fetchall()
                    direct = [r for r in direct_rows if r[3] == selector["claim"] and
                              (selector.get("resolve_alias_root") or selector["alias"] is None or r[2] == selector["alias"]) and
                              (selector["fragment_id"] is None or r[0] == selector["fragment_id"]) and
                              r[1] == self.namespace and
                              (selector.get("subject_id") is None or r[7] == selector["subject_id"])]
                    if len(direct) > 1:
                        sides.append(self._blocked(selector, "ambiguous_current_selector"))
                        continue
                    current = direct[0] if direct else None
                    fid = selector["fragment_id"] or (direct_rows[0][0] if len(direct_rows) == 1 else None)
                    history = []
                    if current is None and fid:
                        cur.execute("""select fragment_id::text,revision,snapshot,history_id
                                       from knowledge.fragment_history
                                       where fragment_id=%s::uuid order by revision,history_id""",
                                    (fid,))
                        self.metrics["statements"] += 1
                        history = cur.fetchall()
                    elif current is None:
                        cur.execute("""select fragment_id::text,revision,snapshot,history_id
                                       from knowledge.fragment_history
                                       where snapshot->>'host_id'=%s and snapshot->>'alias'=%s
                                         and snapshot->>'text'=%s order by fragment_id,revision""",
                                    (self.namespace, selector["alias"], selector["claim"]))
                        self.metrics["statements"] += 1
                        history = cur.fetchall()
                    self.metrics["history_rows"] += len(history)
                    # Event revision/history_id are provenance, not semantic BEFORE-state
                    # identity. Collapse only identical full snapshot states while retaining
                    # every event row that recorded that state.
                    state_groups = {}
                    for event in history:
                        hfid, event_revision, snapshot, history_id = event
                        snap_state = _json(snapshot)
                        key = json.dumps({"fid": hfid, "snapshot": snap_state}, sort_keys=True,
                                         ensure_ascii=False, separators=(",", ":"), default=str)
                        state_groups.setdefault(key, {"fid": hfid, "snapshot": snap_state,
                            "provenance": []})["provenance"].append({"history_id": history_id,
                                "envelope_revision": int(event_revision)})
                    states = list(state_groups.values())
                    matched_history_count = 0
                    lineage_receipt = None
                    lineage_chain = []
                    history_provenance = []
                    if current is None:
                        candidates = []
                        chain_failures = []
                        candidate_fids = sorted({str(item["fid"]) for item in states})
                        for state in states:
                            hfid, snap_candidate = state["fid"], state["snapshot"]
                            before_candidate_revision = int(snap_candidate["revision"])
                            if fid and hfid != fid:
                                continue
                            if snap_candidate.get("text") != selector["claim"]:
                                continue
                            cur.execute("""select id::text,host_id,alias,text,revision,active,source,subject_id::text
                                           from knowledge.fragment where id=%s::uuid and host_id=%s""",
                                        (hfid, self.namespace))
                            self.metrics["statements"] += 1
                            current_candidate = cur.fetchone()
                            if current_candidate is None or not current_candidate[5]:
                                continue
                            if (snap_candidate.get("id") != hfid or snap_candidate.get("host_id") != self.namespace
                                    or snap_candidate.get("subject_id") != current_candidate[7]):
                                chain_failures.append(f"history_identity_mismatch:{hfid}:{before_candidate_revision}")
                                continue
                            edge_chain = []
                            valid_chain = True
                            previous_state = snap_candidate
                            previous_text = snap_candidate["text"]
                            for edge_old in range(before_candidate_revision, int(current_candidate[4])):
                                edge = self._correction_receipt(cur, hfid, edge_old, edge_old + 1, previous_text)
                                if edge is None:
                                    chain_failures.append(f"missing_or_unauthorized_cas_edge:{hfid}:{edge_old}->{edge_old + 1}")
                                    valid_chain = False
                                    break
                                edge_before_refs = edge.get("receipt_source_refs_digest", edge.get("source_refs_fingerprint"))
                                if edge_before_refs != _refs_digest(previous_state.get("source")):
                                    chain_failures.append(f"cas_edge_before_refs_mismatch:{hfid}:{edge_old}->{edge_old + 1}")
                                    valid_chain = False
                                    break
                                next_states = [item["snapshot"] for item in states
                                    if item["fid"] == hfid and int(item["snapshot"].get("revision", 0)) == edge_old + 1]
                                if edge_old + 1 == int(current_candidate[4]):
                                    next_text = current_candidate[3]
                                    next_refs = _refs_digest(_json(current_candidate[6]))
                                elif len(next_states) == 1:
                                    next_state = next_states[0]
                                    if (next_state.get("id") != hfid or next_state.get("host_id") != self.namespace
                                            or next_state.get("subject_id") != current_candidate[7]):
                                        chain_failures.append(f"history_identity_mismatch:{hfid}:{edge_old + 1}")
                                        valid_chain = False
                                        break
                                    next_text = next_state.get("text")
                                    next_refs = _refs_digest(next_state.get("source"))
                                else:
                                    chain_failures.append(f"missing_or_forked_intermediate_beforestate:{hfid}:{edge_old + 1}")
                                    valid_chain = False
                                    break
                                if edge["receipt_new_text"] != next_text:
                                    chain_failures.append(f"cas_edge_new_text_mismatch:{hfid}:{edge_old}->{edge_old + 1}")
                                    valid_chain = False
                                    break
                                edge["after_refs_fingerprint"] = next_refs
                                edge_chain.append(edge)
                                previous_text = next_text
                                previous_state = {"text": next_text, "source": {"evidence_refs": []}}
                                if edge_old + 1 == int(current_candidate[4]):
                                    previous_state["source"] = _json(current_candidate[6])
                                else:
                                    previous_state = next_states[0]
                            if valid_chain and edge_chain and previous_text == current_candidate[3]:
                                candidates.append((state, current_candidate, edge_chain))
                        if len(candidates) != 1:
                            reason = ("missing_selector_history" if not states else
                                chain_failures[0] if chain_failures else "ambiguous_selector_history")
                            blocked = self._blocked(selector, reason)
                            blocked["history_candidate_count"] = len(states)
                            blocked["history_candidate_fids"] = candidate_fids
                            blocked["history_candidate_revisions"] = sorted({int(item["snapshot"].get("revision", 0)) for item in states})
                            blocked["history_provenance"] = [p for state in states for p in state["provenance"]]
                            sides.append(blocked); continue
                        state, current, lineage_chain = candidates[0]
                        fid, snap = state["fid"], state["snapshot"]
                        history_provenance = state["provenance"]
                        lineage_receipt = lineage_chain[-1]
                        before_revision = int(snap["revision"])
                        matched_history_count = 1
                    else:
                        snap = None
                        before_revision = current[4]
                    current_source = _json(current[6])
                    before_claim = _claim_digest(selector["claim"])
                    current_claim = _claim_digest(current[3])
                    before_refs = _refs_digest(_json(snap["source"]) if snap and snap.get("source") else current_source)
                    after_refs = _refs_digest(current_source)
                    row = {"fragment_id": fid, "selector_fingerprint": before_claim,
                           "history_match_count": matched_history_count,
                           "history_fragment_id": fid if matched_history_count else None,
                           "before_revision": int(before_revision), "after_revision": int(current[4]),
                           "before_claim_fingerprint": before_claim, "after_claim_fingerprint": current_claim,
                           "before_refs_fingerprint": before_refs, "after_refs_fingerprint": after_refs,
                           "current_alias": current[2], "current_active": bool(current[5]),
                           "resolved_selector": ({"alias": current[2], "text": current[3],
                               "fragment_id": current[0], "namespace": current[1],
                               "subject_id": current[7]} if selector.get("resolve_alias_root") else None),
                           "original_root_selector": ({"declared_alias": selector.get("declared_root_alias"),
                               "subject_id": selector.get("subject_id"), "namespace": self.namespace,
                               "fingerprint": _digest(json.dumps({"alias": selector.get("declared_root_alias"),
                                   "subject_id": selector.get("subject_id"), "namespace": self.namespace},
                                   sort_keys=True, separators=(",", ":")))} if selector.get("resolve_alias_root") else None),
                           "source_refs_fingerprint": after_refs,
                           "classification": "direct_unchanged" if current[3] == selector["claim"] and
                               (selector.get("resolve_alias_root") or selector["alias"] is None or current[2] == selector["alias"]) else "cas_descendant"}
                    if not current[5]:
                        row.update(self._blocked_fields("current_fragment_inactive"))
                    elif row["classification"] == "direct_unchanged":
                        self.metrics["direct_dependencies"] += 1
                        row.update({"receipt_id": None, "receipt_old_claim_fingerprint": None,
                            "receipt_fragment_id": None, "receipt_before_revision": None,
                            "receipt_after_revision": None, "source_fingerprint": None,
                            "typed_verification": None, "source_authority": None})
                    else:
                        receipt = lineage_receipt or self._correction_receipt(cur, fid, before_revision, current[4], selector["claim"])
                        if receipt is None:
                            row.update(self._blocked_fields("missing_exact_cas_receipt"))
                        else:
                            row.update(receipt)
                            self.metrics["cas_descendants"] += 1
                            if receipt["source_refs_fingerprint"] != after_refs:
                                row["blocked_reason"] = "current_refs_do_not_match_receipt_proof"
                    # Explicit row-level DTO: direct unchanged roots have no history/CAS receipt;
                    # CAS descendants carry only fields read from the matching DB rows above.
                    history_snapshot = _json(snap) if snap is not None else None
                    row.update({
                        "history": {"match_count": matched_history_count,
                            "fragment_id": fid if history_snapshot is not None else None,
                            "before_revision": int(history_snapshot["revision"]) if history_snapshot else int(current[4]),
                            "before_claim_fingerprint": _claim_digest(history_snapshot["text"]) if history_snapshot else before_claim,
                            "provenance": history_provenance,
                            "canonical_before_state": ({"fragment_id": fid, "namespace": self.namespace,
                                "revision": int(history_snapshot["revision"]),
                                "claim_fingerprint": _claim_digest(history_snapshot["text"]),
                                "refs_fingerprint": _refs_digest(history_snapshot.get("source")),
                                "snapshot_fingerprint": _digest(json.dumps(history_snapshot, sort_keys=True,
                                    ensure_ascii=False, separators=(",", ":"), default=str))}
                                if history_snapshot else None)}, 
                        "current_claim": {"fragment_id": fid, "alias": current[2], "text": current[3],
                            "revision": int(current[4]), "active": bool(current[5]), "fingerprint": current_claim},
                        "current_refs": {"fragment_id": fid, "evidence_refs": current_source.get("evidence_refs", []),
                            "fingerprint": after_refs},
                        "cas_receipt": {"receipt_id": row.get("receipt_id"), "fragment_id": row.get("receipt_fragment_id"),
                            "before_revision": int(history_snapshot["revision"]) if lineage_chain else row.get("receipt_before_revision"),
                            "after_revision": int(current[4]),
                            "old_claim_fingerprint": _claim_digest(history_snapshot["text"]) if lineage_chain else row.get("receipt_old_claim_fingerprint"),
                            "source_fingerprint": row.get("source_fingerprint"),
                            "source_refs_fingerprint": row.get("source_refs_fingerprint"),
                            "receipt_source_refs_digest": row.get("receipt_source_refs_digest"),
                            "reference_proof": row.get("reference_proof"),
                            "chain": [{"receipt_id": edge["receipt_id"], "fragment_id": edge["receipt_fragment_id"],
                                "before_revision": edge["receipt_before_revision"], "after_revision": edge["receipt_after_revision"],
                                "old_claim_fingerprint": edge["receipt_old_claim_fingerprint"],
                                "new_claim_fingerprint": _claim_digest(edge["receipt_new_text"]),
                                "source_fingerprint": edge["source_fingerprint"],
                                "source_refs_fingerprint": edge["source_refs_fingerprint"],
                                "receipt_source_refs_digest": edge.get("receipt_source_refs_digest"),
                                "reference_proof": edge.get("reference_proof"),
                                "after_refs_fingerprint": edge["after_refs_fingerprint"],
                                "typed_verification": edge["typed_verification"],
                                "source_authority": edge["source_authority"]} for edge in lineage_chain]}})
                    sides.append(row)
                blocked_reasons = [side["blocked_reason"] for side in sides if side.get("blocked_reason")]
                roots[str(qid)] = {"question_id": str(qid), "root_fingerprint": _question_fingerprint(question[3]),
                    "current_question": {"question_id": str(qid), "host_id": question[1], "status": question[2],
                        "entry_id": question[4], "work_unit_id": question[5],
                        "root_fingerprint": _question_fingerprint(question[3])},
                    "sides": sides, "status": question[2], "entry_id": question[4], "work_unit_id": question[5],
                    "admission": "blocked" if blocked_reasons else "lineage_projected",
                    "blocked_reasons": blocked_reasons}
                self.metrics["root_rows"] += 1
                if blocked_reasons: self.metrics["blocked"] += 1
            # Roll back explicitly; no commit path exists.
            conn.rollback()
        self._rows = roots
        return self

    @staticmethod
    def _blocked_fields(reason):
        return {"receipt_id": None, "receipt_old_claim_fingerprint": None, "receipt_fragment_id": None,
                "receipt_before_revision": None, "receipt_after_revision": None, "source_fingerprint": None,
                "typed_verification": None, "source_authority": None, "blocked_reason": reason}

    def _blocked(self, selector, reason):
        return {"fragment_id": selector.get("fragment_id"), "selector_fingerprint": _claim_digest(selector.get("claim") or ""),
                "history_match_count": 0, "history_fragment_id": None, "before_revision": None,
                "after_revision": None, "before_claim_fingerprint": _claim_digest(selector.get("claim") or ""),
                "after_claim_fingerprint": None, "before_refs_fingerprint": None, "after_refs_fingerprint": None,
                **self._blocked_fields(reason)}

    def _correction_receipt(self, cur, fid, old_revision, new_revision, old_text):
        cur.execute("""select correction_id::text,old_revision,new_revision,old_text,new_text,
                              source_fingerprint,source_refs_digest,origin,evidence
                       from knowledge.source_correction_receipt
                       where host_id=%s and fragment_id=%s::uuid and old_revision=%s and new_revision=%s
                         and old_text=%s order by created_at,correction_id""",
                     (self.namespace, fid, old_revision, new_revision, old_text))
        self.metrics["statements"] += 1
        rows = cur.fetchall()
        self.metrics["cas_receipts"] += len(rows)
        if len(rows) != 1:
            return None
        rid, oldrev, newrev, oldtext, _newtext, source_fp, refs_fp, origin, evidence = rows[0]
        evidence = _json(evidence)
        verification = evidence.get("verification_context") or {}
        judgement = evidence.get("semantic_judgement") or {}
        probability = (judgement.get("probabilities") or {}).get(judgement.get("choice"))
        if probability is None:
            probability = judgement.get("choice_probability")
        contexts = evidence.get("source_contexts") or []
        manifests = {c.get("manifest_sha256") for c in contexts if c.get("origin") == "frozen-import"}
        manifest = next(iter(manifests)) if len(manifests) == 1 else None
        if (int(oldrev) != int(old_revision) or int(newrev) != int(new_revision) or oldtext != old_text
                or len(manifests) != 1 or not _is_sha(manifest) or origin != "frozen-import"
                or judgement.get("choice") != "supported" or isinstance(probability, bool)
                or not isinstance(probability, (int, float)) or probability < 0.9
                or not _is_sha(source_fp) or not _is_sha(refs_fp)):
            return None
        reference_proof = _legacy_replacement_refs_proof(evidence, source_fp)
        semantic_refs_fp = reference_proof["source_refs_fingerprint"] if reference_proof else refs_fp
        proof_payload = reference_proof or {"version": "source-correction-receipt-post-refs-v1",
            "source_refs_fingerprint": refs_fp, "source_fingerprint": source_fp,
            "manifest_sha256": next(iter(manifests)),
            "typed_verification": {"choice": judgement.get("choice"), "probability": probability}}
        return {"receipt_id": rid, "receipt_old_claim_fingerprint": _claim_digest(oldtext),
                "receipt_new_text": _newtext,
                "receipt_fragment_id": fid, "receipt_before_revision": int(oldrev),
                "receipt_after_revision": int(newrev), "source_fingerprint": source_fp,
                "source_refs_fingerprint": semantic_refs_fp, "receipt_source_refs_digest": refs_fp,
                "reference_proof": proof_payload,
                "typed_verification": {"choice": judgement.get("choice"),
                    "probability": probability}, "source_authority": {"origin": origin,
                    "manifest_sha256": next(iter(manifests)), "source_fingerprint": source_fp}}

    def materialize(self, ledger_path, proof_path, output_path):
        """Public provider→existing materializer→immutable snapshot path; caller supplies a loaded proof."""
        from lineage_scope import materialize_snapshot
        return materialize_snapshot(ledger_path, proof_path, output_path, self)

    def resolve_root(self, case, _proof):
        if self._rows is None:
            raise RowProviderError("provider.load(proof) must complete before materialization")
        qid = str(case.get("question_id"))
        row = self._rows.get(qid)
        if row is None:
            raise RowProviderError("root is absent from complete provider projection")
        return row
