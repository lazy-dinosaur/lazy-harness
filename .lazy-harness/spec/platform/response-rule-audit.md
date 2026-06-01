# SDD — Response Rule Audit

Status: accepted
Date: 2026-06-01
Layer: SDD
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SDD: `.lazy-harness/spec/platform/relevant-record-query.md`
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
Related plan: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - implementing or debugging `response.completed` audits for records surfaced before a turn
  - checking whether pre-response relevant-record context was ignored
  - designing journal state for surfaced digest ids
  - designing packet evidence journals for Context Delivery required-read audit
  - moving tool-attached project policy into response lifecycle audit
- Must:
  - read sanitized surfaced digest journal state written by `message.received`
  - read sanitized Context Delivery packet evidence journal only when it can be correlated by safe message/session hashes
  - keep clean turns silent
  - emit concise audit feedback only when evidence strongly shows a surfaced rule or record-completion obligation was missed
  - keep Context Delivery required-read audit advisory-only until dogfood evidence justifies stronger guidance
  - avoid storing raw user/assistant message bodies in journal state
  - keep journal state non-canonical under `.lazy-harness/state/`
- Must not:
  - make generated journal state a source of truth
  - replace deliberate record reads when the audit surfaces a concern
  - encode project policy as one concrete tool branch instead of artifact/context evidence
- Record completion:
  - changes to surfaced digest journal shape, packet evidence journal shape, response audit criteria, or emitted audit output update this SDD and Phase 4/Phase 7 tests
- Related records:
  - `.lazy-harness/spec/platform/pre-response-rule-context.md`
  - `.lazy-harness/ssot/harness-enforcement-policy.md`
  - `.lazy-harness/spec/platform/record-decision-broker.md`
  - `.lazy-harness/tests/response-rule-audit.md`

## Purpose

Response Rule Audit is Phase 4 of the active lazy-harness memory loop:

```text
message.received
→ relevant-record query
→ compact digest injection
→ sanitized surfaced digest journal
→ assistant response/actions
→ response.completed audit/backstop
```

It checks whether the agent ignored a surfaced rule or missed a mandatory record-completion obligation after relevant rules were already injected before the response.

In Phase 5 it also becomes the replacement surface for the historical PR body tool-attached hard block. PR body structure is no longer enforced in `tool.execute.before` by `check-rule-action-boundary.py`; it is surfaced before response and audited after response.

## Journal state contract

Path:

```text
.lazy-harness/state/surfaced-rule-digests.jsonl
```

Status:

- non-canonical runtime state,
- safe to prune,
- not a source of truth,
- used only to connect pre-response context with post-response audit.

Row shape:

```json
{
  "schemaVersion": "1.0",
  "event": "message.received.digest",
  "timestamp": "2026-06-01T00:00:00Z",
  "epochSeconds": 1760000000,
  "messageIdHash": "16-char-hash-or-null",
  "sessionIdHash": "16-char-hash-or-null",
  "turnCount": 42,
  "estimatedTokens": 240,
  "truncated": false,
  "injected": true,
  "entries": [
    {
      "recordPath": ".lazy-harness/ssot/pr-description-format.md",
      "title": "SSOT: Pull request description format",
      "layer": "SSOT",
      "status": "active",
      "scope": "team-policy",
      "recordCompletion": "confirmed PR description changes update this SSOT",
      "bullets": ["Use Why / What / Task sections"]
    }
  ]
}
```

Privacy requirements:

- no raw `last_user_message`, assistant response, full prompt, or full transcript,
- no raw matched cues from user text,
- record paths, titles, record-completion text, and record-authored bullets are allowed,
- message/session identifiers are stored as short stable hashes only.

Retention:

- append-only JSONL with bounded pruning,
- current implementation keeps the newest 200 rows,
- matching prefers same message id hash, then same session id hash.
- payloads without message/session identifiers are not matched to the latest row; this avoids false positives from unrelated fresh digests.
- source-repo `.gitignore` excludes this runtime journal; downstream hosts already ignore installed `.lazy-harness/` via lazy-init.

