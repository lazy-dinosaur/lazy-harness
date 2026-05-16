#!/usr/bin/env bun
/**
 * N1 — Layer Impact Completion Gate
 *
 * Given a set of changed files (staged, to-be-pushed, or recent_tool_calls writes),
 * determine which of the 5 core record layers (DDD / SDD / BDD / TDD / ADR) are
 * impacted, and whether the corresponding records were also updated in the same
 * change set. Emit a JSON document conforming to
 * .lazy-harness/schemas/layer-impact-result.schema.json
 *
 * Heuristic + resolver v0.1: the reference resolver (N2) supplies extra
 * candidateRecords (test-stem / path-stem / ADR-keyword) and the index
 * fingerprint becomes `resolverVersion`. Impacted/updated booleans are still
 * decided by N1 heuristics; the resolver only enriches candidate evidence.
 *
 * Usage:
 *   bun .lazy-harness/scripts/layer-impact-gate.ts \
 *     --file src/main/foo.ts \
 *     --file src/main/bar.ts \
 *     [--from <ref> --to <ref>]    # auto-fill from git diff if no --file
 *     [--source pre-commit|pre-push|response-completed|manual]
 *     [--append-validation]        # log result to logs/validations.jsonl
 *     [--format json|ask]          # default json
 *     [--no-resolver]              # skip N2 resolver enrichment (debug)
 *
 * Exit codes:
 *   0 = pass (no missing layers, or warn-only)
 *   1 = fail (missingLayers.length > 0 AND humanRequired=true)
 *   2 = error (analysis itself failed)
 *
 * Note: v0 always exits 0 unless --strict is passed. We are in observation
 * mode until host-project pilot verifies false-positive rate (N1 success
 * criterion #6: "host-project 실제 변경 3 회로 true positive 검증").
 */

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, appendFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { runCodeChangeTrigger } from '../triggers/code-change'
import type { TriggerCandidate, TriggerLayer } from '../triggers/types'
import { resolveReferences } from './reference-resolver'

type LayerKey = 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr'
type ChangeKind = 'added' | 'modified' | 'deleted' | 'renamed'

interface ChangedFile {
  path: string
  changeKind: ChangeKind
  renamedFrom?: string | null
}

interface LinkKindEntry {
  recordPath: string
  linkKind:
    | 'domain-term'
    | 'spec-contract'
    | 'scenario'
    | 'test'
    | 'decision'
    | 'registry'
    | 'cross-layer'
    | 'path-stem'
    | 'keyword'
  score: number | null
  reason: string | null
}

interface LayerEntry {
  impacted: boolean
  updated: boolean
  candidateRecords: LinkKindEntry[]
  reason: string | null
}

interface LayerImpactResult {
  id: string
  status: 'pass' | 'fail' | 'error'
  category: 'impl' | 'spec' | 'test' | 'env' | 'ssot' | 'infra' | 'unknown'
  humanRequired: boolean
  details: string[]
  suggestedFix: string | null
  evidence: Array<{ path: string; line: number; reason: string }>
  confidence: 'high' | 'medium' | 'low'
  riskTier?: string
  changedFiles: ChangedFile[]
  layerImpact: Record<LayerKey, LayerEntry>
  missingLayers: LayerKey[]
  resolverVersion: string | null
  createdAt: string
}

const LAYER_RECORD_DIR: Record<LayerKey, string> = {
  ddd: '.lazy-harness/domain',
  sdd: '.lazy-harness/spec',
  bdd: '.lazy-harness/behavior',
  tdd: '.lazy-harness/tests',
  adr: '.lazy-harness/decisions'
}

// Map TriggerLayer (detector output) → N1 LayerKey
function detectorLayerToN1(layer: TriggerLayer): LayerKey | null {
  if (layer === 'ddd' || layer === 'sdd' || layer === 'bdd') return layer
  if (layer === 'ssot') return 'ddd' // SSOT terms belong to the domain layer in N1's 5-layer model
  // 'tdd' / 'regression' have no detector yet
  return null
}

interface CliOptions {
  files: ChangedFile[]
  from: string | null
  to: string | null
  source: 'pre-commit' | 'pre-push' | 'response-completed' | 'manual'
  appendValidation: boolean
  format: 'json' | 'ask'
  strict: boolean
  noResolver: boolean
}

