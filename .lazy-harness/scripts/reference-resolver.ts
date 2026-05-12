#!/usr/bin/env bun
/**
 * N2 — Map-aware Reference Resolver
 *
 * For each changed source file, find candidate record files across the 5
 * record layers (DDD/SDD/BDD/TDD/ADR + SSOT for completeness) and emit a
 * reference-map.schema.json document.
 *
 * Resolution strategies (v0, ordered by score):
 *   1. test-stem       (score 0.95) — `foo.ts` ↔ `foo.test.ts` / `foo.spec.ts`
 *   2. path-stem       (score 0.85) — `foo.ts` ↔ `.lazy-harness/<layer>/foo.xml` (or `*foo*`)
 *   3. ADR keyword     (score 0.55) — file basename or directory token appears in ADR md body
 *   4. cross-layer     (score 1.0)  — explicit entry in .lazy-harness/cross-layer/links.json (if present)
 *
 * Index cache:
 *   - generated/reference-index.json holds the full record-path catalog
 *     (one scan of .lazy-harness/<layer>/**), plus a fingerprint = sha1(paths+sizes).
 *   - Re-used across runs; rebuilt automatically when fingerprint mismatches.
 *
 * Usage:
 *   bun .lazy-harness/scripts/reference-resolver.ts \
 *     --file src/main/services/patient-risk.ts \
 *     [--file ...] \
 *     [--rebuild-index] \
 *     [--format json|ask] \
 *     [--out generated/reference-index.json]
 *
 * Exit: always 0 (resolver is informational; consumers decide policy).
 */

import { execFileSync } from 'node:child_process'
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync
} from 'node:fs'
import path from 'node:path'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'

type Layer = 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr' | 'ssot'

type LinkKind =
  | 'domain-term'
  | 'spec-contract'
  | 'scenario'
  | 'test'
  | 'decision'
  | 'registry'
  | 'cross-layer'
  | 'path-stem'
  | 'keyword'

interface Match {
  inputFile: string
  recordPath: string
  layer: Layer
  linkKind: LinkKind
  score: number
  reason: string
  evidence?: Array<{ path: string; line: number; snippet: string }>
}

interface ReferenceMap {
  indexVersion: string
  createdAt: string
  inputFiles: string[]
  matches: Match[]
  warnings?: string[]
}

interface IndexedRecord {
  path: string
  layer: Layer
  size: number
}

interface ReferenceIndex {
  fingerprint: string
  generatedAt: string
  records: IndexedRecord[]
}

const RECORD_DIRS: Record<Layer, string> = {
  ddd: '.lazy-harness/domain',
  sdd: '.lazy-harness/spec',
  bdd: '.lazy-harness/behavior',
  tdd: '.lazy-harness/tests',
  adr: '.lazy-harness/decisions',
  ssot: '.lazy-harness/ssot'
}

const DEFAULT_INDEX_PATH = '.lazy-harness/generated/reference-index.json'

interface CliOptions {
  files: string[]
  rebuildIndex: boolean
  format: 'json' | 'ask'
  out: string
}

function parseCli(argv: string[]): CliOptions {
  const opts: CliOptions = {
    files: [],
    rebuildIndex: false,
    format: 'json',
    out: DEFAULT_INDEX_PATH
  }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--file' && argv[i + 1]) opts.files.push(argv[++i])
    else if (a === '--rebuild-index') opts.rebuildIndex = true
    else if (a === '--format' && argv[i + 1]) opts.format = argv[++i] === 'ask' ? 'ask' : 'json'
    else if (a === '--out' && argv[i + 1]) opts.out = argv[++i]
  }
  return opts
}

function walkRecordFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      out.push(...walkRecordFiles(full))
    } else if (entry.isFile()) {
      // Skip README/notes — the resolver matches against structured records.
      if (entry.name === 'README.md') continue
      out.push(full)
    }
  }
  return out
}

function buildIndex(): ReferenceIndex {
  const records: IndexedRecord[] = []
  for (const layer of Object.keys(RECORD_DIRS) as Layer[]) {
    for (const filePath of walkRecordFiles(RECORD_DIRS[layer])) {
      try {
        const st = statSync(filePath)
        records.push({ path: filePath, layer, size: st.size })
      } catch {
        // ignore unreadable entry
      }
    }
  }
  records.sort((a, b) => a.path.localeCompare(b.path))
  const fp = createHash('sha1')
  for (const r of records) {
    fp.update(`${r.path}|${r.size}|${r.layer}\n`)
  }
  return {
    fingerprint: fp.digest('hex').slice(0, 16),
    generatedAt: new Date().toISOString(),
    records
  }
}