## Packet evidence journal contract

Path:

```text
.lazy-harness/state/context-delivery-packets.jsonl
```

Status:

- non-canonical runtime state,
- safe to prune,
- not a source of truth,
- produced by explicit `lazy context-delivery --journal`, not by heavy `message.received` work.

Row shape:

```json
{
  "schemaVersion": "1.0",
  "event": "context-delivery.packet",
  "timestamp": "2026-06-01T00:00:00Z",
  "epochSeconds": 1760000000,
  "messageIdHash": "16-char-hash-or-null",
  "sessionIdHash": "16-char-hash-or-null",
  "turnCount": 7,
  "packetHash": "16-char-hash",
  "instructionLevel": "self-resolve-before-change",
  "confidence": 0.76,
  "requiredReadCount": 2,
  "optionalReadCount": 1,
  "candidateMeaningCount": 1,
  "fallbackSearchCount": 2,
  "requiredRead": [
    {
      "path": "src/features/reservations/ReservationTable.tsx",
      "kind": "source",
      "confidence": 0.82,
      "matchedQueryCount": 3
    }
  ],
  "optionalRead": [],
  "notes": ["contextIndexSource=generated"]
}
```

Privacy requirements:

- no raw user message, assistant response, prompt, or transcript,
- no raw record bullets or raw grep chunks,
- required/optional read paths, kind, layer, confidence, symbol names, query counts, and short hashes are allowed,
- rows without message/session identifiers are not matched for audit.

## Audit criteria

The Phase 4 helper is intentionally conservative.

It emits output only for strong evidence cases:

1. **Surfaced PR description rule ignored**
   - A surfaced digest entry references PR description or PR workflow guidance.
   - The response turn contains a PR artifact creation/update signal.
   - The PR artifact body evidence lacks `Why:`, `What:`, and `Task:` headings.
2. **Mandatory record-completion guidance missing**
   - A surfaced digest entry has `recordCompletion` text.
   - The turn evidence suggests a confirmed rule/correction/contract/regression/source change.
   - There is no same-turn `.lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}` or knowledge graph capture in recent write tool evidence.

Phase 7 adds one advisory-only case:

3. **Context Delivery required-read evidence may be missing**
   - A correlated packet evidence row exists.
   - The row has `requiredRead` paths and sufficient confidence.
   - The turn uses a mutation tool.
   - Recent read/search evidence does not reference any required-read path.
   - Output starts with `ADVISORY`, never `STOP`.

Everything else stays silent.

## Output contract

When an issue is detected, the helper prints plain text. The response hook wraps it in the standard system-reminder injection JSON.

Example:

```text
STOP. Response rule audit: surfaced PR description guidance appears to be ignored.

문제: 이번 turn 전에 PR description 관련 record가 surfaced 되었지만, 생성/수정된 PR artifact에서 Why / What / Task 구조를 확인하지 못했습니다.

해야 할 일:
  A. PR body를 Why / What / Task 구조로 수정하고 다시 실행 (Recommended)
  B. 이 PR이 예외라면 관련 SSOT/ADR에 예외 사유를 기록
```

Packet advisory example:

```text
ADVISORY. Context Delivery audit: required-read evidence may be missing.

문제: 이번 turn에 Context Delivery Packet requiredRead가 기록되었고 파일 변경 도구가 사용되었지만, 변경 전 requiredRead 경로를 읽은 증거를 찾지 못했습니다.
```

Clean turn contract:

