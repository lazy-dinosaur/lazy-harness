# Jcode Wiring Drift Audit — Medivance dogfood host

Status: retired-history
Date: 2026-05-24
Scope: transient-plan
Related ADR: `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md`
Related SSOT: `.lazy-harness/ssot/rule-sources.md`
Related SDD: `.lazy-harness/spec/platform/project-rule-router.md`

## Summary

A read-only audit of `/home/lazydino/dev/medivance` found that the framework-owned `.lazy-harness/AGENTS.md` is current, but multiple generated/private `.jcode` instruction files are stale because they predate generated markers and are preserved as user-owned by `jcode-wiring.ts`.

This affects the default instruction surface that Jcode loads, not host institutional memory records.

## Evidence

Command outputs were written to:

- `/tmp/lazy-harness-medivance-precise-audit.json`
- `/tmp/lazy-harness-medivance-precise-audit.md`

Core instruction file findings:

| File | Finding |
|---|---|
| `/home/lazydino/dev/medivance/.lazy-harness/AGENTS.md` | OK, matches source hash `486135393ece` |
| `/home/lazydino/dev/medivance/.lazy-harness/JCODE-INTEGRATION.md` | OK, matches source hash `a6707222f827` |
| `/home/lazydino/dev/medivance/.jcode/AGENTS.md` | Diff from fresh generated template, no generated marker, contains stale cues such as `medivance.experimental-lazy-harness`, `/harness-doctor`, `Phase 5`, `framework-contract.md`, `ADR 0007`, `C1~C16`, `harness-init`, `harness-update` |
| `/home/lazydino/dev/medivance/.jcode/config.toml` | Diff from fresh generated template, no generated marker, sets `ignore_project_agents = true` and includes old test hooks/private globs |
| `/home/lazydino/dev/medivance/.jcode/harness/05-lazy-harness.md` | Diff from fresh template, regular stale copy instead of symlink to `../../.lazy-harness/AGENTS.md` |
| `/home/lazydino/dev/medivance/.jcode/harness/10-routing-policy.md` | Diff from fresh generated template, no generated marker |
| `/home/lazydino/dev/medivance/.jcode/harness/20-project-rules.md` | OK, generated marker present, pointer-only template current |

`lazy-sync --dry-run --force` confirmed current code behavior:

- Category A framework body: only `knowledge/graph.jsonl` would update.
- Jcode wiring: preserves markerless `.jcode/AGENTS.md`, `.jcode/config.toml`, `.jcode/harness/10-routing-policy.md`, hooks, and several skills as user-owned.
- `05-lazy-harness.md` is kept just because it exists, with no content/symlink freshness check.

## Risk

- New Jcode sessions in Medivance may load stale `.jcode/AGENTS.md` before or alongside current `.lazy-harness/AGENTS.md`.
- `ignore_project_agents = true` in stale `.jcode/config.toml` can bypass repository/team `AGENTS.md` instructions for that checkout.
- `05-lazy-harness.md` being a regular stale copy prevents current `.lazy-harness/AGENTS.md` updates from propagating through the intended symlink path.
- Generated marker policy is safe for preserving real local customizations, but currently has no stale-template detector for known framework-owned default files that predate markers.

## Recommended next work

1. Add a read-only stale Jcode wiring detector to lazy-harness, likely in `lazy-sync` dry-run/summary and/or doctor smoke.
2. Detect markerless default-surface files with high-confidence stale cues and report actionable remediation instead of silently `keep user-owned`.
3. Special-case `.jcode/harness/05-lazy-harness.md`: if it is a regular file equal to an old framework grammar or missing generated marker, report that it should be replaced by the symlink to `../../.lazy-harness/AGENTS.md`.
4. Provide a safe repair mode that archives markerless stale default files under `.jcode/archive/` before writing current generated templates.
5. Keep true user-owned `.jcode` customizations preserved unless the user explicitly approves repair.

## Rule placement

