# TDD — Original request-list projection

## Rule digest

- Status: advisory
- Layer: TDD
- Scope: host-project
- Aliases:
  - request-list projection
  - 요청 목록 투영
- Applies when: Building offline assessment packets for the approved V2 request-list loss fix.
- Must: Preserve the first-stage declared request independently of returned documents; retain original collection, answers, historical failures, private mapping and deterministic packet order.
- Must not: Infer an empty request from missing provenance, reconstruct requests from final answers/prose/lookup, or promote focused projection checks into model-study success.

## Approval and minimal contract

The latest execution approval in `.lazy-harness/planning/v2-change-tracking-reliability-plan.md` authorizes the minimal fix and real protection checks. This TDD owns the implementation/regression delta; Planning, policies, graph and unrelated experiments remain outside worker write scope.

`assessmentPackets` reads `trials[i].stages[0].runtime.structuredOutput.requested_source_ids`: the original channel used by `protocol.mjs#parseOutput` and snapshotted before lookup by `workflow-body.js`. It copies the declared array without sorting, deduplication or repair, including recognizable malformed declarations. An original `final` envelope with an explicit empty array represents no request. An absent/unreadable declaration or unrecognized original envelope kind throws an explicit provenance error, consistent with the existing missing-run error; no partial packet output or fabricated empty request is returned.

Minimal assessment output delta:

- `requested_source_ids` now means the original first-stage declaration, not response item IDs.
- New `returned_source_ids` contains only lookup items with `status === 'ok'`, in response order. Under the existing lookup contract these items contain supplied source content; `not_found` placeholders are not returned documents.
- `source_response` remains unchanged and retains all statuses, including `not_found` and `invalid_request`. No lookup yields no returned documents, not proof of no original request.
- Initial/final answers, structural errors, manual review fields, private mapping and review-ID ordering are unchanged. Original malformed answers and historical assessment packets are never rewritten.

## Regression coverage

`request-list-projection.test.mjs` protects actual S3B's three declared requests plus zero-item `invalid_request`, valid lookup order, mixed `not_found`/returned content, explicit no request, missing/unreadable first metadata with misleading final/prose/lookup alternatives, malformed-array preservation, and collection/answer/mapping/order immutability. Its minimal S3B extraction names exact source path, SHA256 and JSON pointers; no evaluator answers are included.

The original collection and T0 observation are preserved byte-for-byte under `.local/v2-change-tracking-01/before/`, alongside pre-change assess/runner snapshots, Git status/diff/HEAD and hash ledger. `before/approval.json` quotes the user-confirmed Planning approval verbatim, distinguishes capture time from unknown original event time, and records still-unchanged source at T1.

An ambient markdownlint hook reformatted the optional Planning Markdown snapshot after capture, leaving its old ledger hash stale. Both remain preserved. Supervisor-approved recovery captured new current Planning bytes as `planning-current-recovery.bin`; the parent intentionally appended unrelated read-only research while the worker was blocked. `snapshot-anomaly.json` distinguishes this current-source drift from the snapshot formatting anomaly and verifies all four required original snapshots unchanged. No settings were changed.

## Validation evidence

One combined focused checkpoint: `node --test experiments/v2-reading-comparison/runner.test.mjs experiments/v2-reading-comparison/request-list-projection.test.mjs` — **33 passed, 0 failed/skipped, 181.10384 ms**, exit 0; no retry. Existing 26 tests plus seven new tests. The existing offline preparation test generates temporary fixtures only, not future study inputs.

Actual offline reproduction: `node .local/v2-change-tracking-01/reproduce-request-list.mjs` — exit 0. Original S3B now projects requested 3 / returned 0 with unchanged `invalid_request`, rather than historical requested 0. Raw collection/T0 observation bytes, original answers and private mapping remain unchanged. Current assess SHA256: `573e0f7be7081af38c6ec4526a9ad57c4201b34fe342a9a811045f9a6cf66060`.

