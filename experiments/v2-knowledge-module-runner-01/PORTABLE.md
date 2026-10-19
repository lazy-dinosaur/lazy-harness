# Source-only portability

`portable_source.py` uses an explicit path allowlist, rejects symlink/oversize sources, verifies archive membership and file digests, and extracts only into a new destination. The inventory includes conditional local Python modules and inert runtime SQL seed assets. A Python AST check is only an additional missing-import check, not proof of JS/SQL/live-runtime closure.

Building, verifying and extracting a source bundle must use an explicitly selected local output under ignored scratch. Never add the archive, SOURCE-MANIFEST, a private config, model directory, corpus, ledger, source snapshot, database dump or generated runtime report to Git. Bundling source does not apply migrations, attach extensions, configure services or authorize model/DB effects.

The optional `portable_probe.py` is a **live diagnostic**, not an offline publication test. It requires an explicit private config and exact registered remote host. A vector probe additionally requires a caller-supplied, separately approved query (`--vector --query ...`); the public source contains no business query. Missing configuration is rejected before loading configuration-backed dependencies. Do not execute it during publication.

## Explicit publication and content-safety manifest

`portable_source.ALLOWLIST` is the exact per-file publication/bundle list; `RUNTIME`, `MIGRATIONS` and `PUBLIC_TESTS` enumerate its categories. Only the publication primary, V2 SDD/TDD and append-only verified graph links accompany these experiment paths in Git. A bundle's generated manifest binds each path, byte count and SHA-256 to the selected base revision; it is private test output, not a committed corpus or release.

| Selected source | Safety disposition |
|---|---|
| Root runtime Python, including cleanup/reopen/backfill/merge guards | Generic implementation retained; no configuration, credentials, actual data or operational receipts. Live entry points are not invoked by publication. |
| `fragmenter/check_fragments.py` | Conditional cleanup parser/repair helper included; model generation still requires independent authority. |
| 18 numbered SQL assets | Schema/functions and generic question seeds, including 0001 used by `templates._seed`; no real host/fragment/ledger export and no SQL application. |
| Inactive extension | File-relative CLI resolution, existing V2 tools/contracts retained; no package attachment or SDK upgrade. |
| `scale-03/measure/{run_mapreduce,judge_measure}.py` | Public **synthetic-only adapters** for inherited estimate/resume/chunk/score mechanics. Live CLI fails closed before config/data imports. Original private/paid orchestration, HTTP retries and automatic estimated financial reconciliation are not distributed. Synthetic costs are test inputs, not provider billing. |
| Explicit offline tests | Synthetic fixtures only; private lineage UUIDs/aliases replaced, namespace passed explicitly. No inherited service-starting conftest, installed original PYTHONPATH or private before/plan/raw fixtures. |
| Stable protocol identifiers/model pins | Schema-version strings, deterministic UUID namespaces, image/model identities and generic endpoint defaults are code contracts, not captured business records or active credentials. |

Excluded: actual private catalog/source copies, `knowledge.json`, `dsn.local`, `.local`, raw model output, financial/usage ledgers, source snapshots, vector/model caches, installation backups, `node_modules`, prototypes and frozen originals. No wholesale `scale-04` copy; G16 is separate. This is not a broad secret-scanner certification or an original frozen14 byte-equality claim.

## Reproducible offline acceptance

Run `python3 test_publication_bundle.py` from this directory or by explicit path. The coordinator uses read-only Git metadata to build two deterministic bundles, verifies/extracts into a fresh unrelated temporary tree and launches only explicit Python/Bun test workers. Python workers use `-I -B`, empty fixture HOME/cwd, standard-library-only inert DB modules, filesystem-open audits and denied network/process/DB effects. Private HOME/auth and outside-source canaries must fail. The TS loader test transpiles against a passive schema/host seam and captures a single CLI invocation without executing Python or any SDK/lifecycle hook. Neither seam is a real provider.

The extracted suite covers maintenance skip/code/clause guards, preview, subject-host locking and revision CAS, conditional parser success/failure, default-whole-document and opt-in map/reduce behavior, uncertain/unknown cost holds, 70-question/three-run synthetic budget/resume mechanics, chunk scoring, archive traversal/link/duplicate/missing/tamper denial, source authority, exact citations and immutable runtime DB routing. No PostgreSQL, financial, actual trial, managed SDK or native Pi/OMP certification follows from these checks.

Main's framework validation and source-only offline checks do not certify managed SDK1.3, native Pi/OMP parity, PostgreSQL correctness, financial accounting or an actual trial. Keep those outcomes distinct in the publication primary.