function parseCli(argv: string[]): CliOptions {
  const opts: CliOptions = {
    files: [],
    from: null,
    to: null,
    source: 'manual',
    appendValidation: false,
    format: 'json',
    strict: false,
    noResolver: false
  }
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]
    if (arg === '--file' && argv[i + 1]) {
      opts.files.push({ path: argv[++i], changeKind: 'modified' })
    } else if (arg === '--added' && argv[i + 1]) {
      opts.files.push({ path: argv[++i], changeKind: 'added' })
    } else if (arg === '--deleted' && argv[i + 1]) {
      opts.files.push({ path: argv[++i], changeKind: 'deleted' })
    } else if (arg === '--from' && argv[i + 1]) {
      opts.from = argv[++i]
    } else if (arg === '--to' && argv[i + 1]) {
      opts.to = argv[++i]
    } else if (arg === '--source' && argv[i + 1]) {
      const v = argv[++i] as CliOptions['source']
      opts.source = v
    } else if (arg === '--append-validation') {
      opts.appendValidation = true
    } else if (arg === '--format' && argv[i + 1]) {
      opts.format = argv[++i] === 'ask' ? 'ask' : 'json'
    } else if (arg === '--strict') {
      opts.strict = true
    } else if (arg === '--no-resolver') {
      opts.noResolver = true
    }
  }
  return opts
}

function fillFromGitDiff(opts: CliOptions): void {
  if (opts.files.length > 0) return
  if (!opts.from && !opts.to) return
  const range = opts.to ? `${opts.from ?? 'HEAD'}..${opts.to}` : (opts.from ?? 'HEAD')
  try {
    const out = execFileSync(
      'git',
      ['diff', '--name-status', range],
      { encoding: 'utf8' }
    )
    for (const line of out.split('\n')) {
      if (!line.trim()) continue
      const parts = line.split('\t')
      const status = parts[0]
      if (status?.startsWith('A')) {
        opts.files.push({ path: parts[1], changeKind: 'added' })
      } else if (status?.startsWith('M')) {
        opts.files.push({ path: parts[1], changeKind: 'modified' })
      } else if (status?.startsWith('D')) {
        opts.files.push({ path: parts[1], changeKind: 'deleted' })
      } else if (status?.startsWith('R')) {
        opts.files.push({
          path: parts[2],
          changeKind: 'renamed',
          renamedFrom: parts[1]
        })
      }
    }
  } catch {
    // Caller did not supply --file and git diff failed — leave files empty
    // and let the gate emit a low-confidence pass.
  }
}

function isUnderDir(file: string, dir: string): boolean {
  const norm = file.replace(/\\/g, '/')
  return norm === dir || norm.startsWith(`${dir}/`)
}

function isProductionSource(file: string): boolean {
  // Production source = under a source tree, not a test file, not a framework record.
  // Default tree is src/, but fixtures and host projects may use other roots; we
  // therefore accept any path that is NOT under .lazy-harness/ and NOT a test file.
  // The N1 gate's job is to flag the *gap*, not to enforce a specific tree layout.
  const norm = file.replace(/\\/g, '/')
  if (norm.startsWith('.lazy-harness/')) return false
  if (norm.startsWith('node_modules/')) return false
  if (norm.startsWith('.git/')) return false
  if (isTestFile(norm)) return false
  // Heuristic: must look like a source file (has a code extension)
  return /\.(ts|tsx|js|jsx|mts|cts)$/.test(norm)
}

function isTestFile(file: string): boolean {
  return /\.(test|spec)\.(t|j)sx?$/.test(file) || file.includes('/__tests__/')
}

function computeUpdatedLayers(files: ChangedFile[]): Record<LayerKey, boolean> {
  const out: Record<LayerKey, boolean> = {
    ddd: false,
    sdd: false,
    bdd: false,
    tdd: false,
    adr: false
  }
  for (const f of files) {
    for (const layer of Object.keys(LAYER_RECORD_DIR) as LayerKey[]) {
      if (isUnderDir(f.path, LAYER_RECORD_DIR[layer])) {
        out[layer] = true
      }
    }
    // Real project test files count as TDD updates (records may live in src tree)
    if (isTestFile(f.path)) out.tdd = true
  }
  return out
}