function loadIndex(outPath: string, rebuild: boolean): ReferenceIndex {
  if (!rebuild && existsSync(outPath)) {
    try {
      const cached = JSON.parse(readFileSync(outPath, 'utf8')) as ReferenceIndex
      // Re-fingerprint to detect drift
      const fresh = buildIndex()
      if (fresh.fingerprint === cached.fingerprint) return cached
      // Drift — rebuild and persist
      persistIndex(outPath, fresh)
      return fresh
    } catch {
      // Corrupt cache — rebuild
    }
  }
  const built = buildIndex()
  persistIndex(outPath, built)
  return built
}

function persistIndex(outPath: string, index: ReferenceIndex): void {
  const dir = path.dirname(outPath)
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  writeFileSync(outPath, JSON.stringify(index, null, 2) + '\n', 'utf8')
}

// ─────────────────────────────────────────────────────────────────────��──────
// Resolution strategies
// ────────────────────────────────────────────────────────────────────────────

function basenameStem(filePath: string): string {
  const base = path.basename(filePath)
  return base.replace(/\.(test|spec)\.[tj]sx?$/, '').replace(/\.[a-z0-9]+$/i, '')
}

function isTestPath(filePath: string): boolean {
  return /\.(test|spec)\.[tj]sx?$/.test(filePath) || filePath.includes('/__tests__/')
}

function findTestStem(inputFile: string, index: ReferenceIndex): Match[] {
  // For a production source `foo.ts`, look up sibling/cousin `foo.test.ts` etc.
  // anywhere on disk (not just record dirs). We use a filesystem walk relative
  // to the input file's directory plus a sibling __tests__ folder.
  if (isTestPath(inputFile)) return []
  const stem = basenameStem(inputFile)
  if (!stem) return []
  const dir = path.dirname(inputFile)
  const candidates: string[] = []
  // Common sibling patterns
  for (const ext of ['ts', 'tsx', 'js', 'jsx']) {
    candidates.push(path.join(dir, `${stem}.test.${ext}`))
    candidates.push(path.join(dir, `${stem}.spec.${ext}`))
    candidates.push(path.join(dir, '__tests__', `${stem}.test.${ext}`))
    candidates.push(path.join(dir, '__tests__', `${stem}.spec.${ext}`))
  }
  const matches: Match[] = []
  for (const candidate of candidates) {
    if (existsSync(candidate)) {
      matches.push({
        inputFile,
        recordPath: candidate,
        layer: 'tdd',
        linkKind: 'test',
        score: 0.95,
        reason: `sibling test file matches stem '${stem}'`
      })
    }
  }
  return matches
}

function findPathStem(inputFile: string, index: ReferenceIndex): Match[] {
  // For inputFile foo.ts, find record files whose basename contains the stem.
  // Score weighting:
  //   exact stem match  → 0.85
  //   partial substring → 0.55
  const stem = basenameStem(inputFile).toLowerCase()
  if (!stem) return []
  const matches: Match[] = []
  for (const rec of index.records) {
    const recStem = basenameStem(rec.path).toLowerCase()
    if (recStem === stem) {
      matches.push({
        inputFile,
        recordPath: rec.path,
        layer: rec.layer,
        linkKind: 'path-stem',
        score: 0.85,
        reason: `record basename '${recStem}' equals input stem`
      })
    } else if (recStem.length >= 4 && (recStem.includes(stem) || stem.includes(recStem))) {
      matches.push({
        inputFile,
        recordPath: rec.path,
        layer: rec.layer,
        linkKind: 'path-stem',
        score: 0.55,
        reason: `record basename '${recStem}' overlaps input stem '${stem}'`
      })
    }
  }
  return matches
}

