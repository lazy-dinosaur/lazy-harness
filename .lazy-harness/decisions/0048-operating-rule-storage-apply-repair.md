# ADR 0048 — Operating Rule Storage + Apply Repair (organic, no new hard gate)

- Status: Accepted
- Date: 2026-06-24
- Trigger: Downstream dogfood showed operating rules are neither stored correctly (duplicate / wrong intra-`.lazy-harness` surface) nor applied (stored rules do not change action-time behavior). User: "저장도 제대로 안되는거고 제대로 따르지도 않고 있는거야 ... 제대로 다시 구현해야해".

## Rule digest

- Status: active
- Layer: ADR
- Scope: framework-global
- Aliases:
  - 운영 규칙 저장
  - operating rule
  - 규칙 어디에
  - rule storage
  - apply repair
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
  - surface the deterministic operating-rule/capability catalog at turn-start (`on-message-received.sh`, R3) so stored project rules are visible before action; keep it user-text-agnostic (no classification) and a plain registry enumeration the agent matches, never a `lazy find --purpose` query backend
  - when source-file context is available, derive exact source-work intents from tool labels and resolve them through this host's canonical policy/capability registries before the next source action
- Must not:
  - add a new `tool.execute.before` rule-specific hard gate (the user previously rejected hard gates; ADR 0041)
  - revive `rule-bindings.json`, `check-rule-action-boundary.py` enforcement, or a `lazy find --purpose` pre-turn query backend
  - classify raw user text in hooks; only deterministic label/cue matching of assistant/tool-arg evidence
  - hardcode one framework profile as the only source guidance or ignore host-owned policies/capabilities that match the same exact source-work intent
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
4. **Pre-action surfacing (R3) — included as of the 2026-06-28 amendment (reverses the original exclusion below).** Both lifecycle re-grounding hooks now surface a deterministic operating-rule/capability catalog (`lazy capability list` + `lazy policy list`, shared helper `helpers/operating_rule_catalog.py`): `on-message-received.sh` at turn-start (session baseline) and `on-context.sh` mid-turn after file-ops (per-turn refresh, since turn-start injection is deduped to once-per-session) — so stored rules are visible before action (jcode full-grammar parity). It stays within ADR 0041: the catalog is a plain enumeration the agent matches itself — not a `lazy find --purpose` semantic pre-turn resolver — is identical regardless of user text (no classification), and is advisory/visible with no hard gate. *(Original decision, retained as history: R3 was intentionally excluded to keep `on-message-received.sh` fully static and avoid reviving a retired pre-turn resolver backend; apply relied on grammar + the post-response advisory + the generic pre-action read-debt permit. Dogfood showed post-only surfacing left downstream agents improvising before the stored rule was ever seen — see the amendment section.)*
5. **Exact-intent source-context adaptation.** When `on-context.sh` receives a source-file touch, it maps only the mechanical tool label to source-work intents (`creating_source_file`, `modifying_source_file`, `reviewing_code_organization`) and calls the canonical `lazy capability resolve` / `lazy policy resolve` surfaces. The injected body includes matching host policy/capability ids, source records, summaries, and actions. This is an advisory resolver application, not user-text classification, profile inference, or a second policy engine.

## Consequences

- Stored host operating rules at `default`+ now produce action-time advisories when their discouraged action is used without resolve evidence.
- Intra-`.lazy-harness` wrong-surface and duplicate operating-rule writes are flagged after the write (advisory), closing the placement-gate blind spot.
- No new blocking surface; the only installed blocker remains the generic, non-rule-specific read-debt permit.
- `capabilities.json`/`policies.json` stay host-owned (seed-merge); behavior changes live only in helpers + grammar, so framework sync never overwrites host rules.
- Helper code propagates to hosts via the existing `hooks/lifecycle/helpers/*.py` Category A glob; the edited operational records propagate as already-registered Category A files.

## 2026-06-28 amendment — R3 pre-action catalog surfacing (reverses Decision §4)