function bucketCandidatesByLayer(
  candidates: TriggerCandidate[]
): Record<LayerKey, TriggerCandidate[]> {
  const out: Record<LayerKey, TriggerCandidate[]> = {
    ddd: [],
    sdd: [],
    bdd: [],
    tdd: [],
    adr: []
  }
  for (const c of candidates) {
    const mapped = detectorLayerToN1(c.layer)
    if (mapped) out[mapped].push(c)
  }
  return out
}

function candidatesToRecords(
  layer: LayerKey,
  cands: TriggerCandidate[]
): LinkKindEntry[] {
  const linkKindFor = (l: LayerKey): LinkKindEntry['linkKind'] =>
    l === 'ddd' ? 'domain-term' :
    l === 'sdd' ? 'spec-contract' :
    l === 'bdd' ? 'scenario' :
    l === 'tdd' ? 'test' :
    'decision'
  return cands.slice(0, 8).map((c) => ({
    recordPath: c.filePath,
    linkKind: linkKindFor(layer),
    score: c.confidence === 'high' ? 0.9 : c.confidence === 'medium' ? 0.6 : c.confidence === 'low' ? 0.3 : null,
    reason: c.reason ?? null
  }))
}

export function runLayerImpactGate(opts: CliOptions): LayerImpactResult {
  const createdAt = new Date().toISOString()
  const id = `HOOK-LAYER-IMPACT-${createdAt.replace(/[-:.TZ]/g, '').slice(0, 14)}`

  // 1) Run code-change detectors over the changed source files
  const sourceFiles = opts.files
    .filter((f) => f.changeKind !== 'deleted')
    .map((f) => f.path)
    .filter((p) => isProductionSource(p) || isTestFile(p))

  let candidates: TriggerCandidate[] = []
  let warnings: string[] = []
  if (sourceFiles.length > 0) {
    try {
      const triggerResult = runCodeChangeTrigger({
        files: sourceFiles,
        layer: 'all',
        format: 'json',
        newOnly: true,
        changedOnly: false
      })
      candidates = triggerResult.candidates ?? []
      warnings = triggerResult.warnings ?? []
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e)
      warnings.push(`code-change trigger error: ${message}`)
    }
  }

  const bucket = bucketCandidatesByLayer(candidates)
  const updated = computeUpdatedLayers(opts.files)

  // 1b) Run N2 reference resolver over ALL changed files (not just production),
  // so renamed/added record files contribute matches too. The resolver's
  // matches enrich candidateRecords with explicit scores; impacted/updated
  // booleans are still decided by N1 heuristics below.
  let resolverByLayer: Partial<Record<LayerKey, LinkKindEntry[]>> = {}
  let resolverVersion: string | null = null
  if (!opts.noResolver && opts.files.length > 0) {
    try {
      const refMap = resolveReferences(opts.files.map((f) => f.path))
      resolverVersion = refMap.indexVersion
      for (const m of refMap.matches) {
        // SSOT matches collapse into DDD (same as detectorLayerToN1).
        const lk: LayerKey | null =
          m.layer === 'ddd' || m.layer === 'sdd' || m.layer === 'bdd' || m.layer === 'tdd' || m.layer === 'adr'
            ? (m.layer as LayerKey)
            : m.layer === 'ssot'
              ? 'ddd'
              : null
        if (!lk) continue
        ;(resolverByLayer[lk] ??= []).push({
          recordPath: m.recordPath,
          linkKind: m.linkKind as LinkKindEntry['linkKind'],
          score: m.score,
          reason: m.reason
        })
      }
    } catch (e) {
      const message = e instanceof Error ? e.message : String(e)
      warnings.push(`reference-resolver error: ${message}`)
    }
  }

  function mergeCandidates(
    detectorEntries: LinkKindEntry[],
    resolverEntries: LinkKindEntry[]
  ): LinkKindEntry[] {
    // Deduplicate by (recordPath, linkKind); keep highest score; cap at 8.
    const all = [...detectorEntries, ...resolverEntries]
    const seen = new Map<string, LinkKindEntry>()
    for (const e of all) {
      const key = `${e.recordPath}|${e.linkKind}`
      const prev = seen.get(key)
      if (!prev || (e.score ?? 0) > (prev.score ?? 0)) seen.set(key, e)
    }
    return Array.from(seen.values())
      .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
      .slice(0, 8)
  }

  // 2) Per-layer impacted decision
  const productionChanged = opts.files.some((f) => isProductionSource(f.path))
  const testChanged = opts.files.some((f) => isTestFile(f.path))

  const layerImpact: Record<LayerKey, LayerEntry> = {
    ddd: {
      impacted: bucket.ddd.length > 0,
      updated: updated.ddd,
      candidateRecords: mergeCandidates(
        candidatesToRecords('ddd', bucket.ddd),
        resolverByLayer.ddd ?? []
      ),
      reason: bucket.ddd.length > 0
        ? `${bucket.ddd.length} domain-term candidate(s) from DDD/SSOT detectors`
        : null
    },
    sdd: {
      impacted: bucket.sdd.length > 0,
      updated: updated.sdd,
      candidateRecords: mergeCandidates(
        candidatesToRecords('sdd', bucket.sdd),
        resolverByLayer.sdd ?? []
      ),
      reason: bucket.sdd.length > 0
        ? `${bucket.sdd.length} spec-contract candidate(s) from SDD detector`
        : null
    },
    bdd: {
      impacted: bucket.bdd.length > 0,
      updated: updated.bdd,
      candidateRecords: mergeCandidates(
        candidatesToRecords('bdd', bucket.bdd),
        resolverByLayer.bdd ?? []
      ),
      reason: bucket.bdd.length > 0
        ? `${bucket.bdd.length} scenario candidate(s) from BDD detector`
        : null
    },
    tdd: {
      // v0: production source changed without an accompanying test change → impacted
      // ADR 0020 says TDD is the 5d cross-verify gate; here we only flag the gap signal.
      impacted: productionChanged && !testChanged,
      updated: updated.tdd,
      candidateRecords: mergeCandidates([], resolverByLayer.tdd ?? []),
      reason: productionChanged && !testChanged
        ? 'production source modified without a matching test file change'
        : (testChanged ? 'test file changed in this set' : null)
    },
    adr: {
      // v0: ADR auto-detect for `impacted` stays off — only the resolver can
      // contribute ADR candidateRecords (keyword/path-stem). impacted=true is
      // still reserved for explicit signals (interview-loop, ADR-touching diffs).
      impacted: false,
      updated: updated.adr,
      candidateRecords: mergeCandidates([], resolverByLayer.adr ?? []),
      reason: 'ADR auto-detection is heuristic-off in N1 v0; raise via interview-loop when conflict arises'
    }
  }

  // 3) Projection
  const missingLayers: LayerKey[] = (Object.keys(layerImpact) as LayerKey[])
    .filter((k) => layerImpact[k].impacted && !layerImpact[k].updated)

  const humanRequired = missingLayers.length > 0
  const status: 'pass' | 'fail' = humanRequired && opts.strict ? 'fail' : 'pass'

  // Evidence: surface candidate file paths so hooks can render an actionable message
  const evidence: LayerImpactResult['evidence'] = candidates
    .slice(0, 12)
    .map((c) => ({
      path: c.filePath,
      line: c.line,
      reason: `${c.layer}: ${c.name} — ${c.reason ?? 'detector candidate'}`
    }))

  // Confidence: v0 heuristic-only, so cap at medium unless trivially-empty case
  const confidence: 'high' | 'medium' | 'low' =
    opts.files.length === 0 ? 'low' :
    candidates.length === 0 && !productionChanged ? 'high' :
    'medium'

  const category: LayerImpactResult['category'] =
    layerImpact.sdd.impacted ? 'spec' :
    layerImpact.bdd.impacted ? 'spec' :
    layerImpact.tdd.impacted ? 'test' :
    layerImpact.ddd.impacted ? 'ssot' :
    productionChanged ? 'impl' :
    'unknown'

  const details: string[] = []
  details.push(`source=${opts.source}`)
  details.push(`changedFiles=${opts.files.length} (production=${opts.files.filter((f) => isProductionSource(f.path)).length}, test=${opts.files.filter((f) => isTestFile(f.path)).length})`)
  for (const layer of Object.keys(layerImpact) as LayerKey[]) {
    const e = layerImpact[layer]
    details.push(`${layer}: impacted=${e.impacted} updated=${e.updated}`)
  }
  if (warnings.length > 0) {
    details.push(`warnings=${warnings.length}`)
    for (const w of warnings.slice(0, 4)) details.push(`  warn: ${w}`)
  }

  const suggestedFix = missingLayers.length > 0
    ? `Update record layer(s): ${missingLayers.join(', ')}. Consider running: bun .lazy-harness/scripts/interview-loop.ts --mode collect`
    : null

  return {
    id,
    status,
    category,
    humanRequired,
    details,
    suggestedFix,
    evidence,
    confidence,
    changedFiles: opts.files,
    layerImpact,
    missingLayers,
    resolverVersion,
    createdAt
  }
}

