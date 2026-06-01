# Hook Compliance Dogfood Findings — 2026-06-01

Status: active dogfood finding
Layer: Planning
Date: 2026-06-01
Related SDD: `.lazy-harness/spec/platform/pre-response-rule-context.md`
Related SDD: `.lazy-harness/spec/platform/response-rule-audit.md`
Related SDD: `.lazy-harness/spec/platform/context-delivery-contract.md`
Related SDD: `.lazy-harness/spec/platform/context-broker-dogfood.md`
Related SDD: `.lazy-harness/spec/platform/record-decision-broker.md`
Related SDD: `.lazy-harness/spec/platform/guidance-ladder.md`
Related ADR: `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
Related candidates:

- `.lazy-harness/knowledge/candidates.jsonl#candidate_dogfood_message_received_digest_not_enough_required_read_20260601`
- `.lazy-harness/knowledge/candidates.jsonl#candidate_model_provider_hook_injection_verification_20260601`
- `.lazy-harness/knowledge/candidates.jsonl#candidate_gpt55_med_hook_compliance_dogfood_failure_20260601`

## Trigger

The user provided repeated dogfood screenshots and corrections showing that agents can still fail to read/apply lazy-harness records before acting, even when lifecycle hooks and pre-response digest wiring are present.

The most recent correction was:

```text
기록을 지금 하나도 안보네??
```

This record captures the finding as planning/dogfood evidence. It does not by itself approve implementation changes or hard-stop promotion.

## Records read for this finding

This finding is based on same-turn reads of these canonical records:

