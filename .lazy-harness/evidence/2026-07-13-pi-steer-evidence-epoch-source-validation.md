# Evidence: Pi/OMP mid-turn steer evidence epoch source validation

## Scope

This capsule validates the source work unit that hardens Pi/OMP mid-turn steering in `/home/lazydino/dev/lazy-harness`:

- every non-extension, non-empty `streamingBehavior === "steer"` advances a root-scoped evidence epoch and clears prior recent-tool evidence;
- tool results count as evidence only when their tool call started in the current epoch;
- a late pre-steer result cannot restore stale permission;
- later action remains guarded until fresh post-steer root-bound map/read evidence completes;
- no steer-text classifier, command allowlist, or semantic debt row was added;
- DDD/BDD/SDD/TDD/PRD/planning/package documentation and canonical graph facts were co-updated.

This capsule covers source validation only. Commit, push, and all initialized downstream host sync were explicitly authorized on 2026-07-13 after the source checks; rollout results will be captured in a separate deployment-reach capsule. The map-metadata-versus-required-read semantics backlog remains intentionally out of scope.

## Environment

- Date: 2026-07-13
- Source checkout: `/home/lazydino/dev/lazy-harness`
- Branch: `main`
- Base HEAD before this uncommitted work unit: `56a46011b613f92e65c08d01368fac65ed55afa0`
- Working tree: dirty by design; implementation and evidence are not committed
- Python: `3.14.4`
- Bun: `1.3.14`
- Primary fake runtime fixture: `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract`
- Canonical graph ids: `kg_pi_steer_evidence_epoch_impl_20260713`, `kg_pi_steer_evidence_epoch_test_20260713`

## Commands

Run from `/home/lazydino/dev/lazy-harness` unless noted.

```bash
.lazy-harness/bin/lazy map --overview --complete --format=md
.lazy-harness/bin/lazy map .lazy-harness/spec/platform/pi-agent-package.md --format=md --limit=8
.lazy-harness/bin/lazy map .lazy-harness/spec/platform/search-read-debt-contract.md --format=md --limit=8
.lazy-harness/bin/lazy map packages/lazy-harness-pi/extensions/lazy-harness/index.ts --format=md --limit=8
.lazy-harness/bin/lazy capability resolve --intent changing_framework_cli_surface --format=json
.lazy-harness/bin/lazy capability resolve --intent closing_framework_change_with_external_effects --format=json
.lazy-harness/bin/lazy capability resolve --intent closing_non_trivial_work_unit --format=json
.lazy-harness/bin/lazy capability resolve --intent making_validation_claims --format=json
python3 -m py_compile .lazy-harness/scripts/self-test.py
python3 - <<'PY'
import importlib.util
from pathlib import Path
path = Path('.lazy-harness/scripts/self-test.py').resolve()
spec = importlib.util.spec_from_file_location('lazy_self_test', path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
module.ACTIVE_SCOPE = 'framework'
module.check_pi_package_layout_and_contract()
PY
.lazy-harness/bin/lazy record-lint --format=json
.lazy-harness/bin/lazy graph-hygiene --format=json
git diff --check
python3 .lazy-harness/scripts/self-test.py --scope framework
```

Additional inspection used Pi extension documentation/types to confirm `toolCallId: string` is part of the official `tool_call`/`tool_result` event contract, and Pi Lens diagnostics were run on the edited Python/TypeScript sources before the executable fixture.

## Results

- Focused Pi/OMP package fixture: `✓ Pi package layout and extension contract ok`.
- The fake runtime proves all required steering cases:
  - valid pre-steer record evidence allows a pre-steer write;
  - a read started before steer and completed afterward stays stale;
  - immediate post-steer write is blocked;
  - a fresh post-steer `.lazy-harness` record read restores permission;
  - empty and extension-injected inputs do not re-arm or clear current evidence.