// Generic / framework-noise tokens that we never use for ADR keyword matching.
// Two-layer defense:
//   (a) MANUAL_STOPWORDS — hand-curated path/structural words ('src','main',
//       'services', 'lazy', 'harness', etc) that have no semantic role even if
//       they happen to be rare in the corpus.
//   (b) computeIdfStopwords() — automatically derived from the current ADR
//       corpus. Any token of length ≥ TOKEN_MIN_LEN appearing in ≥30% of
//       ADR files is treated as stopword (low IDF, no discriminative power).
//       Re-computed on every resolver invocation off the loaded index, so
//       the list self-tunes as the ADR corpus grows.
const MANUAL_STOPWORDS = new Set([
  // Project-structural / path-noise
  'lazy',
  'harness',
  'jcode',
  'medivance',
  'main',
  'services',
  'service',
  'src',
  'project',
  'shared',
  'routers',
  'router',
  'preload',
  'renderer',
  'screens',
  'screen',
  'modal',
  'modals',
  // Common English nouns that are too generic to be discriminative even when
  // they happen to be rare in the current ADR corpus.
  'value',
  'values',
  'change',
  'changes',
  'state',
  'check',
  'index',
  'config',
  'tools',
  'plan',
  'plans',
  'notes',
  'rules',
  'gate',
  'gates',
  'file',
  'files',
  'item',
  'items',
  'list',
  'lists',
  'level',
  'levels',
  'schema',
  'schemas',
  'data'
])

const TOKEN_MIN_LEN = 5
const IDF_STOPWORD_THRESHOLD = 0.3 // ≥30% of ADR corpus → stopword

function computeIdfStopwords(index: ReferenceIndex): {
  stop: Set<string>
  df: Map<string, number>
  total: number
} {
  // Walk every ADR body, compute document-frequency for each token, and
  // promote any token with DF/total ≥ IDF_STOPWORD_THRESHOLD to stopword.
  // Cheap: O(ADRs × tokens), runs once per resolver invocation.
  const adrs = index.records.filter((r) => r.layer === 'adr')
  if (adrs.length === 0) return { stop: new Set(), df: new Map(), total: 0 }
  const df = new Map<string, number>()
  for (const rec of adrs) {
    let body = ''
    try {
      body = readFileSync(rec.path, 'utf8').toLowerCase()
    } catch {
      continue
    }
    const seen = new Set<string>()
    for (const match of body.matchAll(/\b[a-z]{5,}\b/g)) {
      seen.add(match[0])
    }
    for (const tk of seen) {
      df.set(tk, (df.get(tk) ?? 0) + 1)
    }
  }
  const cutoff = Math.ceil(adrs.length * IDF_STOPWORD_THRESHOLD)
  const stop = new Set<string>()
  for (const [tk, n] of df) {
    if (n >= cutoff) stop.add(tk)
  }
  return { stop, df, total: adrs.length }
}

function tokensFromPath(filePath: string, stopwords: Set<string>): string[] {
  // Break a path like src/main/services/patient-risk.ts into searchable tokens.
  // Token length ≥ TOKEN_MIN_LEN to avoid English common-word noise (e.g.
  // 'risk', 'data', 'mode'); domain-meaningful identifiers tend to be longer
  // ('patient', 'appointment', 'prescription', 'risk-score').
  const base = basenameStem(filePath).toLowerCase()
  const dirTokens = filePath
    .replace(/\\/g, '/')
    .split('/')
    .filter((p) => p && p !== '.' && p !== '..')
    .map((s) => s.toLowerCase())
  const splitTokens = new Set<string>()
  for (const token of [base, ...dirTokens]) {
    for (const piece of token.split(/[-_.]/)) {
      if (
        piece.length >= TOKEN_MIN_LEN &&
        !MANUAL_STOPWORDS.has(piece) &&
        !stopwords.has(piece)
      ) {
        splitTokens.add(piece)
      }
    }
  }
  return Array.from(splitTokens)
}

