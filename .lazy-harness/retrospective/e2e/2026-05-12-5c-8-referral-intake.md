# 5c-8 E2E Demonstration — Referral Intake Cascade

Date: 2026-05-12
Criterion: 5c-8

## Scenario

A realistic medivance change adds a referral intake search flow:

- DDD: `ReferralIntakeRecord`
- SDD: `referralIntakeSchema`
- BDD: `ReferralIntakePatientSearch`
- SSOT: `calculateReferralChecksum`, `normalizeReferralStatus`
- Lint/typecheck drift: `typecheck-env` fixture classifies missing dependency/config as environment, not code drift

## Reproduce

```bash
bun .lazy-harness/triggers/code-change.ts \
  --scope .lazy-harness/triggers/fixtures/e2e \
  --layer all \
  --format json

bun .lazy-harness/triggers/lint-output.ts \
  --input .lazy-harness/triggers/fixtures/lint-output/typecheck-env.txt \
  --format json
```

## Expected detector result

```json
{
  "layerCounts": {"ddd": 1, "sdd": 1, "bdd": 1, "ssot": 2},
  "candidates": [
    ["ddd", "ReferralIntakeRecord"],
    ["sdd", "referralIntakeSchema"],
    ["bdd", "ReferralIntakePatientSearch"],
    ["ssot", "calculateReferralChecksum"],
    ["ssot", "normalizeReferralStatus"]
  ],
  "crossLayerSummary": {
    "sdd->ddd:gap": 1,
    "bdd->ddd:gap": 1,
    "bdd->sdd:gap": 1
  },
  "structuredAskValidation": {
    "criterionId": "5c-7",
    "ok": true,
    "checkedCandidates": 6,
    "issues": []
  },
  "lintDriftSummary": {
    "tsc:environment:missing-type-definition": 1,
    "tsc:environment:missing-config": 1,
    "tsc:environment:missing-module": 1
  }
}
```

## Gate

`bun run lazy:test` pins this E2E demo via `check_e2e_demo()`.
