"""Source-grounded proposal for correcting an existing canonical fragment.

This is deliberately separate from pair-review receipts: a pair verdict never mutates a
fragment, and a quote-validity check never authorizes a correction. A trusted typed judge
must affirm the proposed replacement against the complete source context.
"""
from __future__ import annotations

import hashlib
import json
import math

import source_evidence

QUESTION = (
    "Assess whether the proposed corrected claim and every supplied target, operation, condition, time, source quote, "
    "and source reason are fully supported by the supplied original-source context and correctly supersede the current "
    "claim. Preserve scope and temporal status. Distinguish preview rasterization from actual vector output, "
    "per-document DOWNLOAD from combined PRINT, and current from historical behavior. Return supported only when "
    "all relevant scope is explicit; otherwise return unsupported or uncertain. Do not infer missing facts. The source "
    "reference digest and proof fingerprint bind the reviewed source context; this is source-origin evidence, not user approval."
)
CRITERIA = {
    "supported": "The source context supports the replacement claim, its temporal status, and its scope against the current claim.",
    "unsupported": "The replacement contradicts or exceeds the cited source context.",
    "uncertain": "The source does not establish the replacement, its scope, or its temporal relationship with sufficient clarity.",
}

CLAIM_SUPPORT_QUESTION = (
    "Does the freshly read authorized source context support the complete current canonical claim exactly as written, "
    "including its target, operation, conditions, time, qualifiers, and scope? Choose supported only when every material "
    "part is explicitly supported; choose unsupported when contradicted and uncertain when evidence is missing or "
    "ambiguous. Quote presence alone is not entailment. Do not rewrite the claim or decide a human question."
)

# A serialized receipt records verification but cannot mint the process-local capability required
# by the protected writer. Only review_correction issues this wrapper after an actual typed call.
_VERIFIED_MARKER = object()


class VerifiedCorrection(dict):
    def __init__(self, value):
        super().__init__(value)
        self._verified_marker = _VERIFIED_MARKER
        self._verified_payload_digest = _payload_digest(self)


def _payload_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()


def seal_verified_correction(value):
    """Re-seal only after trusted internal code adds verifier-bound provenance before protected write."""
    if not isinstance(value, VerifiedCorrection) or value._verified_marker is not _VERIFIED_MARKER:
        raise ValueError("typed-verifier capability is required")
    value._verified_payload_digest = _payload_digest(value)
    return value


def is_verified_correction(value):
    return (isinstance(value, VerifiedCorrection) and value._verified_marker is _VERIFIED_MARKER
            and value._verified_payload_digest == _payload_digest(value))


def _refs_digest(fragment):
    refs = (fragment.get("source") or {}).get("evidence_refs", [])
    return hashlib.sha256(json.dumps(refs, sort_keys=True, ensure_ascii=False,
        separators=(",", ":")).encode()).hexdigest()


