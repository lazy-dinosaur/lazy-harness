"""Public frozen host-source consumer: source reference, never generated/verified truth.

validate/preview/apply/embed authenticate a separately trusted scoped receipt first.
No source edits, graph migration, proposer, verifier, service or credential flags.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import subprocess
from uuid import UUID, uuid5
from xml.etree import ElementTree

import current_v1_import as intake
import current_v1_register as registration
import current_v1_review as review

HOST_KIND = "lazy-harness-host-knowledge-record"
HOST_OWNER = "owned-or-uncertain:host-record-captured-review-required"
NAMESPACE = UUID("918180fe-9566-4d83-91e8-a92fe3493787")
ARTIFACTS = ("result.json", "intake-ledger.jsonl", "candidates.jsonl", "references.jsonl")


def context(receipt, receipt_sha256, ingestion, bundle, host):
    auth = registration.bound_json(receipt, receipt_sha256)
    if (auth.get("schemaVersion") != "current-v1-host-reference/v1"
            or auth.get("host") != host or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,79}", host)
            or auth.get("approvedReferenceUse") != "user-approved-reference"
            or auth.get("truthPromotion") != "none" or auth.get("confidence") != "candidate"
            or auth.get("authorOwnership") != "unverified"
            or auth.get("originKind") != "source_reference"):
        raise ValueError("host reference authorization mismatch")
    parent = registration.bound_json(auth["parentReceipt"], auth["parentReceiptSha256"])
    for field in ("host", "sourceRoot", "sourceVersion", "manifestSha256"):
        if parent.get(field) != auth.get(field):
            raise ValueError("parent receipt binding mismatch")
    for name in ARTIFACTS:
        if registration.digest(Path(ingestion) / name) != auth.get("intakeHashes", {}).get(name):
            raise ValueError("immutable intake hash mismatch")
    result = json.loads((Path(ingestion) / "result.json").read_text())
    if (result["manifest"]["sha256"] != auth["manifestSha256"]
            or result["manifest"]["version"] != auth["sourceVersion"]
            or result["manifest"]["sourceIdentity"]["sourceRoot"] != auth["sourceRoot"]):
        raise ValueError("intake identity mismatch")
    manifest, _, objects = intake.load_and_validate_bundle(Path(bundle),
        expected_manifest_sha256=auth["manifestSha256"], expected_source_root=auth["sourceRoot"],
        expected_namespace="current-v1", expected_version=auth["sourceVersion"])
    by_fp = defaultdict(list)
    for obj in objects:
        by_fp[obj.sha256].append(obj)
    expected = {fp: sorted(o.original_relative_path for o in obs)
                for fp, obs in by_fp.items() if any(o.source_kind == HOST_KIND for o in obs)}
    if auth.get("documents") != expected:
        raise ValueError("full host inventory authorization mismatch")
    # Source kind/ownership is authenticated by the frozen manifest, not supplied candidate text.
    return auth, {fp: by_fp[fp] for fp in sorted(expected)}, manifest


def source_units(obj):
    """Original sections/parent records, NOT truncated first-pass child/index nodes.

    Graph rows are opaque references, not relations. Conflict events with identical
    incoming objects/status share a parent; ALL event locators/metadata survive.
    """
    text = obj.body.decode("utf-8")
    suffix = Path(obj.original_relative_path).suffix.lower()
    if not text.strip():
        return [], "empty-source"
    if suffix == ".xml":
        if re.search(r"<!\s*(DOCTYPE|ENTITY)\b", text, re.I):
            return [], "unsafe-xml-entity"
        try:
            ElementTree.fromstring(text)
        except ElementTree.ParseError:
            return [], "invalid-xml-opaque"
        # Preserve the authored document, attributes and nested children together.
        return [{"text": text, "quote": text, "lineStart": 1, "title": Path(obj.original_relative_path).name,
                 "originKind": "source_structured", "mappingReason": "xml-document-reference-no-typed-mapping"}], None
    if suffix == ".json":
        try:
            json.loads(text)
        except ValueError:
            return [], "invalid-json-opaque"
        return [{"text": text, "quote": text, "lineStart": 1, "title": Path(obj.original_relative_path).name,
                 "originKind": "source_structured", "mappingReason": "json-document-reference-no-typed-mapping"}], None
    if suffix == ".jsonl":
        units, conflicts = [], {}
        for lineno, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except ValueError:
                return [], "invalid-jsonl-opaque"
            unit = {"text": line, "quote": line, "lineStart": lineno,
                    "title": Path(obj.original_relative_path).name, "originKind": "source_structured",
                    "mappingReason": "legacy-record-reference-no-confirmed-typed-mapping"}
            # This exact event schema was inspected: incoming is a conflicting
            # proposed record, not the winner/current graph. Never promote it.
            conflict_keys = {"id", "event", "status", "detectedAt", "targetPath", "idKey",
                             "conflictingId", "existingHash", "incomingHash", "incoming"}
            if isinstance(value, dict) and set(value) == conflict_keys and isinstance(value["incoming"], dict):
                if not review.safe_payload_text(line, len(line)):
                    units.append(unit)  # privacy holding happens before any normalized copy
                    continue
                key = review.canonical_json({k: value[k] for k in ("event", "status", "targetPath", "conflictingId", "existingHash", "incoming")})
                occurrence = {k: v for k, v in value.items() if k != "incoming"}
                occurrence.update(lineStart=lineno, sourceQuoteHash=review.sha256_text(line))
                if key in conflicts:
                    conflicts[key]["occurrences"].append(occurrence)
                    continue
                unit.update(text="Conflict history (not current or verified):\n" + key,
                            mappingReason="exact-conflict-event-schema-incoming-reference-only",
                            occurrences=[occurrence])
                conflicts[key] = unit
            units.append(unit)
        return units, None
    if suffix not in {".md", ".markdown", ".txt"}:
        return [], "unsupported-format-opaque"
    sections, _ = intake.md_sections(text)
    # md_sections omits prose before the first heading; preserve it here.
    if sections and sections[0]["lineStart"] > 1:
        end = sections[0]["lineStart"] - 1
        sections.insert(0, {"text": "\n".join(text.splitlines()[:end]), "lineStart": 1, "title": "Preamble"})
    return [{**u, "quote": u["text"], "originKind": "source_reference",
             "mappingReason": "authored-section-reference-not-generated-claim"} for u in sections], None


def tokenize_units(units):
    """Use the existing pinned multilingual E5 tokenizer runtime, no network/model.

    Keep exact text offsets; 384-token bodies leave room for ctx-v1 and titles.
    No field/index/array-child embedding, no text truncation.
    """
    import config
    import embed
    root = Path(config.load()["embed_model_dir"])
    tokenizer = root / "tokenizer.json"
    if registration.digest(tokenizer) != embed._PINS["tokenizer.json"]:
        raise ValueError("existing tokenizer pin mismatch")
    program = '''import json,sys
from tokenizers import Tokenizer
t=Tokenizer.from_file(sys.argv[1]); t.no_truncation(); t.no_padding()
result=[]
for text in json.load(sys.stdin):
 offsets=[(a,b) for a,b in t.encode(text,add_special_tokens=False).offsets if b>a]
 cuts=[0]
 for i in range(384,len(offsets),384):
  cut=offsets[i][0]
  if cut>cuts[-1]: cuts.append(cut)
 cuts.append(len(text))
 result.append([(a,b) for a,b in zip(cuts,cuts[1:]) if b>a])
json.dump(result,sys.stdout)
'''
    proc = subprocess.run([str(root / "venv/bin/python"), "-c", program, str(tokenizer)],
                          input=json.dumps([u["text"] for u in units]), text=True, capture_output=True, timeout=180)
    if proc.returncode:
        raise ValueError("existing tokenizer runtime unavailable")
    return json.loads(proc.stdout)


def preview(auth, documents, receipt_sha256, *, splitter=tokenize_units):
    coverage, units, held = [], [], Counter()
    for fp, objects in documents.items():
        obj = objects[0]
        row = {"sourceDocFP": fp, "paths": sorted(o.original_relative_path for o in objects),
               "bytes": obj.bytes_count, "sourceKinds": sorted({o.source_kind for o in objects}),
               "originalOwnership": sorted({o.ownership for o in objects}),
               "ownership": sorted({o.ownership for o in objects}), "units": 0, "held": {}, "heldEntries": []}
        coverage.append(row)
        eligible, _ = review.source_kind_eligibility(row, approved_host_reference=True)
        if not eligible or any(o.source_kind != HOST_KIND or o.ownership != HOST_OWNER for o in objects):
            row.update(status="held", reason="mixed-or-unapproved-source-ownership")
            held[row["reason"]] += 1
            continue
        # Only the authenticated .lazy-harness record root is exempted from the
        # original hidden-directory guard; all nested private paths remain blocked.
        if any(not p.startswith(".lazy-harness/") or intake.private_reason(p[len(".lazy-harness/"):]) for p in row["paths"]):
            row.update(status="held", reason="private-or-unapproved-record-path")
            held[row["reason"]] += 1
            continue
        try:
            parts, reason = source_units(obj)
        except UnicodeDecodeError:
            parts, reason = [], "invalid-utf8-opaque"
        if reason:
            row.update(status="held", reason=reason)
            held[reason] += 1
            continue
        counts = Counter()
        for unit in parts:
            if not unit["text"].strip() or (unit["originKind"] == "source_reference" and
                    not any(line.strip() and not review.MARKDOWN_HEADING_RE.match(line.strip()) for line in unit["text"].splitlines())):
                counts["empty-or-heading-only"] += 1
                continue
            quoted_secret = re.search(r'(?i)"(?:password|secret|api[_-]?key|access[_-]?token)"\s*:\s*"[^"\s]+"', unit["quote"])
            if quoted_secret or not review.safe_payload_text(unit["quote"], max(1, len(unit["quote"]))):
                counts["unsafe-body-held"] += 1
                row["heldEntries"].append({"lineStart": unit["lineStart"], "quoteHash": review.sha256_text(unit["quote"]), "reason": "unsafe-body-held"})
                continue
            unit.update(document=row, captureTime=obj.capture_time)
            units.append(unit)
        row.update(status="source-reference", held=dict(counts))
        held.update(counts)
    fragments = {}
    ranges = splitter(units) if units else []
    if len(ranges) != len(units):
        raise ValueError("passage split accounting mismatch")
    duplicates = 0
    for unit, spans in zip(units, ranges):
        row = unit["document"]
        parent = review.stable_id("source-parent", auth["sourceRoot"], auth["sourceVersion"], row["sourceDocFP"],
                                  unit["originKind"], review.sha256_text(unit["text"]))
        if (not spans or spans[0][0] != 0 or spans[-1][1] != len(unit["text"])
                or any(a < 0 or b <= a for a, b in spans)
                or any(a[1] != b[0] for a, b in zip(spans, spans[1:]))):
            raise ValueError("incomplete source passage coverage")
        for start, end in spans:
            body = unit["text"][start:end].strip()
            if not body:
                continue
            # Split offsets must cover the complete normalized parent, not select arbitrary input.
            fp = review.stable_id("source-reference", auth["sourceRoot"], auth["sourceVersion"], row["sourceDocFP"],
                                 parent, review.sha256_text(body))
            direct = unit["text"] == unit["quote"]
            quote = unit["text"][start:end] if direct else unit["quote"]
            line_start = unit["lineStart"] + (unit["text"][:start].count("\n") if direct else 0)
            locator = f"{row['paths'][0]}:{line_start}-{line_start + quote.count(chr(10))}"
            proof = {"sourceRoot": auth["sourceRoot"], "sourceVersion": auth["sourceVersion"],
                     "manifestSha256": auth["manifestSha256"], "sourceDocFP": row["sourceDocFP"],
                     "sourcePath": row["paths"][0], "lineStart": line_start,
                     "lineEnd": line_start + quote.count("\n"),
                     "sourceQuoteHash": review.sha256_text(quote),
                     "parentQuoteHash": review.sha256_text(unit["quote"])}
            # All normalized structured text is backed by the complete safe parent quote.
            source = {"sourceClaimFP": fp, "parentSourceId": parent, "sourceProof": proof,
                "evidence_refs": [{"type": "observed_output", "locator": locator, "quote": quote, **proof}],
                "sourcePaths": row["paths"], "sourceRole": HOST_KIND, "originKind": unit["originKind"],
                "reviewStatus": unit["originKind"], "confidence": "candidate", "truthPromotion": "none",
                "authorOwnership": "unverified", "approvedReferenceUse": "user-approved-reference",
                "originalOwnership": row["originalOwnership"], "receiptSha256": receipt_sha256,
                "validity": {"observedAt": unit["captureTime"], "snapshot": auth["sourceVersion"],
                             "currentTruth": "unverified", "historicalStatus": "preserved-in-source-quote"},
                "mappingReason": unit["mappingReason"], "typedRelations": "not-promoted",
                "claimedMetadata": [list(pair) for pair in re.findall(r"(?im)^(?:-\s*)?(Status|Layer|Scope|Confidence|Date)\s*:\s*(.{1,160})$", unit["quote"])],
                "bodyOffsets": [start, end], "occurrences": unit.get("occurrences", [])}
            if fp in fragments:
                duplicates += 1
                fragments[fp]["source"].setdefault("duplicateLocators", []).append(locator)
                continue
            fid = str(uuid5(NAMESPACE, auth["host"] + "/" + fp))
            title = (unit.get("title") or Path(row["paths"][0]).name).encode("utf-8")[:80].decode("utf-8", "ignore")
            fragments[fp] = {"id": fid, "text": title + "\n" + body, "source": source}
            row["units"] += 1
    for row in coverage:
        if row["status"] == "source-reference" and not row["units"]:
            row.update(status="held", reason="no-safe-meaningful-unit")
    return {"host": auth["host"], "sourceRoot": auth["sourceRoot"], "fragments": list(fragments.values()),
        "coverage": coverage, "summary": {"sourceDocuments": len(coverage), "eligibleUnits": len(fragments),
        "coveredDocuments": sum(r["units"] > 0 for r in coverage), "heldDocuments": sum(r["units"] == 0 for r in coverage),
        "duplicateUnits": duplicates, "heldReasons": dict(held), "textChars": sum(len(f["text"]) for f in fragments.values()),
        "embeddingUnits": len(fragments), "sourceParents": len({f["source"]["parentSourceId"] for f in fragments.values()}),
        "conflictOccurrences": sum(len(u.get("occurrences", [])) for u in units), "typedRelations": 0, "proposerCalls": 0, "judgeCalls": 0,
        "origins": dict(Counter(f["source"]["originKind"] for f in fragments.values()))}}


def register(runtime, plan, *, apply=False):
    """Existing fragment schema, host/domain locks, conflict refusal and bulk inserts.

    Separate UUID namespace/domain prevents any overwrite of generated claims.
    No source-provided relation/SQL/schema is interpreted or executed.
    """
    import store_pg
    runtime.assert_environment()
    host, domain = plan["host"], plan.get("registrationDomain", "host-reference")
    if domain not in {"host-reference", "semantic-reference"}:
        raise ValueError("unapproved registration domain")
    if domain == "semantic-reference" and any(
            f.get("source", {}).get("originKind") != "generated_semantic"
            or not f["source"].get("judgeSha256") for f in plan["fragments"]):
        raise ValueError("semantic registration requires independent judge receipts")
    ids = [f["id"] for f in plan["fragments"]]
    with store_pg.connect(runtime.dsn) as conn, conn.cursor() as cur:
        cur.execute("select pg_advisory_xact_lock(hashtextextended(%s,0))", ("current-v1/" + host,))
        cur.execute("select repo_locator from knowledge.host where host_id=%s", (host,))
        if cur.fetchone() != (plan["sourceRoot"],):
            raise ValueError("existing exact host binding required")
        cur.execute("select id::text,host_id,text,source,confidence::text,active from knowledge.fragment where id=any(%s::uuid[])", (ids,))
        old = {r[0]: r[1:] for r in cur.fetchall()}
        new = []
        for f in plan["fragments"]:
            if f["id"] in old:
                if old[f["id"]] != (host, f["text"], f["source"], "candidate", True):
                    raise ValueError("existing source fragment conflict")
            else:
                new.append(f)
        if apply and new:
            seq = store_pg.next_seq(cur, host, domain)
            cur.executemany("""insert into knowledge.fragment(id,host_id,alias,domain,seq,text,kind,confidence,source)
                values (%s,%s,%s,%s,%s,%s,'fact','candidate',%s::jsonb)""",
                [(f["id"], host, f"{domain}-{seq+i}", domain, seq+i, f["text"], json.dumps(f["source"], ensure_ascii=False))
                 for i, f in enumerate(new)])
    return {**plan["summary"], "host": host, "applied": apply, "new": len(new), "existing": len(old), "newRelations": 0}


def embed_missing(runtime, plan, *, progress=None):
    import embed
    import store_pg
    if embed.PROVIDER != "openrouter" or embed.MODEL_ID != "intfloat/multilingual-e5-large@openrouter":
        raise ValueError("approved embedding model mismatch")
    result = register(runtime, plan)
    if result["new"]:
        raise ValueError("apply source units before embedding")
    ids = [f["id"] for f in plan["fragments"]]
    generated = 0
    # Independent commits bound quota/storage failures. No unbounded retry; the
    # existing provider owns its bounded transport retry. Resume queries revisions.
    for offset in range(0, len(ids), 64):
        batch = ids[offset:offset+64]
        generated += store_pg.backfill_embeddings(runtime.dsn, plan["host"], variant="ctx-v1",
                                                   fragment_ids=batch, limit=len(batch))
        if progress:
            progress({"completedUnits": min(offset+64, len(ids)), "totalUnits": len(ids), "generatedVectors": generated})
    return {**result, "generatedVectors": generated}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "preview", "apply", "embed"])
    for key in ("receipt", "receipt-sha256", "ingestion", "bundle", "host"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--coverage-output", help="derived local coverage, no source bodies or credentials")
    args = parser.parse_args(argv)
    try:
        if args.coverage_output:
            target = Path(args.coverage_output).resolve()
            if not intake.inside(Path.cwd().resolve() / ".local", target):
                raise ValueError("coverage output must be target-local")
        auth, docs, _ = context(args.receipt, args.receipt_sha256, args.ingestion, args.bundle, args.host)
        plan = preview(auth, docs, args.receipt_sha256)
        result = plan["summary"]
        if args.command != "validate":
            import config
            from runtime_db import bind_runtime_db
            runtime = bind_runtime_db(config.require("db_url")["db_url"], provenance="configured-entry")
            if runtime.endpoint[0] in {"unix", "localhost", "127.0.0.1", "::1"}:
                raise ValueError("remote V2 target required")
            result = embed_missing(runtime, plan, progress=lambda p: print(json.dumps({"progress": p}), flush=True)) if args.command == "embed" else register(runtime, plan, apply=args.command == "apply")
        if args.coverage_output:
            target = Path(args.coverage_output).resolve()
            if not intake.inside(Path.cwd().resolve() / ".local", target):
                raise ValueError("coverage output must be target-local")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps({"summary": result, "coverage": plan["coverage"]}, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"ok": True, **result}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
