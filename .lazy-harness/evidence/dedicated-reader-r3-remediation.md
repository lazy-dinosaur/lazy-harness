# Evidence — R3 launch and Parent guidance remediation

Status: static checks passed; live functional completion not demonstrated.

## Applied fixes

- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#readerLaunchValidationError` rejects explicit `toolBudget`, including null, before spawning a Reader. It does not silently rewrite launch arguments or weaken shell guards.
- `.lazy-harness/AGENTS.md` and `packages/lazy-harness-pi/prompts/lazy-harness.md` direct the Parent to omit total-tool overrides, use task-envelope body budgets, prefer native source tools, avoid `2>/dev/null`, and recognize `.lazy-harness/scripts/` as source rather than the Reader canonical-record lane.
- Pending failure guidance drains the child before one final response; terminal no-fallback canaries do not perform incomplete join afterward. This is guidance, not runtime-enforced suppression of Parent final messages.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` protects explicit-budget rejection, omitted-budget acceptance, and distributed prompt wording. Existing shell restriction and join tests remain intact.

## Validation

- Bun bundle and Python syntax/diff checks: PASS.
- Package and generic debt checks: PASS; hook regression: 19 scenarios PASS.
- Independent reviewer `95c84821`: `No issues found`, `OK with notes` (static only).
- Final `lazy validate --plan standard`: PASS, 88.876s; full self-test 88.449s.
- TypeScript LSP still reported 18 unresolved module/Node-type diagnostics in the isolated checkout. No clean TypeScript typecheck is claimed. A later empty cached lens result is not active clean evidence.

## Discovery capture / layer completeness

| Layer | Judgment | Record |
|---|---|---|
| DDD | none | No domain change. |
| SDD | updated | `.lazy-harness/spec/platform/pi-agent-package.md` |
| BDD | updated | `.lazy-harness/behavior/llm-owned-record-retrieval.md` |
| TDD | updated | `.lazy-harness/tests/pi-agent-package.md` |
| ADR | none | Ownership unchanged. |
| SSOT | none | No storage/config ownership change. |
| Planning | updated | `.lazy-harness/planning/agent-neutral-orchestration-pilot.md` |

Graph mapping: `kg_reader_r3_launch_budget_repair` in `.lazy-harness/knowledge/graph.jsonl`. Historical R3 and R2, previous frozen artifacts, main source, and legacy graph rows are preserved. No new live canary, main integration, activation, commit, push, or release was performed in this repair. Remaining risk: guidance compliance and functional parallel completion need live evidence; TypeScript resolution remains unresolved.
