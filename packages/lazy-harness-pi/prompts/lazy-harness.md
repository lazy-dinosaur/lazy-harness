---
name: lazy-harness
summary: Lazy-harness record-first operating reminder for Pi Coding Agent.
---

# Lazy-Harness Prompt

Use the host-local `.lazy-harness` records as the source of truth before host-specific claims or mutations.

1. Run `.lazy-harness/bin/lazy map --overview --format=md --limit=20` first.
2. Pick a concrete feature id, record path, graph id, source path, or test path from that output.
3. Drill into that copied node with `.lazy-harness/bin/lazy map <copied-node> --format=md --limit=8`; never pass raw user text, long natural-language strings, or invented `--query` flags.
4. Read real record/source/test files before editing.
5. Validate proportionally. Do NOT run any validation command after each micro-edit. Finish a coherent mutation batch first; at a deliberate checkpoint run `lazy check` once, then run at most one focused/affected check per changed-behavior batch when needed. Run one `lazy validate --plan standard` only after the final mutation. Reserve direct `lazy test` for an explicit fresh full-regression request or commit/push/release gate. Do not run product-wide typecheck/lint/build just to "cover all bases"; only do that when the user asked, the host test-strategy record requires it, or product code changed.
6. Mutations are guarded by the lazy-harness Pi extension through the generic search/read evidence guard.
