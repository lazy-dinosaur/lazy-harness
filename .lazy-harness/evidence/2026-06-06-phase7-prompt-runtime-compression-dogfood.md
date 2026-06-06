# Evidence: Phase 7 prompt runtime compression dogfood

## Scope

This capsule records Phase 7 dogfood for `feature/prompt-runtime-compression-plan` after implementing prompt/runtime compression, prompt-budget measurement, source feature navigation, advisory context tiers, evidence capsules, and later removal of manual operational-state packets after LLM-first review.

In scope:

- source repo `/home/lazydino/dev/lazy-harness`
- downstream hosts `/home/lazydino/dev/medivance`, `/home/lazydino/dev/medivance-pwa`, `/home/lazydino/dev/medivance-homepage`
- lazy-sync dry-run/force sync behavior
- manifest-managed file-by-file verification
- source and host lazy-harness validation commands
- previous branch comparison against `main`

Out of scope:

- changing host application code
- shortening host-local skill files
- promoting context-delivery into default hooks
- reintroducing operational-state/user-text CLI classifiers without a new LLM-first ADR/SDD
- adding broad hard gates

## Environment

- Date: 2026-06-06
- Source branch: `feature/prompt-runtime-compression-plan`
- Source HEAD: `332e2e8fbc98fa1bc6e6fc4e35972379b2e487b4`
- Baseline branch for comparison: `main`
- Merge base with `main`: `132c0ce34dc1`
- Validation task: `/tmp/jcode-bg-tasks/5308086mck.status.json` completed with exit code 0.

## Commands

Source validation and branch comparison:

```bash
python3 -m py_compile .lazy-harness/scripts/self-test.py .lazy-harness/scripts/prompt-budget.py
python3 .lazy-harness/scripts/self-test.py
.lazy-harness/bin/lazy doctor --profile=smoke
.lazy-harness/bin/lazy prompt-budget --format=json
.lazy-harness/bin/lazy context-index --format=json
git diff --name-status main
git diff --stat main
git diff --name-status main -- .jcode/skills .lazy-harness/skills
```

Downstream sync and verification:

```bash
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts --from /home/lazydino/dev/lazy-harness --target <host> --dry-run
bun /home/lazydino/dev/lazy-harness/.lazy-harness/scripts/lazy-sync.ts --from /home/lazydino/dev/lazy-harness --target <host> --force
python3 /tmp/lazy-phase7/verify-managed-sync.py /home/lazydino/dev/lazy-harness /home/lazydino/dev/medivance /home/lazydino/dev/medivance-pwa /home/lazydino/dev/medivance-homepage
```

Host validation per host:

```bash
.lazy-harness/bin/lazy test
.lazy-harness/bin/lazy doctor --profile=smoke
.lazy-harness/bin/lazy prompt-budget --format=json
.lazy-harness/bin/lazy context-index --format=json
```

## Results

### Source validation

- `python3 .lazy-harness/scripts/self-test.py`: passed, `ran=82`, `skipped=0`.
- `.lazy-harness/bin/lazy doctor --profile=smoke`: passed.
- Source prompt-budget: `status=warn`, `message.received` estimate `259` tokens.
- Previous baseline for rendered `message.received`: `799` estimated tokens.
- Reduction: approximately `67.6%`.
- Source-vs-main comparison changed 30 files and showed no `.jcode/skills` or `.lazy-harness/skills` diffs.

### Previous branch comparison

`git diff --stat main` summary:

```text
.lazy-harness/bin/lazy                             |  14 +
 .lazy-harness/evidence/README.md                   |  18 +
 .../context-tier-manifest.sample.json              |  68 ++
 .../hooks/lifecycle/on-message-received.sh         |  34 +-
 .lazy-harness/knowledge/candidates.jsonl           |   1 +
 .lazy-harness/knowledge/graph.jsonl                |  13 +
 .lazy-harness/manifests/init-categories.json       |  56 +-
 ...ompt-runtime-compression-implementation-plan.md | 863 +++++++++++++++++++++
 .lazy-harness/project/context-tiers.yaml           |  72 ++
 .lazy-harness/project/feature-navigation.xml       | 360 +++++++++
 .lazy-harness/regression/registry.jsonl            |   1 +
 .lazy-harness/schemas/README.md                    |   2 +
 .../schemas/context-tier-manifest.schema.json      |  85 ++
   .lazy-harness/scripts/prompt-budget.py             | 329 ++++++++
 .lazy-harness/scripts/self-test.py                 | 726 ++++++++++++++++-
 .../spec/platform/context-delivery-contract.md     |  16 +
 .../spec/platform/context-tier-manifest.md         | 150 ++++
 .../spec/platform/evidence-capsule-standard.md     | 146 ++++
  .../spec/platform/pre-response-rule-context.md     |  23 +-
 .lazy-harness/spec/platform/prompt-budget.md       | 166 ++++
 .lazy-harness/ssot/capabilities.json               |  43 +-
 .lazy-harness/ssot/project-navigation.md           | 127 +++
 .lazy-harness/templates/evidence-capsule.md        |  35 +
 .lazy-harness/tests/evidence-capsule-standard.md   |  71 ++
 .lazy-harness/tests/pre-response-rule-context.md   |  97 +++
 .lazy-harness/tests/prompt-budget.md               | 118 +++
 30 files changed, 4166 insertions(+), 64 deletions(-)
```

