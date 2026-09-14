# TDD — TDD/Affected forceGate ask-loop regression

Status: protected
Date: 2026-05-17
Layer: TDD (regression case for interview gate dedup)

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - 교차검증 루프 회귀
  - forcegate loop
- Applies when:
  - editing the TDD cross-verify or affected-test-runner interview/forceGate gate logic
  - a `5d-3` Cross-Verify/Affected Test gate STOP re-fires every response for the same source or question
- Must:
  - gate on new unseen question fingerprints only (`forceGate = questions.length > 0`); ask once per fingerprint
  - derive `needsInterview` from newly-pushed questions, not merely a question defined on the plan
  - still report `failed` accurately and re-fire the gate for a brand-new fingerprint
  - preserve complete edited repository identity through affected matching, strategy, execution, result and queue fingerprint; never guess executable repositories from ambiguous space-joined targets
  - recognize a source file's tests across co-located/`__tests__`/`tests` dirs with separator-insensitive (PascalCase↔kebab↔snake) and infix (`.contract`, `.unit`) matching via the shared `scripts/test-match.ts`, so files that DO have tests never false-positive either 5d-3 gate
- Must not:
  - re-ask the same fingerprint every turn while the source path stays in `recent_tool_calls`
- Record completion:
  - formalizing `forceGate`/return-contract semantics updates this TDD and a follow-up SDD

## Bug

Symptoms observed on host `medivance` while editing `src/renderer/src/screens/Appointment/context/AppointmentProvider.tsx`:

- `5d-3 TDD Cross-Verify Gate` STOP block re-appeared on every `response.completed`.
- Same question ID `Q-0dbf1eab9e51ffee` was re-surfaced again and again.
- User answered (`A 로 하자`), but the gate kept firing because `recent_tool_calls` still mentioned the same source path.
- The chat scrollback filled with identical STOP blocks, blocking real work.

The dual symptom existed in `affected-test-runner` (`5d-3 Affected Test Gate`, question `Q-8e866d44709ff49c`) because it shared the same `forceGate` design.

## Root cause

Two scripts owned the same flawed pattern:

1. `.lazy-harness/scripts/tdd-cross-verify.ts`
   - `forceGate = failed > 0`
   - `failed` was derived from "source file has no matching test", which does not change between response.completed events. Even after the question was persisted to `open.xml`, the gate kept firing because `failed > 0` stayed true.
2. `.lazy-harness/scripts/affected-test-runner.ts`
   - `needsInterview = filePlans.some(plan => plan.question !== undefined)`
   - `plan.question` was assigned even when the question's fingerprint was already in the queue (`existing.has(fp)` was only used to skip pushing to `questions[]`, not to suppress `plan.question`).

In both cases the persistence dedup (`seenQueue.has(fp)`) only stopped duplicate XML rows; it never stopped the gate from re-firing. Result: ask-loop until the agent stopped editing or the source path fell out of `recent_tool_calls`.

The self-test even encoded the loop-causing behavior as expected:

- `tdd-cross-verify`: dedup run was checked with `expect_code=2` (i.e. the second run was expected to keep firing the gate).
- `affected-test-runner`: hook test asserted that a second `response.completed` for the same file kept surfacing `5d-3 Affected Test Gate` and the previously-queued question ID.

So both the implementation and the protection encoded "ask every time the source file is mentioned" — which is exactly the ask-loop.

## Fix

Ask-once policy:

- `tdd-cross-verify.ts`: `forceGate = questions.length > 0`. `questions[]` is populated only with brand-new (unseen) fingerprints, so `forceGate` is false once the question has been recorded.
- `affected-test-runner.ts`: `needsInterview` requires the file's question to be in the newly-pushed `questions[]`, not merely defined on the plan.
- self-test:
  - dedup `tdd-cross-verify` run expects `expect_code=0` and `forceGate=false`.
  - affected hook re-surface check now expects silence when the fingerprint is already queued, plus a fresh sanity case (new path → gate fires once → second response stays silent).

`failed` is still reported accurately so reporters/loggers can see the underlying state, but the user-facing gate fires once per fingerprint.

## Why this is correct under ADR 0019 / ADR 0020

- ADR 0019 (구조화된 옵션 ask) requires that the agent ask the user once with a clear A/B/C/D set.
- ADR 0020 (TDD Cross-Verify) requires that any source change without a matching test surface a structured ask.
- Neither ADR mandates that the same fingerprint be re-asked every turn. The ask-loop was an unintended emergent behavior.
- Persistence into `open.xml` is the canonical record that the question is open. Closing/answering it should happen through the interview-loop CLI (`scripts/interview-loop.ts`) or by deleting the entry from `open.xml`. The hook is for surfacing **new** items only.

