# Evidence — Dedicated Reader Runtime v1

Status: **isolated implementation verified; live model smoke and main integration pending**

## Scope

User-approved implementation in `/tmp/lazy-harness-reader-runtime-v1` on branch `work/reader-runtime-v1`, based on clean main `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b`.

In scope:

- dedicated `lazy-harness.record-reader` package resource;
- Reader-first Parent grammar and Reader result packet;
- exact asynchronous launch and content-not-completion join;
- root revision/evidence epoch/model/task/lowered-budget binding;
- cumulative count/line and failed-tool checks;
- canonical layer path containment and record fingerprint reuse;
- current/legacy read-debt bridge with bounded direct fallback;
- steer invalidation and nested parallel action protection;
- Pi print-mode primary stdout plus advisory stderr;
- focused and full framework regression protection.

Out of scope: live model canary, main integration, local commit, push, release, persistent global model setting, old Reader proof/admission machinery, `read_batch`, beacon/holdout work, and the separately gated 37-row graph migration.

## Implementation

- `packages/lazy-harness-pi/agents/record-reader.md`
  - complete map-first canonical record lane;
  - `LAZY_HARNESS_READER_RESULT: complete|incomplete|conflict`;
  - role ceiling 8 reads / 1,600 requested lines with lower Parent limits;
  - no source, mutation, validation, recursion, output file, or proof/admission authority.
