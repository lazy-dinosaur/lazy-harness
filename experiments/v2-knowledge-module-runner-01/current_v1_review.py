#!/usr/bin/env python3
"""CURRENT V1 append-only review/organization pipeline.

This module consumes the already-imported CURRENT V1 first-pass artifacts and writes a
new versioned review overlay under `.local/current-v1-review/<version>/`. It never
mutates first-pass files, the V2 DB, canonical records, or upstream source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import current_v1_import

SCHEMA_VERSION = "current-v1-review/v1"
DEFAULT_OUTPUT_ROOT = Path(".local/current-v1-review")
MAX_GROUP_INPUT_CHARS = 18000
MAX_PROPOSER_OUTPUT_CHARS = 24000
SUPPORTED_MODEL_SOURCE_KINDS = {"project-document-or-linkage-evidence", "source-policy-context"}
DEFERRED_SOURCE_KIND_PATTERNS = ("lazy-harness", "framework", "generated", "private", "excluded")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+\S")

PROMPT = """Extract conservative review candidates from ONLY the private input packet in {FILE}.
Return one JSON object with key `candidates`, an array. Each candidate must have exactly:
facet (DDD|SDD|BDD|TDD|ADR|SSOT|other), claim, relation, source_quote, confidence.
Use exact verbatim source_quote substrings from the packet span. Do not output secrets, paths outside the packet,
canonical facts, human approvals, merge decisions, or unsupported guesses. If the span is framework/history/privacy
or not a business/project fact, return an empty array. No markdown or extra keys.
"""

VERIFY_Q = ("items[{i}] is a proposed fact extracted from the supplied source span. Is the claim fully and directly "
            "supported by the exact source_quote in the same item, without adding business/canonical authority, human "
            "approval, identity merge, or unstated context? Choose supported only for exact source support; choose "
            "uncertain for ambiguity; malformed for schema/source_quote problems; unsupported for no support.")
VERIFY_C = {"supported": "directly supported by exact quote", "uncertain": "ambiguous or needs human/source context",
            "unsupported": "not supported by the quote", "malformed": "bad schema, unbound quote, or unsafe output"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_id(prefix: str, *parts: Any) -> str:
    return f"{prefix}-{hashlib.sha256(canonical_json(parts).encode()).hexdigest()[:24]}"


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


@dataclass(frozen=True)
class Guard:
    source_version: str
    source_manifest_sha256: str
    source_root: str
    ingestion_fp: str
    source_bundle: str


def _safe_inside(root: Path, child: Path) -> bool:
    try:
        child.relative_to(root)
        return True
    except ValueError:
        return False


def load_ingestion(ingestion: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    result = json.loads((ingestion / "result.json").read_text(encoding="utf-8"))
    candidates = list(read_jsonl(ingestion / "candidates.jsonl"))
    ledger = {}
    for row in read_jsonl(ingestion / "intake-ledger.jsonl"):
        fp = row.get("sourceDocFP")
        if isinstance(fp, str):
            ledger[fp] = row
    return result, candidates, ledger


def guard_first(ingestion: Path, source_bundle: Path, expected_manifest_sha256: str, expected_source_root: str,
                expected_parent_manifest_sha256: str | None = None) -> Guard:
    if not expected_manifest_sha256 or not re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256):
        raise ValueError("expected manifest sha256 is required before review")
    if not expected_source_root or not str(expected_source_root).startswith("/"):
        raise ValueError("expected absolute source root is required before review")
    result = json.loads((ingestion / "result.json").read_text(encoding="utf-8"))
    manifest = result.get("manifest") or {}
    if manifest.get("sha256") != expected_manifest_sha256:
        raise ValueError("ingestion manifest hash mismatch")
    ident = manifest.get("sourceIdentity") or {}
    if ident.get("sourceRoot") != expected_source_root:
        raise ValueError("ingestion source root mismatch")
    verify_kwargs = {"expected_manifest_sha256": expected_manifest_sha256, "expected_source_root": expected_source_root,
                     "expected_namespace": "current-v1", "expected_version": manifest.get("version")}
    if expected_parent_manifest_sha256:
        if ((manifest.get("parent") or {}).get("manifestSha256") or (ident.get("parentManifestSha256"))) != expected_parent_manifest_sha256:
            raise ValueError("ingestion parent manifest hash mismatch")
        verify_kwargs["expected_parent_manifest_sha256"] = expected_parent_manifest_sha256
    verified = current_v1_import.source_verified(source_bundle, **verify_kwargs)
    if verified.get("manifestSha256") != expected_manifest_sha256:
        raise ValueError("source bundle manifest hash mismatch")
    return Guard(str(manifest.get("version")), expected_manifest_sha256, expected_source_root,
                 sha256_text((ingestion / "result.json").read_text(encoding="utf-8")), str(source_bundle.resolve()))


def source_class(row: dict[str, Any]) -> str:
    text = " ".join((row.get("sourceKinds") or []) + (row.get("ownership") or []) + (row.get("originalSource") or []))
    low = text.lower()
    if any(p in low for p in ("private", "secret", "unsafe")):
        return "privacy_or_unsafe"
    if any(p in low for p in ("framework", "generated")):
        return "framework_shared_generated"
    if "lazy-harness-host-knowledge-record" in low:
        return "historical_host_record"
    if "source-policy-context" in low:
        return "source_policy_context"
    if "project-document-or-linkage-evidence" in low:
        return "project_document_or_linkage"
    return "unknown_supported_machine_source"


def source_kind_eligibility(row: dict[str, Any], *, approved_host_reference: bool = False) -> tuple[bool, str]:
    """Source-role gate only; content/claim eligibility is decided separately."""
    kinds = set(row.get("sourceKinds") or [])
    cls = source_class(row)
    if approved_host_reference and kinds == {"lazy-harness-host-knowledge-record"} and set(row.get("ownership") or []) == {"owned-or-uncertain:host-record-captured-review-required"}:
        # Invocation-scoped, authenticated reference use; never the old MODEL path.
        return True, "host_source_reference"
    if cls in {"privacy_or_unsafe", "framework_shared_generated", "historical_host_record"}:
        return False, cls
    if kinds & SUPPORTED_MODEL_SOURCE_KINDS:
        return True, cls
    return False, "unsupported_source_class"


def eligible(row: dict[str, Any]) -> tuple[bool, str]:
    return source_kind_eligibility(row)


def has_claim_content(row: dict[str, Any]) -> tuple[bool, str]:
    text = row.get("text") if isinstance(row.get("text"), str) else ""
    if not text.strip():
        return False, "empty_structural_span"
    if row.get("kind") == "markdown-section":
        body_lines = [line for line in text.splitlines() if line.strip() and not MARKDOWN_HEADING_RE.match(line.strip())]
        if not body_lines:
            return False, "heading_only_no_claim_content"
    return True, "claim_content_present"


def group_has_claim_content(group: dict[str, Any]) -> tuple[bool, str]:
    return has_claim_content(group.get("sample") or {})


def group_candidates(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for c in candidates:
        ok, reason = source_kind_eligibility(c)
        key = stable_id("group", c.get("sourceDocFP"), c.get("bodyFP"), c.get("kind"), c.get("title"),
                        c.get("jsonPath"), c.get("xmlPath"), c.get("ownership"), ok)
        g = groups.setdefault(key, {"groupId": key, "eligible": ok, "classification": reason,
            "sourceDocFP": c.get("sourceDocFP"), "bodyFP": c.get("bodyFP"), "kind": c.get("kind"),
            "title": c.get("title"), "sourceKinds": c.get("sourceKinds") or [], "ownership": c.get("ownership") or [],
            "candidateIds": [], "sourceInputIDs": [], "sample": c})
        g["candidateIds"].append(c.get("candidateId")); g["sourceInputIDs"] += c.get("originalSource") or []
    for g in groups.values():
        g["sourceInputIDs"] = sorted(set(x for x in g["sourceInputIDs"] if isinstance(x, str)))
    return groups


def line_span(bundle: Path, ledger_row: dict[str, Any], sample: dict[str, Any]) -> dict[str, Any]:
    paths = ledger_row.get("objectPaths") or []
    if not paths:
        raise ValueError("source_missing")
    object_path = current_v1_import.normalize_rel(paths[0], "objectPath")
    root = bundle.resolve(strict=True)
    p = (root / object_path).resolve(strict=True)
    if not _safe_inside(root, p) or p.is_symlink():
        raise ValueError("source_escape")
    data = p.read_bytes()
    if hashlib.sha256(data).hexdigest() != ledger_row.get("sourceDocFP"):
        raise ValueError("source_hash_mismatch")
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    start = sample.get("lineStart") if isinstance(sample.get("lineStart"), int) else 1
    end = sample.get("lineEnd") if isinstance(sample.get("lineEnd"), int) else min(len(lines), start + 40)
    span = "\n".join(lines[max(0, start - 1):min(len(lines), end)])
    if not span.strip():
        raise ValueError("source_span_empty")
    span = span[:MAX_GROUP_INPUT_CHARS]
    end = start + len(span.splitlines()) - 1
    return {"text": span, "lineStart": start, "lineEnd": end,
            "sourceQuoteHash": sha256_text(span), "sourcePath": (ledger_row.get("sourcePaths") or [None])[0]}


def normalize_reply(reply: Any) -> tuple[str | None, dict[str, Any]]:
    """Backward-compatible adapter: accept old tuple/string and preserve provider usage when present."""
    meta: dict[str, Any] = {"usageKnown": False, "usage": "unknown"}
    if isinstance(reply, dict):
        text = reply.get("text") or reply.get("content") or reply.get("final")
        usage = reply.get("usage") if isinstance(reply.get("usage"), dict) else None
        if usage:
            meta.update({"usageKnown": True, "usage": usage})
        return (text if isinstance(text, str) else None), meta
    if isinstance(reply, tuple):
        text = reply[0] if reply and isinstance(reply[0], str) else None
        if len(reply) > 1 and isinstance(reply[1], dict):
            if "usageKnown" in reply[1] and "usage" in reply[1]:
                meta.update({"usageKnown": bool(reply[1].get("usageKnown")), "usage": reply[1].get("usage", "unknown")})
                if reply[1].get("profile"):
                    meta["profile"] = reply[1].get("profile")
            else:
                meta.update({"usageKnown": True, "usage": reply[1]})
        elif len(reply) > 1 and isinstance(reply[1], (int, float)):
            meta.update({"usageKnown": True, "usage": {"cost_usd": reply[1], "source": "legacy-cost-only"}})
        return text, meta
    return (reply if isinstance(reply, str) else None), meta


def default_proposer(packet: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    import brief
    d = Path(tempfile.mkdtemp(prefix="lh-current-v1-review-"))
    try:
        os.chmod(d, 0o700)
        f = d / "packet.json"
        f.write_text(json.dumps(packet, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        os.chmod(f, 0o600)
        text, meta = normalize_reply(brief.pi_runner(PROMPT.format(FILE=str(f)), str(d)))
        if not text:
            raise RuntimeError("empty proposer output")
        return text, meta
    finally:
        shutil.rmtree(d, ignore_errors=True)


def safe_payload_text(value: Any, limit: int) -> bool:
    """Keep bounded structured text, never provider dumps or credential-like content."""
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        return False
    if any(ord(c) < 32 and c not in "\n\t\r" for c in value):
        return False
    return not re.search(r"(?i)(?:-----BEGIN .*PRIVATE KEY|postgres(?:ql)?://|bearer\s+[a-z0-9._-]+|(?:api[_-]?key|password|secret)\s*[:=]\s*\S+)", value)


def payload_status(candidate: dict[str, Any], span: str) -> str:
    """Legacy hash-only verdicts remain readable, but never become ingestible text."""
    if "claim" not in candidate or "source_quote" not in candidate:
        return "payload_missing"
    claim, quote = candidate["claim"], candidate["source_quote"]
    if not safe_payload_text(claim, 4000) or not safe_payload_text(quote, 8000):
        return "payload_invalid"
    if candidate.get("claimHash") != sha256_text(claim) or candidate.get("quoteHash") != sha256_text(quote):
        return "payload_hash_mismatch"
    if quote not in span:
        return "quote_unbound"
    if candidate.get("status") != "supported" or (candidate.get("verifier") or {}).get("choice") != "supported":
        return "not_supported"
    return "eligible_payload"

def verify_candidates(proposed: list[dict[str, Any]], span: str, judge) -> list[dict[str, Any]]:
    items, valid = [], []
    for i, p in enumerate(proposed):
        quote = p.get("source_quote") if isinstance(p, dict) else None
        claim = p.get("claim") if isinstance(p, dict) else None
        if (not safe_payload_text(quote, 8000) or quote not in span
                or not safe_payload_text(claim, 4000)
                or p.get("facet") not in {"DDD", "SDD", "BDD", "TDD", "ADR", "SSOT", "other"}
                or not safe_payload_text(p.get("relation"), 120)):
            valid.append({"status": "malformed", "reason": "unbound_or_incomplete", "proposalIndex": i}); continue
        items.append({"proposalIndex": i, "claim": claim, "source_quote": quote, "facet": p.get("facet")})
        valid.append({"pendingVerify": True, "proposalIndex": i, "proposal": p})
    if not items:
        return valid
    answers = judge({"items": items}, [json.dumps(x, ensure_ascii=False) for x in items], VERIFY_Q, criteria=VERIFY_C)
    by_index = {item["proposalIndex"]: ans for item, ans in zip(items, answers)}
    out = []
    for row in valid:
        if not row.get("pendingVerify"):
            out.append(row); continue
        ans = by_index.get(row["proposalIndex"], {})
        choice = ans.get("choice")
        if choice not in VERIFY_C:
            choice = "uncertain"
        p = row["proposal"]
        out.append({"status": "supported" if choice == "supported" else (choice or "uncertain"),
            "facet": p.get("facet"), "claim": p["claim"], "source_quote": p["source_quote"],
            "payloadStatus": "present", "claimHash": sha256_text(p["claim"]),
            "quoteHash": sha256_text(p.get("source_quote", "")), "relation": p.get("relation"),
            "verifier": {"role": "typed-jev", "choice": choice, "probabilities": ans.get("probabilities")}})
    return out


def run_pipeline(ingestion: Path, source_bundle: Path, output_root: Path, *, expected_manifest_sha256: str,
                 expected_source_root: str, expected_parent_manifest_sha256: str | None = None,
                 max_model_requests: int = 0, review_version: str | None = None,
                 proposer=default_proposer, judge=None) -> dict[str, Any]:
    guard = guard_first(ingestion, source_bundle, expected_manifest_sha256, expected_source_root, expected_parent_manifest_sha256)
    result, candidates, ledger = load_ingestion(ingestion)
    groups = group_candidates(candidates)
    version = review_version or f"{guard.source_version}-review-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    out = output_root / version
    out.mkdir(parents=True, exist_ok=True)
    cursor_path, progress_path = out / "cursor.json", out / "progress.json"
    processed = set()
    if cursor_path.exists():
        try:
            cur = json.loads(cursor_path.read_text(encoding="utf-8")); processed = set(cur.get("processedGroupIds") or [])
        except json.JSONDecodeError:
            processed = set()
    receipts_path = out / "batchreceipts.jsonl"
    if receipts_path.exists():
        for row in read_jsonl(receipts_path):
            gid = row.get("groupId")
            if isinstance(gid, str) and row.get("status") in {"reviewed", "deferred"}:
                processed.add(gid)
    def existing_model_calls() -> int:
        calls_path = out / "model-role-calls.jsonl"
        if not calls_path.exists():
            return 0
        return sum(1 for row in read_jsonl(calls_path) if row.get("role") == "proposer")

    model_calls = existing_model_calls(); run_model_calls = 0
    outcomes = {"structural_deferred": 0, "eligible_groups": sum(1 for g in groups.values() if g.get("eligible")),
                "model_supported": 0, "model_deferred": 0, "source_error": 0, "not_visited": 0}
    model_pending: set[str] = set()
    for index, gid in enumerate(sorted(groups), start=1):
        if gid in processed:
            continue
        terminal = True
        g = groups[gid]
        receipt_base = {"schemaVersion": SCHEMA_VERSION, "sourceVersion": guard.source_version, "groupId": gid,
                        "candidateIds": g["candidateIds"], "sourceInputIDs": g["sourceInputIDs"],
                        "claimFP": sha256_text(canonical_json({"guard": guard.__dict__, "group": gid}))}
        if not g["eligible"]:
            row = {**receipt_base, "status": "deferred", "outcome": "not_business_canonical", "classification": g["classification"]}
            append_jsonl(out / "batchreceipts.jsonl", row); outcomes["structural_deferred"] += len(g["candidateIds"])
        else:
            claim_ok, claim_reason = group_has_claim_content(g)
            if not claim_ok:
                row = {**receipt_base, "status": "deferred", "outcome": "nonclaim_structural_terminal",
                       "classification": claim_reason, "sourceClassification": g["classification"], "truthPromotion": "none"}
                append_jsonl(out / "batchreceipts.jsonl", row); outcomes["structural_deferred"] += len(g["candidateIds"])
                processed.add(gid)
                continue
            elif model_calls >= max_model_requests:
                outcomes["not_visited"] += len(g["candidateIds"])
                terminal = False
                model_pending.add(gid)
                append_jsonl(out / "batchreceipts.jsonl", {**receipt_base, "status": "pending", "outcome": "model_request_cap_reached",
                    "classification": g["classification"], "truthPromotion": "none"})
                continue
            try:
                span = line_span(source_bundle, ledger[g["sourceDocFP"]], g["sample"])
                packet = {"sourceVersion": guard.source_version, "groupId": gid, "candidateIds": g["candidateIds"],
                          "sourcePath": span["sourcePath"], "lineStart": span["lineStart"], "lineEnd": span["lineEnd"],
                          "span": span["text"], "guard": {"manifestSha256": guard.source_manifest_sha256,
                          "sourceRoot": guard.source_root, "sourceDocFP": g["sourceDocFP"]}}
                start = time.time(); reply, meta = normalize_reply(proposer(packet)); wall = round(time.time() - start, 3)
                model_calls += 1; run_model_calls += 1
                call_row = {**receipt_base, "role": "proposer", "profile": meta.get("profile") or os.environ.get("LH_BRIEF_MODEL", "configured-brief-default"),
                            "status": "ok" if reply else "error", "wallSeconds": wall, "usage": meta.get("usage"),
                            "usageKnown": meta.get("usageKnown"), "requestChars": len(canonical_json(packet)),
                            "promptHash": sha256_text(PROMPT), "rawOutputStored": False}
                append_jsonl(out / "model-role-calls.jsonl", call_row)
                if not reply or len(reply) > MAX_PROPOSER_OUTPUT_CHARS:
                    raise ValueError("malformed_or_oversize_proposer_output")
                data = json.loads(reply)
                props = data.get("candidates") if isinstance(data, dict) and set(data) == {"candidates"} else None
                if not isinstance(props, list) or len(props) > 16:
                    raise ValueError("malformed_proposer_schema")
                verified = verify_candidates(props, span["text"], judge) if judge else []
                for candidate in verified:
                    if candidate.get("claimHash") and candidate.get("quoteHash"):
                        candidate["claimFP"] = stable_id("claim", guard.source_root, guard.source_version,
                            gid, candidate["claimHash"], candidate["quoteHash"])
                supported = [v for v in verified if v.get("status") == "supported"]
                row = {**receipt_base, "status": "reviewed", "outcome": "supported" if supported else "deferred",
                       "sourceProof": {**{k: span[k] for k in ("sourcePath", "lineStart", "lineEnd", "sourceQuoteHash")},
                           "sourceRoot": guard.source_root, "manifestSha256": guard.source_manifest_sha256,
                           "sourceVersion": guard.source_version, "sourceDocFP": g["sourceDocFP"],
                           "reviewVersion": version, "ownership": g["ownership"]},
                       "verifiedCandidates": verified, "truthPromotion": "none"}
                outcomes["model_supported"] += len(supported); outcomes["model_deferred"] += max(0, len(verified) - len(supported))
                append_jsonl(out / "results.jsonl", row); append_jsonl(out / "batchreceipts.jsonl", row)
            except Exception as exc:  # fail item, continue next group; no raw text in artifact
                outcomes["source_error"] += len(g["candidateIds"])
                append_jsonl(out / "batchreceipts.jsonl", {**receipt_base, "status": "deferred", "outcome": "source_error",
                    "errorClass": type(exc).__name__, "truthPromotion": "none"})
        if terminal:
            processed.add(gid)
        if index % 1000 == 0:
            cursor_path.write_text(json.dumps({"sourceVersion": guard.source_version, "processedGroupIds": sorted(processed),
                "pendingModelGroupIds": sorted(model_pending), "nextGroupId": gid, "modelCalls": model_calls,
                "complete": False}, ensure_ascii=False, indent=2), encoding="utf-8")
    cursor_path.write_text(json.dumps({"sourceVersion": guard.source_version, "processedGroupIds": sorted(processed),
        "pendingModelGroupIds": sorted(model_pending), "nextGroupId": None, "modelCalls": model_calls,
        "complete": len(processed) == len(groups) and not model_pending}, ensure_ascii=False, indent=2), encoding="utf-8")
    def cumulative_counts() -> dict[str, Any]:
        terminal: dict[str, dict[str, Any]] = {}
        pending: set[str] = set()
        receipts_path = out / "batchreceipts.jsonl"
        if receipts_path.exists():
            for row in read_jsonl(receipts_path):
                gid = row.get("groupId")
                if not isinstance(gid, str):
                    continue
                if row.get("status") == "pending":
                    if gid not in terminal:
                        pending.add(gid)
                elif row.get("status") in {"reviewed", "deferred"}:
                    terminal[gid] = row; pending.discard(gid)
        pending = {gid for gid in pending if gid not in terminal and gid in groups}
        structural = source_error = model_supported = model_deferred = 0
        for row in terminal.values():
            n = len(row.get("candidateIds") or [])
            if row.get("outcome") == "source_error":
                source_error += n
            elif row.get("status") == "deferred" and row.get("outcome") in {"not_business_canonical", "nonclaim_structural_terminal"}:
                structural += n
            if row.get("status") == "reviewed":
                verified = row.get("verifiedCandidates") or []
                supported = [v for v in verified if isinstance(v, dict) and v.get("status") == "supported"]
                model_supported += len(supported); model_deferred += max(0, len(verified) - len(supported))
        processed_now = set(processed) | set(terminal)
        not_visited = sum(len(groups[gid].get("candidateIds") or []) for gid in pending)
        return {"candidates": len(candidates), "groups": len(groups), "processedGroups": len(processed_now),
                "remainingGroups": len(groups) - len(processed_now), "pendingModelGroups": len(pending),
                "eligible_groups": sum(1 for g in groups.values() if g.get("eligible")),
                "structural_deferred": structural, "model_supported": model_supported, "model_deferred": model_deferred,
                "source_error": source_error, "not_visited": not_visited}

    counts = cumulative_counts()
    if counts["pendingModelGroups"]:
        stop = "model_request_cap_reached_or_missing_budget" if max_model_requests else "missing_model_request_budget_cap"
    else:
        stop = "complete" if counts["remainingGroups"] == 0 else "cursor_remaining"
    progress = {"ok": True, "schemaVersion": SCHEMA_VERSION, "version": version, "generatedAt": utc_now(),
        "sourceVersion": guard.source_version, "sourceManifestSha256": guard.source_manifest_sha256,
        "sourceRoot": guard.source_root, "ingestionResultFP": guard.ingestion_fp, "counts": counts,
        "model": {"requestCap": max_model_requests, "actualRequests": model_calls, "thisRunRequests": run_model_calls,
                  "requestCapScope": "review-version cumulative proposer calls", "usageUnavailableMeans": "unknown-not-zero"},
        "stopReason": stop, "artifacts": {"cursor": str(cursor_path), "batchReceipts": str(out / "batchreceipts.jsonl"),
        "modelRoleCalls": str(out / "model-role-calls.jsonl"), "results": str(out / "results.jsonl")},
        "notes": ["no canonical promotion", "first-pass artifacts untouched", "structural classifications are not business facts"]}
    progress_path.write_text(json.dumps(progress, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_jsonl(out / "log.jsonl", {"event": "run", "at": utc_now(), "progress": progress})
    return progress


def make_judge_from_config():
    import config, capture_audit
    cfg = config.require("jev_api_key", "jev_base_url", "jev_model")
    return capture_audit.make_judge(cfg, max_attempts=1, text_limit=None)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run append-only CURRENT V1 review overlay.")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--ingestion", required=True)
    r.add_argument("--source-bundle", required=True)
    r.add_argument("--expected-manifest-sha256", required=True)
    r.add_argument("--expected-source-root", required=True)
    r.add_argument("--expected-parent-manifest-sha256")
    r.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    r.add_argument("--review-version")
    r.add_argument("--max-model-requests", type=int, default=0)
    r.add_argument("--no-jev", action="store_true", help="structural/proposer-only dry verifier for offline tests")
    args = p.parse_args(argv)
    try:
        judge = None if args.no_jev else make_judge_from_config()
        out = run_pipeline(Path(args.ingestion), Path(args.source_bundle), Path(args.output_root),
            expected_manifest_sha256=args.expected_manifest_sha256, expected_source_root=args.expected_source_root,
            expected_parent_manifest_sha256=args.expected_parent_manifest_sha256,
            max_model_requests=max(0, args.max_model_requests), review_version=args.review_version, judge=judge)
        print(json.dumps(out, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "detail": str(exc)[:200]}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