- `.lazy-harness/spec/platform/context-broker-dogfood.md`
- `.lazy-harness/spec/platform/record-decision-broker.md`
- `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- `.lazy-harness/spec/platform/guidance-ladder.md`
- `.lazy-harness/spec/platform/project-rule-router.md`
- `.lazy-harness/spec/platform/response-rule-audit.md`

## Findings

1. Hook execution is not enough.
   - `message.received` can execute and emit digest context, but dogfood evidence shows the model may still act without reading the surfaced record or required project context.

2. The current evidence chain is incomplete.
   - We need to distinguish:
     1. hook executed,
     2. inject emitted,
     3. provider prompt included the injected context,
     4. model complied by reading/searching records before acting.
   - Current hook timing logs prove script execution, but do not prove provider prompt inclusion or model compliance.

3. Model/provider differences are plausible and currently unmeasured.
   - User screenshot evidence included a `gpt-5.5 med` / OpenAI session that drifted after corrections and short follow-up instructions.
   - The current runtime logs do not include enough model/provider metadata to compare compliance across providers.

4. Short task-start instructions need a stronger resolver path.
   - Examples like `test db 연결해서 띄워봐` can be misinterpreted as a generic dev-script action instead of first resolving project-specific runtime/test DB records and current instance state.

5. Response audit is both too weak and too noisy in different places.
   - Too weak: surfaced digest/self-resolution without a Context Delivery packet may not create auditable required-read evidence.
   - Too noisy/incorrect: record-completion STOP can miss durable capture when it is written through a bash append to `.lazy-harness/knowledge/candidates.jsonl`, because the audit primarily recognizes write/edit/multiedit style evidence.

6. Read-debt production must not rely solely on LLM self-search.
   - User-confirmed constraint: `저것도 llm이 확실하게 검색해서 넘겨야하잔아`.
   - If the same LLM that forgets records is also responsible for deciding which read debts exist, the failure is moved upstream rather than fixed.
   - The reliable path should make a bounded deterministic broker/index/SearchProvider produce candidate `requiredRead` entries from canonical records and safe code/file evidence.
   - The LLM may consume, explain, or escalate the packet, but should not be the only authority that discovers mandatory records before action.
   - When deterministic evidence is ambiguous, the packet should force an option gate rather than allowing the agent to guess.

## Design implication

The next fix should distinguish two roles:

1. **Producer**: deterministic or fixture-protected framework code that searches canonical `.lazy-harness` records, generated indexes, graph entries, and bounded root-local file evidence to produce `requiredRead` / `fallbackSearches`.
   - The producer must do the first-pass discovery itself whenever a generated index, graph, record digest, project profile, or bounded file/code search can identify concrete candidates.
   - It is not enough for the producer to emit only free-form `fallbackSearches` and rely on the same LLM to decide whether those searches matter.
   - `fallbackSearches` are acceptable only when deterministic evidence is insufficient, and they should keep the turn in read-only/option-gate mode until resolved.
2. **Consumer**: the LLM agent that must read/search the produced paths before answer/change, or ask an option gate if candidate meanings conflict.
   - The LLM can still perform second-pass inspection, synthesis, and targeted follow-up searches.
   - The LLM must not be the only actor deciding the mandatory read set before action.

LLM self-resolution can remain a fallback or supplement, but not the only mechanism for read-debt creation. The framework invariant should be: deterministic producer selects or constrains the mandatory context first; LLM exploration is bounded by that packet and cannot skip directly to action.

## Lifecycle hook role split

The pre-start and post-completion hooks should share the same packet/evidence vocabulary, but they should not do the same job.

### Before start / before action

Purpose: prevent the agent from beginning with the wrong context.

Responsibilities:

- Run the deterministic producer first.
- Produce concrete `requiredRead` entries when records/index/graph/project-profile/code hints are available.
- Create a read-debt/permit state for the turn.
- Keep the agent in read-only or option-gate mode until required context is satisfied.
- Avoid making the LLM the only actor that decides what must be searched.

Expected output:

- Context Delivery Packet or equivalent read-debt packet.
- Required path/query evidence.
- Optional/fallback searches only when deterministic evidence is insufficient.

### After completion

Purpose: learn whether the turn complied and update guidance without pretending it can prevent the already-finished mistake.

Responsibilities:

- Compare produced obligations with observed tool evidence.
- Detect skipped reads, false positives, ambiguous tasks, and missing record completion.
- Journal sanitized compliance/miss evidence.
- Feed dogfood metrics and future promotion decisions.
- Emit advisory/ASK/STOP only according to guidance-ladder thresholds.

Expected output:

- Silent pass for clean turns.
- Advisory/ASK when obligations were skipped or evidence is missing.
- STOP only for already-promoted record-completion or hard-stop boundaries.

### Shared contract, different thresholds

Both sides should use shared schemas for:

- `requiredRead`, `optionalRead`, `fallbackSearches`, `candidateMeanings`, `instructionLevel`.
- Safe message/session hashes.
- Sanitized evidence rows.
- Compliance result labels.

But thresholds should differ:

- pre-start: high precision, bounded, action-preventing when concrete required reads exist;
- post-completion: broader recall/audit, false-positive aware, dogfood-learning oriented.

This avoids duplicating logic while preventing the post hook from becoming a late, noisy substitute for pre-action context selection.

## ACP / protocol-level option considered

User raised a possible alternative:

```text
아니면 진짜 acp 를 활용하는것도 방법인것 같기도 해
뭐가 더 좋은방법일까?
```

Current repository search did not find a canonical lazy-harness ACP integration record or concrete Jcode ACP implementation surface. Therefore ACP should be treated as an architecture option, not an available implementation assumption.

### What ACP-like integration could improve

If an Agent Client Protocol layer is available with first-class support for context packets, tool permissions, and tool-result provenance, it could improve the current hook design by making these concepts protocol-native:

- context packet delivery before model turn,
- tool/action permits tied to satisfied read-debts,
- provider/model metadata on each turn,
- prompt-inclusion or context-ack telemetry,
- standardized evidence that a read/search satisfied a required item.

### Why ACP-only is not the immediate recommendation

ACP alone does not solve discovery quality. The deterministic producer still must generate concrete `requiredRead` entries from canonical records/index/graph/project-profile/code hints. If ACP only transports a packet produced by weak LLM self-search, it preserves the same failure in a cleaner protocol.

ACP also appears not to be a current stable host implementation dependency, so choosing ACP-only first would add integration risk before the retrieval/permit semantics are proven.

### Recommended stance

Implement the core as protocol-agnostic packet + read-debt + compliance evidence first, using current lifecycle hooks as the transport. Design the packet/permit schema so it can later be carried by ACP if/when ACP support is available.

In short:

```text
deterministic producer + read-debt semantics = core
hooks = current transport
ACP = possible future/better transport
```

This keeps the hard part, correct context selection and action gating, independent from the transport layer.

## Constraints from canonical records

- ADR 0041 says the target architecture is organic hybrid: pre-response record query plus response.completed audit, not broad tool-specific blocking.
- `guidance-ladder.md` says hard stops require explicit promotion evidence, fixtures, narrowness, and rollback. The current finding is not yet an L5 hard-stop promotion.
- `record-decision-broker.md` says response lifecycle integration should remain shadow/silent by default until dogfood evidence justifies stronger guidance.
- `context-broker-dogfood.md` says aggregate dogfood collection is explicit CLI behavior and must not run automatically from lifecycle hooks.
- `response-rule-audit.md` says Context Delivery required-read audit is advisory-only until stronger evidence exists.

## Recommended next implementation slice

Recommended option remains C from the user-facing option gate:

```text
A+B as TDD-backed implementation:
- add prompt-inclusion / model-compliance telemetry or fixtures,
- add surfaced digest / self-resolution required-read evidence audit,
- keep it ADVISORY/ASK rather than hard STOP,
- preserve clean turns silent,
- include model/provider matrix dogfood evidence.
```

Do not promote a hard STOP yet without a `## Hard-stop promotion` section and fixture path.

