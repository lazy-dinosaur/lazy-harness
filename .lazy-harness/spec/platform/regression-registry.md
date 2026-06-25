# SDD — Fix-Commit Regression Registry

Status: active
Layer: SDD

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Applies when:
  - working on the Fix-commit regression gate (`check-fix-regression.sh`), the regression registry, or its writer
  - debugging a repeating `STOP ... regression entry` advisory on a Fix commit
  - adding or auditing regression entries on any host
- Must:
  - read the registry as JSONL — parse each line and compare the `sha` field, so matching is whitespace/encoding agnostic (a `"sha": "x"` entry and a `"sha":"x"` entry are identical)
  - check only `.lazy-harness/regression/registry.jsonl` for gate satisfaction; `candidates.jsonl` auto-stubs (written by `post-commit.sh`) never satisfy the gate
  - write entries only through `lazy regression add` (validated, canonical serialize): enforce a 40-hex `sha`, reject whole-field `<...>` placeholder tokens in prose (`description`/`reproSteps`) and any embedded `<...>` in `protectedBy` paths, reject `pending` stubs, require ≥1 `protectedBy` path and non-empty `description`/`reproSteps`, and dedup by sha
  - expose `lazy regression lint` to flag invalid/garbage entries (bad sha, placeholder/pending fields, empty required fields, invalid JSON)
- Must not:
  - match the registry with a whitespace-sensitive substring grep (`"sha":"$SHA"`)
  - accept the `candidates.jsonl` auto-stub or a hand-appended raw JSON line as the sanctioned write path
  - mutate registry entries other than appending a validated line via the CLI
- Record completion:
  - changes to the reader, writer, lint, or gate behavior update this SDD, `.lazy-harness/tests/regression-registry.md`, the script/hook, dispatcher, self-test, and manifest together
- Related records:
  - `.lazy-harness/tests/regression-registry.md`

## Purpose

After a `Fix:` commit, the harness wants a durable regression entry — the bug, the test that protects it, and how to reproduce — so the fix cannot silently regress. `check-fix-regression.sh` is the post-turn advisory that nags until such an entry exists. The registry is host-owned runtime data (each host accumulates its own); the reader/writer/gate are framework-owned (Category A, synced).

## Registry format

`.lazy-harness/regression/registry.jsonl` — one JSON object per line:

```json
{"sha":"<40-hex>","description":"<bug>","protectedBy":["<test path>"],"reproSteps":"<repro>"}
```

JSON key order and intra-line whitespace are not significant; readers MUST parse JSON, not match substrings. `candidates.jsonl` holds auto-generated `post-commit.sh` stubs (`status:"candidate"`) and is a reminder surface only.

## Reader contract (`check-fix-regression.sh`)

- Fires only when the last commit subject starts with `Fix: ` (env `LAZY_LIFECYCLE_GIT_LAST_SUBJECT`/`LAZY_LIFECYCLE_GIT_HEAD` preferred, else git).
- Satisfaction: HEAD sha present as the `sha` field of any line in `registry.jsonl` (JSON-parse). Whitespace/format irrelevant.
- `candidates.jsonl` does NOT satisfy the gate (it auto-contains every Fix sha, which would make the gate toothless).
- When unsatisfied, emits a single `STOP` advisory directing the agent to `lazy regression add ...` (never to hand-append raw JSON).

## Writer contract (`lazy regression add`)

```bash
.lazy-harness/bin/lazy regression add --sha <40-hex> --description <text> --test <path> [--test <path>...] --repro <text>
```

- Validates: `sha` matches `^[0-9a-f]{40}$`; `description`/`reproSteps` non-empty and not a bare `<...>` placeholder token (embedded metavariables like `<roomId>` or `<Toaster/>` inside real prose are allowed); ≥1 `--test`, each free of any `<...>` placeholder and non-`pending`. Warns (does not block) when a `protectedBy` path is absent (it may be created by the same fix commit).
- Idempotent: a duplicate sha is a no-op.
- Canonical serialization (`{sha, description, protectedBy, reproSteps}`), appended to `registry.jsonl`. This is the only sanctioned write path — it makes placeholder garbage and malformed shas impossible to introduce.

## Lint contract (`lazy regression lint`)

`lazy regression lint [--format=json|md] [--fail-on-issues]` reports entries failing validation: `invalid-json`, `bad-sha`, `bad-description`, `bad-repro`, `missing-protected-by`, `placeholder-protected-by`, `pending-protected-by`. `bad-description`/`bad-repro` fire only when the prose field is empty or a bare `<...>` placeholder token — embedded metavariables (`<roomId>`, `<Toaster/>`), CLI args, and key/tag formats inside real prose are NOT flagged; `placeholder-protected-by` still fires on any `<...>` inside a `protectedBy` path. Read-only; supports host migration and the self-test.

## Enforcement boundary

- The reader is an L3 post-turn advisory (`response.completed`), not a blocking git hook (ADR 0016/0041/0048: dev edits stay non-blocking; the commit/push gate is `lazy test`).
- `post-commit.sh` keeps auto-writing a `candidates.jsonl` stub per Fix commit (reminder), independent of the gate.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/spec/platform/regression-registry.md` — this contract.
  - `.lazy-harness/tests/regression-registry.md` — regression contract.
  - `.lazy-harness/hooks/lifecycle/helpers/check-fix-regression.sh` — JSON-parse reader + STOP advisory.
  - `.lazy-harness/scripts/regression.ts` — validated `add` + `lint` CLI.
  - `.lazy-harness/bin/lazy` — dispatches `lazy regression`.
  - `.lazy-harness/hooks/post-commit.sh` — auto `candidates.jsonl` stub writer.
  - `.lazy-harness/scripts/self-test.py` — `check_fix_regression_registry`.
- Key symbols:
  - `cmdAdd` / `lintEntries` / `readEntries` (`.lazy-harness/scripts/regression.ts`).
- Tests / protection:
  - `.lazy-harness/scripts/self-test.py#check_fix_regression_registry`
  - `python3 .lazy-harness/scripts/self-test.py --scope framework`

## Rule placement

- Rule: the Fix-commit regression gate reads the registry by JSON-parsing the `sha` field (whitespace agnostic) and writes only through the validated `lazy regression add` CLI.
- Scope: framework-global
- Primary record: `.lazy-harness/spec/platform/regression-registry.md`
- Why not AGENTS.md: this is a platform validation/CLI contract, not prompt grammar.
- Why not local notes: shared framework behavior for all hosts.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: this contract.
- BDD: a Fix commit shows a STOP advisory until `lazy regression add` registers the sha; satisfied entries are silent.
- TDD: `.lazy-harness/tests/regression-registry.md` + self-test protect reader matching and writer validation.
- ADR: governed by ADR 0016/0041 (advisory gate, no new dev-time hard gate).
- SSOT: registry format defined here; registry data is host-owned runtime.
