# Operating Rule Storage + Apply Repair — 2026-06-24

Status: active-implementation
Layer: Planning
Date: 2026-06-24
Supersedes (repair direction): `.lazy-harness/planning/project-rule-adaptation-regression-audit-20260610.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related ADR: `.lazy-harness/decisions/0044-project-operating-rulebook.md`
Related ADR: `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SSOT: `.lazy-harness/ssot/rule-lifecycle.md`
Related SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`
Related TDD: `.lazy-harness/tests/project-operating-rulebook.md`

## Trigger

User report (2026-06-24), dogfooded on a downstream host: operating rules are neither **stored** correctly nor **applied** correctly.

```text
저장도 제대로 안되는거고 제대로 따르지도 않고 있는거야 ... 제대로 다시 구현해야해
```

Concrete observed failure (downstream host): an agent re-derived a PR-body rule that already existed in `.lazy-harness/ssot/pr-description-format.md` + a `capabilities.json` binding, wrote a duplicate into an unrelated SSOT (`pr-worktree-first-workflow.md`), and PRs kept being drafted without the required body format.

This is the same theme the user raised on 2026-06-10 ("프로젝트마다 다른 규칙들이 ... 유연하게 변형될수 있는게 목표인데 왜이렇게됬지?"), but the 2026-06-10 audit pre-dates ADR 0044/0046 and its repair plan is stale (see "Stale plan delta").

## Confirmed scope (user-confirmed)

- Fix the lazy-harness **framework** so the same problem does not recur in host projects; propagate via `lazy sync`/`lazy update`.
- Restore the **adaptation bridge** (audit Phase 4/5 intent) **and** close the **storage** hole. Both halves.
- Stay organic per ADR 0041: advisory + grammar + deterministic label matching. **No new hard gate**, no tool-specific policy, no revived `rule-bindings.json`/`check-rule-action-boundary` enforcement, no revived `lazy find --purpose` pre-turn query backend.
- **R3 excluded** (user-confirmed): `on-message-received.sh` stays fully static transport. Pre-response auto-surfacing of concrete rules is intentionally not added because it would require reviving a retired pre-turn resolver backend (ADR 0041 Phase 7).

## Root cause (verified at code level, 2026-06-24)

Two halves, both from concrete wiring defects — not merely "design too soft".

### Storage (저장) — wrong-place / duplicate undetected
- `.lazy-harness/hooks/lifecycle/helpers/check-project-rule-placement.sh` exits 0 on the FIRST write matching `LAZY_CAPTURE_RE` to ANY `.lazy-harness/<layer>` (lines ~177-183). It only guards `.jcode`/Jcode-memory over-routing and same-response placement-block duplication. It does NOT detect operating-rule semantics written to a wrong/non-canonical surface inside `.lazy-harness`, nor duplication of an existing policy/capability.
- Canonical store for operating-rule semantics is `ssot/policies.json` (+ `ssot/capabilities.json` for action binding); `rules/**` is a demoted compatibility/explain surface (ADR 0046, `retiredCanonicalSemantics=true`). Nothing steers an operating-rule write toward the canonical store.

### Apply (따르기) — misses never flagged
- `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py:missed_discouraged_action` only fires for capabilities at level `warn`/`block` (line ~449). The seed `project-operating-rulebook` capability is level `discover`, and downstream hosts commonly register operating rules at `default` — so the apply-time advisory never fires for them.
- Pre-response is static (no concrete rule surfaced). With R3 excluded this is accepted; apply relies on (a) the agent calling existing `lazy ... resolve` (grammar) and (b) the post-response advisory.
- The existing generic pre-action guard (`on-tool-execute-before.sh` → `check-read-debt-permit.py`) already forces *some* root-bound search before mutation, but it is not operating-rule specific.

### Benign drift (do NOT "fix")
- `check-response-rule-audit.py:63` SEARCH_DEBT_LEVELS excludes `harness-first-static` while `check-read-debt-permit.py:47` includes it. Git history (`e8b9f37` then `3f5a827`) shows both started in sync and the static-transport refactor added the level to the permit only. This exclusion is **correct**: `harness-first-static` is written every turn unconditionally, and the audit's search-evidence branch (line ~561) is NOT mutation-gated, so including it would fire on every read-only turn. The permit is action-gated, so it is safe there. Action: document, do not change.

## Stale plan delta (2026-06-10 audit vs current structure)

| 2026-06-10 phase | Current status | Action |
|---|---|---|
| Define `Project Rule Application` SDD | function absorbed by `policy-machinery-v2.md` + ADR 0046 | do NOT create a new SDD |
| Revive `rule-bindings.json` machine applicability | superseded; capabilities.json/policies.json carry it | do NOT revive |
| Register ops rules as capabilities | mechanism implemented (kind/level + preferred/discouraged) | reuse as-is |
| Improve pre-response surfacing (Phase 4) | static by design; auto-surfacing = retired backend | EXCLUDED (R3) |
| Middle-rung warn/default (Phase 5) | warn-only post-response on explicit policy_context | repaired via R1 default-level firing |
| Downstream fixtures (Phase 6) | warn-level worktree fixture exists; default-level missing | extend (R6) |

## Repair phases (current structure, ADR-0041-compliant)

### R1 — apply-audit repair
- `check-response-rule-audit.py:missed_discouraged_action`: fire for level in `{default, warn, block}` (was `{warn, block}`). Keep `discover`/`recommend` silent (level semantics preserved; `lazy-evidence-capsule` stays recommend/non-blocking).
- Add a clarifying comment at the SEARCH_DEBT_LEVELS definition documenting the intentional `harness-first-static` exclusion (benign drift above). No runtime change there.

### R2 — storage-time correctness (new helper)
- New `check-operating-rule-storage.py` (response.completed, advisory, exit 0, fail-open):
  - **Dedup / resolve-first**: if the turn writes to `ssot/capabilities.json`, `ssot/policies.json`, or `rules/*.md` (operating-rule stores) WITHOUT prior `lazy (policy|capability|rules) resolve` evidence this turn → advisory: possible duplicate; resolve existing rules first; canonical = policies.json + capabilities.json.
  - **Wrong-surface**: if the turn writes operating-rule SEMANTICS (strict cues: preferred/discouraged/canonical command, warn/block, workflow-gating "must/always ... before commit/push/merge/yield/pr/mutation") to a non-canonical `ssot/*.md` that is not a recognized policy/capability/registry record → advisory: operating-rule semantics belong in policies.json + capabilities.json; `rules/**` is compat/explain.
  - Conservative cue gating + `open-gates.json` dedup + echo-guard; negative cases (plain fact SSOT write, write to canonical store, resolve-evidence present) stay silent.
- Wire into `on-response-completed.sh` helper loop (after the placement gate) and `scripts/lifecycle-check.py` HELPERS list.

### R4 — grammar + record alignment
- `.lazy-harness/AGENTS.md`: concise rule — before ADDING an operating rule, `lazy (policy|capability|rules) resolve` to find existing rules (anti-duplication); canonical store = policies.json + capabilities.json, `rules/**` compat.
- Align `ssot/rule-sources.md`, `spec/platform/project-rule-router.md`, `spec/platform/response-rule-audit.md` with R1/R2 behavior.

### R5 — ADR + supersession
- New `decisions/0048-operating-rule-storage-apply-repair.md`: record the apply-audit repair + storage helper, explicitly keeping organic/no-hard-gate posture and the R3 exclusion rationale.
- Mark the 2026-06-10 audit `superseded-by` this plan/ADR for the repair direction (keep its diagnosis as history).

### R6 — regression (BOTH-tagged; runs on hosts via `lazy test`)
- self-test: `missed_discouraged_action` fires at `default` level (extend existing warn fixture), stays silent at `recommend`/`discover`.
- self-test: new storage helper fires on (a) rule-store write without resolve evidence, (b) operating-rule prose into a non-canonical ssot .md; stays silent on (c) resolve evidence present, (d) write to policies.json/capabilities.json, (e) plain fact SSOT write.
- Register any new spec/test/ssot/planning/ADR records in `manifests/init-categories.json` categories.A (self-test enforces). New python helper rides the existing `hooks/lifecycle/helpers/*.py` glob (no manifest edit).

## Propagation

- Hook/script/schema changes auto-propagate via Category-A globs (no manifest edit).
- New `.md` records (plan, ADR, SDD/SSOT edits to per-file-registered records, tests) require `manifests/init-categories.json` entries; self-test guards enforce.
- `capabilities.json`/`policies.json` are seed-merge (host-owned) — framework helpers must not overwrite host entries; behavior changes live in helpers/grammar only.

## Review (검수)

- ADR-0041: all new behavior is response.completed advisory + deterministic label/cue matching + grammar; no new `tool.execute.before` rule gate; existing read-debt permit untouched. No hard gate reintroduced (user previously rejected hard gates).
- Level semantics: `discover`/`recommend` stay silent; advisories at `default`/`warn`/`block`.
- False-positive control for R2: strict operating-rule cues, exclude meta-records, open-gates dedup, negative self-test cases.
- Do not revive `rule-bindings.json` / `check-rule-action-boundary` enforcement / `lazy find --purpose`.

## Implementation map

- Status: `in-progress`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — R1 default-level firing + comment.
  - `.lazy-harness/hooks/lifecycle/helpers/check-operating-rule-storage.py` — R2 new helper.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — wire R2 helper.
  - `.lazy-harness/scripts/lifecycle-check.py` — HELPERS list parity.
  - `.lazy-harness/AGENTS.md`, `.lazy-harness/ssot/rule-sources.md`, `.lazy-harness/spec/platform/project-rule-router.md`, `.lazy-harness/spec/platform/response-rule-audit.md` — R4.
  - `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md` — R5.
  - `.lazy-harness/scripts/self-test.py`, `.lazy-harness/manifests/init-categories.json` — R6.
- Evidence (2026-06-24 read-only maps): explore agents MachineryMap / HookMap / SpecAdrMap / TestSyncMap.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Machine index:
  - graph ids: `pending until graph rows added in R6`

## Rule placement

- Rule: operating-rule storage must steer to the canonical typed-policy store and detect intra-harness wrong-surface/duplicate writes; apply-time advisories must fire for default-level host operating rules.
- Scope: framework-global
- Primary record: `.lazy-harness/planning/operating-rule-storage-apply-repair-20260624.md`
- Why not AGENTS.md: this is a multi-file implementation plan; AGENTS.md gets only the concise resolve-before-add grammar (R4).
- Why not `.jcode`: shared framework behavior for all hosts.
- Confirmation: user-confirmed

## Discovery capture

- DDD: no domain vocabulary change.
- SDD: update response-rule-audit + project-rule-router; no new `Project Rule Application` SDD (superseded by policy-machinery-v2).
- BDD: agent-visible apply advisory now fires for default-level host rules.
- TDD: new default-level + storage-helper regressions (R6).
- ADR: successor ADR 0048; ADR 0041/0044/0046 remain the governing architecture.
- SSOT: align rule-sources; rule-lifecycle unchanged (still phase5-organic).
- Planning: this record; supersedes the 2026-06-10 audit repair direction.