```text
stdout = ""
exit = 0
```

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — writes sanitized surfaced digest journal after successful digest injection.
  - `.lazy-harness/scripts/context-delivery.ts` — writes sanitized packet evidence journal for explicit `--journal` use.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — reads the journal and emits conservative response audit feedback.
  - `.lazy-harness/hooks/lifecycle/on-response-completed.sh` — runs the audit helper in the legacy response.completed chain.
  - `.lazy-harness/scripts/lifecycle-check.py` — runs the same audit helper in shadow/orchestrator lifecycle checks.
  - `.lazy-harness/scripts/self-test.py` — protects journal privacy, ignored surfaced PR rule detection, missing record-completion detection, and silent clean turns.
  - `.gitignore` — excludes `.lazy-harness/state/surfaced-rule-digests.jsonl` runtime state in the source checkout.
  - `.gitignore` — excludes `.lazy-harness/state/context-delivery-packets.jsonl` runtime state in the source checkout.
- Key symbols:
  - `sanitized_entries` (`on-message-received.sh`) — strips query output down to record-authored fields.
  - `surfaced-rule-digests.jsonl` (`on-message-received.sh`) — non-canonical journal state.
  - `matching_journal` (`check-response-rule-audit.py`) — resolves same-turn digest state by safe hashes/freshness.
  - `appendPacketJournal` (`context-delivery.ts`) — appends bounded sanitized packet evidence rows.
  - `packet_required_paths` (`check-response-rule-audit.py`) — extracts required-read paths from packet evidence.
  - `has_required_read_evidence` (`check-response-rule-audit.py`) — checks recent read/search tool evidence before advisory output.
  - `pr_artifact_missing_headings` (`check-response-rule-audit.py`) — artifact/context check for PR body structure.
  - `mandatory_record_completion_missing` (`check-response-rule-audit.py`) — conservative record-completion check.
  - `check_response_rule_audit_from_surfaced_digest` (`self-test.py`) — Phase 4 regression fixture.
- Flow:
  1. `message.received` receives current user message.
  2. Relevant Record Query returns JSON digest entries with `--require-digest`.
  3. Hook renders the injection body and appends sanitized entry metadata to `.lazy-harness/state/surfaced-rule-digests.jsonl`.
  4. `response.completed` runs normal helpers and the new response rule audit helper.
  5. Audit helper matches journal row for the message/session and emits only on strong miss evidence.
  6. Explicit `lazy context-delivery --journal` may append packet evidence for dogfood collection.
  7. Packet audit emits advisory-only output when correlated required-read evidence appears ignored before mutation.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest`
  - `.lazy-harness/scripts/self-test.py#check_context_delivery_packet_journal_phase7`
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection`
  - `.lazy-harness/scripts/lifecycle-parity-runner.py`
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
  - SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
  - Planning: `.lazy-harness/planning/record-query-context-loop-transition-plan.md`
  - SDD: `.lazy-harness/spec/platform/record-decision-broker.md`
  - TDD: `.lazy-harness/tests/response-rule-audit.md`
- Machine index:
  - graph ids: `kg_sdd_response_rule_audit_spec`, `kg_response_rule_audit_helper_impl`, `kg_response_rule_audit_journal_impl`, `kg_response_rule_audit_self_test`

## Rule placement

- Rule: `response.completed` audits surfaced digest misses using sanitized pre-response journal state, but successful/clean turns must remain silent.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/response-rule-audit.md`
- Why not AGENTS.md: this is a platform lifecycle contract and runtime state design, not universal grammar text.
- Why not `.jcode`: the behavior is shared lazy-harness framework behavior and must sync to downstream hosts.
- Confirmation: user approved proceeding with the recommended Phase 4.

## Discovery capture

- DDD: no domain vocabulary change.
- SDD: this file captures Phase 4 contract.
- BDD: agent behavior changes only when a surfaced rule is missed; normal turns stay silent.
- TDD: `.lazy-harness/tests/response-rule-audit.md` and self-test fixtures added.
- ADR: no successor ADR needed; implements ADR 0041.
- SSOT: no new ownership policy; implements harness enforcement policy.
- Planning: record-query context loop Phase 4 now implemented.
