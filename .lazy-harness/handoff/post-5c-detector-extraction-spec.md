# Post-5c Detector Extraction Handoff Spec

Date: 2026-05-12
Branch: `experimental/lazy-harness`
Workspace: `/home/lazydino/dev/medivance.experimental-lazy-harness`
Owner boundary: `.lazy-harness/` framework work only

## Purpose

Continue post-5c hardening by extracting detector bodies from `.lazy-harness/triggers/code-change.ts` into focused detector modules without changing behavior.

5c is already complete and pinned by framework-owned validation. This task is a maintainability refactor only.

## Current verified baseline

Latest known state before this handoff:

```text
1720 .lazy-harness/triggers/code-change.ts
  27 .lazy-harness/triggers/common.ts
  36 .lazy-harness/triggers/registries.ts
  94 .lazy-harness/triggers/structured-ask.ts
  71 .lazy-harness/triggers/cross-layer.ts
1948 total
```

Already extracted:

```text
.lazy-harness/triggers/
  common.ts             # compactSignature, isTypescriptFile, normalizePath, splitIdentifierWords, unique
  registries.ts         # XML/registry known-term readers
  structured-ask.ts     # validateStructuredAsks
  cross-layer.ts        # buildCrossLayerMap
```

Still monolithic:

```text
.lazy-harness/triggers/code-change.ts
  - CLI parsing and orchestration
  - file collection and git changed-only helpers
  - DDD detector
  - SDD detector
  - BDD detector
  - SSOT detector
  - detector-specific constants/helpers
  - ask formatting
```

## Non-negotiable rules

1. Work only on `experimental/lazy-harness`.
2. Do not change CLI behavior.
3. Do not change JSON output shape.
4. Do not change detector heuristics during extraction.
5. Do not broaden fixture baselines unless behavior change is deliberate, documented, and approved.
6. Do not reintroduce `.jcode` as the primary doctor. Lazy-harness owns `lazy:test` and `lazy:doctor`.
7. Do not delete fixtures or old validation artifacts.
8. Because `.lazy-harness/` is ignored, new files must be staged with `git add -f`.

## Target layout

```text
.lazy-harness/triggers/
  code-change.ts              # CLI + orchestration only
  types.ts                    # shared public types
  common.ts                   # shared pure helpers
  registries.ts               # known terms + XML readers
  structured-ask.ts           # structured ask validation
  cross-layer.ts              # cross-layer consistency map
  detectors/
    ddd.ts
    sdd.ts
    bdd.ts
    ssot.ts
```

Optional later, only if it reduces coupling cleanly:

```text
.lazy-harness/triggers/constants.ts
.lazy-harness/triggers/detectors/shared.ts
```

Do not create optional files unless extraction pressure makes them clearly useful.

## Required extraction order

Use small commits and validate after each detector.

### 1. DDD detector extraction

Create:

```text
.lazy-harness/triggers/detectors/ddd.ts
```

Move DDD-specific pieces from `code-change.ts`:

```text
interface DeclarationCandidate
extractDeclarations
getPreviousDeclarationNames
declarationFromInterface
declarationFromTypeAlias
toDddCandidate
buildDddAsk
inferMatchedDddTerms
isAcronymCandidate
inferAmbiguousAcronyms
inferAmbiguousAcronymsFromObjectFields
isAmbiguousAcronymWord
canonicalAcronymDisplay
hasKnownTerm
getAcronymCompoundPrefix
filePathToDomainHint
countTypeMembers
countUnionLiterals
isPascalCase
```

Likely export surface:

```ts
export interface DeclarationCandidate { ... }
export function extractDeclarations(sourceFile: SourceFile): DeclarationCandidate[]
export function getPreviousDeclarationNames(project: Project, filePath: string, warnings: string[]): Set<string>
export function toDddCandidate(...): TriggerCandidate | null
export function buildDddAsk(...): StructuredAsk
export function inferMatchedDddTerms(...): string[]
export function isAcronymCandidate(term: string): boolean
```

Keep public behavior identical. If helper visibility is unclear, prefer exporting a little more temporarily over changing logic.

### 2. SDD detector extraction

Create:

```text
.lazy-harness/triggers/detectors/sdd.ts
```

Move SDD-specific pieces:

```text
interface ContractCandidate
extractContracts
extractZodSchemas
extractTrpcProcedures
getPreviousContractKeys
contractKey
toSddCandidate
getDddReferenceTerms
uniqueTermsByLower
isMeaningfulDddTerm
classifyNounWord
filterDddTermWords
isZodHelperComposite
getSddConfidence
buildSddAsk
findZodCall
isZodCallExpression
getCallHead
isExportedVariableDeclaration
isInExportedDeclaration
getTrpcOperation
getProcedureName
getTrpcInputSchema
inferDddTerms
isZodExpressionText
```

Dependency note:

- SDD depends on DDD helpers for acronym ambiguity and matched DDD terms.
- Avoid circular imports. Prefer moving shared acronym/domain-word helpers to `detectors/shared.ts` only if needed.

### 3. BDD detector extraction

Create:

```text
.lazy-harness/triggers/detectors/bdd.ts
```

Move BDD-specific pieces:

```text
hasNaturalLanguageFlow
scenarioFromMessage
scenarioFromUiCode
uiFlowEvidence
isMultiStepUiFlow
countUiHandlers
extractComponentName
isRegisteredScenario
buildBddCrossRef
readKnownEndpointsForBdd
buildBddAsk
detectBdd
extractScenarioNameFromMessage
findFirstUiFlowLine
```

Likely export surface:

```ts
export function detectBdd(cli: Pick<CliOptions, ...>, files: string[], knownDddTerms: Set<string>): TriggerCandidate[]
```

