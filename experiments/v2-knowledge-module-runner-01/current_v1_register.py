"""Scoped reference-use recovery and candidate registration; no truth promotion.

CLI receives separately trusted receipt/results digests, never credentials. All
DB routing comes from the existing private config, frozen once at entry.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
from uuid import UUID, uuid5

import current_v1_review as review


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound_json(path, expected):
    if not re.fullmatch(r"[0-9a-f]{64}", expected or "") or digest(path) != expected:
        raise ValueError("trusted artifact digest mismatch")
    return json.loads(Path(path).read_text())


def context(receipt_path, receipt_sha256, ingestion, bundle, host):
    auth = bound_json(receipt_path, receipt_sha256)
    full = auth.get("recoveryScope") == "full-old-model-groups"
    if full and (auth.get("roleCaps") != {"proposer": 4244, "judge": 4244}
                 or auth.get("seedUsage") != {"proposer": 4, "judge": 3}):
        raise ValueError("full recovery budget mismatch")
    group_limit = 4244 if full else 50
    if (auth.get("schemaVersion") != "current-v1-reference-use/v1"
            or auth.get("host") != host or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", host)
            or auth.get("approvedReferenceUse") != "user-approved-reference"
            or auth.get("truthPromotion") != "none" or auth.get("confidence") != "candidate"
            or auth.get("authorOwnership") != "unverified"
            or not 0 < len(auth.get("groupIds", [])) <= group_limit
            or len(set(auth["groupIds"])) != len(auth["groupIds"])):
        raise ValueError("reference authorization mismatch")
    guard = review.guard_first(Path(ingestion), Path(bundle), auth["manifestSha256"], auth["sourceRoot"])
    if guard.source_version != auth["sourceVersion"]:
        raise ValueError("reference version mismatch")
    _, candidates, ledger = review.load_ingestion(Path(ingestion))
    groups = review.group_candidates(candidates)
    manifest = json.loads((Path(bundle) / "manifest.json").read_text())
    inventory = {r["path"]: r for r in manifest["inventory"]}
    selected = {}
    allowed = auth.get("paths", [])
    if not allowed or len(set(allowed)) != len(allowed):
        raise ValueError("missing approved paths")
    for gid in auth["groupIds"]:
        g = groups.get(gid)
        if (not g or not g["eligible"] or not review.group_has_claim_content(g)[0]
                or not g["sourceInputIDs"] or not set(g["sourceInputIDs"]) <= set(allowed)):
            raise ValueError("unapproved source group")
        for path in g["sourceInputIDs"]:
            raw = inventory.get(path, {})
            if (raw.get("sha256") != g["sourceDocFP"] or raw.get("ownership") not in g["ownership"]
                    or raw.get("sourceKind") not in g["sourceKinds"]
                    or raw.get("disposition") not in {"captured", "captured_needs_review"}
                    or raw.get("contentRef") not in ledger[g["sourceDocFP"]].get("objectPaths", [])):
                raise ValueError("snapshot provenance mismatch")
        span = review.line_span(Path(bundle), ledger[g["sourceDocFP"]], g["sample"])
        if span["sourcePath"] not in g["sourceInputIDs"]:
            raise ValueError("source path mismatch")
        selected[gid] = (g, span)
    return auth, selected


def proof(auth, gid, g, span, version):
    return {**{k: span[k] for k in ("sourcePath", "lineStart", "lineEnd", "sourceQuoteHash")},
            "sourceRoot": auth["sourceRoot"], "sourceVersion": auth["sourceVersion"],
            "manifestSha256": auth["manifestSha256"], "sourceDocFP": g["sourceDocFP"],
            "reviewVersion": version, "ownership": g["ownership"], "groupId": gid}


def recover(auth, selected, directory, receipt_sha256, *, proposer=None, judge=None):
    """Exclusive new version; durable reservations BEFORE calls, never replay uncertain calls."""
    if auth.get("recoveryScope") == "full-old-model-groups":
        raise ValueError("use cumulative full recovery controller")
    directory = Path(directory)
    if directory.resolve() != Path(auth["reviewDirectory"]).resolve():
        raise ValueError("review directory authorization mismatch")
    directory.mkdir(parents=True, exist_ok=False)
    os.chmod(directory, 0o700)
    proposer = proposer or review.default_proposer
    judge = judge or review.make_judge_from_config()
    review.append_jsonl(directory / "authorization.jsonl", {**auth, "receiptSha256": receipt_sha256})
    counts = Counter()
    version = directory.name
    for gid, (g, span) in selected.items():
        base = {"groupId": gid, "candidateIds": g["candidateIds"], "sourceInputIDs": g["sourceInputIDs"],
                "classification": g["classification"], "sourceVersion": auth["sourceVersion"],
                "sourceProof": proof(auth, gid, g, span, version), "truthPromotion": "none"}
        packet = {"sourceVersion": auth["sourceVersion"], "groupId": gid,
                  "sourcePath": span["sourcePath"], "lineStart": span["lineStart"], "lineEnd": span["lineEnd"],
                  "span": span["text"], "guard": {"manifestSha256": auth["manifestSha256"],
                  "sourceRoot": auth["sourceRoot"], "sourceDocFP": g["sourceDocFP"]}}
        try:
            if counts["proposerCalls"] >= 50:
                raise ValueError("proposer budget exhausted")
            counts["proposerCalls"] += 1
            review.append_jsonl(directory / "calls.jsonl", {"groupId": gid, "role": "proposer", "state": "reserved", "rawOutputStored": False})
            reply, meta = review.normalize_reply(proposer(packet))
            if not reply or len(reply) > review.MAX_PROPOSER_OUTPUT_CHARS:
                raise ValueError("invalid proposer output")
            data = json.loads(reply)
            if not isinstance(data, dict) or set(data) != {"candidates"} or not isinstance(data["candidates"], list) or len(data["candidates"]) > 16:
                raise ValueError("invalid proposer schema")
            def bounded_judge(*args, **kwargs):
                if counts["judgeCalls"] >= 50:
                    raise ValueError("judge budget exhausted")
                counts["judgeCalls"] += 1
                review.append_jsonl(directory / "calls.jsonl", {"groupId": gid, "role": "judge", "state": "reserved", "rawOutputStored": False})
                return judge(*args, **kwargs)
            verified = review.verify_candidates(data["candidates"], span["text"], bounded_judge)
            for c in verified:
                if c.get("claimHash") and c.get("quoteHash"):
                    c["claimFP"] = review.stable_id("claim", auth["sourceRoot"], auth["sourceVersion"], gid, c["claimHash"], c["quoteHash"])
                counts[c.get("status", "malformed")] += 1
            row = {**base, "status": "reviewed", "verifiedCandidates": verified,
                   "model": {"proposer": meta.get("profile", "configured-brief-default"), "judge": "configured-typed-jev"}}
        except Exception as exc:
            counts["errorGroups"] += 1
            row = {**base, "status": "error", "errorClass": type(exc).__name__, "verifiedCandidates": []}
        review.append_jsonl(directory / "results.jsonl", row)
    summary = {"reviewVersion": version, "selectedGroups": len(selected), "counts": dict(counts),
               "resultsSha256": digest(directory / "results.jsonl"), "receiptSha256": receipt_sha256}
    (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def preview(auth, selected, results, results_sha256, receipt_sha256):
    """Validate all rows before any DB operation. Do not substitute source for claim."""
    if digest(results) != results_sha256:
        raise ValueError("review digest mismatch")
    fragments, excluded, seen = [], Counter(), set()
    for row in review.read_jsonl(Path(results)):
        gid = row.get("groupId")
        if gid not in selected or gid in seen:
            raise ValueError("foreign or duplicate review group")
        seen.add(gid)
        g, span = selected[gid]
        version = Path(results).parent.name
        if (row.get("sourceProof") != proof(auth, gid, g, span, version)
                or row.get("truthPromotion") != "none" or row.get("candidateIds") != g["candidateIds"]
                or row.get("sourceInputIDs") != g["sourceInputIDs"]):
            raise ValueError("review provenance mismatch")
        if row.get("status") != "reviewed":
            excluded["errorGroups"] += 1
            continue
        cs = row.get("verifiedCandidates")
        if not isinstance(cs, list) or len(cs) > 16:
            raise ValueError("invalid reviewed schema")
        for c in cs:
            status = review.payload_status(c, span["text"]) if isinstance(c, dict) else "payload_invalid"
            if status != "eligible_payload":
                excluded[status] += 1
                continue
            fp = review.stable_id("claim", auth["sourceRoot"], auth["sourceVersion"], gid, c["claimHash"], c["quoteHash"])
            if (c.get("claimFP") != fp or c.get("facet") not in {"DDD", "SDD", "BDD", "TDD", "ADR", "SSOT", "other"}
                    or not review.safe_payload_text(c.get("relation"), 120)):
                raise ValueError("claim fingerprint or classification mismatch")
            source = {"evidence_refs": [{"type": "observed_output", "locator": f"{span['sourcePath']}:{span['lineStart']}-{span['lineEnd']}",
                      "quote": c["source_quote"], **row["sourceProof"]}],
                      "claimFP": fp, "claimHash": c["claimHash"], "quoteHash": c["quoteHash"],
                      "sourceProof": row["sourceProof"], "classification": g["classification"],
                      "facet": c["facet"], "relation": c["relation"], "verifier": c["verifier"],
                      "model": row.get("model"), "reviewSha256": results_sha256,
                      "receiptSha256": receipt_sha256, "approvedReferenceUse": "user-approved-reference",
                      "originalOwnership": g["ownership"], "authorOwnership": "unverified",
                      "truthPromotion": "none", "confidence": "candidate"}
            fid = str(uuid5(UUID("4d98a4d5-66bf-4d04-b660-9950bfc458e8"), auth["host"] + "/" + fp))
            fragments.append({"id": fid, "text": c["claim"], "source": source})
    if seen != set(selected):
        raise ValueError("incomplete review group accounting")
    return {"host": auth["host"], "sourceRoot": auth["sourceRoot"], "fragments": fragments,
            "summary": {"groups": len(seen), "eligibleClaims": len(fragments), "excluded": dict(excluded)}}


def register(runtime_db, plan, *, apply=False):
    import store_pg
    runtime_db.assert_environment()
    created = existing = 0
    host = plan["host"]
    with store_pg.connect(runtime_db.dsn) as conn, conn.cursor() as cur:
        cur.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", ("current-v1/" + host,))
        cur.execute("select repo_locator from knowledge.host where host_id=%s", (host,))
        oldhost = cur.fetchone()
        if oldhost and oldhost[0] != plan["sourceRoot"]:
            raise ValueError("host binding conflict")
        if apply and not oldhost:
            cur.execute("insert into knowledge.host(host_id,name,repo_locator) values (%s,%s,%s)",
                        (host, "Med reference candidate pilot", plan["sourceRoot"]))
        for f in plan["fragments"]:
            cur.execute("select host_id,text,source,confidence::text,active from knowledge.fragment where id=%s", (f["id"],))
            old = cur.fetchone()
            if old:
                if old != (host, f["text"], f["source"], "candidate", True):
                    raise ValueError("existing fragment conflict")
                existing += 1
                continue
            created += 1
            if apply:
                seq = store_pg.next_seq(cur, host, "emr-reference")
                cur.execute("""insert into knowledge.fragment(id,host_id,alias,domain,seq,text,kind,confidence,source)
                    values (%s,%s,%s,'emr-reference',%s,%s,'fact','candidate',%s::jsonb)""",
                    (f["id"], host, f"emr-reference-{seq}", seq, f["text"], json.dumps(f["source"], ensure_ascii=False)))
    return {**plan["summary"], "host": host, "applied": apply, "new": created, "existing": existing}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["recover", "validate", "preview", "apply", "embed"])
    for key in ("receipt", "receipt-sha256", "ingestion", "bundle", "host"):
        p.add_argument("--" + key, required=True)
    p.add_argument("--review-dir")
    p.add_argument("--results")
    p.add_argument("--results-sha256")
    args = p.parse_args(argv)
    try:
        auth, selected = context(args.receipt, args.receipt_sha256, args.ingestion, args.bundle, args.host)
        if args.command == "recover":
            result = recover(auth, selected, args.review_dir, args.receipt_sha256)
        else:
            plan = preview(auth, selected, args.results, args.results_sha256, args.receipt_sha256)
            result = plan["summary"]
            if args.command != "validate":
                import config
                from runtime_db import bind_runtime_db
                runtime = bind_runtime_db(config.require("db_url")["db_url"], provenance="configured-entry")
                if runtime.endpoint[0] in {"unix", "localhost", "127.0.0.1", "::1"}:
                    raise ValueError("remote V2 target required")
                result = register(runtime, plan, apply=args.command == "apply")
                if args.command == "embed":
                    if result["new"]:
                        raise ValueError("register candidates before embeddings")
                    import store_pg
                    ids = [f["id"] for f in plan["fragments"]]
                    result["generatedVectors"] = store_pg.backfill_embeddings(runtime.dsn, args.host, variant="ctx-v1", fragment_ids=ids, limit=len(ids)) if ids else 0
        print(json.dumps({"ok": True, **result}, ensure_ascii=False))
        return 0
    except Exception as exc:
        # No provider, driver, or config text escapes the private process.
        print(json.dumps({"ok": False, "error": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
