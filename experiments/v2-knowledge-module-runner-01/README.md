# Experimental V2 knowledge module — source review

This directory is an isolated experimental source publication, not Main activation or a release. It preserves V2's distinct domain routing, configured Pi brief writer, host/source authority and immutable runtime-DB binding. G16 is a separate stacked review branch, not a replacement for V2.

## Boundaries

- `knowledge_cli.py` is the worker entry; `poller.py` owns worktime review/digestion. Registration is not completion; a question is not user confirmation; source review is not a human answer. Subject merges require the protected user-answer workflow. Fragment revisions/history and exact host/source bindings remain authoritative.
- `brief.py` defaults to one whole-document writer call; map/reduce is explicitly opt-in. Writer usage may be unknown, never inferred free. `embed.py` supports local pinned E5-small and configured OpenRouter E5-large. Configuration and provider/model identity must match the stored corpus. Publication does not select or activate a provider.
- `current_v1_*`, `semantic_plan.py` and `lineage_*` consume separately trusted, hash-bound inputs; no receipts, source snapshots, original ledgers or corpus are distributed here. Their fixed cohort/budget protections are not grants for a new job. Old pending/unknown reservations are not reset or replayed.
- The Pi extension is inert source until explicitly attached. Do **not** attach it in an offline test: lifecycle handlers can invoke configured source review. Its existing SDK requirements are independent of Main's 0.85.1 development baseline; managed SDK1.3/native compatibility is not certified by this publication.
- Numbered SQL files are source assets, not an applied schema or proof of PostgreSQL correctness. `templates.py` reads migration 0001 at runtime. No database, Docker, inference, embedding, real receipt handling or policy activation is authorized by source publication.

## Navigation

- `config.py`: private per-host configuration and explicit atomic source root/host override.
- `runtime_db.py`: immutable endpoint identity; ambient PG routing is rejected.
- `source_evidence.py`, `source_review.py`, `source_correction.py`, `source_generation.py`, `source_metadata_repair.py`: exact root/source proofs, semantic verification and protected correction/metadata boundaries.
- `store_pg.py`, `worktime_driver.py`, `digest_driver.py`, `subject_dict.py`, `subject_merge.py`: persistence/review/digestion and host-scoped subject ownership.
- `cleanup.py`, `merge_guard.py`, `reopen_duplicates.py`, `backfill_structure.py`: distinct V2 maintenance signatures retained, preview/dry-run and protected host/revision ownership; no G16 replacement.
- `scale-03/measure/run_mapreduce.py` and `judge_measure.py`: synthetic-only public fixture adapters, live orchestration explicitly unavailable. They do not reconcile unknown financial charges or activate any provider.
- `test_publication_bundle.py`: fresh clean extraction plus isolated Python and inert JS-host acceptance; see the content-safety manifest in [PORTABLE.md](PORTABLE.md).
- `portable_source.py`: explicit source-only package inventory and checksum-bound extraction. See [PORTABLE.md](PORTABLE.md).
- [INSTALL.md](INSTALL.md): requirements and non-execution preflight, not an installation grant.

The publication primary is `.lazy-harness/planning/repository-publication-review.md`. No personal operational logs or prior live results are source fixtures.
