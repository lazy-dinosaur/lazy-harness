"""Fail-closed CAS-lineage materialization for immutable normal-poller scopes.

Providers are read-only projections; they must return row-level history and receipt
fields. Human-readable summary booleans in audit artifacts are never authority.
"""
import hashlib
import json
from pathlib import Path


class LineageProofError(ValueError):
    pass


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def materialize_snapshot(ledger_path, proof_path, output_path, provider):
    ledger = json.loads(Path(ledger_path).read_text(encoding="utf-8"))
    proof = json.loads(Path(proof_path).read_text(encoding="utf-8"))
    cases = ledger.get("cases") if isinstance(ledger, dict) else None
    if not isinstance(cases, list) or len(cases) != 315:
        raise LineageProofError("original 315-root baseline missing")
    baseline = hashlib.sha256(json.dumps(cases, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if proof.get("read_only") is not True or proof.get("database", {}).get("original_baseline_roots") != 315:
        raise LineageProofError("lineage proof is not bound to the 315-root read-only baseline")
    bindings = {}
    root_fingerprints = {}
    for case in cases:
        qid = str(case.get("question_id"))
        candidate = provider.resolve_root(case, proof)
        if not isinstance(candidate, dict) or candidate.get("question_id") != qid:
            raise LineageProofError("provider did not bind an exact root")
        root_fingerprint = candidate.get("root_fingerprint")
        question = candidate.get("current_question")
        if (not _sha(root_fingerprint) or not isinstance(question, dict)
                or question.get("question_id") != qid or question.get("root_fingerprint") != root_fingerprint
                or not isinstance(question.get("host_id"), str) or not question.get("host_id")
                or (proof.get("namespace") is not None and question.get("host_id") != proof.get("namespace"))):
            raise LineageProofError("provider projection lacks exact current-question identity/fingerprint")
        root_fingerprints[qid] = root_fingerprint
        if candidate.get("admission") == "blocked":
            reasons = candidate.get("blocked_reasons")
            raise LineageProofError(f"root {qid} is explicitly blocked: {reasons!r}")
        sides = candidate.get("sides")
        if not isinstance(sides, list) or len(sides) != 2:
            raise LineageProofError("root pair proof incomplete")
        ids = []
        for side in sides:
            if side.get("blocked_reason"):
                raise LineageProofError(f"root {qid} dependency {side.get('fragment_id')} is explicitly blocked: {side['blocked_reason']}")
            required = ("classification", "fragment_id", "selector_fingerprint", "history",
                        "current_claim", "current_refs", "cas_receipt", "typed_verification", "source_authority")
            missing = [f"sides[].{key}" for key in required if key not in side]
            if missing:
                raise LineageProofError("lineage provider projection missing required row-level fields: " + ", ".join(missing))
            history, claim, refs = side["history"], side["current_claim"], side["current_refs"]
            receipt, typed, authority = side["cas_receipt"], side["typed_verification"], side["source_authority"]
            if not all(isinstance(v, dict) for v in (history, claim, refs, receipt)):
                raise LineageProofError("lineage proof DTO must contain structured history/current/CAS objects")
            common = (side["selector_fingerprint"] == claim.get("fingerprint")
                      and claim.get("fragment_id") == side["fragment_id"] and claim.get("active") is True
                      and refs.get("fragment_id") == side["fragment_id"]
                      and refs.get("fingerprint") == side.get("after_refs_fingerprint")
                      and side.get("after_claim_fingerprint") == claim.get("fingerprint")
                      and side.get("after_revision") == claim.get("revision")
                      and side.get("after_refs_fingerprint") == side.get("before_refs_fingerprint") if side.get("classification") == "direct_unchanged" else True)
            failure_reason = "lineage_predicate_mismatch"
            if side["classification"] == "direct_unchanged":
                root_selector = side.get("original_root_selector")
                resolved_selector = side.get("resolved_selector")
                if root_selector is not None:
                    valid = (isinstance(root_selector, dict) and isinstance(resolved_selector, dict)
                        and root_selector.get("namespace") == question.get("host_id")
                        and root_selector.get("subject_id") == resolved_selector.get("subject_id")
                        and resolved_selector.get("namespace") == question.get("host_id")
                        and resolved_selector.get("fragment_id") == side.get("fragment_id")
                        and _sha(root_selector.get("fingerprint")))
                else:
                    valid = True
                valid = (valid and common and history.get("match_count") == 0 and history.get("fragment_id") is None
                         and history.get("before_revision") == claim.get("revision")
                         and history.get("before_claim_fingerprint") == claim.get("fingerprint")
                         and receipt.get("receipt_id") is None and typed is None and authority is None
                         and side.get("before_revision") == side.get("after_revision")
                         and side.get("before_claim_fingerprint") == side.get("after_claim_fingerprint")
                         and side.get("before_refs_fingerprint") == side.get("after_refs_fingerprint"))
                if not valid and root_selector is not None:
                    failure_reason = "resolved_selector_namespace_subject_or_current_identity_mismatch"
            elif side["classification"] == "cas_descendant":
                chain = receipt.get("chain")
                if not isinstance(chain, list) or not chain:
                    chain = [{"receipt_id": receipt.get("receipt_id"), "fragment_id": receipt.get("fragment_id"),
                        "before_revision": receipt.get("before_revision"), "after_revision": receipt.get("after_revision"),
                        "old_claim_fingerprint": receipt.get("old_claim_fingerprint"),
                        "new_claim_fingerprint": side.get("after_claim_fingerprint"),
                        "source_fingerprint": receipt.get("source_fingerprint"),
                        "source_refs_fingerprint": receipt.get("source_refs_fingerprint"),
                        "receipt_source_refs_digest": receipt.get("receipt_source_refs_digest"),
                        "reference_proof": receipt.get("reference_proof"),
                        "after_refs_fingerprint": refs.get("fingerprint"),
                        "typed_verification": typed, "source_authority": authority}]
                expected_revision = side.get("before_revision")
                expected_claim = side.get("before_claim_fingerprint")
                expected_refs = side.get("before_refs_fingerprint")
                chain_valid = True
                for edge in chain:
                    edge_typed, edge_auth = edge.get("typed_verification"), edge.get("source_authority")
                    edge_before_refs = edge.get("receipt_source_refs_digest") or edge.get("source_refs_fingerprint")
                    reference_proof = edge.get("reference_proof")
                    if (edge.get("fragment_id") != side["fragment_id"]
                        or edge.get("before_revision") != expected_revision
                        or edge.get("after_revision") != expected_revision + 1
                        or edge.get("old_claim_fingerprint") != expected_claim
                        or edge_before_refs != expected_refs
                        or not edge.get("receipt_id")
                        or not isinstance(edge_typed, dict) or edge_typed.get("choice") != "supported"
                        or isinstance(edge_typed.get("probability"), bool)
                        or not isinstance(edge_typed.get("probability"), (int, float)) or edge_typed["probability"] < .9
                        or not isinstance(edge_auth, dict) or edge_auth.get("origin") != "frozen-import"
                        or not _sha(edge_auth.get("manifest_sha256"))
                        or edge_auth.get("source_fingerprint") != edge.get("source_fingerprint")
                        or not _sha(edge.get("source_fingerprint")) or not _sha(edge.get("source_refs_fingerprint"))
                        or (reference_proof is not None and (not isinstance(reference_proof, dict)
                            or reference_proof.get("source_refs_fingerprint") != edge.get("source_refs_fingerprint")
                            or reference_proof.get("source_fingerprint") != edge.get("source_fingerprint")
                            or reference_proof.get("manifest_sha256") != edge_auth.get("manifest_sha256")))):
                        chain_valid = False
                        failure_reason = f"cas_chain_edge_invalid:{edge.get('before_revision')}->{edge.get('after_revision')}"
                        break
                    expected_revision = edge["after_revision"]
                    expected_claim = edge["new_claim_fingerprint"]
                    expected_refs = edge.get("after_refs_fingerprint")
                    if not _sha(expected_refs):
                        chain_valid = False
                        failure_reason = f"cas_chain_intermediate_refs_missing:{edge.get('after_revision')}"
                        break
                valid = (claim.get("fingerprint") == side.get("after_claim_fingerprint")
                         and claim.get("revision") == side.get("after_revision") and claim.get("active") is True
                         and refs.get("fingerprint") == side.get("after_refs_fingerprint")
                         and history.get("match_count") == 1 and history.get("fragment_id") == side["fragment_id"]
                         and history.get("before_revision") == side.get("before_revision")
                         and history.get("before_claim_fingerprint") == side.get("selector_fingerprint")
                         and chain_valid and expected_revision == side.get("after_revision")
                         and expected_claim == side.get("after_claim_fingerprint")
                         and chain[-1].get("source_refs_fingerprint") == refs.get("fingerprint")
                         and expected_refs == side.get("after_refs_fingerprint")
                         and refs.get("fingerprint") == side.get("after_refs_fingerprint")
                         and all(_sha(side.get(k)) for k in ("selector_fingerprint", "before_claim_fingerprint", "after_claim_fingerprint", "before_refs_fingerprint", "after_refs_fingerprint")))
            else:
                valid = False
            if not valid:
                if side["classification"] == "cas_descendant" and chain_valid:
                    if expected_revision != side.get("after_revision"):
                        failure_reason = "cas_chain_does_not_reach_current_revision"
                    elif expected_claim != side.get("after_claim_fingerprint"):
                        failure_reason = "cas_chain_terminal_claim_mismatch"
                    elif chain[-1].get("source_refs_fingerprint") != refs.get("fingerprint"):
                        failure_reason = "current_refs_do_not_match_terminal_semantic_receipt"
                    elif expected_refs != side.get("after_refs_fingerprint"):
                        failure_reason = "cas_chain_terminal_reference_state_mismatch"
                raise LineageProofError(f"root {qid} dependency {side.get('fragment_id')}: {failure_reason}")
            ids.append(str(side["fragment_id"]))
        if len(set(ids)) != 2:
            raise LineageProofError("root pair dependencies are not unique")
        bindings[qid] = {"fragment_ids": sorted(ids), "sides": sides}
    snapshot = {"version": "normal-poller-lineage-v1", "immutable": True,
                "baseline_fingerprint": baseline, "original_ledger_sha256": hashlib.sha256(Path(ledger_path).read_bytes()).hexdigest(),
                "proof_sha256": hashlib.sha256(Path(proof_path).read_bytes()).hexdigest(),
                "root_question_ids": sorted(bindings),
                "question_fragment_pairs": {qid: value["fragment_ids"] for qid, value in bindings.items()},
                "question_fingerprints": root_fingerprints, "bindings": bindings}
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    snapshot["snapshot_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        if existing != snapshot:
            raise LineageProofError("immutable lineage snapshot path already contains different bytes")
    else:
        target.write_text(json.dumps(snapshot, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return snapshot