function findAdrKeyword(
  inputFile: string,
  index: ReferenceIndex,
  stopwords: Set<string>,
  df: Map<string, number>,
  totalAdrs: number
): Match[] {
  const tokens = tokensFromPath(inputFile, stopwords)
  if (tokens.length === 0) return []
  const matches: Match[] = []
  const adrRecords = index.records.filter((r) => r.layer === 'adr')
  // IDF-weighted scoring. For each matching token:
  //   tokenScore = 0.4 + 0.4 * idf
  //   idf = log(N / (1 + df)) / log(N)         ∈ (0, 1)
  // The 0.4 base ensures any keyword match starts above the 0.0 floor; rare
  // tokens (df=1) approach 0.8, common-but-not-stopword (df~6/22≈27%) drop to
  // ~0.5 which is below the candidate-cap default and easy to filter out.
  // A match-level threshold (MATCH_SCORE_FLOOR) drops matches whose weighted
  // score lands too close to the base, which kills the "5 ADRs all matched on
  // a single high-DF token" pattern observed in host-pilot pass 2 ('hooks').
  const MATCH_SCORE_FLOOR = 0.5
  for (const rec of adrRecords) {
    let body = ''
    try {
      body = readFileSync(rec.path, 'utf8').toLowerCase()
    } catch {
      continue
    }
    const evidence: Match['evidence'] = []
    const hitTokens: string[] = []
    let weightSum = 0
    for (const tk of tokens) {
      if (body.includes(tk)) {
        hitTokens.push(tk)
        const tkDf = df.get(tk) ?? 1
        // idf ∈ (0, 1] — extremely rare token (df=1, N=20) gives ~1.0,
        // moderately common (df=N/2) gives ~0.23.
        const idf = totalAdrs > 1 ? Math.log(totalAdrs / (1 + tkDf)) / Math.log(totalAdrs) : 1
        weightSum += Math.max(idf, 0)
        const lines = body.split('\n')
        const lineIdx = lines.findIndex((l) => l.includes(tk))
        if (lineIdx >= 0) {
          evidence.push({
            path: rec.path,
            line: lineIdx + 1,
            snippet: lines[lineIdx].slice(0, 160)
          })
        }
      }
    }
    if (hitTokens.length === 0) continue
    // Average IDF across hits so multiple weak hits don't compound into a
    // false-positive (a commit mentioning 3 mid-DF tokens shouldn't outscore
    // a commit mentioning 1 rare token).
    const avgIdf = weightSum / hitTokens.length
    const rawScore = 0.4 + 0.4 * avgIdf
    const score = Math.min(0.8, Math.max(0, rawScore))
    if (score < MATCH_SCORE_FLOOR) continue
    matches.push({
      inputFile,
      recordPath: rec.path,
      layer: 'adr',
      linkKind: 'keyword',
      score: Math.round(score * 100) / 100,
      reason: `ADR body mentions: ${hitTokens.join(', ')} (avg IDF ${avgIdf.toFixed(2)})`,
      evidence: evidence.slice(0, 3)
    })
  }
  // Burst suppression: if a single token fires across ≥ADR_BURST_THRESHOLD
  // ADRs for the same input file, that token is almost certainly under the
  // IDF stopword cutoff but still corpus-wide noise (host-pilot pass 3:
  // 'hooks' df=5/23=22% matched 5 ADRs with identical score). Drop any
  // single-token match that appears in a burst — multi-token matches survive
  // because the combination is far less likely to be coincidence.
  //
  // Threshold is scaled with corpus size so it's not a magic constant: at
  // N=23 ADRs the floor is 5 (≈22%); at N=10 ADRs it's still ≥3.
  // The fixture C case ('patient' df=3) sits at ~13% which we want to keep.
  const ADR_BURST_THRESHOLD = Math.max(3, Math.ceil(totalAdrs * 0.18))
  const singleTokenMatches = matches.filter((m) => /^ADR body mentions: [^,]+ /.test(m.reason))
  if (singleTokenMatches.length >= ADR_BURST_THRESHOLD) {
    const tokenCounts = new Map<string, number>()
    for (const m of singleTokenMatches) {
      const tok = m.reason.match(/^ADR body mentions: ([^,]+) /)?.[1]
      if (tok) tokenCounts.set(tok, (tokenCounts.get(tok) ?? 0) + 1)
    }
    const burstTokens = new Set<string>()
    for (const [tok, n] of tokenCounts) {
      if (n >= ADR_BURST_THRESHOLD) burstTokens.add(tok)
    }
    return matches.filter((m) => {
      const tok = m.reason.match(/^ADR body mentions: ([^,]+) /)?.[1]
      // Multi-token matches have a comma; single-token reason has no comma
      // before the parenthetical. Burst-flagged single-token matches drop.
      if (!tok) return true
      if (m.reason.includes(', ')) return true
      return !burstTokens.has(tok)
    })
  }
  return matches
}

