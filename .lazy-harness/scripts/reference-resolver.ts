#!/usr/bin/env bun
/**
 * N2 — Map-aware Reference Resolver (AI-first redesign, N2.5)
 *
 * For each changed source file, find candidate record files across the
 * record layers (DDD/SDD/BDD/TDD/ADR/SSOT) and emit a reference-map document.
 *
 * Resolution strategies (AI-first, ADR 0024):
 *   1. cross-layer-link (score 1.0)   — explicit entry in cross-layer/links.json
 *   2. test-stem        (score 0.95)  — sibling test file (foo.ts ↔ foo.test.ts)
 *   3. path-stem (exact, score 0.85)  — record basename equals input stem
 *   4. (semantic search) — DELEGATED to SearchProvider (AI direct grep + Read).
 *      framework 가 검색 알고리즘 직접 구현하지 않음 (ADR 0024 §2). 호출자
 *      (host AI) 가 AGENTS.md 의 Layer 매핑 룰 따라 능동 grep + Read 수행.
 *
 * 본 단순화의 근거:
 *   - N2 의 IDF/burst suppression/stopwords/ADR-keyword/path-stem partial 가
 *     검색 알고리즘 직접 구현 패턴이라 host-corpus 의존성 (매직 상수) 야기.
 *     ADR 0023 의 검증은 그대로지만, 그 구현 70% 를 ADR 0024 가 deprecate.
 *   - 본 resolver 는 이제 "확정적 매칭" (cross-layer + test-sibling + exact stem)
 *     만 수행. 의미론적 매칭은 AGENTS.md 룰 따라 AI 에 위임.
 *
 * Index cache:
 *   - generated/reference-index.json 에 record 카탈로그 + sha1 fingerprint.
 *   - drift 시 자동 rebuild.
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

type LinkKind = 'cross-layer' | 'test' | 'path-stem'

interface Match {
  inputFile: string
  recordPath: string
  layer: Layer
  linkKind: LinkKind
  score: number
  reason: string
}

interface ReferenceMap {
  indexVersion: string
  createdAt: string
  inputFiles: string[]
  matches: Match[]
  /** Hint to the caller (AI) that AGENTS.md §1 의 semantic search 도 필요할 수 있음 */
  semanticSearchHint?: string
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

// ─────────────────────────────────────────────────────────────────────────────
// Index build / load
// ─────────────────────────────────────────────────────────────────────────────

function walkRecordFiles(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      out.push(...walkRecordFiles(full))
    } else if (entry.isFile() && entry.name !== 'README.md') {
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

function persistIndex(outPath: string, index: ReferenceIndex): void {
  const dir = path.dirname(outPath)
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  writeFileSync(outPath, JSON.stringify(index, null, 2) + '\n', 'utf8')
}

function loadIndex(outPath: string, rebuild: boolean): ReferenceIndex {
  if (!rebuild && existsSync(outPath)) {
    try {
      const cached = JSON.parse(readFileSync(outPath, 'utf8')) as ReferenceIndex
      const fresh = buildIndex()
      if (fresh.fingerprint === cached.fingerprint) return cached
      persistIndex(outPath, fresh)
      return fresh
    } catch {
      // corrupt cache — rebuild
    }
  }
  const built = buildIndex()
  persistIndex(outPath, built)
  return built
}

// ─────────────────────────────────────────────────────────────────────────────
// Resolution strategies (확정적 매칭만)
// ─────────────────────────────────────────────────────────────────────────────

function basenameStem(filePath: string): string {
  const base = path.basename(filePath)
  return base.replace(/\.(test|spec)\.[tj]sx?$/, '').replace(/\.[a-z0-9]+$/i, '')
}

function isTestPath(filePath: string): boolean {
  return /\.(test|spec)\.[tj]sx?$/.test(filePath) || filePath.includes('/__tests__/')
}

/** test-stem (score 0.95) — sibling test file. */
function findTestStem(inputFile: string, _index: ReferenceIndex): Match[] {
  if (isTestPath(inputFile)) return []
  const stem = basenameStem(inputFile)
  if (!stem) return []
  const dir = path.dirname(inputFile)
  const candidates: string[] = []
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

/**
 * path-stem (exact only, score 0.85) — record basename equals input stem.
 *
 * 변경 (ADR 0024 N2.5): partial substring match 제거. exact match 만 유지.
 * 의미론적 fuzzy 매칭은 AGENTS.md §1 의 semantic search (AI 능동 grep) 에 위임.
 */
function findPathStem(inputFile: string, index: ReferenceIndex): Match[] {
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
    }
  }
  return matches
}

