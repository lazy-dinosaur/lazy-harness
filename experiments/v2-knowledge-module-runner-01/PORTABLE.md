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
| 23 numbered SQL assets | Schema/functions and generic question seeds, including 0001 used by `templates._seed`; no real host/fragment/ledger export and no SQL application. |
| Inactive extension | File-relative CLI resolution, existing V2 tools/contracts retained; no package attachment or SDK upgrade. |
| `scale-03/measure/{run_mapreduce,judge_measure}.py` | Public **synthetic-only adapters** for inherited estimate/resume/chunk/score mechanics. Live CLI fails closed before config/data imports. Original private/paid orchestration, HTTP retries and automatic estimated financial reconciliation are not distributed. Synthetic costs are test inputs, not provider billing. |
| Explicit offline tests | Synthetic fixtures only; private lineage UUIDs/aliases replaced, namespace passed explicitly. No inherited service-starting conftest, installed original PYTHONPATH or private before/plan/raw fixtures. |
| Stable protocol identifiers/model pins | Schema-version strings, deterministic UUID namespaces, image/model identities and generic endpoint defaults are code contracts, not captured business records or active credentials. |

Excluded: actual private catalog/source copies, `knowledge.json`, `dsn.local`, `.local`, raw model output, financial/usage ledgers, source snapshots, vector/model caches, installation backups, `node_modules`, prototypes and frozen originals. G16 adds only the exact code/SQL/synthetic fixture paths listed in `portable_source`, never a wholesale `scale-04` copy. No broad secret-scanner certification or original frozen14 byte-equality claim.

## Reproducible offline acceptance

Run `python3 test_publication_bundle.py` from this directory or by explicit path. The coordinator uses read-only Git metadata to build two deterministic bundles, verifies/extracts into a fresh unrelated temporary tree and launches only explicit Python/Bun test workers. Python workers use `-I -B`, empty fixture HOME/cwd, standard-library-only inert DB modules, filesystem-open audits and denied network/process/DB effects. Private HOME/auth and outside-source canaries must fail. The TS loader test transpiles against a passive schema/host seam and captures a single CLI invocation without executing Python or any SDK/lifecycle hook. Neither seam is a real provider.

The extracted suite covers maintenance skip/code/clause guards, preview, subject-host locking and revision CAS, conditional parser success/failure, default-whole-document and opt-in map/reduce behavior, uncertain/unknown cost holds, 70-question/three-run synthetic budget/resume mechanics, chunk scoring, archive traversal/link/duplicate/missing/tamper denial, source authority, exact citations and immutable runtime DB routing. No PostgreSQL, financial, actual trial, managed SDK or native Pi/OMP certification follows from these checks.

Main's framework validation and source-only offline checks do not certify managed SDK1.3, native Pi/OMP parity, PostgreSQL correctness, financial accounting or an actual trial. Keep those outcomes distinct in the publication primary.

## G16 repository-shaped source closure

`portable_source.py build --repository --output <ignored-local-path>` selects `REPOSITORY_ALLOWLIST`: the exact module allowlist under `experiments/v2-knowledge-module-runner-01/` plus explicit Native source/tests under `experiments/v2-native-minlive/`. `verify` and `extract` require the matching `--repository` profile. The module-only layout remains for V2 compatibility; Native requires the repository shape. Archive membership/digests stay strict in either profile.

G16 adds domain-scoped subjects/aliases/parents, typed identity/write/validation receipts, model-bound embedding/cache/admission and top-K routing, unit-first writing/grounding and dynamic host source. Numbered SQL is exactly 0001–0023 in runtime order; apply-form alternatives are not additional migrations. `local_db.migration_paths` shares the loader's ordered asset list; a fake asset consumer is not a PostgreSQL engine. Migration 0023 must exist for rejected-write diagnostics; no automatic restore migration is authorized.

The public caller, catalog and inventory are explicitly **synthetic-only**. `write_confirmed(plan, home, approval)` preserves exact digest, isolated home, both plan identities and conflicting-catalog refusal; ten neutral fixture areas are not business approval. `prepare.inputs` requires explicit `LH_G16_FIXTURE_MANIFEST` selecting the distributed synthetic manifest. Private baselines are explicitly unavailable, not recreated. Synthetic carry values are not original balances or runtime admission. Original source/plan hashes and original before/receipt manifests are not distributed.

Actual `jev_failure.py` is published as received-error/receipt-check source, not approved financial runtime provenance. HTTP status/error self-report cannot establish zero cost. `Paid`, financial resolution/release, production construction, Docker and non-prepare pipeline entry fail closed before live effects. A separately attested Native controller retains its independent exact external Trust/quote/history/admission gates; the fixture caller cannot provision a live lease. No automatic grants, refunds, zero-price defaults or replay rights are supplied.

Supervisor entrypoint: `python3 experiments/v2-knowledge-module-runner-01/test_g16_publication.py` from the repository root (or by absolute path). It creates an exact fresh repository extraction and runs focused G16/import/SQL/catalog/financial probes, inherited synthetic caller compatibility, V2 offline suites and JS host/broker fixtures from unrelated cwd/empty HOME. Python denies private opens and network/process/DB effects except the caller's two exact reviewed Node fixture commands; JS uses injected fake runtime/transport with no model discovery. Broader legacy owned-process tests remain published but are not claimed as covered by this restricted focused batch. No test/check/validation was run by the source writer; all results remain supervisor-owned pending gates.