Exact commands, exit codes, timestamps and log hashes are in `.local/v2-change-tracking-01/commands.json`; first-run logs and `post-fix-reproduction.json` are retained. Ambient pi-lens reported JavaScript/TypeScript clean on changed source/test writes; no direct LSP tool or build was invoked. Parent owns the single final `lazy check` / `lazy validate --plan standard` boundary and independent review. These are real T2 projection checks only, not a model/CLI trial, new generic runner, study-input preparation or broad selftest.

### Parent checkpoint
- Independent reviewer `7d84ee8c-e5bb-4420-b97c-e2d78babe56b` found no issues and returned ready-for-input-preparation. Static review only; original workflow `c8e6419a-c6f5-482b-b6b8-a9f0b3a6044f` completed.
- Parent independently checked six current source/evidence hashes against the after manifest: all matched before this evidence capsule was appended. Primary LSP checked changed source and new test:2 clean,0 diagnostics.
- Parent ran `lazy check` once (exit1,0.478s) and `lazy validate --plan standard` once (exit1,0.455s). Standard stopped at fast-static-check. Existing Archify image/archive artifacts were treated as text and rejected for NUL bytes; logs also warn about quoted non-ASCII temporary paths. This is not a green project validation or a failure of the33 focused projection checks.
- Remaining log entries also flag historical smoke/study native display artifacts named `.json` as JSON parse errors (`.local/v2-reading-runtime-iInlC0/...`); those original outputs are retained, not repaired or renamed to obtain green validation. No error entry names the newly changed projection source/test.
- Full command results and hash checks: `.local/v2-change-tracking-01/parent-validation-01.json`; preserved logs `parent-check-01.log.bin` and `parent-standard-01.log.bin`. No cleanup, artifact deletion, policy change or retry performed. Existing unrelated validation maintenance remains separate from the approved study.

## Implementation map

- `experiments/v2-reading-comparison/assess.mjs` — `assessmentPackets`: original first-stage request projection, explicit provenance failure and returned-document list; existing offline CLI preserves original bytes.
- `experiments/v2-reading-comparison/protocol.mjs` — unchanged `parseOutput` selects native `structuredOutput`; `lookup` distinguishes `ok` content and `not_found` placeholders.
- `experiments/v2-reading-comparison/workflow-body.js` — unchanged first result snapshot precedes validation/lookup/resume.
- `experiments/v2-reading-comparison/request-list-projection.test.mjs` — seven named focused regression tests and provenance-linked minimal S3B fixture.
- `experiments/v2-reading-comparison/runner.test.mjs` — unchanged existing 26-test offline suite, combined into one checkpoint with new tests.
- `.local/v2-change-tracking-01/reproduce-request-list.mjs` — one-off actual raw collection reproduction, original answer/private-mapping/byte checks, new post-fix packet artifacts; not model input.
- `.lazy-harness/tests/v2-reading-comparison.md` — historical actual comparison and parent correction, retained unchanged.
- `.lazy-harness/tests/test-strategy.xml` — bounded focused validation authority.
- `.lazy-harness/spec/platform/code-organization-profile.md` — exact creating/modifying source policy and capability resolution found advisory baseline only. COP-01/02/03/05: request/response names stay distinct under the existing local packet owner; no organization change needed.
- Machine graph/generated index: explicitly outside worker write scope; no automatic promotion.

## SDD/BDD/SSOT/DDD judgments

| Layer | Judgment |
|---|---|
| SDD | Experiment assessment contract correction and additive returned-document field documented above under approved minimal fix; no independent product API delta or separate SDD promotion. |
| BDD | No independent visible product-flow delta; offline projection only, original lookup/resume behavior unchanged. |
| SSOT | No independent ownership/config/policy delta; native original payload remains authority, artifact copies are evidence only. |
| DDD | No independent domain-rule delta; request versus returned-document distinction implements the approved experiment correction. |

## Discovery capture / Rule placement

This single TDD captures the approved fix, output semantics and regression evidence. No new operating policy or architecture choice. Parent retains Planning/graph ownership. Host migration remains separate: record-lint issues=1/advisories=0 and 37 legacy graph rows were previously surfaced; guided migration requires separate approval and can be resumed, never auto-rewritten here.
