// .lazy-harness/scripts/contract-diff.ts
// Phase 5b: skeleton only — ADR 0008 defers implementation to 5b-2a.
// See `.lazy-harness/decisions/0008-ast-contract-diff-deferred.md`.

export type RiskTier = 'public-api' | 'internal' | 'test'
export type Confidence = 'high' | 'medium' | 'low'

export type ContractDiffType =
  | 'signature-change'
  | 'type-change'
  | 'visibility-change'
  | 'removal'
  | 'addition'

export interface ContractDiff {
  path: string
  type: ContractDiffType
  before: string
  after: string
  riskTier: RiskTier
  confidence: Confidence
}

export interface ContractDiffOptions {
  /** Paths to scan; default = all changed files between fromSha..toSha */
  paths?: string[]
  /** Skip files larger than N bytes (default 1 MB) */
  maxFileBytes?: number
}

/**
 * Compute contract diff between two git SHAs using TypeScript AST.
 *
 * **Status**: NOT IMPLEMENTED in Phase 5b.
 *
 * Implementation deferred to 5b-2a:
 * - Requires ts-morph (~30 MB)
 * - Requires evidence that contract drift is a real problem in medivance
 * - See `.lazy-harness/decisions/0008-ast-contract-diff-deferred.md`
 */
export async function diffContracts(
  _fromSha: string,
  _toSha: string,
  _opts: ContractDiffOptions = {},
): Promise<ContractDiff[]> {
  throw new Error(
    'Not implemented — see ADR 0008 (Deferred to 5b-2a). ' +
      'For now, run `git diff --name-only <fromSha>..<toSha>` and review manually.',
  )
}

/**
 * Lightweight 5b-interim alternative: just record which paths changed under src/.
 * No AST analysis. Used by post-commit hook.
 */
export function summarizeTouchedContracts(
  changedPaths: string[],
): { path: string; isLikelyContract: boolean }[] {
  return changedPaths.map((path) => ({
    path,
    isLikelyContract:
      /\/(routers|services|contracts|schemas|types)\//.test(path) ||
      /\.(prisma|trpc|ipc)\.ts$/.test(path),
  }))
}
