# Workflow Compression Router SDD

Status: draft-accepted
Date: 2026-05-19
Decision: ADR 0037

## Purpose

The workflow compression router summarizes existing lazy-harness obligations into a small typed route recommendation. It helps agents avoid re-interpreting every AGENTS rule on every request.

The router is advisory. Records, ADRs, hooks, and queues remain authoritative.

## Non-goals

The router must not:

- create a new canonical layer,
- replace DDD/SDD/BDD/TDD/ADR/SSOT,
- skip record-first search for host-dependent work,
- close question queues,
- write files,
- create records,
- auto-select a Recommended option,
- downgrade ambiguous or risky work.

## CLI contract

```bash
.lazy-harness/bin/lazy route --message "..." --format=json
.lazy-harness/bin/lazy route --message "..." --format=md
.lazy-harness/bin/lazy route --message "..." --format=md --log
.lazy-harness/bin/lazy route-summary --format=md
.lazy-harness/bin/lazy route-audit --commits=12 --format=md
```

Optional inputs:

```bash
--changed-files file1,file2
--file file1 --file file2
```

The command is read-only by default and exits 0 for all valid invocations. Invalid CLI flags exit non-zero before routing. `--log` intentionally appends non-canonical telemetry only.

## Telemetry contract

For real dogfooding work, route telemetry is collected automatically by the Jcode `response.completed` lifecycle hook when `last_user_message` exists. Agents may also use `--log` for explicit route probes:

```bash
.lazy-harness/bin/lazy route --message "..." --format=md --log
```

Telemetry path:

```text
.lazy-harness/logs/route-decisions.jsonl
```

Telemetry entry requirements:

- append-only JSONL,
- no raw user message,
- stable `messageHash`, optional `messageIdHash`, and `messageLength`,
- route axes: intent/scope/risk/confidence/gate/record/impl-map,
- evidence axes: matched/risk/scope/path signals, gate reason code, changed-file kinds, truncation flag,
- validation and non-negotiable summaries,
- non-canonical, never sufficient to close a queue or satisfy a record obligation.

Summary command:

```bash
.lazy-harness/bin/lazy route-summary --format=json
.lazy-harness/bin/lazy route-summary --format=md
```

`route-summary` reads `route-decisions.jsonl` and optional `route-feedback.jsonl` to report counts, ratios, and recommendations for second-stage AGENTS/profile/heuristic work.

`route-audit` reclassifies recent git commits using commit subject hashes plus changed file paths. It stores no raw commit subjects in output by default; it emits subject hashes, file counts, route axes, evidence, and false-negative flags.

Route audit flags include:

- `risk-review-required` — route risk is high;
- `destructive-evidence` — destructive/delete evidence is present;
- `contract-risk-path` — Prisma/TRPC/auth/permission path evidence is present;
- `possible-risk-undercall` — risk stayed low despite risk/path evidence;
- `destructive-without-gate` — destructive evidence exists but gate is none;
- `path-scope-undercall` — path evidence suggests behavior/contract but scope remains code-local;
- `candidate-for-contract-behavior-risk` — canonical-looking work still routes as candidate.

Automatic lifecycle telemetry is best-effort and silent. It must not emit hook output or change gate behavior. Duplicate lifecycle calls with the same `message_id` are deduplicated by `messageIdHash`. The response hook passes dirty/staged changed file paths to the router when available so risk visible only in diffs can influence telemetry.

The response hook must parse the lifecycle payload from stdin, not by copying the full payload into an environment variable. Real `response.completed` payloads can include large `recent_tool_calls` previews, so env-based parsing can silently fail before telemetry is appended. The hook accepts `last_user_message` plus camelCase/input aliases for forward compatibility. If no usable message field exists, it may append non-canonical diagnostics to `.lazy-harness/logs/route-telemetry-debug.jsonl`, but that file must store payload keys, byte counts, hashes, and alias presence only, never raw user message content.

Operational timing: telemetry is primarily useful **after sustained normal use**, not from one-off immediate inspection. Immediate checks may verify plumbing only: hook registration, append behavior, JSONL validity, and dedupe. Decisions such as AGENTS compression, profile presets, or router heuristic changes should wait for accumulated dogfooding samples and `route-summary` trends.

## Output schema

```json
{
  "ok": true,
  "mode": "workflow-route",
  "schemaVersion": "1.0",
  "message": "...",
  "changedFiles": [],
  "route": {
    "intent": "feature | fix | refactor | investigation | docs | release | unknown",
    "scope": "trivial | code-local | behavior | contract | ownership | unknown",
    "risk": "low | medium | high",
    "confidence": "low | medium | high",
    "affectedLayers": ["ddd", "sdd", "bdd", "tdd", "adr", "ssot"],
    "recordSearch": {
      "mode": "none | recommended | required",
      "targets": [],
      "reason": "string"
    },
    "recordCapture": {
      "mode": "none | candidate | canonical",
      "target": null,
      "reason": "string"
    },
    "implementationMap": {
      "tier": "none | file-map | symbol-flow | full-graph",
      "reason": "string"
    },
    "gate": {
      "mode": "none | narrow-confirm | option-gate",
      "reason": null
    },
    "validation": ["commit-time-lazy-test"],
    "nonNegotiables": [],
    "evidence": {
      "matchedSignals": [],
      "riskEvidence": [],
      "scopeEvidence": [],
      "pathEvidence": [],
      "gateReasonCode": "none | short-reference | high-risk | behavior | contract | ownership | unknown",
      "truncatedLikely": false,
      "changedFileCount": 0,
      "changedFileKinds": []
    }
  },
  "rationale": [],
  "warnings": []
}
```