## Discovery capture

- Capture status: promoted from transient chat/candidate evidence into planning record.
- Canonical implementation change: not yet made.
- TDD/SDD update required before implementation: yes, if audit criteria, packet shape, telemetry fields, or emitted output changes.
- Candidate JSONL remains useful as raw dogfood finding index, but this planning record is the durable summary for the current investigation.

## Rule placement

- Rule: Agents may fail to actually read/apply surfaced records even when pre-response hooks execute; hook compliance must be measured as execution → injection → prompt inclusion → model compliance.
- Scope: transient-plan, framework-global candidate.
- Primary record: `.lazy-harness/planning/hook-compliance-dogfood-findings-20260601.md`.
- Why not AGENTS.md: this is not a stable operating rule yet; it is a dogfood finding and implementation backlog.
- Why not `.jcode`: this concerns lazy-harness framework behavior, not local/private Jcode wiring only.
- Confirmation: user-confirmed symptoms; implementation direction still needs option-gate approval.

## Implementation map

No implementation was changed by this record.

Existing implementation surfaces to inspect before any fix:

- `.lazy-harness/hooks/lifecycle/on-message-received.sh` — runs pre-turn relevant-record query and emits injection JSON.
- `.lazy-harness/scripts/relevant-record-query.ts` — ranks and renders compact rule digests.
- `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — post-turn surfaced-rule and required-read audit.
- `.lazy-harness/scripts/context-delivery.ts` — explicit Context Delivery packet generation and journaling.
- `.lazy-harness/scripts/record-decision-broker.ts` — deterministic post-turn Record Decision Packet generator.
- `.lazy-harness/scripts/context-broker-dogfood.ts` — explicit aggregate dogfood collector.
- `.lazy-harness/scripts/self-test.py` — fixture home for lifecycle, audit, dogfood, and telemetry regression tests.

Protection to add before/with implementation:

- TDD fixture for `hook executed` but `inject not emitted`.
- TDD fixture for `inject emitted` but no provider/model telemetry.
- TDD fixture for surfaced digest followed by mutation/execution without record/read evidence.
- TDD fixture proving clean/no-record-needed turns remain silent.
- Dogfood matrix row shape for model/provider compliance without raw prompt storage.

## Implementation result — 2026-06-01

Status: implemented and committed in source repo.

Source commit:

- `2225239cbeab4b7227d9073a22f44fa665a959b8` — `Feat: enforce context read-debt before actions`

Implemented architecture:

```text
user message
→ message.received lifecycle hook
→ bounded deterministic Context Delivery producer
→ sanitized packet journal with concrete requiredRead paths
→ read/search tools remain allowed
→ action/mutation tools require evidence for every requiredRead path
→ response.completed audits missed evidence after the turn
```

Key implementation files:

- `.lazy-harness/hooks/lifecycle/on-message-received.sh` — runs bounded `context-delivery.ts --journal` and renders read-debt context when concrete packet evidence exists.
- `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py` — packet-scoped pre-action permit gate.
- `.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh` — runs read-debt permit before legacy search-performed helper.
- `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py` — post-response advisory now checks evidence for every concrete requiredRead path.
- `.lazy-harness/scripts/jcode-wiring.ts` — patches generated/user-owned `.jcode/config.toml` with a narrow `tool.execute.before`, `tool = "*"` read-debt hook.
- `.lazy-harness/scripts/self-test.py` — protects read-debt action-block, read-allow, satisfied-action silence, mixed batch block, message.received packet journal, and response audit all-path evidence cases.

Canonical records updated:

- `.lazy-harness/spec/platform/context-delivery-contract.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/spec/platform/response-rule-audit.md`
- `.lazy-harness/spec/platform/guidance-ladder.md`
- `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- `.lazy-harness/ssot/harness-enforcement-policy.md`
- `.lazy-harness/ssot/rule-lifecycle.md`
- `.lazy-harness/tests/response-rule-audit.md`
- `.lazy-harness/knowledge/graph.jsonl`
- `.lazy-harness/generated/implementation-index.json`

