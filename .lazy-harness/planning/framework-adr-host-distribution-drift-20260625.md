# Planning — Framework ADR → Host Distribution Drift (operational-adrs allowlist gap)

Status: open
Created: 2026-06-25
Layer: Planning
Related SSOT/manifest: `.lazy-harness/manifests/init-categories.json`
Related ADR: `.lazy-harness/decisions/0050-pi-omp-only-runtime.md`, `.lazy-harness/decisions/0027-standalone-source-of-truth-repo.md`

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global
- Applies when:
  - adding a framework ADR that AGENTS.md or a synced Category A file (hook/spec/manifest) references
  - auditing why a host's `.lazy-harness/framework/operational-adrs/` is missing a referenced ADR
- Must:
  - add any framework ADR referenced by AGENTS.md or a synced Category A file to the operational-adrs allowlist in `init-categories.json` (with `targetPath: framework/operational-adrs/<file>`), so the reference resolves on hosts
- Must not:
  - assume host `.lazy-harness/decisions/` carries framework ADRs (host decisions/ is host-owned, never synced — ADR 0027)

## Root cause

Framework ADRs do NOT sync into a host's `.lazy-harness/decisions/` (host-owned
institutional memory, ADR 0027). Framework ADRs that hosts must resolve are synced
to `.lazy-harness/framework/operational-adrs/` via an **explicit allowlist** in
`init-categories.json`. That allowlist was `{0030,0031,0032,0033,0034,0037,0040,0041,0046,0048}`
and was NOT updated when ADR 0035/0038/0050/0051 were created — even though they are
referenced by synced files:

- 0050 — `check-destructive-command.py`, `check-rule-action-boundary.py` (hooks); `jcode-skill-creation.md`, `pi-mcp-parity.md`, `rule-sources.md` (specs, "superseded by 0050").
- 0038 — `on-context.sh`, `on-message-received.sh` (hooks); AGENTS.md §2.3.
- 0035 — AGENTS.md (interview queue-close mandate).
- 0051 — `pi-agent-package.md` SDD (jcode-parity).

Result: the references dangled on hosts (host `framework/operational-adrs/` had only
the 10 allowlisted ADRs). The medivance worktree agent searched host `decisions/`
for `0050-pi-omp-only-runtime.md`, did not find it, and reported a broken reference.

## Fix applied (2026-06-25)

- Added 0035, 0038, 0050, 0051 to the operational-adrs allowlist in `init-categories.json`.
- Marked the retired `lazy-skill-create` skill source (`packages/lazy-harness-pi/skills/lazy-skill-create/SKILL.md`) as RETIRED so the Pi/OMP runtime stops exposing the stale "Create a project-local custom Jcode skill wrapper" description.
- Re-synced all hosts so `framework/operational-adrs/0050…0051` land and the refs resolve.

## 2026-06-25 completion — full allowlist audit + preventive self-test

A path-form audit of every synced canonical record found **nine more** framework ADRs
referenced but missing from the allowlist: 0028, 0029, 0039, 0042, 0043, 0044, 0045,
0047, 0049. The original fix patched only the four the medivance agent reported; these
nine would also dangle on hosts. `record-lint` did not surface them (host-side it skips
Category-A framework records and only flags non-existent `.lazy-harness/...md` paths).

- Added all nine to the operational-adrs allowlist in `init-categories.json`.
- Added `check_operational_adr_allowlist_complete` (self-test, FRAMEWORK_ONLY) + TDD record
  `.lazy-harness/tests/operational-adr-allowlist-completeness.md` (path-form refs in synced
  canonical records, >= 0026, fences stripped; closes follow-up 1).

## Open follow-ups (backlog)

1. **Preventive self-test (framework scope). — DONE 2026-06-25.** `check_operational_adr_allowlist_complete`
   enforces that every framework ADR (>= 0026) path-referenced by a synced canonical record is in the
   operational-adrs allowlist, at the commit/push gate. See the 2026-06-25 completion section above and
   `.lazy-harness/tests/operational-adr-allowlist-completeness.md`.

2. **`.jcode` artifact cleanup on hosts (host mutation — needs user confirm).** Hosts
   still carry `.jcode/skills/` and wt-cli `.jcode` symlinks despite ADR 0050 removing
   the jcode runtime. `lazy sync` (Category A copy) does not prune these; a `lazy update`
   migration or explicit, confirmed removal is required. Not auto-done (potentially
   destructive, host-owned).

## Discovery capture

- DDD: none.
- SDD: none changed (the manifest is SSOT/config, not an SDD contract change).
- BDD: none.
- TDD: candidate — preventive self-test for allowlist completeness (follow-up 1).
- ADR: none new (0050/0051 already exist; this is a distribution-config fix, not a new decision).
- SSOT: `init-categories.json` allowlist corrected (manifest config).
- Planning: this record.
