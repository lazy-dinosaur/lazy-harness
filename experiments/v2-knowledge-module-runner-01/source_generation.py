"""Bounded source-grounded correction generation followed by separate typed verification.

The generator never writes. It uses the existing isolated Pi/Luna adapter from brief.py; Jev is
only the independent verifier, and the protected store writer remains the sole mutation path.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import source_correction
import source_evidence

MAX_CONTEXT_CHARS = source_evidence.MAX_ORIGINAL_CONTEXT_CHARS
MAX_OUTPUT_CHARS = 8_000
_REQUIRED = {"quotes", "target", "operation", "condition", "time", "corrected_text", "action", "why"}

METADATA_PROMPT = """Create a citation-only recovery proposal using ONLY the private input packet in {FILE}.
The current canonical claim is not to be rewritten. Return exactly one JSON object with keys `quotes` (one exact verbatim source substring per existing citation) and `why`. Select only quotes that directly support the entire unchanged claim; use the surrounding source context, including historical/current qualifiers and conditions. Do not choose headings/breadcrumbs, infer unsupported facts, or return replacement claim text. If support is unclear, return an empty quotes array and explain why. No markdown or extra keys.
"""

PROMPT = """Create one conservative correction proposal using ONLY the private input packet in {FILE}.
The packet contains the current canonical claim, fragment identity/revision, source proof fingerprint, and
freshly verified source contexts. Return exactly one JSON object with keys quotes (array of exact verbatim source substrings), target,
operation, condition, time, corrected_text, action, why. No markdown or extra keys. `action` must be
`replace_claim` only if source proves the current claim wrong and supports the complete replacement;
otherwise use `no_change`. Preserve entity identity, qualifiers, conditions, dates, and scope. Do not
invent facts, merge entities, repair citations, or request human approval. If support is insufficient,
return no_change with empty corrected_text and explain why. `quotes` must be exact substrings of the source.
"""


def _default_generate(prompt, cwd):
    # This is the already-configured read-only Luna/Pi agent adapter, not a new provider choice.
    import brief
    return brief.pi_runner(prompt, cwd)


def _reply_text_usage(reply):
    if isinstance(reply, tuple):
        text = reply[0] if reply and isinstance(reply[0], str) else None
        meta = reply[1] if len(reply) > 1 and isinstance(reply[1], dict) else {"usageKnown": False, "usage": "unknown"}
        return text, meta
    if isinstance(reply, dict):
        text = reply.get("text") if isinstance(reply.get("text"), str) else None
        usage = reply.get("usage") if isinstance(reply.get("usage"), dict) else None
        return text, {"usageKnown": bool(usage), "usage": usage or "unknown"}
    return (reply if isinstance(reply, str) else None), {"usageKnown": False, "usage": "unknown"}


def generate_metadata_references(fragment, provider, judge, *, generator=None):
    """Propose exact replacement citations for an unchanged claim and separately verify its support."""
    if (not isinstance(fragment, dict) or not isinstance(fragment.get("id"), str)
            or not isinstance(fragment.get("revision"), int) or fragment["revision"] < 1
            or not isinstance(fragment.get("text"), str) or not fragment["text"].strip()):
        return {"status": "evidence_needed", "reason": "invalid_fragment_identity"}
    try:
        original = provider.recover_original_context(fragment)
    except (source_evidence.SourceEvidenceError, OSError) as exc:
        reason = exc.code if isinstance(exc, source_evidence.SourceEvidenceError) else "source_io_error"
        return {"status": "evidence_needed", "reason": reason}
    contexts = original["evidence"]
    corpus = "\n\n".join(str(item.get("context", "")) for item in contexts)
    old_refs = (fragment.get("source") or {}).get("evidence_refs", [])
    if not corpus or len(corpus) > MAX_CONTEXT_CHARS or not old_refs or len(old_refs) > 12:
        return {"status": "evidence_needed", "reason": "source_context_limit_or_missing_refs"}
    directory = Path(tempfile.mkdtemp(prefix="lh-source-metadata-"))
    try:
        os.chmod(directory, 0o700)
        packet_file = directory / "metadata-input.json"
        packet_file.write_text(json.dumps({"fragment": {"id": fragment["id"], "revision": fragment["revision"],
            "current_claim": fragment["text"], "existing_references": len(old_refs)},
            "source_contexts": contexts}, ensure_ascii=False), encoding="utf-8")
        os.chmod(packet_file, 0o600)
        response, generation_usage = _reply_text_usage((generator or _default_generate)(METADATA_PROMPT.format(FILE=str(packet_file)), str(directory)))
    except Exception as exc:  # provider/agent failures remain internal retry evidence
        return {"status": "evidence_needed", "reason": "metadata_proposal_failed", "failure": type(exc).__name__}
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    if not isinstance(response, str) or len(response) > MAX_OUTPUT_CHARS:
        return {"status": "evidence_needed", "reason": "invalid_metadata_proposal"}
    try:
        proposal = json.loads(response)
    except (TypeError, json.JSONDecodeError):
        return {"status": "evidence_needed", "reason": "metadata_proposal_not_json"}
    quotes = proposal.get("quotes") if isinstance(proposal, dict) and set(proposal) == {"quotes", "why"} else None
    if (not isinstance(quotes, list) or len(quotes) != len(old_refs)
            or not all(isinstance(q, str) and q.strip() and q in corpus for q in quotes)
            or not isinstance(proposal.get("why"), str) or not proposal["why"].strip()):
        return {"status": "evidence_needed", "reason": "metadata_proposal_unbound_or_incomplete"}
    try:
        candidates = source_evidence.literal_quote_references(contexts, quotes)
        new_refs = []
        for quote in quotes:
            matches = [ref for ref in candidates if ref["quote"] == quote]
            if len(matches) != 1:
                return {"status": "evidence_needed", "reason": "ambiguous_metadata_quote"}
            new_refs.append({key: value for key, value in matches[0].items() if not key.startswith("_")})
        review_fragment = {**fragment, "source": {**(fragment.get("source") or {}), "evidence_refs": new_refs}}
        verified = source_correction.verify_current_claim(review_fragment, provider, judge)
        original_after = provider.recover_original_context(fragment)
        if original_after["fingerprint"] != original["fingerprint"]:
            return {"status": "evidence_needed", "reason": "source_changed_during_generation"}
    except (source_evidence.SourceEvidenceError, OSError) as exc:
        reason = exc.code if isinstance(exc, source_evidence.SourceEvidenceError) else "source_io_error"
        return {"status": "evidence_needed", "reason": reason}
    if verified.get("status") != "supported":
        return verified
    return {"status": "supported", "fragment_id": fragment["id"], "revision": fragment["revision"],
        "source_recovery_fingerprint": original["fingerprint"], "new_refs": new_refs,
        "metadata_reason": proposal["why"][:500], "semantic_verification": verified,
        "generation_usage": generation_usage}


def generate_and_verify(fragment, provider, judge, *, generator=None):
    """Generate a strict typed proposal from verified source and separately Jev-verify it.

    Returns a source_correction proposal only on successful typed support. All model calls and source
    reads happen before the protected CAS writer opens a DB transaction.
    """
    if (not isinstance(fragment, dict) or not isinstance(fragment.get("id"), str)
            or not isinstance(fragment.get("revision"), int) or isinstance(fragment.get("revision"), bool)
            or fragment["revision"] < 1 or not isinstance(fragment.get("text"), str)
            or not fragment["text"].strip()):
        return {"status": "evidence_needed", "reason": "invalid_fragment_identity"}
    recovered = False
    try:
        before = provider.read_fragment(fragment)
    except (source_evidence.SourceEvidenceError, OSError):
        try:
            before = provider.recover_original_context(fragment)
            recovered = True
        except (source_evidence.SourceEvidenceError, OSError) as exc:
            reason = exc.code if isinstance(exc, source_evidence.SourceEvidenceError) else "source_io_error"
            return {"status": "evidence_needed", "reason": reason}
    contexts = before["evidence"]
    corpus = "\n\n".join(str(item.get("context", "")) for item in contexts)
    if not corpus or len(corpus) > MAX_CONTEXT_CHARS:
        return {"status": "evidence_needed", "reason": "source_context_limit"}
    directory = Path(tempfile.mkdtemp(prefix="lh-source-proposal-"))
    try:
        os.chmod(directory, 0o700)
        source_file = directory / "verified-input.json"
        packet = {"fragment": {"id": fragment["id"], "revision": fragment["revision"], "text": fragment["text"]},
                  "proof_fingerprint": before["fingerprint"], "source_contexts": contexts}
        source_file.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
        os.chmod(source_file, 0o600)
        call = generator or _default_generate
        response, generation_usage = _reply_text_usage(call(PROMPT.format(FILE=str(source_file)), str(directory)))
    except Exception as exc:  # noqa: BLE001 - failure is internal retry evidence, not a conflict
        return {"status": "evidence_needed", "reason": "generation_failed", "failure": type(exc).__name__}
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    if not isinstance(response, str) or len(response) > MAX_OUTPUT_CHARS:
        return {"status": "evidence_needed", "reason": "invalid_generation_output"}
    try:
        proposal = json.loads(response)
    except (TypeError, json.JSONDecodeError):
        return {"status": "evidence_needed", "reason": "generation_not_json"}
    if not isinstance(proposal, dict) or set(proposal) != _REQUIRED:
        return {"status": "evidence_needed", "reason": "generation_schema_mismatch"}
    if proposal.get("action") != "replace_claim":
        return {"status": "no_change", "reason": "generator_declined", "why": str(proposal.get("why", ""))[:500],
                "source_fingerprint": before["fingerprint"]}
    quotes = proposal.get("quotes")
    scope = {key: proposal.get(key) for key in ("target", "operation", "condition", "time")}
    if (not isinstance(quotes, list) or not quotes or any(not isinstance(q, str) or not q.strip() or q not in corpus for q in quotes)
            or not all(isinstance(value, str) and value.strip() for value in scope.values())
            or not isinstance(proposal.get("corrected_text"), str)
            or not proposal["corrected_text"].strip()
            or proposal["corrected_text"].strip() == fragment["text"].strip()
            or not isinstance(proposal.get("why"), str) or not proposal["why"].strip()):
        return {"status": "evidence_needed", "reason": "unsupported_or_incomplete_generation"}
    review_fragment = fragment
    if recovered:
        try:
            candidates = source_evidence.literal_quote_references(contexts, quotes)
            # Recovery is automatic only when every generated quote maps to one exact source span.
            # Ambiguous spans stay internal for a later proposal; never select the first candidate.
            selected = []
            for quote in quotes:
                matches = [ref for ref in candidates if ref["quote"] == quote]
                if len(matches) != 1:
                    return {"status": "evidence_needed", "reason": "ambiguous_original_quote"}
                selected.append({key: value for key, value in matches[0].items() if not key.startswith("_")})
            review_fragment = {**fragment, "source": {**(fragment.get("source") or {}), "evidence_refs": selected}}
            after = provider.read_fragment(review_fragment)
        except (source_evidence.SourceEvidenceError, OSError):
            return {"status": "evidence_needed", "reason": "source_changed_during_generation"}
        try:
            original_after = provider.recover_original_context(fragment)
        except (source_evidence.SourceEvidenceError, OSError):
            return {"status": "evidence_needed", "reason": "source_changed_during_generation"}
        if original_after["fingerprint"] != before["fingerprint"]:
            return {"status": "evidence_needed", "reason": "source_changed_during_generation"}
        replacement_fingerprint = after["fingerprint"]
    else:
        try:
            after = provider.read_fragment(fragment)
        except (source_evidence.SourceEvidenceError, OSError):
            return {"status": "evidence_needed", "reason": "source_changed_during_generation"}
        if after["fingerprint"] != before["fingerprint"]:
            return {"status": "evidence_needed", "reason": "source_changed_during_generation"}
        replacement_fingerprint = before["fingerprint"]
    verification_context = {"target": scope["target"], "operation": scope["operation"],
        "condition": scope["condition"], "time": scope["time"], "source_reason": proposal["why"],
        "source_quotes": quotes}
    try:
        verified = source_correction.review_correction(review_fragment, proposal["corrected_text"], provider,
            judge, review_context=verification_context)
    except Exception as exc:  # noqa: BLE001 - verifier transport/model failures are retry evidence
        return {"status": "evidence_needed", "reason": "typed_verification_failed", "failure": type(exc).__name__}
    if verified.get("status") != "supported":
        return {"status": "evidence_needed", "reason": verified.get("reason", "typed_verification_failed"),
                "source_fingerprint": before["fingerprint"]}
    # Preserve generation provenance separately from the independent typed verifier.
    verified["evidence"]["generation"] = {"reviewer": "configured-pi-agent", "action": proposal["action"],
        "why": proposal["why"], "target": scope["target"], "operation": scope["operation"],
        "condition": scope["condition"], "time": scope["time"], "quotes": quotes,
        "proof_fingerprint": before["fingerprint"], "source_root": str(provider.host_root),
        "fragment_id": fragment["id"], "revision": fragment["revision"], "original_text": fragment["text"],
        "usage": generation_usage}
    if recovered:
        refs_digest = __import__("hashlib").sha256(json.dumps((fragment.get("source") or {}).get("evidence_refs", []),
            sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        verified["source_refs_digest"] = refs_digest
        verified["evidence"]["source_recovery"] = {"verification": "unverified-original-context",
            "original_fingerprint": before["fingerprint"], "replacement_fingerprint": replacement_fingerprint,
            "replacement_refs": review_fragment["source"]["evidence_refs"]}
    # The receipt identity covers generation evidence too; writer validates this complete proposal hash.
    import hashlib
    verified["correction_key"] = hashlib.sha256(json.dumps({k: v for k, v in verified.items() if k != "correction_key"},
        sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
    return source_correction.seal_verified_correction(verified)
