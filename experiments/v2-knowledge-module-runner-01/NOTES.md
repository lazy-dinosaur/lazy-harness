# Work-unit baseline 0004 (local draft)

The optional baseline stores a host-scoped history cursor, capture time and optional Git ref. Changed add facts are rejudged with a freshly searched current-canon excerpt; target revisions still use CAS. Changed code evidence blocks acceptance until its source is reconciled; missing Git/ref remains unknown rather than unchanged. Existing null-baseline units remain legacy. No remote migration or paid evaluation was run.

# DB polling digester

`poller.py` acquires a dedicated PostgreSQL session advisory lock for one tick, then processes oldest completed/eligible units, proposed entries, and missing plain/ctx-v1 vectors in that order. All queue state remains in PG; atomic local retry hints (exponential backoff/stuck) can be deleted to resume. `store_pg.digest` and `store_pg.batch` each commit their DB writes in one transaction; injected Jev calls run outside those write transactions and may repeat after interruption (cost only). `check_receipt.dedup_key` is unique. A transient embedding outage leaves accepted fragments pending for later backfill. No timer was installed or paid call made.

# Worktime driver

`worktime_driver.py` injects a judge into proposed-entry microbatches; failed items stay proposed. The packet questions reuse `first-load-01/prep.py:TEMPLATE` (matching the migration seed). Update uses the seeded intent wire; deprecate lacks a complete seeded wire and raises `NotImplementedError`. The optional utterance verdict is returned but `store_pg.batch` does not persist it; digestion requires a fresh verdict when needed. No scheduler or paid judge was run.

# Completion-gated digestion

A one-shot driver checks completion before judging, refreshes update/deprecate target text and revision, and delegates the final transactional acceptance to `store_pg.digest`. Repeated or concurrent calls return noop after the first absorption. Completion signals are AND-gated and idempotent; abandonment expires unswallowed entries. The current work_unit_event schema has only a `source` text field, so signal evidence is retained on `work_unit.completion_sources` rather than on the append-only event row. No actor scheduler or network call is installed by this change.

# Module assembly 01

Fragment assembly imports the experiment checker as its single validation authority, retries injected calls, and keeps per-attempt raw hashes/validation without promoting failures. The Jev judge extracts the pilot's two-attempt score validation into an injected HTTP callable, uses model-bearing packets and exposes selected judgements. The CLI now offers Jev or oracle collection, operation-aware decide, and model-required call. Local unit and regression coverage was added; no actual Jev/LLM calls are required for tests. Isolation for actual fragment-generation calls remains an external caller obligation.

# Embedding outage policy

The digest transaction still commits accepted fragment/receipt/absorption changes when the local encoder is unavailable. Only vector encoding is skipped, with `embedding_pending=true` in the digest result. A future `backfill_embeddings` repairs missing/stale vector revisions. Rolling back confirmed knowledge solely because an optional local search accelerator is offline would lose the primary result. Database upsert failures are not swallowed: they roll back the transaction, preserving atomic database writes. `_infer` in `embed.py` remains exclusively as the offline original-algorithm parity oracle in tests; production calls only use the HTTP resident model.

The `0003` migration is a local draft and must not be applied outside the isolated test container without separate user approval.

# Local cutoff measurement

The 500-document set has 56 supported and 8 unsupported questions. Gold cosine: min .8476, median .9064, max .9445; highest non-gold candidate per supported question: min .8327, median .8845, max .9442. Candidate thresholds and exact counts are in `test_embed_server.log`. Of the measured candidates, .89 is the highest preserving 54/56 all@5 (no cutoff: 54/56; .90: 53/56). This is a vector-candidate cutoff, **not an abstention rule**: trigram text scoring still returns 15/15 for all eight unsupported questions at every threshold. At .89 the seven real queries return only the text matches (six top-1 retained); the text-miss `작업 목록은 어디 저장해?` is now empty. This trade-off requires explicit review before production adoption. Previous complete run: 158.72s; this run: 54.36s (`python3 -m pytest -q`). Container and embedding process are removed by fixtures.


# Topic collection / context variant

`ctx-v1` preserves fragment.text unchanged. For embedding only, the passage encoder receives
`passage: [kind=<kind>; domain=<domain>; siblings=<text>] <body>` (the service adds `passage: `).
Sibling text is from up to three active fragments in the same host/group, ordered by UUID,
each truncated to 80 characters and the joined text truncated to 160 characters. No group
means empty siblings. All context comes from stored DB rows; no LLM or external API.
Plain and ctx-v1 vectors have independent keys and revision checks. After changing a group
member, backfill ctx-v1 for that host to refresh context of its siblings; ordinary revision
checks alone cannot detect changed sibling context. Collection's oracle is a fixture only:
`judge(query, candidates) -> [{"relevant": bool, "novel": bool}, ...]` in candidate order.
Candidates are dicts with id (UUID string), host_id, text, kind, group_id, score, ranks,
and evidence_quote. `collect --oracle` accepts a JSON array of gold UUID strings; explicit
`collect --judge jev` uses the injected Jev judge (network only when called). Default cosine cutoff is off; callers may opt in explicitly.