Validation in source repo:

- `python3 -m py_compile .lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py .lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py .lazy-harness/scripts/self-test.py` passed.
- `python3 .lazy-harness/scripts/doctor.py --profile full --scope framework` passed.
- `python3 .lazy-harness/scripts/self-test.py` passed.
- `.lazy-harness/bin/lazy graph-hygiene --format=md --fail-on-issues` passed.
- `python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --root . --format=md --strict` passed.
- Git pre-commit ran `.lazy-harness/bin/lazy test` and passed before commit.

## Host sync validation — 2026-06-01

After implementation, Category A framework files were synced from source commit `2225239cbeab4b7227d9073a22f44fa665a959b8` into both dogfood hosts:

- `/home/lazydino/dev/medivance`
- `/home/lazydino/dev/medivance-pwa`

Sync command class:

```bash
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts \
  --from /home/lazydino/dev/lazy-harness \
  --target <host> \
  --force
```

Observed sync result for each host:

- `updated: 12`
- `unchanged: 151`
- `missing: 0`
- `.lazy-harness/state/synced-from-commit` marker updated to `2225239cbeab4b7227d9073a22f44fa665a959b8`.
- `.jcode/config.toml` received `# BEGIN lazy-harness read-debt action permit hook` and `command = ".lazy-harness/hooks/lifecycle/on-tool-execute-before.sh"`.

Host validation passed on both hosts:

