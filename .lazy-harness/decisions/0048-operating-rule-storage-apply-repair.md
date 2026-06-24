# ADR 0048 — Operating Rule Storage + Apply Repair (organic, no new hard gate)

- Status: Accepted
- Date: 2026-06-24
- Trigger: Downstream dogfood showed operating rules are neither stored correctly (duplicate / wrong intra-`.lazy-harness` surface) nor applied (stored rules do not change action-time behavior). User: "저장도 제대로 안되는거고 제대로 따르지도 않고 있는거야 ... 제대로 다시 구현해야해".

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Applies when:
  - implementing or debugging how operating rules are stored and applied
  - deciding whether an operating-rule guard should be advisory or a hard gate
  - changing capability `level` semantics for the response-completed missed-action audit
  - 사용자가 운영 규칙 저장 위치/중복/따르기/적용을 이야기한다
- Must:
  - keep operating-rule guidance organic: response.completed advisory + grammar + deterministic label/cue matching of assistant/tool-arg evidence
  - fire the discouraged-action advisory for capabilities at `default`/`warn`/`block`; keep `discover`/`recommend` silent
  - detect intra-`.lazy-harness` wrong-surface and duplicate operating-rule writes via an advisory storage helper
  - keep the canonical store as `.lazy-harness/ssot/policies.json` (+ `capabilities.json`), `rules/**` compat/explain
- Must not:
  - add a new `tool.execute.before` rule-specific hard gate (the user previously rejected hard gates; ADR 0041)
  - revive `rule-bindings.json`, `check-rule-action-boundary.py` enforcement, or a `lazy find --purpose` pre-turn query backend
  - classify raw user text in hooks; only deterministic label/cue matching of assistant/tool-arg evidence
- Record completion:
  - changes to the storage helper, the missed-action level set, or the canonical-store policy update this ADR plus `spec/platform/response-rule-audit.md`, `ssot/rule-sources.md`, and self-test