function loadCrossLayerLinks(): Record<string, string[]> {
  const linksPath = '.lazy-harness/cross-layer/links.json'
  if (!existsSync(linksPath)) return {}
  try {
    return JSON.parse(readFileSync(linksPath, 'utf8')) as Record<string, string[]>
  } catch {
    return {}
  }
}

function findCrossLayer(inputFile: string, links: Record<string, string[]>): Match[] {
  const matches: Match[] = []
  const linked = links[inputFile] ?? []
  for (const target of linked) {
    // Infer layer from path
    let layer: Layer = 'ddd'
    for (const [l, dir] of Object.entries(RECORD_DIRS)) {
      if (target.startsWith(dir)) {
        layer = l as Layer
        break
      }
    }
    matches.push({
      inputFile,
      recordPath: target,
      layer,
      linkKind: 'cross-layer',
      score: 1.0,
      reason: 'explicit cross-layer link'
    })
  }
  return matches
}

// ────────────────────────────────────────────────────────────────────────────
// Main resolve API
// ────────────────────────────────────────────────────────────────────────────

export function resolveReferences(
  files: string[],
  opts: { rebuildIndex?: boolean; indexOut?: string } = {}
): ReferenceMap {
  const out = opts.indexOut ?? DEFAULT_INDEX_PATH
  const index = loadIndex(out, opts.rebuildIndex ?? false)
  const links = loadCrossLayerLinks()
  const idfData = computeIdfStopwords(index)

  const collected: Match[] = []
  for (const f of files) {
    collected.push(...findCrossLayer(f, links))
    collected.push(...findTestStem(f, index))
    collected.push(...findPathStem(f, index))
    collected.push(...findAdrKeyword(f, index, idfData.stop, idfData.df, idfData.total))
  }

  // De-dup by (inputFile, recordPath, linkKind), keep highest score
  const seen = new Map<string, Match>()
  for (const m of collected) {
    const key = `${m.inputFile}|${m.recordPath}|${m.linkKind}`
    const prev = seen.get(key)
    if (!prev || m.score > prev.score) seen.set(key, m)
  }
  // Sort by inputFile then score desc
  const matches = Array.from(seen.values()).sort((a, b) =>
    a.inputFile === b.inputFile ? b.score - a.score : a.inputFile.localeCompare(b.inputFile)
  )

  return {
    indexVersion: index.fingerprint,
    createdAt: new Date().toISOString(),
    inputFiles: files,
    matches
  }
}

function formatAsk(map: ReferenceMap): string {
  if (map.matches.length === 0) {
    return `[N2] No record matches for ${map.inputFiles.length} input file(s). (index=${map.indexVersion})`
  }
  const lines: string[] = []
  lines.push(`[N2] ${map.matches.length} match(es) across ${map.inputFiles.length} input file(s):`)
  let last = ''
  for (const m of map.matches) {
    if (m.inputFile !== last) {
      lines.push('')
      lines.push(`• ${m.inputFile}`)
      last = m.inputFile
    }
    lines.push(`    ${(m.score).toFixed(2)}  [${m.layer}/${m.linkKind}] ${m.recordPath} — ${m.reason}`)
  }
  return lines.join('\n')
}

function main(): void {
  const opts = parseCli(process.argv.slice(2))
  if (opts.files.length === 0) {
    // Build/refresh index and print stats only
    const idx = loadIndex(opts.out, opts.rebuildIndex)
    const counts: Record<string, number> = {}
    for (const r of idx.records) counts[r.layer] = (counts[r.layer] ?? 0) + 1
    console.log(JSON.stringify({ indexVersion: idx.fingerprint, recordCounts: counts, totalRecords: idx.records.length }, null, 2))
    return
  }
  const result = resolveReferences(opts.files, { rebuildIndex: opts.rebuildIndex, indexOut: opts.out })
  if (opts.format === 'ask') {
    console.log(formatAsk(result))
  } else {
    console.log(JSON.stringify(result, null, 2))
  }
}

const currentFile = fileURLToPath(import.meta.url)
if (process.argv[1] && path.resolve(process.argv[1]) === currentFile) {
  main()
}
