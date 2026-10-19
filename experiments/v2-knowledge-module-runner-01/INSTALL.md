# V2 source requirements and installation boundary

This public copy supplies source, not a configured or installed runtime. Installation, authenticated Pi execution, provider requests, PostgreSQL/SQL application, model downloads and service activation need their own explicit scope and approval. Do not run them as publication checks.

## Requirements (not installed by this document)

- Python >=3.12; `psycopg` or `psycopg2` for PostgreSQL-backed imports. Offline tests must inject DB/model seams and must not open a database.
- A separately provisioned PostgreSQL environment with pgvector/pg_trgm for live use. The stacked G16 source contains 23 ordered numbered SQL assets in `migrations/`; do not combine numbered migrations with historical alternative apply forms. No alternative apply forms, applied receipts, dumps or actual state are included in this source package.
- Optional local E5 service: the model/tokenizer pins are in `embed.py`; ONNX Runtime, NumPy and tokenizers are external dependencies. No weights, model venv, calibration evidence or inference output is included.
- Optional remote embedding/Jev: existing private configuration and separately approved provider profile, limits and financial authority. Source defaults and example placeholders are not permission to call a service.
- G16's asynchronous embedding transport additionally depends on `httpx`; import-only/fake public checks do not install it or authorize an HTTP request. Optional calibration/financial runtime evidence is not included. See `PORTABLE.md` for synthetic-only and fail-closed boundaries.
- Optional Pi extension: existing compatible authenticated runtime and separately approved project attachment. Do not upgrade Main/global SDK to satisfy a prototype. Main's source baseline remains 0.85.1; managed SDK1.3 is an unvalidated compatibility boundary, not a passed gate.

## Configuration ownership

`config.py` resolves environment overrides, then a private JSON file, then code defaults. Use `knowledge.example.json` only as a shape example, never as credentials or an approved host. A real configuration file must be owner-only (0600). `LH_KNOWLEDGE_CONFIG` can select an explicit file; otherwise the V2 namespace is used. Never reuse V1 settings/services or expose real configuration in Git or logs.

A source authority requires an explicit per-host root; root/host overrides form an atomic pair. Import manifests must stay inside that root and preserve their exact hashes. A runtime DB context binds endpoint/database/user once and rejects ambient PG routing and later target substitution.

No deployment units are installed or enabled by this publication. The lifecycle, resource lease, cleanup and rollback plan belong to a separately approved runtime operation. Use isolated synthetic inputs for offline verification; public fixture confirmation is not real business approval.