- Trigger: downstream dogfood (medivance) — an agent asked to open a PR never saw the stored PR-body rule before acting and improvised, because turn-start only injected a "go search records" reminder and operating rules surfaced only mid-turn (`on-context.sh`, after file ops) or post-response (advisory). User confirmed R3 is the right direction and approved implementation.
- Root cause: the symptom is the direct consequence of the original R3-exclusion — nothing put the relevant operating rule in front of the agent before it acted; jcode was stable because it force-loaded project rules into every turn (always visible).
- Change: a shared helper `helpers/operating_rule_catalog.py` builds a deterministic catalog from `lazy capability list` + `lazy policy list` (`- \`<id>\` (<level>): <appliesWhen/appliesTo intents>`). `on-message-received.sh` injects it in the static turn-start body (session baseline); `on-context.sh` injects it in the mid-turn re-grounding (per-turn refresh after file-ops) because turn-start injection is deduped to once-per-session (`index.ts` `before_agent_start`; `pi-agent-package` §19) and on-context previously surfaced policy titles only, not capabilities. The agent resolves the matching intent (`lazy capability resolve --intent <intent>` / `lazy rules resolve`) and follows the stored convention before acting.
- Guardrails preserved (ADR 0041 / this ADR's Must-not): deterministic enumeration, not a query backend (§24); identical output regardless of user text (§25, fixture-enforced); advisory/visible, no hard gate (§23).
- Budget: turn-start estimate ~551→~758 tokens on the source repo, within the 1000 hard max (`check_prompt_budget_measurement`); no threshold change. Catalog entries capped (14) and intents truncated to bound host growth.
## 2026-07-20 amendment — host source-policy adaptation

- Trigger: the user restated the original framework goal: storing a reusable Code Organization Profile is not sufficient; project-specific rules must change actual agent behavior. The first Profile v1 implementation still hardcoded one framework profile pointer after source touches and only listed host rule ids in a generic catalog.
- Change: `on-context.sh` now derives exact source-work intents from file-tool labels and asks the existing capability/policy resolvers for this host's matches. `operating_rule_catalog.py` renders those canonical resolver results beside the bounded all-rule catalog.
- Host boundary: the framework Code Organization Profile remains a recommend-level baseline. Host-project policies/capabilities may add narrower source guidance through the same registries and are surfaced without being overwritten or reinterpreted by the framework.
- Behavior boundary: source records, summaries, and capability actions are surfaced before the next source step; record/docs-only touches keep the generic catalog but receive no source-adaptation block.
- Safety boundary: no raw user-text classification, architecture/profile inference, warn/block promotion, tool-specific hard gate, or second policy engine is introduced.
- Protection: a minimal temp-host regression owns a host-only source policy/capability and proves it appears in source context while remaining absent from record-only context.

## Implementation map

- Status: `implemented`
- Source files:
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — R1 default-level firing + documented level-set exclusion.
  - `.lazy-harness/hooks/lifecycle/helpers/check-operating-rule-storage.py` — R2 storage advisory helper.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — wires the storage helper after the placement gate.
  - `.lazy-harness/scripts/lifecycle-check.py` — HELPERS parity.
  - `.lazy-harness/AGENTS.md`, `.lazy-harness/ssot/rule-sources.md`, `.lazy-harness/spec/platform/response-rule-audit.md`, `.lazy-harness/spec/platform/project-rule-router.md` — grammar/record alignment.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — R3 turn-start catalog injection (imports `helpers/operating_rule_catalog.catalog_lines`); 2026-06-28 amendment.
  - `.lazy-harness/hooks/lifecycle/helpers/operating_rule_catalog.py` — shared deterministic catalog builder plus canonical exact-intent resolver rendering used by source-touch context; 2026-07-20 amendment.
  - `.lazy-harness/hooks/lifecycle/on-context.sh` — R3 mid-turn (per-turn) catalog injection; 2026-06-28 amendment.
- Key symbols:
  - `missed_discouraged_action` (`check-response-rule-audit.py`) — now `{default, warn, block}`.
  - `rule_store_write` / `wrong_surface_write` / `has_resolve_evidence` (`check-operating-rule-storage.py`).
  - `catalog_lines` / `catalog_entries` / `context_guidance_lines` (`helpers/operating_rule_catalog.py`) — bounded registry catalog plus host-specific canonical resolver output for mechanically derived source-work intents.
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_operating_rule_storage_helper`
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest` (default-level + recommend-silent cases)
  - `.lazy-harness/scripts/self-test.py#check_message_received_surfaces_operating_rule_catalog` (R3 catalog surfaced at turn-start; user-text-agnostic)
  - `.lazy-harness/scripts/self-test.py#check_on_context_surfaces_operating_rule_catalog` (R3 catalog surfaced mid-turn incl. capabilities)
  - `.lazy-harness/scripts/self-test.py#check_code_organization_profile` (host-only source policy/capability resolves into source context; record-only context has no source-adaptation block)
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

## Discovery capture — 2026-07-20 host source-policy adaptation

- DDD: no independent delta; no business vocabulary or invariant changed.
- SDD: Code Organization Profile and Pi/OMP package contracts gain host-resolved source guidance.
- BDD: no product-visible flow; agent source-context guidance remains advisory.
- TDD: Code Organization Profile and Pi/OMP package regression records gain the host-only adaptation fixture.
- ADR: this amendment records why exact-intent source resolution extends the existing R3 catalog without reintroducing semantic user-text routing.
- SSOT: no registry schema or seed semantic change; existing host-owned policy/capability stores remain canonical.
- Planning: no new plan; this approved bounded amendment closes the source-organization canary of the existing adaptation bridge.