- Related records:
  - `.lazy-harness/planning/operating-rule-storage-apply-repair-20260624.md`
  - `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - `.lazy-harness/decisions/0044-project-operating-rulebook.md`
  - `.lazy-harness/decisions/0046-policy-machinery-typed-policy-canonical.md`

## Context

The storage split is already correct (ADR 0044 → 0046: typed `policies.json` canonical, `capabilities.json` binding, `rules/**` compat). The regression was in the middle of the adaptation path — turning stored rules into action-time behavior — and in storage-time correctness:

1. **Apply dormancy.** `check-response-rule-audit.py:missed_discouraged_action` only fired for capabilities at `warn`/`block`. The seed `project-operating-rulebook` capability is `discover`, and hosts commonly register operating rules at `default`, so the advisory never fired for real host rules.
2. **Storage hole.** `check-project-rule-placement.sh` treats the first write to any `.lazy-harness/<layer>` as satisfying placement. It only guards `.jcode`/Jcode-memory over-routing; it cannot see operating-rule semantics written to a wrong/non-canonical `ssot/*.md`, nor duplication of an existing rule, inside `.lazy-harness`. This is exactly how a downstream agent duplicated an existing PR-body rule into an unrelated SSOT.

The 2026-06-10 regression audit diagnosed this but its 6-phase repair plan pre-dates ADR 0044/0046 (it proposed a `Project Rule Application` SDD and reviving `rule-bindings.json`, both superseded). The user required re-planning against the current structure.

A benign git drift exists: `check-response-rule-audit.py` excludes `harness-first-static` from its search-debt level set while `check-read-debt-permit.py` includes it. This is correct: `harness-first-static` is written every turn and the audit's search-evidence branch is not mutation-gated, so including it would fire on read-only turns; the action-gated pre-action permit owns that level. It is documented, not changed.

## Decision

Repair both halves organically, with no new hard gate, and propagate via framework Category A:

1. **Apply (R1).** `missed_discouraged_action` fires for `default`/`warn`/`block` (`discover`/`recommend` stay silent). Document the intentional `harness-first-static` exclusion.
2. **Storage (R2).** Add `check-operating-rule-storage.py` (response.completed, advisory, exit 0, fail-open, one advisory/turn via `open-gates.json`):
   - rule-store write (`ssot/capabilities.json`, `ssot/policies.json`, `rules/*.md`) without prior `lazy (policy|capability|rules) resolve` evidence → duplication advisory;
   - operating-rule semantics (preferred/discouraged command, `warn`/`block`, workflow-gating before commit/push/merge/yield/PR/mutation) written as prose into a non-canonical `ssot/*.md` (not an allowlisted meta record) → wrong-surface advisory.
3. **Grammar (R4).** AGENTS.md gains a thin resolve-before-add pointer; `ssot/rule-sources.md`, `spec/platform/response-rule-audit.md`, `spec/platform/project-rule-router.md` document the behavior and scope boundary.
4. **Pre-response surfacing (R3) is intentionally excluded.** Keeping `on-message-received.sh` fully static avoids reviving a retired pre-turn resolver backend (ADR 0041 Phase 7). Apply relies on grammar + the post-response advisory + the existing generic pre-action read-debt permit.

## Consequences

- Stored host operating rules at `default`+ now produce action-time advisories when their discouraged action is used without resolve evidence.
- Intra-`.lazy-harness` wrong-surface and duplicate operating-rule writes are flagged after the write (advisory), closing the placement-gate blind spot.
- No new blocking surface; the only installed blocker remains the generic, non-rule-specific read-debt permit.
- `capabilities.json`/`policies.json` stay host-owned (seed-merge); behavior changes live only in helpers + grammar, so framework sync never overwrites host rules.
- Helper code propagates to hosts via the existing `hooks/lifecycle/helpers/*.py` Category A glob; the edited operational records propagate as already-registered Category A files.

## Implementation map

- Status: `implemented`
- Source files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — R1 default-level firing + documented level-set exclusion.
  - `.lazy-harness/hooks/lifecycle/helpers/check-operating-rule-storage.py` — R2 storage advisory helper.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — wires the storage helper after the placement gate.
  - `.lazy-harness/scripts/lifecycle-check.py` — HELPERS parity.
  - `.lazy-harness/AGENTS.md`, `.lazy-harness/ssot/rule-sources.md`, `.lazy-harness/spec/platform/response-rule-audit.md`, `.lazy-harness/spec/platform/project-rule-router.md` — grammar/record alignment.
- Key symbols:
  - `missed_discouraged_action` (`check-response-rule-audit.py`) — now `{default, warn, block}`.
  - `rule_store_write` / `wrong_surface_write` / `has_resolve_evidence` (`check-operating-rule-storage.py`).
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_operating_rule_storage_helper`
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest` (default-level + recommend-silent cases)
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Cross-layer links:
  - Planning: `.lazy-harness/planning/operating-rule-storage-apply-repair-20260624.md`
  - SDD: `.lazy-harness/spec/platform/response-rule-audit.md`, `.lazy-harness/spec/platform/project-rule-router.md`
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`, `0044`, `0046`
- Machine index:
  - graph ids: `pending`

## Rule placement

- Rule: operating-rule storage steers to the typed-policy canonical store with advisory wrong-surface/duplicate detection; apply-time advisories fire for default-level host rules; all organic, no new hard gate.
- Scope: framework-global
- Primary record: `.lazy-harness/decisions/0048-operating-rule-storage-apply-repair.md`
- Why not AGENTS.md: AGENTS.md gets only a thin pointer (180-line cap); the decision/rationale belongs in an ADR.
- Why not `.jcode`: shared framework behavior for all hosts.
- Confirmation: user-confirmed

## Discovery capture

- DDD: no domain vocabulary change.
- SDD: response-rule-audit + project-rule-router updated; no new `Project Rule Application` SDD (superseded by policy-machinery-v2).
- BDD: apply advisory now fires for default-level host rules; storage advisory on wrong-surface/duplicate writes.
- TDD: `check_operating_rule_storage_helper` + default-level case in `check_response_rule_audit_from_surfaced_digest`.
- ADR: this ADR; ADR 0041/0044/0046 remain governing.
- SSOT: `rule-sources.md` updated; `rule-lifecycle.md` unchanged (still phase5-organic).
- Planning: `operating-rule-storage-apply-repair-20260624.md` supersedes the 2026-06-10 audit's repair direction.
