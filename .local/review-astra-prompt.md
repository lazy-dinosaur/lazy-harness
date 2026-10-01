You are reviewing a design + implementation (read-only: use read/grep/find/ls only, change nothing). Answer in Korean.

Project: lazy-harness v2 knowledge module, repo root = current directory.
Code: experiments/v2-knowledge-module-runner-01/ — fact_form.py, fact_text.py, subject_dict.py, merge_form.py, dedup.py,
knowledge_cli.py (record, contradictions), digest_driver.py (run_digestion, _subject_domain), store_pg.py (digest,
_canon_duplicate, _leaf_pairs, scan_contradictions, review_list, review_resolve, _reopen, _write_form, _assign_subject),
migrations/0009_subject_dictionary.sql, migrations/0010_fact_form.sql, pi-extension/knowledge.ts.
Design decisions: .lazy-harness/spec/v2-knowledge-module-schema-delta.md lines 55-80 (items dated 2026-09-30 .. 2026-10-01).
Measurements and open problems: .lazy-harness/planning/v2-knowledge-module-open-gaps.md from the line starting
'### 문장 구조 저장 시험 1~5차' to the end (pilots, contra02-05, render-ko-01, search-b2, flow3 runs).

Goal of the system: a parent LLM records atomic knowledge facts into a temporary ledger; a single digester applies them
to a canonical store; facts are Korean leaf sentences joined by English operators (IF/THEN/AND/OR/EVEN IF/EXCEPT
WHEN/BEFORE/AFTER/BECAUSE) and stored with a parsed structure (form, fragment_leaf); a host-wide subject dictionary;
the user is asked only about contradictions and conflicts; Jev (a cheap judge model) is used for judgements.

Review questions (be concrete: file:line, scenario, why it is wrong, what to do instead):
1. Places where we solved something with heuristics / regex / LLM calls although the stored schema (form, leaves,
   subject_id, expected_revision, history) already allows an exact or cheaper solution.
2. Logic bugs or race conditions: digestion transaction, stale-base merge, 'unit = one commit', review_resolve/_reopen,
   superseded-in-unit 'last record wins', subject registration only at digestion, contradiction logging/closing.
3. Places where data can be silently lost or wrong canon can stay (e.g. flow3 runs: mixed 300/800/1000 values left,
   contradictions missed because subjects differ).
4. Design drift: anything that contradicts the stated principles (ledger records are commands; ask the user only
   contradictions/conflicts; digester is the only canon writer; atomic facts; Korean is a view only).
5. Over-engineering or steps that add cost/complexity without measured benefit.
Give a prioritized list (P0/P1/P2) of at most 15 findings, then a short overall verdict. Do not restate the design.