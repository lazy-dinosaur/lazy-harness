# Discovery vs Loading — Rollout + Measurement (2026-06-24)

Status: active
Layer: Planning
Related ADR: `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`

## Context

ADR 0049 separates discovery (which records exist — mandatory, complete, lean) from loading (full record bodies — just-in-time, targeted). Target = 3-tier ladder catalog → digest → body. This record tracks rollout + measured results.

## Tier status (all three now in place)

- **Tier 0 — Catalog (discovery): DONE.** `lazy map --overview --complete` mandated across callsites (`on-message-received.sh`, `AGENTS.md`, `check-read-debt-permit.py`, `agent-activate.ts`, `retrieval-coverage-audit.ts`). Complete md ~6.7k tok, 215/215 records (100% catalog recall) vs truncated `--limit=20` ~4.6k tok / 52% recall.
- **Tier 1 — Digest filter: DONE.** Canonical Rule digest coverage 151/151 (100%) after backfilling 94 records (decisions 44, spec 20+10, tests 22, ssot 8) via parallel subagents + coordinator. Digests derived from each record body, Status from lifecycle (active / deprecated for superseded / reverted for 0008 / needs-review for proposed-or-legacy). self-test 87/87 green after backfill.
- **Tier 2 — Targeted loading: DONE (guidance).** `on-message-received.sh`: "read … only for records the task implicates (Rule digest first where present; do not read-to-cover-all-layers)".

## Measured results (token proxy bytes/4; per task = avg of 4 framework feature queries)

| Mode | Discovery | Loading | Total/task | Catalog recall |
|---|---:|---:|---:|---:|
| No-harness | 0 | 0 | ~0 | 0% |
| Previous (truncated overview + read-all-layers) | 4,646 | 72,561 | ~77,200 | 52% |
| Current targeted-body (complete + feature records) | 6,713 | 7,097 | ~13,800 | 100% |
| Current 3-tier (complete + digest, 100% cov, REAL) | 6,713 | 1,289 | ~8,000 | 100% |

- Targeted loading is the big lever: read-all-layers 72,561 → feature-records 7,097 (−65k/task).
- Digest tier is the secondary (now real, not estimated): targeted-body 7,097 → targeted-digest 1,289 (−5.8k/task). Digest = 15% of body where present.
- Net: previous ~77k/task → current 3-tier ~8k/task = ~90% reduction, while catalog recall 52% → 100%.

## Remaining (optional)

1. **Dogfood** the complete mandate + targeted/digest loading on a downstream host: confirm real-world token/latency and that agents actually follow targeted loading (the 90% is a proxy upper-bound gap; real per-task varies).
2. **Benchmark digest axis** — bake `followupDigestRead` into `retrieval-workflow-benchmark` now that coverage is 100%, so the 1,289/task is a tracked regression metric.
3. **`no_harness` zero baseline** in the benchmark for the harness-vs-no-harness delta.
4. **Downstream hosts backfill their own records later** (host-owned, separate from this framework-source backfill). Confirmed scope: framework source backfilled now; each host project backfills its `.lazy-harness` records on its own schedule.

## Record quality enforcement (digest durability)

Done 2026-06-24 (closes the decay gap found in inspection):
- `record-write-update-policy.md` already mandates authoring `## Rule digest` on reusable records (self-test-protected).
- AGENTS.md §2.4 now surfaces the Rule digest mandate alongside Implementation map (was Implementation-map-only — the asymmetry that let coverage decay to ~37%).
- `record-audit.ts` adds a `missing-rule-digest` advisory code for canonical reusable records (domain/spec/behavior/tests/decisions/ssot, excluding README); 0 after backfill.
- fingerprint overview-amortization REVERTED: unsafe under symlinked worktrees / multi-session (relies on LLM hash-memory + risks reusing a stale catalog = silent-skip vs `default=모름`).

Done 2026-06-24 — `lazy record-lint` built (`.lazy-harness/scripts/record-lint.ts` + bin/lazy + SDD `spec/platform/record-lint.md` + TDD `tests/record-lint.md`): validates canonical records for digest presence, valid Status/Layer/Scope enums, Layer-path match, Applies-when/Must bullets, and broken `.lazy-harness/...md` refs (code fences excluded; `...` placeholders skipped). ENFORCED at the commit/push gate via self-test `check_record_lint_cli` (framework must be 0) — runtime-agnostic, NOT a dev-time hard gate (ADR 0016/0041/0048). record-audit keeps the advisory `missing-rule-digest` dashboard. Initial audit found 43 issues (13 non-enum statuses, 5 missing-layer, 1 bad-scope, 1 missing-applies-when, 23 broken refs); all cleaned to 153/153 clean. Downstream: record-lint.ts auto-syncs via the `scripts/` Category A glob; the `lazy-record-quality` guided skill ships in `packages/lazy-harness-pi/skills/` and installs with `lazy pi install` / `lazy omp install` (NOT Jcode — this host does not use Jcode).

## Non-goals

- No change to option-gate / read-debt / mutation-guard policy from ADR 0049.
- No conditional/skippable discovery (rejected: violates `default=모름`).
