# TDD — V2 reading-display SDK cost compatibility repair 05

## Rule digest

- Status: active
- Status note: active evidence
- Layer: TDD
- Scope: host-project
- Covers: `experiments/v2-reading-display-02/runner.mjs` cost admission only
- Aliases:
  - reading display cost repair
  - SDK 비용 호환 수리
- Applies when: official Pi SDK catalog cost metadata includes non-rate keys such as `tiers`
- Must: validate required finite nonnegative rates; validate tier thresholds/rates; select the highest applicable context tier; preserve cumulative spend and reader reservation fail-closed.

## Regression

The official `gpt-5.6-luna` catalog cost has five keys (`input`, `output`, `cacheRead`, `cacheWrite`, `tiers`). The previous `Object.values(cost).every(Number.isFinite)` rejected this valid object. The focused regression exercises the actual installed `ModelRuntime` catalog object, malformed/missing/negative/nonfinite rates, malformed tiers, and an applicable higher tier.

## Four-layer independent-delta matrix

| Layer | Independent delta? | Judgment |
|---|---|---|
| SDD | no | Existing runner contract/provider/model/order unchanged; only catalog compatibility implementation is corrected. |
| BDD | no | No reader-facing flow or fixture/question behavior changed. |
| SSOT | no | No config/env/schema ownership changed; cumulative accounting remains in runner constants. |
| DDD | no | No domain rule or terminology changed. |

## Implementation map

- `experiments/v2-reading-display-02/runner.mjs`: `calculateWorstPerCall` validates required rates and tiers, chooses the applicable upper-bound tier, and feeds `evaluateAdmission`/`executeStudy` cumulative admission.
- `experiments/v2-reading-display-02/fixtures.json`: frozen input; hash unchanged.
- `.lazy-harness/evidence/v2-reading-display-reviewed-manifest05.json`: reviewed hash gate for repaired runner; not an approval.
- Installed SDK evidence: `/home/lazydino/.npm-global/lib/node_modules/@earendil-works/pi-coding-agent/dist/core/model-runtime.d.ts`, `docs/models.md`; official catalog object was exercised by `costCompatibilityRegression`.
- Protected by: `node experiments/v2-reading-display-02/runner.mjs --offline`.
- Cross-layer: no independent SDD/BDD/SSOT/DDD delta.

## Evidence

- Actual catalog rates: input 0.2, output 1.2, cacheRead 0.02, cacheWrite 0.25 ($/M); tier above 272000: 0.4, 1.8, 0.04, 0.5; contextWindow 272000.
- Focused regression: passed; 5 malformed cases rejected and applicable tier selected.
- Runner SHA-256: `606d79602f6bf5efd36ea37f07d8559c3c6a5883ba9d3f1854c6690830ceabab`.
- Fixture SHA-256: `df08ea991305c12233dd813e9774a51d2f7a39702757498425f6599f77214af4`.
- No reader call was made; prereview is parent-owned and not claimed here.