- `.lazy-harness/bin/lazy test`
- `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- `python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --root . --format=json`

Known non-blocking note:

- `/home/lazydino/dev/medivance-pwa` doctor reported `D07 package health warn`; smoke/host validation still passed.
- Source repo still has pre-existing runtime log dirtiness in `.lazy-harness/logs/validations.jsonl`; it was intentionally excluded from the read-debt commit.

## User correction — search-debt before read-debt

User-corrected after implementation:

```text
llm이 하게 해야한다니까?
검색을 했나 안했나를 측정하게하고 검색을 안했으면 먼저 하도록 강제하는식으로가야지 안그래??
```

Correction:

- The framework must not pretend a non-LLM deterministic hook can reliably understand multilingual semantic intent such as Korean `예약시트` mapping to English records/code.
- The LLM or a searcher agent must perform semantic expansion and root-bound searches.
- The harness should measure whether that search happened, not claim it can always know the semantic target first.
- If an implementation-likely or host-context-dependent turn has no high-confidence requiredRead packet yet, the hook should create **search-debt**, not only fail open.
- Before action/mutation tools run, the permit gate should accept either:
  1. satisfied concrete `requiredRead` evidence when known, or
  2. prior search evidence when the packet is in self-resolve/fallback mode.
- Search evidence means visible tool evidence such as `agentgrep`, `grep`, `rg`, `read` after search, Context Delivery/searcher packet output, or bounded root-local file/code searches.
- Once LLM search finds concrete records/files, read-debt can then require those paths to be read before action.

Corrected target architecture:

```text
user message
→ lightweight hook classifies turn as maybe host-context-dependent
→ if concrete paths are known: requiredRead/read-debt
→ if concrete paths are unknown: search-debt with fallbackSearches/self-resolve instruction
→ LLM performs semantic expansion + root-bound searches
→ harness measures search evidence
→ no search evidence before action => block and force search first
→ concrete paths found => read evidence before action
→ action/mutation proceeds
```

This is stronger and more accurate than the initial deterministic-producer framing. The hook may still use indexes/aliases/project profiles when available, but the prevention boundary for ambiguous terms must be search evidence, not deterministic semantic certainty.

Subagent implication, user-confirmed:

- Search-debt should become a portable search ticket/packet.
- The main LLM may satisfy it directly with root-bound search tools.
- If broad/risky/parallel search is useful, the same ticket can be handed to a searcher subagent.
- The subagent must return packet-shaped evidence: candidate meanings, queries run, requiredRead, optionalRead, confidence, and fallback searches.
- The harness can then measure the returned search evidence the same way it measures main-agent search evidence.
- This makes subagent delegation an extension of the same search-debt contract, not a separate ad-hoc prompt path.

## Search-debt implementation result — 2026-06-01

Status: implemented in source repo after user correction.

Corrected implementation:

```text
correlated Context Delivery packet
→ if requiredRead exists with confidence: read-debt
→ else if self-resolve/delegate-search with fallbackSearchCount: search-debt
→ search/read tools and explicit searcher handoff allowed
→ action/mutation tools blocked until required search/read evidence exists
```

Key changes:

- `.lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py`
  - enforces both search-debt and read-debt,
  - treats `agentgrep`, `grep`, `rg`/`find` shell searches, Context Delivery/searcher packet evidence, and explicit searcher handoff as search evidence,
  - blocks non-search subagent/swarm action before search evidence.
- `.lazy-harness/hooks/lifecycle/on-message-received.sh`
  - renders `Context Delivery search-debt` when no concrete requiredRead exists,
  - tells LLM/searcher to expand multilingual/user terms and perform root-bound semantic search.
- `.lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py`
  - adds advisory-only audit for search-debt followed by mutation without search evidence.
- `.lazy-harness/scripts/self-test.py`
  - protects search-debt action block, search-tool allow, explicit searcher handoff allow, search-satisfied action, and response audit advisory/silence cases.

Validation performed:

- `python3 -m py_compile .lazy-harness/hooks/lifecycle/helpers/check-read-debt-permit.py .lazy-harness/hooks/lifecycle/helpers/check-response-rule-audit.py .lazy-harness/scripts/self-test.py`
- Direct search-debt permit fixture: action blocked without search evidence and allowed after `agentgrep` evidence.
- `python3 .lazy-harness/scripts/hard-stop-promotion-audit.py --root . --format=md --strict`
- `python3 .lazy-harness/scripts/self-test.py`
- `python3 .lazy-harness/scripts/doctor.py --profile full --scope framework`
- `.lazy-harness/bin/lazy graph-hygiene --format=md --fail-on-issues`

Discovery capture:

- DDD: none.
- SDD: updated Context Delivery, pre-response context, and response audit contracts.
- BDD: none.
- TDD: updated response-rule-audit/context-delivery tests.
- ADR: updated ADR 0041 architecture decision.
- SSOT: updated harness enforcement and rule lifecycle policy.
- Planning: this record updated with user correction and implementation result.