## 2026-06-28 — matcher false-positive on kebab-case / infix tests (second facet)

A second cause of the same-file double-STOP surfaced on host `medivance-homepage`: both 5d-3 gates (`tdd-cross-verify` + `affected-test-runner`) fired for `src/features/billing/SubscribedDownloadView.tsx` even though `src/features/billing/__tests__/subscribed-download-view.contract.test.tsx` existed and passed (6 tests). Each gate asked separately (distinct fingerprint schemes), so the user saw "the same gate firing twice".

Root cause: both gates carried byte-identical, too-narrow matchers — `candidateTestPaths` checked only co-located/`__tests__` with the EXACT PascalCase stem, and `siblingTestFiles` matched by lowercased-stem `includes()` in the source's own dir. A kebab-case `.contract` test matched neither (`"subscribed-download-view…".includes("subscribeddownloadview")` is false), so both gates false-positived even though the test existed.

Fix: extracted a single shared matcher `scripts/test-match.ts` (imported by both gates) that scans co-located + `__tests__/` + `tests/` dirs and matches separator-insensitively (PascalCase↔kebab↔snake) using leading dot-segment-prefix comparison, so infixes (`.contract`, `.unit`) are recognized while unrelated files (`OtherView.test.tsx`) are not. Files that genuinely lack a test still fire (true positive); the ask-once dedup above is unchanged. Note: consolidating the two gates' user-facing ask (so a genuinely test-less file is asked once, not twice) was scoped out — option A (matcher) only.

## 2026-06-28 — quoted-path / non-existent source false-positive (third facet)

A third false-positive: editing a RECORD that *quotes* a source path (e.g. this TDD record / ADR 0048 / `candidates.jsonl` mentioning `src/features/billing/SubscribedDownloadView.tsx`) made `check-tdd-cross-verify.sh` extract that path from the Edit `args_preview` (the regex scans the edit BODY, not just the edit target) and fire 5d-3 for a file that is not even in this repo. `tdd-cross-verify.ts` / `affected-test-runner.ts` never checked the source file exists.

Fix (two layers): (1) existence guard — both gates skip a source file when `!existsSync(file)` (kind `ignored`, reason `not-found`). (2) **edit-target-only extraction (fundamental, user-chosen)** — the extension (`index.ts`) computes `edit_target` (the file actually written/edited: `file_path`/`path`/`filePath`, or `[PATH#TAG]` patch headers) and both gate hooks scan `call.edit_target`, NOT the `args_preview` body. So editing a record that merely *quotes* `src/foo.tsx` yields `edit_target` = the record `.md` → no source extracted → no fire. Real source edits still fire; quoted / cross-repo / non-existent paths never do.

Host-parity follow-up: the existence guard (1) interacted with the static `tdd-cross-verify-stop` lifecycle-parity fixture, which edits `.lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts` — a framework self-test fixture NOT synced to hosts. Before the guard the gate fired regardless of existence; after it, the gate stays silent on hosts (file absent) → `lifecycle-parity --fail-on-mismatch` → `check_lifecycle_fixture_intake_cli` flips green→fail on hosts (the mid-session flip seen in dogfood). Fix: the parity fixture is now self-contained via a `sourceFiles` map — `prepare_env` writes the stub source into the copied host before replay (mirrors `decisionsFixture`/`decisionsFallback`), so `existsSync` passes and the gate fires on source AND hosts.

## Task366 — repository routing and development capture compatibility

User-approved repair is isolated source work followed by independent review before main/deployment admission. The external desktop/backend report is not locally reproduced; the operative synthetic regression supplies two actual repositories with identical relative names, directory/file spaces and commas, distinct test strategies and real Bun tests. The session host supplies the canonical runner and shared question queue; each edited repository supplies matching paths, configuration and explicit test cwd. All inherited `GIT_*` selectors are removed before discovery and test execution. Queue fingerprints/crossRefs and runner results now carry the owning root, preventing same-relative-path collisions. Existing questions retain historical IDs; a root-qualified identity may require one fresh question after upgrade.

The helper resolves a complete `edit_target`, not a suffix in prose. Multiple calls preserve multiple identities. Missing or ambiguous legacy space-joined source fields produce an explicit unresolved-target advisory rather than guessed execution or silent success. Matching tests and strategy/package paths cannot escape the owning root via symlinks. A non-Git initialized session host retains relative-path support. This supersedes only the older blanket statement that cross-repository edits never fire: genuine edited foreign repositories are routed, not skipped; quoted record bodies still do not trigger the gate.