- Full framework self-test: `lazy-harness self-test ok (scope=framework, ran=84, skipped=0)`.
- Python parser and direct LSP error check passed. The final Pi Lens full scan emitted one `bare-except` finding at `self-test.py:443`, but both `HEAD` and current source use `except json.JSONDecodeError`; the edited self-test hunks begin around line 1709, so this is a baseline scanner false positive rather than an introduced bare clause.
- The final TypeScript scan emitted 12 dependency-resolution diagnostics for the source package (`@earendil-works/pi-coding-agent`, `typebox`, Node modules/typings, and `process`). The same imports/environment references exist in `HEAD`; no diagnostic points to the new epoch logic, and Bun successfully imported/executed the extension through the focused fake runtime.
- Record lint: `inspected=163`, `cleanRecords=163`, `issueCount=0`.
- Final graph hygiene: `rows=666`, `invalidRows=0`, `uniqueIds=666`, `duplicateIds=0`.
- Final graph hygiene retained only two pre-existing command-string-as-path warnings (`kg_pi_omp_global_bootstrap_default_20260623`, `kg_pi_omp_project_activation_command_20260623`). The new steering rows add no warning.
- `git diff --check`: clean.
- Intermediate fixture corrections made the fake runtime match real event order (`before_agent_start → tool_call → tool_result`) and changed the initial evidence from arbitrary `x.md` to a root-bound `.lazy-harness` record. An initial graph link using `#symbol` produced two path warnings; the uncommitted append was undone and re-appended with existing file paths before final validation.

## Interpretation

The evidence supports high confidence that the source implementation enforces an instruction-scoped evidence boundary for Pi/OMP mid-turn steering without semantic classification or command-specific policy. Epoch tagging prevents both already-cached evidence and late parallel pre-steer results from satisfying the next action guard, while preserving read-only recovery.

The evidence does **not** prove:

- a live paid/model-bearing interactive Pi or OMP run;
- commit or remote branch reachability;
- package sync to initialized downstream hosts;
- downstream deployment reach;
- the separate question of whether map metadata alone can satisfy search-debt versus required-read debt.

Those claims must remain pending until their own commands/evidence are produced.

## Reproduce

Minimal source verification:

```bash
cd /home/lazydino/dev/lazy-harness
python3 -m py_compile .lazy-harness/scripts/self-test.py
python3 .lazy-harness/scripts/self-test.py --scope framework
.lazy-harness/bin/lazy record-lint --format=json
.lazy-harness/bin/lazy graph-hygiene --format=json
git diff --check
```

For the narrow runtime regression only, run the focused import snippet from the Commands section and confirm `✓ Pi package layout and extension contract ok`.

## Related records

- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/spec/platform/pi-agent-package.md`
- `.lazy-harness/spec/platform/search-read-debt-contract.md`
- `.lazy-harness/spec/platform/pre-response-rule-context.md`
- `.lazy-harness/behavior/llm-owned-record-retrieval.md`
- `.lazy-harness/domain/searchable-record-memory.md`
- `.lazy-harness/tests/pi-agent-package.md`
- `.lazy-harness/tests/pre-action-search-evidence-guard.md`
- `.lazy-harness/tests/pre-response-rule-context.md`
- `.lazy-harness/decisions/0041-organic-hybrid-rule-guidance.md`
- `.lazy-harness/decisions/0045-purpose-scoped-retrieval.md`
- `.lazy-harness/planning/pi-agent-plugin-adapter.md`
- `.lazy-harness/planning/searchable-record-context-retrieval-implementation-plan.md`
- `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- `.lazy-harness/knowledge/graph.jsonl#kg_pi_steer_evidence_epoch_impl_20260713`
- `.lazy-harness/knowledge/graph.jsonl#kg_pi_steer_evidence_epoch_test_20260713`

## Retention / privacy

Retain this capsule with the source records and eventual rollout evidence. It contains summarized framework validation only. No secrets, credentials, personal data, raw conversation transcript, raw assistant response, or unrelated product data are included.