function appendValidationLog(result: LayerImpactResult): void {
  const logPath = process.env.LAZY_HARNESS_VALIDATIONS_FILE || path.join('.lazy-harness', 'logs', 'validations.jsonl')
  const dir = path.dirname(logPath)
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  appendFileSync(logPath, JSON.stringify(result) + '\n', 'utf8')
}

function formatAsk(result: LayerImpactResult): string {
  if (result.missingLayers.length === 0) {
    return `[N1] OK — no missing record layers. (changedFiles=${result.changedFiles.length}, candidates=${result.evidence.length})`
  }
  const lines: string[] = []
  lines.push('[N1] 변경된 코드와 짝지을 record layer 가 비어 있습니다.')
  lines.push('')
  lines.push(`누락 layer: ${result.missingLayers.join(', ')}`)
  lines.push('')
  for (const layer of result.missingLayers) {
    const entry = result.layerImpact[layer]
    lines.push(`- ${layer.toUpperCase()} (${entry.reason ?? 'detector signal'})`)
    for (const cand of entry.candidateRecords.slice(0, 3)) {
      lines.push(`    • ${cand.linkKind}: ${cand.recordPath}${cand.reason ? ' — ' + cand.reason : ''}`)
    }
  }
  lines.push('')
  lines.push('옵션:')
  lines.push('  A. interview-loop 으로 누락 layer 를 채우는 구조화 질문 생성 (Recommended)')
  lines.push('  B. 이번 변경은 intentional 로 기록 (decisions/<adr>.md 신규)')
  lines.push('  C. 부분 갱신: 일부 layer 만 지금 채우고 나머지는 다음 commit')
  lines.push('  D. 직접 입력 / skip')
  return lines.join('\n')
}

