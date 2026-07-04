#!/usr/bin/env bun
/**
 * record-structure-audit.ts — read-only structural-readiness audit for the memory-device design.
 *
 * Measures (deterministic, no LLM, no mutation):
 *   1. surface-term coverage — records whose digest carries non-empty Aliases/Surface terms,
 *      plus Korean surface-term presence anywhere in the record body.
 *   2. reachability — in-file `.lazy-harness/...md` link graph (outbound + inbound),
 *      orphan records (zero inbound), zero-outbound records, connected components
 *      over the undirected link graph.
 *   3. link density distribution — outbound link counts per record.
 *   4. graph.jsonl schema census — rows per schema generation (drift quantification).
 *
 * Scope: canonical layers (domain/spec/behavior/tests/decisions/ssot) always;
 * extended scope (planning/plans/knowledge *.md) included for link-graph edges so
 * scatter across non-canonical locations is visible.
 *
 * Contract: W1 of `.lazy-harness/planning/memory-device-implementation-plan.md`.
 * Output is a BEFORE baseline for W2/W3/W5; cue-only, not semantic authority.
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'

type Format = 'json' | 'md'

const CANONICAL_DIRS = ['domain', 'spec', 'behavior', 'tests', 'decisions', 'ssot']
const EXTENDED_DIRS = ['planning', 'plans', 'knowledge']

interface Args {
  root: string
  format: Format
}

function parseArgs(argv: string[]): Args {
  const args: Args = { root: process.cwd(), format: 'md' }
  for (const a of argv) {
    if (a.startsWith('--format=')) {
      const f = a.slice('--format='.length)
      if (f === 'json' || f === 'md') args.format = f
    } else if (a.startsWith('--root=')) {
      args.root = path.resolve(a.slice('--root='.length))
    }
  }
  return args
}

function findHarnessRoot(start: string): string | null {
  let cur = path.resolve(start)
  while (true) {
    if (existsSync(path.join(cur, '.lazy-harness'))) return cur
    const parent = path.dirname(cur)
    if (parent === cur) return null
    cur = parent
  }
}

function listMarkdown(dir: string): string[] {
  const out: string[] = []
  if (!existsSync(dir)) return out
  const walk = (d: string) => {
    for (const entry of readdirSync(d)) {
      const p = path.join(d, entry)
      const st = statSync(p)
      if (st.isDirectory()) walk(p)
      else if (entry.endsWith('.md') && entry !== 'README.md') out.push(p)
    }
  }
  walk(dir)
  return out
}

function stripFences(text: string): string {
  return text.replace(/```[\s\S]*?```/g, '')
}

const LINK_RE = /\.lazy-harness\/[A-Za-z0-9_\-./]+?\.md/g
const HANGUL_RE = /[\uAC00-\uD7A3]/

function digestSection(text: string): string | null {
  const m = text.match(/## Rule digest\n([\s\S]*?)(?=\n## |$)/)
  return m ? m[0] : null
}

function hasNonEmptyListField(section: string, field: string): boolean {
  // matches "- Aliases:" / "- Surface terms:" followed by at least one "  - x" bullet
  const re = new RegExp(`- ${field}:\\s*\\n(\\s+- \\S[^\\n]*)`, 'i')
  return re.test(section)
}

function main(): number {
  const args = parseArgs(process.argv.slice(2))
  const root = findHarnessRoot(args.root)
  if (!root) {
    console.error('record-structure-audit: no .lazy-harness root found')
    return 1
  }
  const lh = path.join(root, '.lazy-harness')
  const rel = (p: string) => path.relative(root, p)

  const canonical = CANONICAL_DIRS.flatMap((d) => listMarkdown(path.join(lh, d)))
  const extended = EXTENDED_DIRS.flatMap((d) => listMarkdown(path.join(lh, d)))
  const allDocs = [...canonical, ...extended]
  const docSet = new Set(allDocs.map(rel))

  // --- link graph (in-file references, fences stripped) ---
  const outbound = new Map<string, Set<string>>()
  const inbound = new Map<string, Set<string>>()
  for (const doc of allDocs) {
    const key = rel(doc)
    const body = stripFences(readFileSync(doc, 'utf8'))
    const targets = new Set<string>()
    for (const m of body.matchAll(LINK_RE)) {
      const t = m[0]
      if (t !== key && docSet.has(t)) targets.add(t)
    }
    outbound.set(key, targets)
    for (const t of targets) {
      if (!inbound.has(t)) inbound.set(t, new Set())
      inbound.get(t)!.add(key)
    }
  }

  const canonicalRel = canonical.map(rel)
  const orphans = canonicalRel.filter((r) => (inbound.get(r)?.size ?? 0) === 0).sort()
  const zeroOutbound = canonicalRel.filter((r) => (outbound.get(r)?.size ?? 0) === 0).sort()

  // link density distribution over canonical records
  const counts = canonicalRel.map((r) => outbound.get(r)?.size ?? 0).sort((a, b) => a - b)
  const sum = counts.reduce((a, b) => a + b, 0)
  const pct = (q: number) => counts[Math.min(counts.length - 1, Math.floor(q * counts.length))] ?? 0

  // --- connected components (undirected, over all docs) ---
  const parent = new Map<string, string>()
  const find = (x: string): string => {
    let r = x
    while (parent.get(r) !== r) r = parent.get(r)!
    let c = x
    while (parent.get(c) !== c) {
      const n = parent.get(c)!
      parent.set(c, r)
      c = n
    }
    return r
  }
  const union = (a: string, b: string) => {
    const ra = find(a)
    const rb = find(b)
    if (ra !== rb) parent.set(ra, rb)
  }
  for (const d of docSet) parent.set(d, d)
  for (const [src, targets] of outbound) for (const t of targets) union(src, t)
  const compSizes = new Map<string, number>()
  for (const d of docSet) {
    const r = find(d)
    compSizes.set(r, (compSizes.get(r) ?? 0) + 1)
  }
  const components = [...compSizes.values()].sort((a, b) => b - a)
  const isolatedDocs = components.filter((s) => s === 1).length

  // --- surface-term coverage (canonical only) ---
  let withAliases = 0
  let withSurfaceTerms = 0
  let withKorean = 0
  const missingSurface: string[] = []
  for (const doc of canonical) {
    const text = readFileSync(doc, 'utf8')
    const digest = digestSection(text)
    const hasAlias = digest ? hasNonEmptyListField(digest, 'Aliases') : false
    const hasSurface = digest ? hasNonEmptyListField(digest, 'Surface terms') : false
    if (hasAlias) withAliases++
    if (hasSurface) withSurfaceTerms++
    if (HANGUL_RE.test(text)) withKorean++
    if (!hasAlias && !hasSurface) missingSurface.push(rel(doc))
  }

  // --- graph.jsonl schema census ---
  const graphPath = path.join(lh, 'knowledge', 'graph.jsonl')
  const schemaCensus: Record<string, number> = {}
  let graphRows = 0
  let graphParseErrors = 0
  if (existsSync(graphPath)) {
    for (const line of readFileSync(graphPath, 'utf8').split('\n')) {
      if (!line.trim()) continue
      graphRows++
      try {
        const row = JSON.parse(line)
        const gen = row.predicate
          ? 'subject-predicate-object'
          : row.relation && row.subject
            ? 'subject-relation-target'
            : row.relation
              ? 'source-relation-target'
              : 'unknown'
        schemaCensus[gen] = (schemaCensus[gen] ?? 0) + 1
      } catch {
        graphParseErrors++
      }
    }
  }

  const result = {
    schemaVersion: '1.0',
    mode: 'record-structure-audit',
    root,
    generatedAt: new Date().toISOString(),
    scope: {
      canonicalRecords: canonical.length,
      extendedDocs: extended.length,
      totalDocs: allDocs.length,
    },
    surfaceTerms: {
      canonicalWithAliases: withAliases,
      canonicalWithSurfaceTerms: withSurfaceTerms,
      canonicalWithKoreanText: withKorean,
      coverageRate: canonical.length ? +(withAliases / canonical.length).toFixed(3) : 0,
      missingCount: missingSurface.length,
    },
    reachability: {
      orphanCanonicalRecords: orphans.length,
      orphans,
      zeroOutboundCanonical: zeroOutbound.length,
      connectedComponents: components.length,
      largestComponent: components[0] ?? 0,
      isolatedDocs,
    },
    linkDensity: {
      canonicalAvgOutbound: canonical.length ? +(sum / canonical.length).toFixed(2) : 0,
      p50: pct(0.5),
      p90: pct(0.9),
      max: counts[counts.length - 1] ?? 0,
    },
    graphSchemaCensus: {
      rows: graphRows,
      parseErrors: graphParseErrors,
      generations: schemaCensus,
    },
    note: 'Read-only structural baseline (W1, memory-device-implementation-plan). Cue-only; not semantic authority.',
  }

  if (args.format === 'json') {
    console.log(JSON.stringify(result, null, 2))
  } else {
    const r = result
    console.log('# Record structure audit (W1 baseline)')
    console.log('')
    console.log(`- root: \`${r.root}\``)
    console.log(`- scope: canonical=${r.scope.canonicalRecords}, extended=${r.scope.extendedDocs}, total=${r.scope.totalDocs}`)
    console.log('')
    console.log('## Surface terms (grep bait)')
    console.log(`- aliases coverage: ${r.surfaceTerms.canonicalWithAliases}/${r.scope.canonicalRecords} (${Math.round(r.surfaceTerms.coverageRate * 100)}%)`)
    console.log(`- surface-terms coverage: ${r.surfaceTerms.canonicalWithSurfaceTerms}/${r.scope.canonicalRecords}`)
    console.log(`- records containing Korean text: ${r.surfaceTerms.canonicalWithKoreanText}`)
    console.log('')
    console.log('## Reachability (walking)')
    console.log(`- orphan canonical records (zero inbound): ${r.reachability.orphanCanonicalRecords}`)
    for (const o of r.reachability.orphans) console.log(`  - \`${o}\``)
    console.log(`- zero-outbound canonical records: ${r.reachability.zeroOutboundCanonical}`)
    console.log(`- connected components: ${r.reachability.connectedComponents} (largest=${r.reachability.largestComponent}, isolated docs=${r.reachability.isolatedDocs})`)
    console.log('')
    console.log('## Link density (canonical outbound)')
    console.log(`- avg=${r.linkDensity.canonicalAvgOutbound}, p50=${r.linkDensity.p50}, p90=${r.linkDensity.p90}, max=${r.linkDensity.max}`)
    console.log('')
    console.log('## graph.jsonl schema census')
    console.log(`- rows=${r.graphSchemaCensus.rows}, parseErrors=${r.graphSchemaCensus.parseErrors}`)
    for (const [gen, c] of Object.entries(r.graphSchemaCensus.generations)) console.log(`  - ${gen}: ${c}`)
    console.log('')
    console.log(`> ${r.note}`)
  }
  return 0
}

process.exit(main())