`git diff --name-status main` summary:

```text
M	.lazy-harness/bin/lazy
A	.lazy-harness/evidence/README.md
A	.lazy-harness/fixtures/context-delivery/context-tier-manifest.sample.json
M	.lazy-harness/hooks/lifecycle/on-message-received.sh
M	.lazy-harness/knowledge/candidates.jsonl
M	.lazy-harness/knowledge/graph.jsonl
M	.lazy-harness/manifests/init-categories.json
A	.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md
A	.lazy-harness/project/context-tiers.yaml
A	.lazy-harness/project/feature-navigation.xml
M	.lazy-harness/regression/registry.jsonl
M	.lazy-harness/schemas/README.md
A	.lazy-harness/schemas/context-tier-manifest.schema.json
A	.lazy-harness/scripts/prompt-budget.py
M	.lazy-harness/scripts/self-test.py
M	.lazy-harness/spec/platform/context-delivery-contract.md
A	.lazy-harness/spec/platform/context-tier-manifest.md
A	.lazy-harness/spec/platform/evidence-capsule-standard.md
M	.lazy-harness/spec/platform/pre-response-rule-context.md
A	.lazy-harness/spec/platform/prompt-budget.md
M	.lazy-harness/ssot/capabilities.json
A	.lazy-harness/ssot/project-navigation.md
A	.lazy-harness/templates/evidence-capsule.md
A	.lazy-harness/tests/evidence-capsule-standard.md
A	.lazy-harness/tests/pre-response-rule-context.md
A	.lazy-harness/tests/prompt-budget.md
```

### File-by-file sync verification

Manifest-managed file verification output:

```json
{
  "source": "/home/lazydino/dev/lazy-harness",
  "sourceSha": "332e2e8fbc98fa1bc6e6fc4e35972379b2e487b4",
  "hosts": [
    {
      "host": "medivance",
      "files_equal": 182,
      "directories_checked": 9,
      "knowledge_exact": 422,
      "knowledge_conflicts": 3,
      "stale_checked": 123,
      "marker": "332e2e8fbc98"
    },
    {
      "host": "medivance-pwa",
      "files_equal": 182,
      "directories_checked": 9,
      "knowledge_exact": 422,
      "knowledge_conflicts": 3,
      "stale_checked": 123,
      "marker": "332e2e8fbc98"
    },
    {
      "host": "medivance-homepage",
      "files_equal": 182,
      "directories_checked": 9,
      "knowledge_exact": 425,
      "knowledge_conflicts": 0,
      "stale_checked": 123,
      "marker": "332e2e8fbc98"
    }
  ]
}
```

Highlights:

- all three hosts synced to `332e2e8fbc98`
- each host has `182` manifest-managed files byte-equal to source
- stale managed files checked: `123` per host
- knowledge JSONL seed rows represented with expected conflict handling
- no skill file diffs were introduced

### Host validation summary

```json
[
  {
    "host": "medivance",
    "lazyTest": "passed",
    "doctorSmoke": "passed",
    "promptBudgetStatus": "warn",
    "messageReceivedTokens": 261,
    "skillSurfaces": [
      {
        "path": ".jcode/skills/dev-instance/SKILL.md",
        "lineCount": 62,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-doc-ingest/SKILL.md",
        "lineCount": 42,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-doctor/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-init/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-project-profile/SKILL.md",
        "lineCount": 47,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-skill-create/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-sync/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-test/SKILL.md",
        "lineCount": 68,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-update/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      }
    ],
    "contextRecords": 237,
    "contextFeatures": 0,
    "operationalTaskKind": "validation",
    "operationalRisk": "medium",
    "operationalFallback": true,
    "operationalCapabilities": []
  },
  {
    "host": "medivance-pwa",
    "lazyTest": "passed",
    "doctorSmoke": "passed",
    "promptBudgetStatus": "warn",
    "messageReceivedTokens": 259,
    "skillSurfaces": [
      {
        "path": ".jcode/skills/lazy-doc-ingest/SKILL.md",
        "lineCount": 42,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-doctor/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-init/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-project-profile/SKILL.md",
        "lineCount": 47,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-skill-create/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-sync/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-test/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-update/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      }
    ],
    "contextRecords": 91,
    "contextFeatures": 0,
    "operationalTaskKind": "validation",
    "operationalRisk": "medium",
    "operationalFallback": true,
    "operationalCapabilities": []
  },
  {
    "host": "medivance-homepage",
    "lazyTest": "passed",
    "doctorSmoke": "passed",
    "promptBudgetStatus": "warn",
    "messageReceivedTokens": 259,
    "skillSurfaces": [
      {
        "path": ".jcode/skills/lazy-doc-ingest/SKILL.md",
        "lineCount": 42,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-doctor/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-init/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-project-profile/SKILL.md",
        "lineCount": 47,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-skill-create/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-sync/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-test/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/lazy-update/SKILL.md",
        "lineCount": 18,
        "status": "pass",
        "rawStatus": "pass",
        "enforcement": "advisory"
      },
      {
        "path": ".jcode/skills/medivance-figma-fidelity/SKILL.md",
        "lineCount": 570,
        "status": "warn",
        "rawStatus": "fail",
        "enforcement": "advisory"
      }
    ],
    "contextRecords": 80,
    "contextFeatures": 0,
    "operationalTaskKind": "validation",
    "operationalRisk": "medium",
    "operationalFallback": true,
    "operationalCapabilities": []
  }
]
```