If importing `CliOptions` causes awkward coupling, create a narrower local options type in `bdd.ts`:

```ts
interface BddDetectorOptions {
  lastUserMessage?: string;
}
```

Then keep `CliOptions` private to `code-change.ts`.

### 4. SSOT detector extraction

Create:

```text
.lazy-harness/triggers/detectors/ssot.ts
```

Move SSOT-specific pieces:

```text
interface SsotUtilityCandidate
extractSsotUtilities
getPreviousSsotKeys
ssotKey
classifySsotUtility
inferSsotDomainHint
toSsotCandidate
buildSsotAsk
getSsotConfidence
```

SSOT depends on registry-known helper names and Trigger types. Keep the registry reading in `registries.ts`; pass known SSOT names from orchestration.

## Shared constants and coupling guidance

The following constants are currently shared across detectors or close to shared:

```text
ACRONYM_LENGTH
DOMAIN_SEED_NOUNS
KNOWN_ACRONYM_EXPANSIONS
DOMAINISH_SUFFIXES
ZOD_HELPER_WORDS
EXCLUDED_PATTERNS
DDD_INFERENCE_STOP_WORDS
SHORT_ACRONYM_NOISE_WORDS
```

Recommended approach:

1. For DDD extraction, leave constants in `code-change.ts` only if it avoids churn.
2. If extracted detector needs many constants, move them together to either:
   - `detectors/shared.ts` for detector-private shared logic, or
   - `constants.ts` if they become broadly public to the trigger package.
3. Do not duplicate constants across detector files.
4. Do not change constant values during extraction.

## Orchestration expectations

After extraction, `code-change.ts` should ideally retain only:

```text
imports
CodeChangeLayer type
CliOptions interface
DEFAULT_* constants
runCodeChangeTrigger
collectFiles
gitChangedFiles
walkTypescriptFiles
getSourceFile
parseCliArgs
formatAsk
formatCrossLayerAsk
main
```

`runCodeChangeTrigger` should keep the same high-level flow:

1. Parse/merge options.
2. Collect files.
3. Read known terms/registries.
4. Build ts-morph project.
5. Run selected detectors based on `--layer`.
6. Build cross-layer map.
7. Validate structured asks.
8. Return `TriggerRunResult`.

## Validation commands

Run after each detector extraction:

```bash
git diff --check
bun run lazy:test
```

Run before each commit:

```bash
bun run lazy:doctor
.lazy-harness/hooks/pre-push.sh origin dummy
git status --short
```

Useful trigger smoke:

```bash
bun .lazy-harness/triggers/code-change.ts \
  --scope .lazy-harness/triggers/fixtures \
  --layer all \
  --format json \
| jq '{counts: ([.candidates[].layer] | group_by(.) | map({(.[0]): length}) | add), cross: .crossLayer.summary, ask: .structuredAskValidation}'
```

Expected pinned full fixture counts:

```json
{"ddd":6,"sdd":2,"bdd":3,"ssot":7}
```

Expected pinned full cross-layer summary:

```text
sdd->ddd:gap = 2
bdd->ddd:gap = 3
bdd->sdd:gap = 3
ssot->ddd:gap = 2
```

Useful E2E smoke:

```bash
bun .lazy-harness/triggers/code-change.ts \
  --scope .lazy-harness/triggers/fixtures/e2e \
  --layer all \
  --format json \
| jq '{counts: ([.candidates[].layer] | group_by(.) | map({(.[0]): length}) | add), cross: .crossLayer.summary, ask: .structuredAskValidation}'
```

Expected E2E counts:

```json
{"ddd":1,"sdd":1,"bdd":1,"ssot":2}
```

Expected E2E cross-layer summary:

```text
sdd->ddd:gap = 1
bdd->ddd:gap = 1
bdd->sdd:gap = 1
```

## Commit strategy

Commit one extraction at a time:

```text
Refactor(lazy-harness): extract ddd detector
Refactor(lazy-harness): extract sdd detector
Refactor(lazy-harness): extract bdd detector
Refactor(lazy-harness): extract ssot detector
```

Because `.lazy-harness/` is ignored:

```bash
git add -f .lazy-harness/triggers/detectors/ddd.ts .lazy-harness/triggers/code-change.ts
```

Adjust paths per detector.

## Known risk from previous extraction

During the first refactor pass, `uniqueTermsByLower` was accidentally removed and `lazy:test` caught:

```text
ReferenceError: uniqueTermsByLower is not defined
```

So do not rely on static reading only. Always run `bun run lazy:test` after each extraction.

## Package health is separate

`bun run typecheck:node` currently fails because of environment/package health:

```text
Cannot find type definition file for 'electron-vite/node'
@electron-toolkit/tsconfig/tsconfig.node.json not found
```

This is already classified by 5c-6 as package/environment drift, not lazy-harness detector regression. Do not mix package dependency remediation into detector extraction unless explicitly assigned.

## Definition of done

This handoff task is done when:

1. `code-change.ts` is orchestration-focused and significantly smaller.
2. All four detector files exist under `.lazy-harness/triggers/detectors/`.
3. CLI flags and output shape are unchanged.
4. `bun run lazy:test` passes.
5. `bun run lazy:doctor` passes.
6. `.lazy-harness/hooks/pre-push.sh origin dummy` passes and leaves the working tree clean.
7. Each detector extraction is committed separately on `experimental/lazy-harness`.

## Suggested first command for the next agent

```bash
cd /home/lazydino/dev/medivance.experimental-lazy-harness \
  && git status -sb \
  && bun run lazy:test \
  && rg -n "^(export function|function) " .lazy-harness/triggers/code-change.ts
```