function main(): void {
  const opts = parseCli(process.argv.slice(2))
  fillFromGitDiff(opts)

  let result: LayerImpactResult
  try {
    result = runLayerImpactGate(opts)
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e)
    const createdAt = new Date().toISOString()
    result = {
      id: `HOOK-LAYER-IMPACT-${createdAt.replace(/[-:.TZ]/g, '').slice(0, 14)}-ERR`,
      status: 'error',
      category: 'unknown',
      humanRequired: false,
      details: [`error: ${message}`],
      suggestedFix: null,
      evidence: [],
      confidence: 'low',
      changedFiles: opts.files,
      layerImpact: {
        ddd: { impacted: false, updated: false, candidateRecords: [], reason: 'analysis aborted' },
        sdd: { impacted: false, updated: false, candidateRecords: [], reason: 'analysis aborted' },
        bdd: { impacted: false, updated: false, candidateRecords: [], reason: 'analysis aborted' },
        tdd: { impacted: false, updated: false, candidateRecords: [], reason: 'analysis aborted' },
        adr: { impacted: false, updated: false, candidateRecords: [], reason: 'analysis aborted' }
      },
      missingLayers: [],
      resolverVersion: null,
      createdAt
    }
  }

  if (opts.appendValidation) appendValidationLog(result)

  if (opts.format === 'ask') {
    console.log(formatAsk(result))
  } else {
    console.log(JSON.stringify(result, null, 2))
  }

  if (result.status === 'fail') process.exit(1)
  if (result.status === 'error') process.exit(2)
}

const currentFile = fileURLToPath(import.meta.url)
if (process.argv[1] && path.resolve(process.argv[1]) === currentFile) {
  main()
}