- `packages/lazy-harness-pi/package.json`
  - `pi.subagents.agents=["./agents"]`;
  - `pi-subagents.agents=["./agents"]`;
  - no OMP-subagent claim.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`
  - `ReaderRunState`, `readerTaskField`, `readerLaunchValidationError`, `readerLaunchState`, `readerFallbackError`, `canonicalReaderRecordPath`, `parseReaderRunId`, `RECORD_READER_ROLE_MARKER`, `readerRuntimeRoots`, `lazy_reader_join`, and `printModeAdvisory`;
  - action remains blocked after launch until explicit content join;
  - terminal invalid outcomes enable bounded fallback instead of stranding the Parent;
  - `batch.tool_calls`, `batch.toolCalls`, and `multi_tool_use.parallel.tool_uses` recurse through nested actions;
  - `ctx.mode === "print"` emits advisory stderr without queuing a response-replacing follow-up;
  - the dedicated Reader replacement prompt bypasses Parent reminder/debt/tool/context/response-completed lifecycle handlers in the child process, while a normal Parent on the same root remains active.
- `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` and `check-search-performed.sh`
  - exact non-error complete join satisfies debt;
  - incomplete/error join and nested parallel mutation cannot bypass it.
- `.lazy-harness/AGENTS.md`, `on-message-received.sh`, package prompt, and README
  - dedicated Reader first, Sol Medium Parent source/test lane, Luna Low Reader route, content join, direct fallback.
- `.lazy-harness/scripts/self-test.py`
  - package/no-proof contract;
  - exact launch identity and lowered budget;
  - completion-not-join and pending-action barrier;
  - terminal fallback, unparseable run id, traversal rejection, fingerprint reuse, steer invalidation;
  - complete join allow / incomplete join deny / nested parallel mutation deny;
  - print stderr separation and explicit TUI/JSON/RPC follow-up behavior.

## Independent review

The first review returned `BLOCK` with four P1 findings: terminal fallback deadlock, nested parallel mutation bypass, launch identity/lowered-budget under-binding, and canonical `..` traversal. It also noted explicit JSON/RPC coverage and stale status text.

The sole writer fixed every finding. The blockers-only re-review used refreshed map/drill/diff evidence and returned:

- `No issues found.`
- isolated merge verdict: `OK`;
- residual risk: live model/package-discovery smoke and main integration remain intentionally unperformed.

Reviewer artifact: `.pi-subagents/artifacts/5d110976_reviewer_output.md` (untracked worktree artifact).

## Live canary preflight boundary

R1 at `/tmp/lh-reader-runtime-live-canary-r1-20260906` passed source/package/model preflight but was superseded before any model run when source review found missing dedicated-Reader lifecycle isolation. Its contract and preflight remain immutable; `preflight-terminal.json` records `SUPERSEDED-BEFORE-MODEL`. The role-marker isolation and focused fake-runtime fixture were added before preparing any new live root.

## Validation

Focused checks:

- TypeScript Bun bundle: PASS;
- Python compile / shell syntax / package JSON / `git diff --check`: PASS;
- `check_pi_package_layout_and_contract`: PASS;
- `check_tool_execute_before_hook`: PASS (`19` scenarios, including legacy cache seed/reset/recovery);
- record-lint: `186/186`, zero issues/advisories;
- `lazy check`: PASS.

Final standard attempt 1 failed in full self-test because executable self-test code embedded a concrete provider/model string rejected by D06 and because the Reader-first reminder dropped the required `First grounding only` phrase. The implementation switched code-level model validation to explicit launch-model ↔ task-model equality, retained the model choice in package grammar, restored the canonical phrase, and passed the focused doctor/message/package/guard checks.

Final standard attempt 2:

- `lazy validate --plan standard`: PASS (`173.797s`);
- fast static: PASS (`0.468s`);
- full self-test: PASS (`173.216s`).

After the R1 preflight exposed missing Reader-child lifecycle isolation, the added role-marker isolation passed the focused package fixture and a fresh final standard run: `89.829s` total, including full self-test `89.468s`. This evidence-only update does not change runtime behavior after the green boundary.

### Post-R2 static correction closure

The user-selected per-read cap and safe-source alignment was hardened through successive adversarial reviews. Findings covered compound/nested shell mutation, stale fallback evidence, max-observed/failed/zero ledgers, shell find/tree/write filters, git/tree output, unsafe `cd`, quoted/escaped `rg --pre`, unrestricted Reader-child bash, and legacy cache ordering/recovery. All findings remain preserved in planning; one resumed reviewer infrastructure failure remains exact: `Cannot read properties of undefined (reading 'create')`.

The final implementation adds a dedicated Reader-child tool boundary, positive internally consistent complete-ledger checks, conservative TypeScript/Python shell parity, pre-join evidence truncation after incomplete or errored-complete joins, legacy cache invalidation before its fast path, and exact fresh post-failure map recovery. Focused package/generic-debt/19-scenario checks passed. Final independent review `7bd36fb6` returned `No issues found` / isolated `OK`.

Post-R2 standard checkpoint: `lazy validate --plan standard` PASS (`76.201s`), including fast static `0.262s` and full self-test `75.869s`. R2 remains terminal-incomplete; this is static correction evidence only, not a live rerun or main-integration authorization.

Key static-source SHA-256 at closure:

- Reader role: `b1b5a50be033164bd308501180505fab428ed5c6b48ddc432e5537e14a18e24e`;
- extension: `09f5b125b1c7e127c74c4b7d5985c2bba042243a4fd9ff97154b107c353cb038`;
- current debt helper: `cee300b8304a0c0b0d4d92345585879786e8de5399dac356751690d854de91bb`;
- legacy debt helper: `7cb72be16ca54b272f2259619acead841f413cea449ba4133cded5975063949e`;
- self-test: `61b8680d9f4fb981286c9df357cdee8797741657633881506ef99aba4ec08d1a`;
- package manifest: `e5f2db4a25d252623edbc37fe3af8ddbd8416dbd121566fa720082315a366e93`.

## Preservation

- Main worktree was not reset, cleaned, staged, or modified by source implementation.
- No implementation commit, push, merge, release, package activation, or persistent model-setting mutation occurred.
- Historical topology/model attempts and their terminal outcomes remain immutable.
- The 37 legacy graph rows remain untouched and separately migration-gated.

## Discovery capture — post-R2 static closure

| Layer | Judgment | Disposition |
|---|---|---|
| DDD | `none` | Existing Reader/Parent/join vocabulary remains sufficient; no independent domain rule changed. |
| SDD | `updated` | `pi-agent-package.md` and `search-read-debt-contract.md` own the child tool boundary, ledger, shell, and fallback/cache contracts. |
| BDD | `none` | No independent user-visible flow changed; the existing Reader/Parent content and output scenarios remain applicable. |
| TDD | `updated` | `pi-agent-package.md` and `pre-action-search-evidence-guard.md` record the 19 focused scenarios, reviewer closure, and standard regression evidence. |
| ADR | `none` | Dedicated Reader ownership and direct-fallback decision are unchanged; no new trade-off was selected. |
| SSOT | `updated` | `harness-enforcement-policy.md` records the isolated enforcement state and keeps main integration gated. |
| Planning | `updated` | `agent-neutral-orchestration-pilot.md` preserves the adversarial finding/fix lineage and separately gated next decisions. |

No unresolved factual candidate remains for `candidates.jsonl` or `graph-drafts.jsonl`; all captured facts are code-, test-, review-, or validation-backed. No discovery-capture step was intentionally skipped.
