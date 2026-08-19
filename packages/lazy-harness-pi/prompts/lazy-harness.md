---
name: lazy-harness
summary: Lazy-harness record-first operating reminder for Pi Coding Agent.
---

# Lazy-Harness Prompt

Use the host-local `.lazy-harness` records as the source of truth before host-specific claims or mutations.

1. At the start of a new work unit, run one `.lazy-harness/bin/lazy map --overview --complete --format=md`, drill into one copied concrete node, and read only the governing digest plus exact linked source/test needed before mutation or a host-specific completion claim.
2. Reuse unchanged governing-record evidence across later normal messages. Do not rerun overview/map/read because another turn started; re-ground only for a new session, real scope change, explicit steer, or changed/deleted governing record.
3. Never pass raw user text, long natural-language strings, or invented `--query` flags to `lazy map`; map/index output is navigation, not read proof.
4. Finish a coherent mutation batch before validation. Run `lazy check` once at a deliberate checkpoint, at most one focused/affected check per changed-behavior batch, and one final `lazy validate --plan standard`. Reserve direct `lazy test` for explicit fresh regression or commit/push/release gates.
5. Keep green validation output to status/count/time; store detailed logs outside the conversation. Mutations remain guarded by the first-grounding evidence gate.
