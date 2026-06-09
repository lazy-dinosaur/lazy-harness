---
name: lazy-harness
summary: Lazy-harness record-first operating reminder for Pi Coding Agent.
---

# Lazy-Harness Prompt

Use the host-local `.lazy-harness` records as the source of truth before host-specific claims or mutations.

1. Run `.lazy-harness/bin/lazy map --overview --format=md --limit=20` first.
2. Drill into relevant records with `.lazy-harness/bin/lazy map '<token>' --format=md --limit=8`.
3. Read real record/source/test files before editing.
4. Mutations are guarded by the lazy-harness Pi extension through the generic search/read evidence guard.
