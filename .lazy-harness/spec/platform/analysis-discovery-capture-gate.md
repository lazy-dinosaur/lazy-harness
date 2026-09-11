# Analysis Discovery Capture Gate

Status: accepted
Layer: SDD
Related ADR: `.lazy-harness/decisions/0034-analysis-discovery-plan-capture-gate.md`
Related TDD: `.lazy-harness/tests/capture-gate-false-positive.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - capture gate
  - 캡처 게이트
  - 발견 기록 강제
- Applies when:
  - analysis or a user correction yields a durable fact, reason, ownership boundary or plan
  - the Pi adapter completes a response with a capture judgement
- Must:
  - let the evidence-reading LLM judge necessity, relevance, same-fact reuse and current approval
  - capture required durable facts before completion, normally in one existing primary record
  - keep missing, failed, stale or unrelated structural evidence explicitly unverified
  - preserve the whole raw primary answer, independently of the capture packet/advisory
  - keep execution approval and destructive safeguards separate from storage evidence
- Must not:
  - classify raw user, assistant or tool text by layer/correction/plan keywords to emit capture STOP
  - equate absent judgement with no-record, or tool IDs/hashes with semantic truth or approval
  - force unchanged status to rewrite records or ask again merely to discharge capture
- Record completion:
  - packet/delivery changes update this SDD and the primary false-positive TDD
- Related records:
  - `.lazy-harness/ssot/cli-tool-boundary.md`
  - `.lazy-harness/spec/platform/record-write-update-policy.md`
  - `.lazy-harness/spec/platform/record-decision-broker.md`
  - `.lazy-harness/decisions/0038-requirements-first-change-gate.md`

## Candidate approval and legacy conflict

This isolated source candidate implements the user-selected B design1 direction:
LLM judgement plus runtime structural evidence, not a new completion tool. It is
not approval for live-host sync or adoption. The old at-least-three-layer + plan
keyword STOP and seven-label bypass are superseded **on analysis and correction
capture routes only** by this contract, consistent with CLI Tool Boundary.
Other safety helpers are not disabled. User corrections still require durable
capture when they change ownership, reasons, constraints or decisions; stale
implementation approval remains stale under ADR 0038.

Historical 2026-07-14 replace-alias fix and subsequent unresolved live recurrence
remain in the primary TDD and `.lazy-harness/evidence/2026-07-14-pi-agent-end-structural-trace.md`.
Their helper-only silence did not prove real successful storage. The legacy
threshold contract is not a second active rule for this candidate.

## Assistant envelope

The LLM emits its complete ordinary answer, then optionally one terminal envelope
when making a capture decision. Missing output is unverified, never no-record.
Mandatory capture expectations remain in model guidance; the runtime does not
infer that an unlabelled status response needs a record or an extra model turn.

```text
Primary answer, without replacing or abbreviating it.
<record-judgement>
{"disposition":"required","reason":"why capture is required","facts":[{"path":".lazy-harness/planning/example.md","fact":"the relevant fact, reason and ownership"}]}
</record-judgement>
```

- Dispositions: `required`, `reuse`, `no-record`, `pending`. Reason is nonempty.
- Facts: at most 20 nonempty `path`/`fact` pairs. Required/reuse need facts;
  no-record requires an empty list. Pending explicitly retains unresolved work.
- The envelope is at most 8192 UTF-8 bytes, exactly one opening/closing boundary,
  with nothing after the closing marker. Unknown fields/dispositions, malformed
  JSON or ambiguous boundaries remain unverified. No raw answer bytes are removed,
  including on a valid envelope. User/tool quoted packets cannot be judgements.
- Do not ask the LLM for unseen toolCallIds, hashes, root, session or epoch fields.
  The real adapter adds those it can verify. It never supplies semantic gold.
- Broker v1 remains an explicit advisory CLI: `record-updated` and recommended
  records are not receipts. Its separation of advisory judgement from canonical
  mutation is reused, not its incompatible no-receipt schema or automatic journal.

## Structural evidence and lifetime

`CaptureEvidence` belongs to one extension instance, one active root/work unit.
It retains at most 128 latest relevant targets (write/read receipts per target),
256 pending calls and 256 recent IDs. Unrelated calls do not displace target
receipts merely because `recent_tool_calls` projects the last 40 events. Eviction
is conservative: read the existing record and rejudge instead of duplicating it.

Session start/shutdown, real non-extension steer and invalidated work-unit
fingerprints clear capture state. A normal new turn advances the epoch; an old
write/read does not silently become current. Reuse requires a successful **current
read callback** plus current assistant `reuse` judgement and unchanged bytes.
A current required write remains usable after a matching readback. No separate
journal or cross-session restoration is introduced.

A link requires a nonempty string ID from an allowed started callback, matching
root, epoch, tool name, input fingerprint and canonical target, followed by actual
successful `tool_result` (`isError === false`; explicit `is_error=true` vetoes).
Args alone, missing result/content, missing/empty/nonstring ID, failed insert/edit,
late old callbacks or changed input cannot establish success. Supported leaf names
include write/edit/insert/replace/multiedit and filesystem write_file/edit_file;
namespaced forms are normalized structurally. Batch args without individual
successful callbacks are not receipts.

Targets are root-contained `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning,plans}/`
Markdown/XML/JSON/JSONL records and named knowledge candidate/draft/correction
JSONL stores. `memory.md`, external roots and escaping symlinks are not supported.
At result and response completion the adapter bounds file reads to 1 MiB and
checks current SHA-256 bytes. Larger/missing/changed files stay unverified.
A read callback may expose only a selected region; runtime readback proves bytes,
not that the LLM understood or read every fact. Relevance and completeness remain
LLM-owned, never keyword or substring classifiers.

## Delivery and protection

`on-response-completed.sh` invokes the shared capture helper once and returns its
`capture` object separately from the ordered safety `inject`. Both legacy and
orchestrator engines keep this separation. The explicit correction helper delegates
to the same transport, not another classifier/schema. Hook callers without the
adapter field do not gain a fabricated assessment; explicit helper inspection
returns unverified when it is absent.

Pi sends a separate `lazy-harness-capture` custom message with `triggerTurn:false`.
Pending/unverified is visible, linked/no-record is non-disruptive; assessment
metadata explicitly says semantic judgement unverified and approval not evaluated.
The primary assistant message is never replaced. Capture alone does not call
`sendUserMessage`, retry an action, solicit approval, or launch another LLM.
Other safety advisories retain their existing bounded continuation behavior.

## Implementation map

- Status: `needs-review`
- Validation: isolated candidate; acceptance evidence is in the primary TDD.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — real tool_call,
  tool_result and agent_end handlers; guidance and independent advisory delivery.
- `packages/lazy-harness-pi/extensions/lazy-harness/capture-evidence.ts` —
  `CaptureEvidence.start/complete/evaluate/reset`; bounded typed evidence authority.
- `.lazy-harness/hooks/lifecycle/helpers/check-analysis-discovery-capture.sh` —
  typed transport only; correction helper delegates here.
- `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — independent capture field.
- `.lazy-harness/scripts/lifecycle-check.py` — other safety helper order, no duplicate capture STOP.
- `tests/lazy-harness/pi-capture-evidence.test.ts` — official Pi ExtensionRunner
  callback dispatch, actual read/write tools and actual response hook/helper processes.
- `.lazy-harness/scripts/self-test.py#check_analysis_discovery_capture_helper` —
  helper shape checks and source-side adapter regression invocation.
- Graph: `kg_b_capture_structural_impl`, `kg_b_capture_structural_test`.

## Rule placement

- Scope: isolated candidate for framework-global capture transport.
- Primary narrative: `.lazy-harness/tests/capture-gate-false-positive.md`.
- This SDD owns only the independent packet/delivery contract delta.
- Confirmation: user-approved B source-path repair; no live integration approval.
