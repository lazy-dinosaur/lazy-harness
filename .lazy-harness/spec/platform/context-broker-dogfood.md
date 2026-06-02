# SDD — Context Broker Dogfood Collector

Status: accepted
Date: 2026-06-01
Layer: SDD
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
Related SDD: `.lazy-harness/spec/platform/record-decision-broker.md`
Related SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related TDD: `.lazy-harness/tests/context-broker-dogfood.md`
Related plan: `.lazy-harness/planning/native-context-broker-implementation-plan.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - collecting dogfood evidence for Native Context Broker before runtime hook integration
  - checking HostApp or HostApp PWA context-delivery and record-decision behavior after sync
  - deciding whether response.completed shadow/advisory integration has enough false-positive evidence
- Must:
  - run only as an explicit CLI, not from `message.received` or `response.completed`
  - distinguish automatic shadow journals from explicit aggregate dogfood collection
  - collect sanitized context-delivery and record-decision summaries from host roots
  - store case labels and message hashes, not raw user messages
  - keep output under `.lazy-harness/state/` as non-canonical runtime evidence
  - preserve clean/no-record-needed decision evidence for dogfood turns that only collect data
  - report host marker and per-case errors without mutating canonical records
  - leave confirmed/grounded canonical record promotion to the agent workflow after analysis
- Must not:
  - blindly/directly write canonical DDD/SDD/BDD/TDD/ADR/SSOT records from raw collector rows
  - store raw prompts, full transcripts, raw record bullets, or raw grep chunks
  - replace response.completed audit or imply STOP-level enforcement
- Record completion:
  - changes to dogfood row shape, privacy fields, default cases, host execution behavior, or CLI name update this SDD, TDD record, ADR 0041, the native context broker plan, and self-test fixture
- Related records:
  - `.lazy-harness/spec/platform/context-delivery-contract.md`
  - `.lazy-harness/spec/platform/record-decision-broker.md`
  - `.lazy-harness/tests/context-broker-dogfood.md`

## CLI

```bash
.lazy-harness/bin/lazy context-dogfood \
  --host /path/to/host-project-a \
  --host /path/to/host-project-b \
  --case surface::"기능패널 고쳐줘" \
  --format=md
```

Default output path:

```text
.lazy-harness/state/context-broker-dogfood.jsonl
```

Default cases when none are supplied:

- `feature-surface::기능패널 고쳐줘`
- `status-readonly::상태 요약`

## Operator handoff — when the user says “dogfood 확인해줘”

Run the explicit aggregate collector from the lazy-harness source root. The user should not have to prepare inputs manually.

```bash
SOURCE_ROOT="$PWD"
SOURCE_SHA="$(git rev-parse HEAD)"

for HOST in /path/to/host-project-a /path/to/host-project-b; do
  bun .lazy-harness/scripts/lazy-sync.ts --from "$SOURCE_ROOT" --target "$HOST" --force
done

.lazy-harness/bin/lazy context-dogfood \
  --host /path/to/host-project-a \
  --host /path/to/host-project-b \
  --format=md
```

Then verify:

```bash
for HOST in /path/to/host-project-a /path/to/host-project-b; do
  (cd "$HOST" && .lazy-harness/bin/lazy test)
  (cd "$HOST" && python3 .lazy-harness/scripts/doctor.py --profile smoke)
  (cd "$HOST" && python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --root . --format=json)
