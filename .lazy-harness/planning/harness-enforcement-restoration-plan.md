# Harness Enforcement Restoration Experiment

Status: reverted-experiment
Date: 2026-05-31
Reverted: 2026-06-01
Layer: Planning
Related SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md`
Replacement plan: `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md`

## Summary

This plan originally restored hard enforcement by reintroducing edit/write/multiedit blocking gates and adding runtime/dev-instance action-boundary checks. The implementation was committed and dogfooded, then rejected by the user because it made the workflow feel too slow and too tool-attached.

The source implementation was reverted. This record remains as institutional memory so the same path is not repeated without understanding why it failed.

## What was tried

The reverted experiment attempted to restore enforcement by:

- re-adding generated Jcode `edit`, `write`, and `multiedit` blocking `tool.execute.before` hooks,
- patching existing user-owned `.jcode/config.toml` files with a mandatory Layer 2 block,
- adding runtime/dev-instance bash action-boundary checks,
- adding regression tests for those concrete guards,
- syncing and validating Medivance and Medivance PWA.

## Validation during experiment

The experiment did pass technical validation before it was rejected:

- Source `.lazy-harness/scripts/self-test.py`: pass.
- Source `python3 .lazy-harness/scripts/doctor.py --profile smoke`: pass.
- Downstream Medivance `.lazy-harness/bin/lazy test`: pass.
- Downstream Medivance PWA `.lazy-harness/bin/lazy test`: pass.

## Why it was reverted

User feedback:

- The workflow became too slow.
- The approach felt too attached to concrete tools like bash/dev-cli/gh rather than framework-level and organic.
- The desired direction is still hybrid, but not this C+ v1 hard-gate/tool-attached form.

## Replacement direction

C+ v2 organic hybrid:

```text
ambient relevant rule context
+ graduated guidance ladder
+ lightweight action/journal continuity
+ very narrow hard stops only for irreversible or repeatedly failed boundaries
```

See `.lazy-harness/planning/organic-hybrid-rule-guidance-plan.md`.

## Rule placement

- Rule: The hard-gate/tool-attached enforcement restoration experiment is reverted; do not treat it as the target architecture.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/harness-enforcement-restoration-plan.md`
- Why not AGENTS.md: this is historical planning memory, not active operational grammar.
- Why not `.jcode`: this records shared framework dogfood evidence, not local/private Jcode preference.
- Confirmation: user-confirmed

## Discovery capture

- DDD: none.
- SDD: tool-attached runtime/action-boundary design was rejected as primary architecture.
- BDD: agent workflow must not feel slowed by broad edit/write hard gates.
- TDD: reverted implementation tests should not remain active as required fixtures.
- ADR: future ADR needed for organic hybrid replacement.
- SSOT: `.lazy-harness/ssot/harness-enforcement-policy.md` updated with reverted experiment result.
- Planning: this record is retained as reverted-experiment memory.