Highlights:

- `medivance`: `lazy test`, doctor smoke, prompt-budget, and context-index passed in the original dogfood run; operational-state was later removed after LLM-first review.
- `medivance-pwa`: `lazy test`, doctor smoke, prompt-budget, and context-index passed in the original dogfood run; operational-state was later removed after LLM-first review.
- `medivance-homepage`: `lazy test`, doctor smoke, prompt-budget, and context-index passed in the original dogfood run; operational-state was later removed after LLM-first review.
- `medivance-homepage` retains the 570-line `.jcode/skills/medivance-figma-fidelity/SKILL.md` unchanged; prompt-budget reports it as `enforcement=advisory`, `rawStatus=fail`, `status=warn`.

### Dogfood findings fixed during Phase 7

1. Host-owned capability registries:
   - Problem: Phase 5/6 self-tests initially required `lazy-evidence-capsule` in downstream `capabilities.json`.
   - Fix: framework scope requires it; host scope allows absence and validates only if present.
   - Commit: `2d2439d`.

2. Prompt-budget records missing from sync manifest:
   - Problem: downstream self-test received `prompt-budget.py` and self-test changes but not `spec/platform/prompt-budget.md` / `tests/prompt-budget.md`.
   - Fix: add both records to Category A sync manifest.
   - Commit: `b18b718`.

3. Context-tier fixture referenced source/host-owned paths:
   - Problem: synced fixture referenced files not guaranteed in downstream hosts.
   - Fix: fixture now references framework-synced/common records only.
   - Commit: `7786b9b`.

4. Skill prompt enforcement policy:
   - Problem: prompt-budget hard-failed host-local long `SKILL.md` prompts.
   - Fix: skills remain measured, but are advisory-only warnings and never require automatic shortening.
   - Commit: `332e2e8`.

5. Header-index retrieval idea:
   - Problem: user proposed a root-bound header/chunk index CLI idea during dogfood.
   - Action: recorded only as a candidate, no implementation or runtime change.
   - Commit: `e2c729f`.

## Interpretation

Phase 7 supports keeping the compact static `message.received` prompt, prompt-budget measurement, and deterministic navigation surfaces. The operational-state helper was subsequently removed because user-message CLI classification conflicts with the LLM-first direction.

Decision gate outcome:

- Keep compact prompt: yes. Token reduction is above 30% and host validations passed.
- Revert Phase 2 compact prompt: no evidence requiring revert.
- Keep operational-state: no. Removed/deferred after LLM-first review; do not classify request semantics in CLI regex helpers.
- Promote new broad hard stop: no.
- Treat skills as hard prompt-budget failures: no. Skills are on-demand instruction assets and should remain advisory in prompt-budget.

Known caveats:

- Prompt-budget stale note superseded: after pointer-only `.jcode/harness/05-lazy-harness.md`, duplicate grammar count is 0 and prompt-budget passes in source validation.
- Context feature count is `0` on downstream hosts unless they add host-owned `.lazy-harness/project/feature-navigation.xml`.

## Reproduce

1. Checkout `/home/lazydino/dev/lazy-harness` at `332e2e8fbc98fa1bc6e6fc4e35972379b2e487b4`.
2. Run source validation commands listed above.
3. Run lazy-sync dry-run and force sync into the three dogfood hosts.
4. Run `/tmp/lazy-phase7/verify-managed-sync.py` against all hosts.
5. Run host validation commands for each host.
6. Confirm no `.jcode/skills/**` files changed and homepage's long Figma skill remains advisory-only.

## Related records

- `.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md`
- `.lazy-harness/spec/platform/prompt-budget.md`
- `.lazy-harness/tests/prompt-budget.md`
- `.lazy-harness/spec/lazy-sync-drift-detection.md`
- `.lazy-harness/spec/platform/context-tier-manifest.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/knowledge/candidates.jsonl`

## Retention / privacy

This capsule stores summarized command results, file paths, commit IDs, and aggregate validation metrics. It does not store raw user messages, secrets, credentials, personal data, raw assistant responses, unrelated product data, or excessive raw logs.