- Rule: stale generated Jcode instruction files must not be treated as current harness defaults just because they are markerless user-owned files.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/jcode-wiring-drift-audit.md`
- Why not AGENTS.md: this is not a universal agent grammar rule yet; it is an implementation/audit backlog for generated wiring freshness.
- Why not `.jcode`: the issue concerns framework-generated wiring policy and should be visible from the lazy-harness source repo, not stored only in one host's private Jcode directory.
- Confirmation: inferred-from-record

## Implementation map

- Primary files inspected:
  - `.lazy-harness/scripts/jcode-wiring.ts` — generated marker and user-owned preservation logic.
  - `.lazy-harness/scripts/lazy-sync.ts` — Category A sync and Jcode wiring invocation.
  - `.lazy-harness/manifests/init-categories.json` — Category A sync surface.
  - `/home/lazydino/dev/medivance/.jcode/AGENTS.md` — stale active Jcode private entrypoint.
  - `/home/lazydino/dev/medivance/.jcode/config.toml` — stale config with `ignore_project_agents = true`.
  - `/home/lazydino/dev/medivance/.jcode/harness/05-lazy-harness.md` — stale regular copy of framework grammar.
- Related validation commands:
  - `bun .lazy-harness/scripts/lazy-sync.ts --from /home/lazydino/dev/lazy-harness --target /home/lazydino/dev/medivance --dry-run --force`
  - ad-hoc read-only hash comparison scripts saved outputs under `/tmp/`.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0029-generated-project-local-jcode-wiring.md`
  - SSOT: `.lazy-harness/ssot/rule-sources.md`
  - SDD: `.lazy-harness/spec/platform/project-rule-router.md`

## 2026-05-26 verification — stale status vs completed state

Status: verified-current
Confirmation: inferred-from-record-and-validation

The 2026-05-24 audit text is historical, but the repair implementation and dogfood host state are current as of this check.

Source repository evidence:

- Current branch: `main` at `75e03ec Record host sync closeout` with uncommitted `.lazy-harness` changes.
- `.lazy-harness/scripts/jcode-wiring.ts` contains stale markerless generated-default detection, archive, and repair logic.
- `.lazy-harness/scripts/self-test.py` contains `check_jcode_wiring_repairs_stale_defaults`.
- Source validation passed:
  - `.lazy-harness/scripts/self-test.py`: passed, including `jcode stale default repair ok`.
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`: passed.

Dogfood host evidence:

- `/home/lazydino/dev/medivance` and `/home/lazydino/dev/medivance-pwa` both have the same SHA-256 for the two key framework files as source:
  - `.lazy-harness/scripts/jcode-wiring.ts`
  - `.lazy-harness/scripts/self-test.py`
- Current `lazy-sync --dry-run --force` reports Jcode wiring unchanged for marker-managed files and only framework record/log artifacts pending.
- Both hosts have current marker/symlink state:
  - `.jcode/AGENTS.md`: generated marker present.
  - `.jcode/config.toml`: generated marker present.
  - `.jcode/harness/05-lazy-harness.md`: symlink to framework AGENTS path.
  - `.jcode/harness/10-routing-policy.md`: generated marker present.
- Host validation passed after focused rerun:
  - `/home/lazydino/dev/medivance`: doctor smoke passed; self-test host passed.
  - `/home/lazydino/dev/medivance-pwa`: doctor smoke passed; self-test host initially showed a transient `project rule placement helper` failure in a parallel validation batch, then focused rerun passed with exit code 0.

Current conclusion:

```text
The stale Jcode wiring audit is no longer an unimplemented host drift finding.
The repair code exists, is synced into both dogfood hosts, and validates in source plus both hosts.
Remaining work is source hygiene: commit the uncommitted implementation/record changes if accepted, and clear or explain the source `$LAZY_RUNTIME_ROOT/state/open-gates.json` project-rule-placement fingerprint.
```

## Rule placement

- Rule: 2026-05-24 stale Jcode wiring audit is historical; 2026-05-26 evidence shows the repair implementation is present and validated in source, Medivance, and Medivance PWA, but not committed in the source repository yet.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/jcode-wiring-drift-audit.md`
- Why not AGENTS.md: this is a point-in-time dogfood verification result, not a universal agent instruction.
- Why not `.jcode`: this concerns shared framework-generated wiring and installed host dogfood state, not local/private Jcode-only workflow.
- Confirmation: inferred-from-record-and-validation

## Discovery capture

- DDD: no domain terminology change.
- SDD: existing generated Jcode wiring contract evidence confirmed, no new contract introduced.
- BDD: no UI/user flow change.
- TDD: validation evidence confirmed `check_jcode_wiring_repairs_stale_defaults` protects this repair path.
- ADR: no new design decision; existing ADR 0029 remains the related decision.
- SSOT: no ownership/source-of-truth change.
- Planning: updated here to avoid treating the stale audit as current unresolved work.