/** cross-layer-link (score 1.0) — explicit links.json entry. */
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

// ─────────────────────────────────────────────────────────────────────────────
// Main resolve API
// ─────────────────────────────────────────────────────────────────────────────

export function resolveReferences(
  files: string[],
  opts: { rebuildIndex?: boolean; indexOut?: string } = {}
): ReferenceMap {
  const out = opts.indexOut ?? DEFAULT_INDEX_PATH
  const index = loadIndex(out, opts.rebuildIndex ?? false)
  const links = loadCrossLayerLinks()

  const collected: Match[] = []
  for (const f of files) {
    collected.push(...findCrossLayer(f, links))
    collected.push(...findTestStem(f, index))
    collected.push(...findPathStem(f, index))
  }

  // De-dup by (inputFile, recordPath, linkKind), keep highest score
  const seen = new Map<string, Match>()
  for (const m of collected) {
    const key = `${m.inputFile}|${m.recordPath}|${m.linkKind}`
    const prev = seen.get(key)
    if (!prev || m.score > prev.score) seen.set(key, m)
  }
  const matches = Array.from(seen.values()).sort((a, b) =>
    a.inputFile === b.inputFile ? b.score - a.score : a.inputFile.localeCompare(b.inputFile)
  )

  // AI 에 "의미론적 검색은 너 (AI) 가 해" 라는 명시적 hint 부여.
  // AGENTS.md §1 Layer 매핑 룰 따라 `grep -rli '<token>' .lazy-harness/{ddd,...}/`
  // 능동 수행 + Read 로 의미론적 매칭 마무리.
  const semanticSearchHint =
    matches.length === 0
      ? 'No deterministic matches. Per AGENTS.md §1, perform semantic search: ' +
        `grep -rli '<core-token>' .lazy-harness/{ddd,sdd,bdd,tdd,decisions,ssot}/`
      : undefined

  return {
    indexVersion: index.fingerprint,
    createdAt: new Date().toISOString(),
    inputFiles: files,
    matches,
    ...(semanticSearchHint ? { semanticSearchHint } : {})
  }
}

function formatAsk(map: ReferenceMap): string {
  const lines: string[] = []
  if (map.matches.length === 0) {
    lines.push(`[N2] No deterministic matches for ${map.inputFiles.length} input file(s). (index=${map.indexVersion})`)
    if (map.semanticSearchHint) {
      lines.push(`     ${map.semanticSearchHint}`)
    }
    return lines.join('\n')
  }
  lines.push(`[N2] ${map.matches.length} match(es) across ${map.inputFiles.length} input file(s):`)
  let last = ''
  for (const m of map.matches) {
    if (m.inputFile !== last) {
      lines.push('')
      lines.push(`• ${m.inputFile}`)
      last = m.inputFile
    }
    lines.push(`    ${m.score.toFixed(2)}  [${m.layer}/${m.linkKind}] ${m.recordPath} — ${m.reason}`)
  }
  return lines.join('\n')
}

function main(): void {
  const opts = parseCli(process.argv.slice(2))
  if (opts.files.length === 0) {
    const idx = loadIndex(opts.out, opts.rebuildIndex)
    const counts: Record<string, number> = {}
    for (const r of idx.records) counts[r.layer] = (counts[r.layer] ?? 0) + 1
    console.log(
      JSON.stringify(
        { indexVersion: idx.fingerprint, recordCounts: counts, totalRecords: idx.records.length },
        null,
        2
      )
    )
    return
  }
  const result = resolveReferences(opts.files, {
    rebuildIndex: opts.rebuildIndex,
    indexOut: opts.out
  })
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
