# TDD — Experimental V2 public source relocation

## Rule digest

- Status: active
- Layer: TDD
- Scope: host-project
- Aliases:
  - V2 public relocation probes
  - source-only V2 offline checks
- Applies when:
  - relocating or publishing the experimental V2 source copy
- Must:
  - run source-only tests with synthetic inputs, isolated HOME and unrelated cwd
  - reject unapproved process, database and network effects
  - retain unknown usage, reserved-call no-replay, host/root/quote and runtime-routing guards
- Must not:
  - report fake SQL/import checks as PostgreSQL, native SDK, financial or actual-trial success
  - execute legacy service-starting pytest fixtures during source-only publication
- Related records:
  - `.lazy-harness/spec/v2-knowledge-module-schema-delta.md`
  - `.lazy-harness/planning/repository-publication-review.md`

## Protection and current evidence

The initial checkpoint's 13 tests/0.837s remain historical, not publication completion. Final acceptance entry is `python3 experiments/v2-knowledge-module-runner-01/test_publication_bundle.py`. It builds two deterministic checksum-bound bundles and tests a fresh extraction with unrelated cwd and empty HOME, no original PYTHONPATH or installed runtime SDK. Each of nine explicit Python suites runs in a separate `-I -B` worker with inert DB modules, filesystem-open audits, private HOME/auth/outside-source denial canaries and denied network/process/driver effects. The coordinator alone launches these fixture workers and Bun plus read-only Git metadata commands. No dependency installation, inference, native runtime, PostgreSQL, Docker or product CLI execution is involved.

Protected cases include the initial runtime/SQL/config/query/source/routing/whole-document/reservation boundaries; inherited runtime DB, execution-scope, source-review gate, correction-receipt, hint-rebind and lineage protections; maintenance code/clause/partial-overlap/preview, host-lock and stale-revision-CAS cases; conditional cleanup parser success and writer failure; default/opt-in map/reduce, parallelism and cleanup, unknown usage, synthetic 70-question/three-run budget/resume, nonfinite/negative/unknown cost and ambiguous-call holds; synthetic chunk score mapping. Lineage tests use synthetic IDs/aliases and explicitly selected namespace, never captured private row payloads. Live measurement/judging entry points reject absent explicit synthetic adapters before private configuration or data imports.

The exact allowlist includes all needed runtime modules, maintenance/parser helpers, 18 inert SQL assets, inactive extension and public tests. The manifest rejects traversal, links, duplicate/missing/tampered members and wrong digests. SQL 0001 is loaded through `templates._seed`, not a fake Postgres claim. The JS relocation test transpiles the existing extension with a passive host/schema seam, verifies registration has no effects and captures one file-relative CLI call preserving caller cwd/host; no SDK, Python process or lifecycle activation occurs.

Final check counts/durations and actual commit/remote equality are reported by the terminal publication run, not baked into a self-referential evidence commit. Limits remain PostgreSQL semantics, live financial/provider approval, managed SDK1.3/native Pi/OMP compatibility and original frozen14 byte-equality: none is certified by these source checks. G16 and its additional closure stay separate. Legacy service-starting pytest fixtures and real business source/plan/ledger/raw/model inputs are deliberately excluded, not silently executed or declared green.

## Layer completeness matrix

| Layer | Judgment |
|---|---|
| SDD | Independent explicit diagnostic/query/lineage namespace, synthetic measurement adapter and source-package asset boundaries; captured in `.lazy-harness/spec/v2-knowledge-module-schema-delta.md`. |
| BDD | No independent visible product flow; no runtime/extension activation. |
| SSOT | No independent configuration ownership/default delta; private configuration and existing DB/source bindings remain authoritative. |
| DDD | No independent business/domain-rule delta; fixtures are synthetic and confer no business approval. |

## Implementation map

- `experiments/v2-knowledge-module-runner-01/test_public_relocation.py#PublicRelocation`: direct synthetic suite.
- `experiments/v2-knowledge-module-runner-01/portable_probe.py#probe`: early config and explicit query boundary.
- `experiments/v2-knowledge-module-runner-01/portable_source.py#inventory`: explicit Python/SQL/loader source closure candidate.
- `experiments/v2-knowledge-module-runner-01/runtime_db.py#RuntimeDBContext`, `source_evidence.py#read_reference`, `config.py#source_authority`: retained boundaries exercised by the suite.
- `experiments/v2-knowledge-module-runner-01/brief.py#brief`, `current_v1_recovery.py#reserve`, `source_correction.py#is_verified_correction`: whole-document/unknown-usage/no-replay/capability protections.
- `experiments/v2-knowledge-module-runner-01/test_publication_bundle.py#PublicationBundle`: clean extraction, manifests, denial workers and inert JS loader orchestration.
- `experiments/v2-knowledge-module-runner-01/test_brief_mapreduce_offline.py#MeasurementOffline`: inherited scoring/resume mechanics via synthetic-only adapters, no accounting fallback.
- `experiments/v2-knowledge-module-runner-01/cleanup.py#run`, `backfill_structure.py#apply`, `merge_guard.py#code_missing`, `reopen_duplicates.py#classify`: synthetic maintenance tests in `PublicRelocation`.
- `experiments/v2-knowledge-module-runner-01/fragmenter/check_fragments.py#parse`: conditional cleanup dependency with success/failure probes.
- Explicit inherited offline suites: execution scope, runtime DB isolation, source-correction receipts, source-hint rebinding, source-review gates and lineage scope/provider mapping. Each runs separately to prevent global mock/module state contamination.
- Governing primary: `.lazy-harness/planning/repository-publication-review.md`.

## Discovery capture / Rule placement

This is the existing V2 source-review TDD path, sanitized for publication. Further relocation evidence belongs here or in the primary capsule; private command manifests/logs stay ignored. No broad legacy graph/cache migration or duplicated operational policy is part of this work.
