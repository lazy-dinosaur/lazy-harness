# Evidence — Reader follow-through after R3 remediation

Status: R4 TERMINAL-INCOMPLETE (no retry); subsequent native-notification repair passed static checks, not a new live run.

## Resolved typecheck

The unresolved-dependency LSP report was investigated rather than suppressed. An external, bounded TypeScript configuration resolves the installed Pi SDK 0.85.1, typebox 1.3.7, and Node declarations 25.0.10 explicitly. With dependencies resolved, three real extension type errors became visible:

- before_agent_start returned a string/array union against Pi's string-only signature;
- Reader join complete/incomplete results inferred incompatible details types;
- existing move-tool result branches inferred incompatible details types.

`packages/lazy-harness-pi/extensions/lazy-harness/index.ts` now has string/array overloads for `appendSystemPromptBody`, a typed Pi event parameter, and a shared explicit `TextToolResult` return shape. Runtime behavior is unchanged: OMP array support remains protected by the existing package fixture; no blanket any return or diagnostic suppression was added.

- Resolved `tsc --noEmit` strict extension-source check: PASS. Config: `/tmp/lh-reader-resolved-typecheck.json`; R4 snapshot-specific copy `resolved-typecheck.json`.
- Scope limitation: `skipLibCheck` excludes dependency declaration internals. This is not a clean project-wide LSP claim.
- Package fixture including Pi string/OMP array behavior: PASS.
- Final standard checkpoint: PASS, 121.247s; full self-test 120.593s.

## Fresh verification dispatch

Following the user's request to continue through the remaining work, one fresh R4 was prepared at `/tmp/lh-reader-canary-r4-kcrjrt6k`; R3 was not retried or edited. `execution-scope.json`, `prompt.md`, `checklist.json`, `source-manifest.json`, and `preflight.json` bind the new inputs. Preflight verified source bytes, package discovery, exact listed models, strict resolved extension typecheck, and empty sessions/run directories. It does not by itself prove model success.

R4 prompt keeps the R3 question and eight critical criteria while explicitly omitting total-tool overrides, allowing native-only Parent source inspection, and draining a pending child before one terminal response. Budgets remain Reader six/1,200/200 and Parent two/500. Exact requested topology is Sol Medium Parent plus Luna Low Reader. Dispatch: `calm-delta`; one-shot launcher uses exclusive started receipt and no auto-retry.

No functional PASS is claimed until actual transcripts, counters, citations, and delivered answer are audited. Main integration, activation, commit, push, release, and legacy graph migration remain outside this work.

## Discovery capture

- DDD — none: no domain delta.
- SDD — none: type annotations repair declared compatibility, not runtime contract semantics.
- BDD — none: existing runtime behavior retained; R3 guidance is tested separately.
- TDD — updated: resolved typecheck and existing fixture outcomes captured here; live outcome pending.
- ADR — none: Reader ownership unchanged.
- SSOT — none: temporary external typecheck configuration is not canonical project configuration.
- Planning — updated: this evidence capsule captures bounded continuation and pending verification without promoting a result prematurely.


## R4 observed outcome and subsequent repair

- Actual topology: one Sol Medium Parent and one Luna Low Reader. Reader run `5421ce26-b719-4f02-b389-27e92b662959`.
- Reader completed all six body reads (1,200 requested lines), zero failed calls, and delivered a complete packet. Parent requested two reads/500 lines; one failed on a guessed nonexistent `.lazy-harness/scripts/lazy.ts`, then Parent continued.
- Join rejected the actual notification because runtime completion recognition depended only on legacy `subagent_wait`; `bg_wait` had no matching active run. Parent subsequently tried status and another join, both failing. This violated the no-retry protocol. No substantive answer or quality PASS.
- Duration 146.59s; combined provider tokens 231,138; reported combined cost $0.24734316. All manifest-bound source bytes preserved.
- Immutable result `terminal-outcome.json`; artifact manifest SHA-256 `d8fedd2120f5dadb68c344b94f1f5cba6165d0523280cb773ca74288f89885b9`.

Correction: `index.ts#observeReaderPacket` observes typed native context notifications matching dedicated Reader header, complete marker, root/revision/epoch; join requires observed content. One launch per epoch prevents ambiguous same-epoch notifications. Legacy wait alone remains insufficient. Parent grammar requires source discovery before body reads. Source correction does not relabel R4 or claim live-model adherence.

Regression fixture now succeeds with notification-only delivery and no legacy wait, rejects stale/wait-only evidence and duplicate launches, and exercises old ledger/path checks after valid notification. Independent review `ec84d66d`: No issues found / OK. Earlier review `535a2bf3` was evidence-blocked; resumed `5f6cd540` failed with `Cannot read properties of undefined (reading 'create')`; preserved separately.

Final strict resolved extension tsc: PASS. Final standard: PASS 105.665s (full self-test 105.301s). SDD/TDD/Planning updated; DDD/BDD/ADR/SSOT have no independent semantic delta. Mapping: `kg_reader_native_notification_r4_fix`; primary contracts `.lazy-harness/spec/platform/pi-agent-package.md` and `.lazy-harness/tests/pi-agent-package.md`. No new canary after R4 was launched.