The capture defect is mixed-version development layout, not a missing new release implementation. Remote main `80cf3be485d22a8036723e415f8b4e95f897786f` already contains the typed response hook/helper; accepted Reader release `5d3220215cb1b1df29ca8e60bffd39191ea990db` retains those bytes. The new regression swaps exact `58fbcbf` development hook/helper fixtures into an actual Pi SDK fixture, observes the missing-assessment warning, then restores the exact upstream two-file delta. Valid no-record and write/read evidence become linked while missing/invalid judgement remains unverified. The final answer/envelope is not rewritten, settings are not treated as hook compatibility, and Reader/full-ledger semantics are unchanged.

Implementation/protection additions:
- `.lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh`: complete-target resolution, owner grouping, clean Git env, canonical runner invocation and truthful failures.
- `.lazy-harness/scripts/affected-test-runner.ts`: `assertOwnedPath`, explicit `runConfiguredTests` cwd/env, `repositoryRoot` in result/crossRef/fingerprint.
- `tests/lazy-harness/affected-repository-routing.test.py`: full response hook → helper → real runner → real configured Bun tests, poisoned Git environment, distinct repositories/configs, failure, queue dedup, ambiguity, non-Git layout and symlink boundaries; invoked by `check_affected_test_runner`.
- `tests/lazy-harness/pi-capture-evidence.test.ts`: actual SDK development-style compatibility case plus existing valid/invalid/primary-answer protections.
- `tests/lazy-harness/fixtures/capture-legacy-58fbcbf/`: exact historical hook/helper bytes for regression only, not shipped hooks.
- Packaging already distributes `hooks/**` and `scripts/**`; source-only regression fixtures stay source-only. No manifest expansion or Pi/native API change.

Discovery capture: this TDD is the primary durable repair capsule. Detailed commands, first failures, source/dependency hashes, full patches and pending main/deployment admission live outside source in `/tmp/lh-gate-capture-main-deploy-r1/evidence/`. Production/development roots and settings are unchanged in phase1. The registered unreviewed `479531b` worktree is comparison evidence only; no adoption, edits or ownership-clearance claim. The accepted Reader46-path lineage is retained exactly by the candidate baseline, not replaced with dirty development bytes. Separately pending37 legacy graph rows are untouched; guided migration remains separately approvable.

| Layer | Task366 judgment |
|---|---|
| SDD | Existing absolute edit identity and typed capture contract repaired; additive internal result root documented here, no independent public API design |
| BDD | No app flow delta; existing primary-answer and truthful notice behavior retained |
| SSOT | No live ownership/config/binding changes; candidate uses accepted deployed lineage and preserves host queue ownership |
| DDD | No independent vocabulary/business-rule delta |

### Task366 R2 — independent review corrections

The first candidate's green six-case routing/28-case SDK/90-check standard receipts are retained, not release admission: independent review returned BLOCKED with two P1s. Absolute owner routing ignored `LAZY_LIFECYCLE_SANDBOX_CONTEXT=1`, escaping the framework-only lifecycle sandbox and duplicating real tests in compare mode. Whole-field extension filtering also silently ignored a joined source→record field ending in `.md`.

The affected helper now checks complete existing identity before extension filtering. Unresolved legacy fields containing a source suffix emit an ambiguity/missing-target advisory in either source→record or record→source order, without extracting an executable path. Genuine existing single records, including source-like names, remain silent. Sandbox context produces explicit `not-executed: lifecycle sandbox` output before owner discovery/runner execution; it never asserts tests passed or writes an affected-test question. Compare mode keeps its existing live-output authority and metadata-only logging: this deliberate non-executing shadow can differ from successful live output, so that mismatch is not production replacement readiness.

`tests/lazy-harness/affected-repository-routing.test.py` now copies the full actual framework lifecycle topology, including `lifecycle-check.py`, all preceding helpers and runtime adapters; none are stubbed or disabled. New cases cover both mixed-field orders, genuine single records, direct `lifecycle-check.py --sandbox` with zero real test receipts, and full compare with exactly one live receipt per owner. The sandbox/compare cases include two external repositories and an absolute source in the original session repository. The prior routing/configuration/failure/queue/space/symlink cases and unchanged capture suite remain protected.

R2 evidence and updated patch/manifests live in `/tmp/lh-gate-capture-main-deploy-r1/r2-evidence/`; original source/patch/receipts and actual structured blocked review are frozen there separately. `479531b` remains protected comparison-only with unresolved ownership; coordinator `01a078f8` is not its owner. No original development/main/host/settings/native/Reader change or separate37-row migration is included.

