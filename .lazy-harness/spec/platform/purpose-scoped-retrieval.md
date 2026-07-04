# Map-First Retrieval

Status: accepted
Layer: SDD
Date: 2026-06-22
Related ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`, `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md`
Related DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md`
Related BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md`
Related TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md`
Related SSOT: `.lazy-harness/ssot/cli-tool-boundary.md`

## Rule digest

- Status: active
- Layer: SDD
- Scope: framework-global
- Aliases:
  - lazy map
  - 맵 명령
  - drill-down
  - 드릴다운
  - overview 계약
- Applies when:
  - changing retrieval prompt guidance
  - changing `lazy map`, record-index, graph/index navigation, or search/read evidence semantics
  - reviewing whether a CLI should locate context for the agent
- Must:
  - make the LLM/searcher the semantic judgement owner
  - start from `lazy map --overview` as a project map/inventory
  - use `lazy map <feature-id|record-path|graph-id|source-path>` only for concrete nodes copied from the map/index
  - require real record/source/test reads before relying on map candidates
  - ask a 3-5 option gate or state the missing prerequisite when no concrete node exists
  - preserve rulebook/capability resolution as action-policy helpers, not fact search
- Must not:
  - use keyword grep/rg/find fallback after map traversal
  - expose or recommend `lazy find --purpose ...`
  - accept raw user text, long natural-language strings, or invented `--query` syntax as `lazy map` traversal input
- Record completion:
  - retrieval changes update ADR/DDD/BDD/TDD/SSOT, prompt hook, self-test, feature navigation, and graph/candidate rows together.

## CLI contract

Canonical retrieval entrypoints:

```bash
.lazy-harness/bin/lazy map --overview [--complete] [--format=json|md] [--limit=N] [--fresh]
.lazy-harness/bin/lazy map <feature-id|record-path|graph-id|source-path> [--format=json|md] [--limit=N] [--fresh]
.lazy-harness/bin/lazy rules resolve ...
.lazy-harness/bin/lazy capability resolve ...
```

Removed entrypoint:

```bash
.lazy-harness/bin/lazy find --purpose ...
```

`lazy map` is not a search box. It is a map traversal helper. The agent must inspect the overview, choose concrete nodes, read the linked records/source/tests, and only then answer or mutate.

## Map traversal flow

1. Run `lazy map --overview` to inspect layer counts, feature anchors, graph relation inventory, generated indexes, and drill-down candidates.
2. LLM chooses concrete nodes from the returned map: feature id, canonical record path, graph id, source path, or test path.
3. Run `lazy map <node>` for nearby records/source/tests/graph ids.
4. Read record bodies, Rule digest, Implementation map, graph links, source files, and tests.
5. If the map is empty or ambiguous, ask a 3-5 option gate or state the missing prerequisite; do not run keyword grep/rg/find fallback.

## Complete discovery mode

`default=모름` (ADR 0049) makes discovery — knowing which records EXIST — mandatory and non-skippable; the agent cannot self-certify that no relevant record exists. But the default `--overview` truncates each layer to `--limit` (e.g. 20), so layers with more records hide the rest, and an agent that only reads the overview silently skips them.

`lazy map --overview --complete` is the complete lean discovery index:

- lists every record (path, title, status) across all layers, untruncated (ignores `--limit` for the inventory);
- omits graph sample-row dumps and drill-down candidate dumps (compact graph relation counts are retained);
- sets `complete: true` and adds a complete-mode note in markdown.

Discovery (which records exist) is mandatory + complete + lean via this mode; loading (reading full record bodies) stays just-in-time and targeted — read the records the task implicates, not a read-until-all-layers sweep. See ADR 0049 for the discovery-vs-loading boundary.

## Retired purpose-scoped find

`lazy find` was removed after dogfood on 2026-06-22 showed agents delegated semantic search to exact-token CLI output, overused `--purpose fact`, and fabricated query-style `lazy map --query` commands. Cross-project validation also showed weak source recall:

- lazy-harness feature-navigation mapped path recall: 63/137.
- Medivance implementation-index source recall: 14/81.
- Medivance PWA implementation-index source recall: 39/94.

This evidence supports map/index traversal plus LLM-owned search/read judgement, not CLI-owned candidate retrieval.

## Implementation map

- Status: `map-first-retrieval-implemented`
- Primary files:
  - `.lazy-harness/scripts/record-map.ts` — overview and concrete node traversal helper; rejects free-form map input.
  - `.lazy-harness/hooks/lifecycle/on-message-received.sh` — static prompt now teaches map-first traversal and forbids raw user text/query flags for `lazy map`.
  - `.lazy-harness/bin/lazy` — no longer exposes `find` dispatch/help.
  - `.lazy-harness/ssot/capabilities.json` — no longer registers retrieval-purpose capabilities.
  - `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — no longer treats `lazy find` as search evidence.
  - `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — no longer treats `lazy find` as search evidence.
  - `.lazy-harness/project/feature-navigation.xml` — indexes `map-first-retrieval` rather than `lazy find`.
- Key symbols:
  - `record-map.ts:parseArgs`
  - `record-map.ts:validateTraversalKey`
  - `record-map.ts:buildRecordMapOverview`
  - `record-map.ts:buildRecordMapOverview` `complete` parameter — untruncated lean discovery index (ADR 0049)
  - `self-test.py:check_purpose_scoped_retrieval_cli` — retained name for compatibility, now protects map-first removal of `lazy find`.
- Tests:
  - `.lazy-harness/scripts/self-test.py#check_purpose_scoped_retrieval_cli`
  - `.lazy-harness/scripts/self-test.py#check_record_index_generator_phase3`
  - `.lazy-harness/scripts/self-test.py#check_message_received_hook_context_injection`
  - `.lazy-harness/scripts/self-test.py#check_read_debt_permit_generic_external_action`
  - `.lazy-harness/scripts/self-test.py#check_response_rule_audit_from_surfaced_digest`

## Layer completeness impact

- DDD: `.lazy-harness/domain/purpose-scoped-retrieval.md` redefines retrieval vocabulary around map-first traversal.
- BDD: `.lazy-harness/behavior/purpose-scoped-retrieval.md` defines the expected agent behavior.
- TDD: `.lazy-harness/tests/purpose-scoped-retrieval.md` protects removed `find`, map input rejection, and map-first prompts.
- SSOT: `.lazy-harness/ssot/cli-tool-boundary.md` remains the semantic-authority boundary.
- ADR: `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md` records the superseding decision.
- ADR: `.lazy-harness/decisions/0049-discovery-vs-loading-complete-lean-discovery.md` adds the discovery-vs-loading boundary and the complete lean discovery mode.