## Axis definitions

### `intent`

| Value | Meaning |
|---|---|
| `feature` | Add or change capability. |
| `fix` | Bug/regression correction. |
| `refactor` | Internal restructuring with intended behavior preservation. |
| `investigation` | Analysis, diagnosis, evaluation, planning, or research. |
| `docs` | Documentation/prose-only request. |
| `release` | Build, publish, deploy, version, hotfix, or release notes. |
| `unknown` | Router cannot classify with enough confidence. |

### `scope`

| Value | Meaning |
|---|---|
| `trivial` | Copy/style/comment/prose with no host-specific contract or behavior impact. |
| `code-local` | Local implementation change without known user-visible or contract change. |
| `behavior` | User-visible flow, UI behavior, CLI behavior, or scenario change. |
| `contract` | API, IPC, schema, component props, config/env, hook contract, CLI contract. |
| `ownership` | Source-of-truth, project identity, rule placement, upstream/downstream boundary. |
| `unknown` | Scope unclear. |

### `risk`

| Value | Meaning |
|---|---|
| `low` | Reversible, local, no data/release/security boundary. |
| `medium` | Behavior/contract/test/hook impact or non-trivial implementation. |
| `high` | Destructive, irreversible, release, database, auth/security, source-of-truth ownership. |

### `recordSearch.mode`

| Value | Meaning |
|---|---|
| `none` | No host detail dependency detected. |
| `recommended` | Useful context likely exists, but failure to search is not a router-level force gate. |
| `required` | Host-dependent detail, contract, behavior, risk, ownership, or ambiguity detected. |

`required` does not itself perform the search. The agent must still use AGENTS/records.

### `recordCapture.mode`

| Value | Meaning |
|---|---|
| `none` | No durable capture needed. |
| `candidate` | Durable non-canonical capture in candidates/planning is enough for now. |
| `canonical` | Confirmed truth, contract, behavior, regression, ownership, or decision must converge to DDD/SDD/BDD/TDD/ADR/SSOT. |

### `implementationMap.tier`

| Value | Meaning |
|---|---|
| `none` | No implementation impact. |
| `file-map` | Files/roles/validation are enough. |
| `symbol-flow` | Key symbols, flow, and focused tests required. |
| `full-graph` | MD map + graph.jsonl edges + generated index expectation. |

### `gate.mode`

| Value | Meaning |
|---|---|
| `none` | No human decision needed before safe progress. |
| `narrow-confirm` | One likely candidate exists, but confirmation is useful or required. |
| `option-gate` | Multiple real outcomes, unresolved ambiguity, high risk, or source-of-truth conflict. |

## Default action table

| Scope | Risk | Record search | Capture | Impl map | Gate | Validation |
|---|---|---|---|---|---|---|
| trivial | low | none | none | none | none | commit-time-lazy-test |
| code-local | low | recommended | candidate | file-map | none | focused-test if obvious + commit-time-lazy-test |
| code-local | medium | required | candidate | file-map | narrow-confirm if record/code uncertain | focused-test + lazy-test |
| behavior | medium | required | canonical | symbol-flow | narrow-confirm or option-gate if flow ambiguous | focused-test + lazy-test |
| contract | medium | required | canonical | symbol-flow | narrow-confirm or option-gate if choices exist | focused-test + lazy-test |
| ownership | high | required | canonical | full-graph | option-gate | explicit-confirmation + lazy-test + doctor-smoke |
| any | high | required | canonical | full-graph | option-gate | explicit-confirmation + lazy-test + doctor-smoke |
| unknown | any | required | candidate | file-map | option-gate | lazy-test |

## Compression rules

Allowed:

- deduplicate repeated questions,
- batch related questions,
- emit one route summary,
- use narrow-confirm for one high-confidence candidate,
- reuse already-answered evidence,
- recommend without self-selecting.

Forbidden:

- skipping record-first search where required,
- suppressing real ambiguity,
- treating candidate as canonical,
- treating generated cache as canonical,
- chat-only queue closure,
- tool calls after unresolved force gate,
- hidden source-of-truth decisions.

## Heuristic classification guidance

The initial router is deterministic and conservative:

- Destructive/release/db/auth/security/force-push/delete/drop/migration → high risk, option-gate.
- API/IPC/schema/env/config/hook/CLI/component prop → contract.
- UI/user flow/screen/button/click/behavior/scenario → behavior.
- source-of-truth/ownership/upstream/downstream/rule placement/project identity → ownership.
- Changed files under schema/model directories, API/RPC router paths, auth/permission paths, UI screens/components, and tests produce path evidence independent of message text.
- Combined route should use max-risk/max-scope semantics: changed-file evidence may escalate a seemingly trivial or vague message.
- `messageLength >= 500` is marked `truncatedLikely` because lifecycle payload extraction can cap long messages.
- bug/regression/fix → fix intent, tdd affected.
- refactor/cleanup/internal → refactor intent.
- docs/readme/comment/copy typo → docs/trivial unless host policy terms appear.
- unclear short pronouns or ambiguous references → unknown, option-gate.

## Implementation map

- `.lazy-harness/scripts/task-router.ts` implements the read-only CLI.
- `.lazy-harness/bin/lazy` dispatches `route`.
- `.lazy-harness/hooks/lifecycle/on-response-completed.sh` supplies dirty/staged changed-file path context to automatic route telemetry.
- `.lazy-harness/fixtures/task-router/*.json` define self-test cases.
- `.lazy-harness/scripts/self-test.py` validates fixtures and read-only invariants.