| Layer | R2 judgment |
|---|---|
| SDD | Existing side-effect-safe sandbox/compare and edit-identity contracts restored; no independent API or engine change |
| BDD | No app flow delta; shadow non-execution is truthful while existing live output remains authoritative |
| SSOT | Existing sandbox flag/root and host queue ownership retained; no live binding/configuration change |
| DDD | No independent domain vocabulary or business rule delta |

## Implementation map

- Affected scripts:
  - `.lazy-harness/scripts/tdd-cross-verify.ts` — `verifyTddCrossReferences` return shape
  - `.lazy-harness/scripts/affected-test-runner.ts` — `needsInterview` derivation
  - `.lazy-harness/scripts/test-match.ts` — shared `matchingTests`/`candidateTestPaths` (separator-insensitive + `__tests__`/`tests` + infix); single source for both gates
  - both gates: `existsSync` existence guard skips non-existent (quoted / cross-repo) source paths (`reason: not-found`) before asking
  - `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — `editTargetPaths` + `edit_target` field; both gate hooks scan `call.edit_target` (not `args_preview` body) — edit-target-only extraction
  - `.lazy-harness/scripts/lifecycle-parity-runner.py` — `sourceFiles` fixture support; `tdd-cross-verify-stop` writes its stub source so the existence guard passes on hosts (parity green→fail flip fix)
- Affected lifecycle helpers (unchanged in code, but rely on the new contract):
  - `.lazy-harness/hooks/lifecycle/helpers/check-tdd-cross-verify.sh`
  - `.lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh`
- Protection:
  - `.lazy-harness/scripts/self-test.py` — `check_tdd_cross_verify`, `check_affected_test_runner`
  - Fresh-fingerprint sanity test added so the dedup never silently swallows a brand-new ask.
  - `.lazy-harness/triggers/fixtures/tdd-cross-verify/KebabContractView.tsx` + `__tests__/kebab-contract-view.contract.test.tsx` — regression fixture; `check_tdd_cross_verify` asserts the PascalCase→kebab `.contract` layout is recognized (forceGate=false)
  - `check_tdd_cross_verify` asserts a non-existent source path is ignored (no question, forceGate=false) — quoted-path false-positive guard
  - lifecycle-shadow self-test asserts a `.md` edit that quotes a source path does NOT fire 5d-3 (`quoted_payload`); `tdd-cross-verify-stop` parity fixture + `tdd_payload` carry `edit_target`

## Manual reproduction proof

```
$ for i in 1 2 3; do bun .lazy-harness/scripts/tdd-cross-verify.ts \
    --files .lazy-harness/triggers/fixtures/tdd-cross-verify/missing-test.ts \
    --queue /tmp/test-q.xml --format json; done
run 1: forceGate=true  questions=1  failed=1   # asks once
run 2: forceGate=false questions=0  failed=1   # stays silent
run 3: forceGate=false questions=0  failed=1   # stays silent
```

Before the fix, all three runs reported `forceGate=true` (the loop).

## Discovery capture

- DDD: none — no domain term changes. The "interview gate" / "ask-once" idea is part of the existing ADR 0019/0020 ubiquitous language.
- SDD: candidate — should formalize the `verifyTddCrossReferences` and `runAffectedTests` return contracts, especially the `forceGate` semantics ("new unanswered question exists this response"). Tracked under follow-up; not blocking this fix.
- BDD: none — no visible user flow; the change is internal gate semantics.
- TDD: updated — this record + new dedup/fresh-fingerprint assertions in `self-test.py`.
- ADR: none — ADR 0019 / 0020 intent unchanged; this is a defect fix that brings code back in line with intent.
- SSOT: none — no config/schema/ownership change.

## Layer completeness

2026-06-28 matcher fix (shared `test-match.ts`) cross-layer judgement:
- SDD: none required — the test-matching heuristic is internal 5d-3 gate logic, documented in this record's Implementation map (`scripts/test-match.ts`); no separate component/contract record consumes it. A formal "test-match contract" SDD stays the non-blocking candidate noted in Discovery capture.
- BDD: none required — no product/user flow changed; the only visible effect is fewer false-positive 5d-3 STOPs, which is internal harness lifecycle, not an app behavior record.
- SSOT: none — no config/schema/ownership/source-of-truth changed; matching is heuristic, not driven by a stored glob/config.
- DDD: none — no new domain term; "matching test" is existing ADR 0019/0020 vocabulary.