def propose_agent_correction(fragment, corrected_text, provider, *, explanation, source_quotes, temporal_scope,
                             minimum_confidence=0.9):
    """Bind a source-grounded agent correction to exact source quotations and explicit scope.

    This path is intentionally not human approval: it produces a machine-auditable source proposal,
    and the protected CAS writer still decides whether the current fragment can be changed.
    """
    if (not isinstance(fragment, dict) or not isinstance(fragment.get("id"), str)
            or not isinstance(fragment.get("revision"), int) or fragment["revision"] < 1
            or not isinstance(fragment.get("text"), str) or not isinstance(corrected_text, str)
            or not corrected_text.strip() or corrected_text.strip() == fragment["text"].strip()
            or not isinstance(explanation, str) or not explanation.strip()
            or not isinstance(temporal_scope, dict)
            or set(temporal_scope) != {"target", "operation", "condition", "time"}
            or not all(isinstance(v, str) and v.strip() for v in temporal_scope.values())):
        return {"status": "evidence_needed", "reason": "invalid_agent_correction_scope"}
    try:
        before = provider.read_fragment(fragment)
    except source_evidence.SourceEvidenceError as exc:
        return {"status": "evidence_needed", "reason": type(exc).__name__}
    corpus = "\n".join(e.get("quote", "") + "\n" + e.get("context", "") for e in before["evidence"])
    if not isinstance(source_quotes, list) or not source_quotes or any(not isinstance(q, str) or q not in corpus for q in source_quotes):
        return {"status": "evidence_needed", "reason": "agent_quote_not_bound_to_source"}
    after = provider.read_fragment(fragment)
    if before["fingerprint"] != after["fingerprint"]:
        return {"status": "evidence_needed", "reason": "source_changed_during_review"}
    answer = {"reviewer": "source-grounded-agent", "choice": "supported", "probabilities": {"supported": 1.0},
              "explanation": explanation, "source_quotes": source_quotes, "temporal_scope": temporal_scope}
    proposal = {"status": "supported", "fragment_id": fragment["id"], "expected_revision": fragment["revision"],
        "expected_text": fragment["text"], "corrected_text": corrected_text.strip(),
        "source_fingerprint": before["fingerprint"], "source_refs_digest": _refs_digest(fragment),
        "origin": next(iter({e["origin"] for e in before["evidence"]}))
            if len({e["origin"] for e in before["evidence"]}) == 1 else "mixed",
        "evidence": {"source_contexts": before["evidence"], "semantic_judgement": answer}}
    proposal["correction_key"] = hashlib.sha256(json.dumps(proposal, sort_keys=True,
        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return proposal


def verify_current_claim(fragment, provider, judge, *, minimum_confidence=0.9):
    """Independently verify an unchanged current claim against freshly read replacement source refs."""
    try:
        before = provider.read_fragment(fragment)
    except source_evidence.SourceEvidenceError as exc:
        return {"status": "evidence_needed", "reason": exc.code}
    state = {"fragment": {"id": fragment.get("id"), "revision": fragment.get("revision"),
        "current_claim": fragment.get("text"), "source_fingerprint": before["fingerprint"],
        "source_contexts": before["evidence"]}}
    answers = judge(state, ["claim_support"], CLAIM_SUPPORT_QUESTION, criteria={
        "supported": "Every material part of the current claim is supported.",
        "unsupported": "The source contradicts at least one material part.",
        "uncertain": "The source does not establish the complete claim."})
    if not isinstance(answers, list) or len(answers) != 1 or not isinstance(answers[0], dict):
        raise ValueError("current-claim verifier must return one typed choice")
    answer = answers[0]
    choice = answer.get("choice")
    probability = (answer.get("probabilities") or {}).get(choice) if isinstance(answer.get("probabilities"), dict) else None
    try:
        after = provider.read_fragment(fragment)
    except source_evidence.SourceEvidenceError:
        return {"status": "evidence_needed", "reason": "source_changed_during_review"}
    if before["fingerprint"] != after["fingerprint"]:
        return {"status": "evidence_needed", "reason": "source_changed_during_review"}
    if (choice != "supported" or isinstance(probability, bool) or not isinstance(probability, (int, float))
            or not math.isfinite(probability) or probability < minimum_confidence):
        return {"status": "evidence_needed", "reason": "current_claim_not_source_verified",
                "choice": choice if choice in ("unsupported", "uncertain") else "uncertain"}
    origins = {item["origin"] for item in before["evidence"]}
    return {"status": "supported", "fragment_id": fragment["id"], "revision": fragment["revision"],
        "source_fingerprint": before["fingerprint"], "origin": next(iter(origins)) if len(origins) == 1 else "mixed",
        "judgement": answer}


def review_correction(fragment, corrected_text, provider, judge, *, review_context=None, minimum_confidence=0.9):
    """Return an apply-ready source proposal only after typed semantic support and stable reread."""
    if (not isinstance(fragment, dict) or not isinstance(fragment.get("id"), str)
            or not isinstance(fragment.get("revision"), int) or fragment["revision"] < 1
            or not isinstance(fragment.get("text"), str) or not fragment["text"].strip()
            or not isinstance(corrected_text, str) or not corrected_text.strip()
            or corrected_text.strip() == fragment["text"].strip()):
        return {"status": "evidence_needed", "reason": "invalid_correction_identity_or_text"}
    try:
        before = provider.read_fragment(fragment)
    except source_evidence.SourceEvidenceError as exc:
        return {"status": "evidence_needed", "reason": type(exc).__name__}
    if review_context is not None and (not isinstance(review_context, dict)
            or set(review_context) - {"target", "operation", "condition", "time", "source_reason", "source_quotes", "proposal_provenance"}
            or not {"target", "operation", "condition", "time", "source_reason", "source_quotes"}.issubset(review_context)
            or not all(isinstance(v, str) and v.strip() for k, v in review_context.items()
                       if k not in ("source_quotes", "proposal_provenance"))
            or ("proposal_provenance" in review_context and not isinstance(review_context["proposal_provenance"], dict))
            or not isinstance(review_context.get("source_quotes"), list)
            or not review_context["source_quotes"]
            or any(not isinstance(q, str) or not q.strip() for q in review_context["source_quotes"])):
        return {"status": "evidence_needed", "reason": "invalid_correction_review_context"}
    if review_context is not None:
        corpus = "\n".join(item.get("quote", "") + "\n" + item.get("context", "")
                           for item in before["evidence"])
        if any(quote not in corpus for quote in review_context["source_quotes"]):
            return {"status": "evidence_needed", "reason": "review_quote_not_bound_to_source"}
    state = {"fragment": {"id": fragment["id"], "revision": fragment["revision"],
                           "current_claim": fragment["text"], "proposed_claim": corrected_text,
                           "review_context": review_context, "source_fingerprint": before["fingerprint"],
                           "source_refs_digest": _refs_digest(fragment),
                           "source_contexts": before["evidence"]}}
    if len(json.dumps(state, ensure_ascii=False)) > 60000:
        return {"status": "evidence_needed", "reason": "context_limit"}
    answers = judge(state, ["correction"], QUESTION, criteria=CRITERIA)
    if not isinstance(answers, list) or len(answers) != 1 or not isinstance(answers[0], dict):
        raise ValueError("source correction judge must return one typed choice")
    answer = answers[0]
    choice = answer.get("choice")
    probabilities = answer.get("probabilities")
    confidence = probabilities.get(choice) if isinstance(probabilities, dict) else None
    if (choice != "supported" or isinstance(confidence, bool) or not isinstance(confidence, (int, float))
            or not math.isfinite(confidence) or confidence < minimum_confidence):
        return {"status": "evidence_needed", "reason": "correction_not_semantically_supported",
                "choice": choice if choice in CRITERIA else "uncertain"}
    try:
        after = provider.read_fragment(fragment)
    except source_evidence.SourceEvidenceError:
        return {"status": "evidence_needed", "reason": "source_changed_during_review"}
    if before["fingerprint"] != after["fingerprint"]:
        return {"status": "evidence_needed", "reason": "source_changed_during_review"}
    proposal = {"status": "supported", "fragment_id": fragment["id"],
        "expected_revision": fragment["revision"], "expected_text": fragment["text"],
        "corrected_text": corrected_text.strip(), "source_fingerprint": before["fingerprint"],
        "source_refs_digest": _refs_digest(fragment), "origin": next(iter({e["origin"] for e in before["evidence"]}))
            if len({e["origin"] for e in before["evidence"]}) == 1 else "mixed",
        "evidence": {"source_contexts": before["evidence"], "semantic_judgement": answer,
                     **({"verification_context": review_context} if review_context is not None else {})}}
    proposal["correction_key"] = hashlib.sha256(json.dumps(proposal, sort_keys=True,
        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return VerifiedCorrection(proposal)