done
```

Success criteria:

- both host markers match the source `HEAD` after sync,
- collector writes sanitized rows to `.lazy-harness/state/context-broker-dogfood.jsonl`,
- each row has `messageHash` and no raw case message,
- feature-surface case produces useful Context Delivery required-read evidence,
- status-readonly case stays `recordDecision.disposition=no-record-needed`,
- host `lazy test`, doctor smoke, and hard-stop audit pass.

Do not promote response.completed behavior from this alone. Summarize row counts, required-read paths, dispositions, errors, and false-positive observations first; only then design audit/advisory changes.

## Row shape

Each row is sanitized runtime evidence:

```json
{
  "schemaVersion": "1.0",
  "event": "context-broker.dogfood",
  "timestamp": "2026-06-01T00:00:00.000Z",
  "host": "/path/to/host-project-a",
  "hostMarker": "cb23317a96d6...",
  "caseLabel": "reservation",
  "messageHash": "16-char-hash",
  "contextDelivery": {
    "ok": true,
    "instructionLevel": "self-resolve-before-change",
    "confidence": 0.6,
    "requiredReadCount": 1,
    "optionalReadCount": 2,
    "candidateMeaningCount": 1,
    "fallbackSearchCount": 3,
    "topRequiredRead": [
      { "path": ".lazy-harness/behavior/feature-surface.md", "kind": "record", "confidence": 0.82 }
    ]
  },
  "packetJournal": {
    "checked": true,
    "hasMessageHash": true,
    "rawMessagePresent": false
  },
  "recordDecision": {
    "ok": true,
    "disposition": "no-record-needed",
    "trigger": "validation-only",
    "confidence": 0.86,
    "recommendedActions": ["none"]
  },
  "errors": []
}
```

## Execution rules

1. For each host/case, run host-local `lazy context-delivery --journal --format=json`.
2. Read the latest host packet journal row only to verify sanitized journal behavior.
3. Run host-local `lazy record-decision --validation-only` because the collector itself should not blindly create durable record obligations; the agent workflow must promote confirmed/grounded dogfood findings into canonical records after analysis.
4. Append one sanitized row per host/case to the collector output unless `--dry-run` is set.
5. Keep failures per-row in `errors`; do not fail the whole collector for one bad case unless the script itself cannot run.

## Privacy rules

Allowed:

- host path,
- host sync marker,
- case label,
- message hash,
- context/decision counts,
- required-read paths/kinds/confidence,
- record-decision disposition/trigger/action names,
- compact error summaries.

Forbidden:

- raw case message in JSONL or JSON output,
- raw user prompt or assistant response,
- full transcript,
- raw record bullets,
- API keys/secrets.

## Relationship to future response.completed integration

This collector is the explicit aggregate step before stronger response.completed shadow/advisory wiring.

There are two evidence streams:

1. Automatic shadow journal: normal development can append sanitized Record Decision observations via `response.completed` to `.lazy-harness/state/record-decision-packets.jsonl`.
2. Explicit aggregate dogfood: `lazy context-dogfood` must be run by the agent/operator to compare real hosts and collect Context Delivery + Record Decision summaries in `.lazy-harness/state/context-broker-dogfood.jsonl`.

The user does not need to hand-collect evidence, but the agent must still run the explicit collector when asked to check dogfood. If the analysis finds confirmed or strongly grounded framework knowledge, the agent workflow must automatically create/update the appropriate canonical records.

It should answer:

```text
Do Context Delivery and Record Decision Packets produce stable, sanitized, low-noise evidence on real hosts?
```

If enough rows show clean/no-record-needed behavior and useful candidate-needed cases, future response.completed advisory or stricter audit integration can consume or generate similar packets. Until then, this collector remains explicit and non-blocking.

## Implementation map

- Status: `implemented`
- Primary files:
  - `.lazy-harness/scripts/context-broker-dogfood.ts` - explicit collector CLI.
  - `.lazy-harness/bin/lazy` - exposes `lazy context-dogfood`.
  - `.lazy-harness/scripts/context-delivery.ts` - host-local Context Delivery packet and packet journal source.
  - `.lazy-harness/scripts/record-decision-broker.ts` - host-local Record Decision Packet generator.
  - `.lazy-harness/scripts/self-test.py` - `check_context_broker_dogfood_collector` fixture.
  - `.gitignore` - excludes `.lazy-harness/state/context-broker-dogfood.jsonl`.
- Flow:
  1. Operator runs `lazy context-dogfood` with one or more `--host` roots.
  2. Collector invokes host-local lazy CLIs.
  3. Collector writes sanitized JSONL rows to its own state path.
  4. Later analysis can summarize false-positive/coverage behavior before hook integration.
  5. Next-session handoff starts from the Operator handoff command above when the user says “dogfood 확인해줘”.
- Protection:
  - `.lazy-harness/scripts/self-test.py#check_context_broker_dogfood_collector`
    - validates sanitized collector output and the Operator handoff / automatic-vs-explicit evidence stream contract.

## Validation plan

- Fixture host with reservation behavior record should produce a context-delivery success row.
- Collector JSON/JSONL must not contain raw `기능패널 고쳐줘` message.
- Record decision for collection-only dogfood should be `no-record-needed`.
- Markdown dry-run should render a summary without writing collector JSONL.
- HostApp and HostApp PWA should pass collector smoke after sync and marker check.

## Rule placement

- Rule: Native Context Broker dogfood evidence should be collected through an explicit sanitized CLI before response.completed integration.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/context-broker-dogfood.md`
- Why not AGENTS.md: this is an implementation/data-collection contract, not base agent grammar.
- Why not `.jcode`: this must sync to hosts and be usable by lazy-harness scripts.
- Confirmation: user-confirmed by selecting option B after generator completion.

## Discovery capture

- DDD: none.
- SDD: updated, this record defines the dogfood collector contract and next-run handoff.
- BDD: none; visible behavior is CLI/report output only.
- TDD: `.lazy-harness/tests/context-broker-dogfood.md` protects fixture behavior.
- ADR: ADR 0041 receives a dogfood collector follow-up note.
- SSOT: rule lifecycle references explicit dogfood evidence before hook integration.
- Planning: native context broker plan marks dogfood collector implemented and next dogfood evidence loop active.
