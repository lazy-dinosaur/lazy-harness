#!/usr/bin/env bun
/**
 * Graph Hygiene (SDD: spec/platform/graph-hygiene.md)
 *
 * Read-only lint for .lazy-harness/knowledge/graph.jsonl path/id hygiene.
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { homedir } from 'node:os'
import { join, resolve } from 'node:path'

interface Args {
  root: string
  graph: string
  source?: string
  format: 'json' | 'md'
  failOnIssues: boolean
  migrationPlan: boolean
}

interface Issue {
  code: 'invalid-json' | 'missing-id' | 'duplicate-id' | 'comma-joined-path' | 'missing-path'
  severity: 'error' | 'warning'
  line: number
  id?: string
  path?: string
  message: string
}

interface GraphHygieneResult {
  ok: boolean
  mode: 'graph-hygiene.inspect'
  schemaVersion: '1.0'
  root: string
  graphPath: string
  inspectedAt: string
  summary: {
    rows: number
    invalidRows: number
    uniqueIds: number
    duplicateIds: number
    supersededTrails: number
    missingIds: number
    pathReferences: number
    missingPaths: number
    sourceOnlyPaths: number
    commaJoinedPaths: number
    issues: number
  }
  issues: Issue[]
  nextActions: string[]
  migrationPlan?: {
    legacySchemaRows: number
    removedFrameworkRefs: number
    recordJcodeMentions: number
    proposals: MigrationProposal[]
  }
}

interface MigrationProposal {
  kind: 'legacy-schema-row' | 'removed-framework-ref' | 'record-body-jcode-mention'
  line: number
  id?: string
  detail: string
  proposal: string
}

// ADR 0050 (Pi/OMP-only runtime) removed these framework files; legacy host graph rows may
// still reference them. Mirror of lazy-sync.ts KNOWN_REMOVED_MANAGED_FILES (not importable:
// that script executes main() at module load). CO-CHANGE: extend both lists together.
const REMOVED_FRAMEWORK_FILES = new Set([
  '.lazy-harness/scripts/jcode-wiring.ts',
  '.lazy-harness/scripts/skill-create.ts',
  '.lazy-harness/scripts/operational-state.ts',
  '.lazy-harness/scripts/task-router.ts',
  '.lazy-harness/scripts/context-broker-dogfood.ts',
  '.lazy-harness/scripts/context-delivery.ts',
  '.lazy-harness/scripts/relevant-record-query.ts',
  '.lazy-harness/scripts/context-index.ts',
  '.lazy-harness/spec/platform/graph-explain.md',
  '.lazy-harness/spec/platform/graph-path.md',
  '.lazy-harness/spec/platform/graph-query.md',
  '.lazy-harness/spec/platform/graph-cleanup.md',
])

function isLegacySchemaRow(row: Record<string, unknown>): boolean {
  if ('predicate' in row || 'relation' in row) return false
  return ('from' in row && 'to' in row) || ('type' in row && ('source' in row || 'target' in row || 'from' in row))
}

const JCODE_SCAN_DIRS = ['domain', 'spec', 'behavior', 'tests', 'decisions', 'ssot']
const JCODE_RE_G = /jcode/gi

// Detection-only: record BODIES mentioning jcode. graph-migrate never edits record bodies;
// it reports so the human can judge (historical narration stays vs stale present-tense claims
// → lazy-record-quality). Scans the 6 canonical layer dirs under the host root.
function scanRecordJcode(root: string): { file: string; hits: number }[] {
  const out: { file: string; hits: number }[] = []
  const walk = (dir: string, rel: string): void => {
    let entries: string[]
    try { entries = readdirSync(dir) } catch { return }
    for (const entry of entries) {
      const abs = join(dir, entry)
      let st
      try { st = statSync(abs) } catch { continue }
      if (st.isDirectory()) { walk(abs, `${rel}/${entry}`); continue }
      if (!entry.endsWith('.md')) continue
      let text: string
      try { text = readFileSync(abs, 'utf8') } catch { continue }
      const hits = (text.match(JCODE_RE_G) || []).length
      if (hits > 0) out.push({ file: `${rel}/${entry}`, hits })
    }
  }
  for (const d of JCODE_SCAN_DIRS) walk(join(root, '.lazy-harness', d), `.lazy-harness/${d}`)
  return out
}

function parseArgs(argv: string[]): Args {
  const root = process.env.LAZY_HOST_ROOT || process.cwd()
  const args: Args = {
    root,
    graph: join(root, '.lazy-harness', 'knowledge', 'graph.jsonl'),
    source: process.env.LAZY_FRAMEWORK_SOURCE,
    format: 'md',
    failOnIssues: false,
    migrationPlan: false,
  }
  let graphProvided = false
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if ((arg === '--root' || arg === '--host') && next) {
      args.root = next
      i += 1
    } else if (arg.startsWith('--root=')) {
      args.root = arg.slice('--root='.length)
    } else if (arg.startsWith('--host=')) {
      args.root = arg.slice('--host='.length)
    } else if (arg === '--graph' && next) {
      args.graph = next
      graphProvided = true
      i += 1
    } else if (arg.startsWith('--graph=')) {
      args.graph = arg.slice('--graph='.length)
      graphProvided = true
    } else if (arg === '--source' && next) {
      args.source = next
      i += 1
    } else if (arg.startsWith('--source=')) {
      args.source = arg.slice('--source='.length)
    } else if (arg === '--format' && next) {
      if (next !== 'json' && next !== 'md' && next !== 'markdown') throw new Error(`Unsupported --format: ${next}`)
      args.format = next === 'markdown' ? 'md' : next
      i += 1
    } else if (arg.startsWith('--format=')) {
      const value = arg.slice('--format='.length)
      if (value !== 'json' && value !== 'md' && value !== 'markdown') throw new Error(`Unsupported --format: ${value}`)
      args.format = value === 'markdown' ? 'md' : value
    } else if (arg === '--fail-on-issues') {
      args.failOnIssues = true
    } else if (arg === '--migration-plan') {
      args.migrationPlan = true
    } else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown argument: ${arg}`)
    }
  }
  args.root = resolve(args.root)
  args.graph = resolve(graphProvided ? args.graph : join(args.root, '.lazy-harness', 'knowledge', 'graph.jsonl'))
  if (args.source) args.source = lazyDir(resolve(args.source))
  else args.source = defaultSource(args.root)
  return args
}

function printHelp(): void {
  console.log(`Graph Hygiene\n\nUsage:\n  bun .lazy-harness/scripts/graph-hygiene.ts [--format md|json] [--root <host>] [--source <framework>] [--graph <path>] [--fail-on-issues] [--migration-plan]\n  .lazy-harness/bin/lazy graph-hygiene --format=md\n  .lazy-harness/bin/lazy graph-hygiene --migration-plan --format=md\n\nRead-only lint for .lazy-harness/knowledge/graph.jsonl. Reports invalid JSON, missing IDs, duplicate IDs, comma-joined path strings, missing host-relative paths, and source-only paths that exist in the framework source but not the host.\n\nDuplicate-id policy: append-only supersession legitimately reuses an id (1 active row + status:superseded history). Only 2+ ACTIVE (non-superseded) rows sharing an id are a duplicate-id error; 1-active+superseded trails are counted as supersededTrails, not errors.\n\n--migration-plan additionally proposes (read-only, never writes): normalization of legacy-schema rows (from/to/type variants) to subject/predicate/object, supersede notes for references to ADR-0050-removed framework files, and detection-only reporting of record-body jcode mentions (fixed via lazy-record-quality, not here). Apply graph proposals only through the lazy-graph-migrate guided skill (batch + user approval).`)
}

function lazyDir(path: string): string {
  return path.endsWith('.lazy-harness') ? path : join(path, '.lazy-harness')
}

function defaultSource(root: string): string | undefined {
  const candidates = [
    process.env.LAZY_SOURCE_ROOT,
    join(homedir(), 'dev', 'lazy-harness'),
    join(homedir(), 'dev', 'lazy-harness', '.lazy-harness'),
  ].filter(Boolean) as string[]
  for (const candidate of candidates) {
    const lazy = lazyDir(resolve(candidate))
    if (existsSync(lazy) && resolve(lazy) !== resolve(join(root, '.lazy-harness'))) return lazy
  }
  return undefined
}

function existsInSource(args: Args, path: string): boolean {
  return Boolean(args.source && path.startsWith('.lazy-harness/') && existsSync(join(args.source, path.slice('.lazy-harness/'.length))))
}

function extractPaths(row: Record<string, unknown>): string[] {
  const out: string[] = []
  for (const key of ['path', 'file', 'sourcePath', 'targetPath']) {
    const value = row[key]
    if (typeof value === 'string') out.push(value)
    else if (Array.isArray(value)) out.push(...value.filter((item): item is string => typeof item === 'string'))
  }
  const evidence = row.evidence
  if (Array.isArray(evidence)) {
    for (const item of evidence) {
      if (item && typeof item === 'object' && typeof (item as { path?: unknown }).path === 'string') out.push((item as { path: string }).path)
    }
  }
  const links = row.links
  if (Array.isArray(links)) {
    for (const item of links) {
      if (!item || typeof item !== 'object') continue
      const target = (item as { target?: unknown }).target
      if (typeof target === 'string' && target.startsWith('.lazy-harness/')) out.push(target)
    }
  }
  return [...new Set(out)]
}

function addIssue(issues: Issue[], issue: Issue): void {
  issues.push(issue)
}

function inspect(args: Args): GraphHygieneResult {
  const issues: Issue[] = []
  if (!existsSync(args.graph)) {
    return {
      ok: true,
      mode: 'graph-hygiene.inspect',
      schemaVersion: '1.0',
      root: args.root,
      graphPath: args.graph,
      inspectedAt: new Date().toISOString(),
      summary: { rows: 0, invalidRows: 0, uniqueIds: 0, duplicateIds: 0, supersededTrails: 0, missingIds: 0, pathReferences: 0, missingPaths: 0, sourceOnlyPaths: 0, commaJoinedPaths: 0, issues: 0 },
      issues: [],
      nextActions: ['No graph.jsonl found. Create graph records through implementation maps or knowledge intake before relying on graph navigation.'],
    }
  }
  const idGroups = new Map<string, { line: number; status: string }[]>()
  let rows = 0
  let invalidRows = 0
  let pathReferences = 0
  let missingPaths = 0
  let sourceOnlyPaths = 0
  let commaJoinedPaths = 0
  let missingIds = 0
  const proposals: MigrationProposal[] = []
  for (const [index, line] of readFileSync(args.graph, 'utf8').split(/\r?\n/).entries()) {
    const lineNumber = index + 1
    if (!line.trim()) continue
    rows += 1
    let row: Record<string, unknown>
    try {
      row = JSON.parse(line) as Record<string, unknown>
    } catch (error) {
      invalidRows += 1
      addIssue(issues, { code: 'invalid-json', severity: 'error', line: lineNumber, message: error instanceof Error ? error.message : String(error) })
      continue
    }
    const id = typeof row.id === 'string' ? row.id : ''
    if (!id) {
      missingIds += 1
      addIssue(issues, { code: 'missing-id', severity: 'error', line: lineNumber, message: 'Graph row is missing string id.' })
    } else {
      const status = typeof row.status === 'string' ? row.status : ''
      const group = idGroups.get(id)
      if (group) group.push({ line: lineNumber, status })
      else idGroups.set(id, [{ line: lineNumber, status }])
    }
    if (args.migrationPlan && isLegacySchemaRow(row)) {
      const subject = String(row.subject ?? row.from ?? row.source ?? '?')
      const predicate = String(row.type ?? '?')
      const object = String(row.to ?? row.target ?? '?')
      proposals.push({
        kind: 'legacy-schema-row',
        line: lineNumber,
        id: id || undefined,
        detail: `legacy keys ${Object.keys(row).filter((k) => ['from', 'to', 'type', 'note'].includes(k)).join('/')}`,
        proposal: `append normalized row {subject: ${subject}, predicate: ${predicate}, object: ${object}} (carry note→summary, confidence) and mark this row status:superseded — append-only, never rewrite in place; verify file/symbol facts via source read BEFORE applying (progressive-knowledge-graph Must)`,
      })
    }
    for (const path of extractPaths(row)) {
      pathReferences += 1
      if (path.includes(',')) {
        commaJoinedPaths += 1
        addIssue(issues, { code: 'comma-joined-path', severity: 'warning', line: lineNumber, id: id || undefined, path, message: 'Path field appears to contain multiple comma-joined paths; use one graph row per path or an explicit path array.' })
      }
      if (args.migrationPlan && REMOVED_FRAMEWORK_FILES.has(path)) {
        proposals.push({
          kind: 'removed-framework-ref',
          line: lineNumber,
          id: id || undefined,
          detail: `references framework file removed by ADR 0050: ${path}`,
          proposal: 'append a superseding note row (status:superseded, pointer: .lazy-harness/decisions/0050-pi-omp-only-runtime.md) mirroring the framework Phase 2 treatment; do not delete the original row',
        })
      }
      if (path.startsWith('.') && !existsSync(join(args.root, path))) {
        if (existsInSource(args, path)) {
          sourceOnlyPaths += 1
          continue
        }
        missingPaths += 1
        addIssue(issues, { code: 'missing-path', severity: 'warning', line: lineNumber, id: id || undefined, path, message: 'Host-relative path does not exist.' })
      }
    }
  }
  // Duplicate-id policy (2026-07-05, user-approved): append-only supersession legitimately creates
  // same-id trails. A group with <=1 active (non-superseded) row + superseded rest is a historical
  // trail, NOT a duplicate error. Only 2+ ACTIVE rows sharing an id are a real duplicate.
  let supersededTrails = 0
  for (const [gid, entries] of idGroups) {
    if (entries.length < 2) continue
    const active = entries.filter((e) => e.status !== 'superseded')
    if (active.length >= 2) {
      for (const e of active.slice(1)) {
        addIssue(issues, { code: 'duplicate-id', severity: 'error', line: e.line, id: gid, message: `Duplicate active id: ${active.length} non-superseded rows share this id (first at line ${active[0].line}). Supersede all but one with status:superseded (append-only) or fix the id.` })
      }
    } else {
      supersededTrails += 1
    }
  }
  const duplicateIds = issues.filter((issue) => issue.code === 'duplicate-id').length
  let recordJcodeMentions = 0
  if (args.migrationPlan) {
    for (const { file, hits } of scanRecordJcode(args.root)) {
      recordJcodeMentions += 1
      proposals.push({
        kind: 'record-body-jcode-mention',
        line: 0,
        detail: `record body mentions jcode (${hits}x): ${file}`,
        proposal: 'DETECTION ONLY — human judgment via lazy-record-quality: keep historical narration (e.g. ADR 0050/0051 jcode history), rewrite only stale present-tense jcode claims. graph-migrate never edits record bodies.',
      })
    }
  }
  return {
    ok: issues.filter((issue) => issue.severity === 'error').length === 0,
    mode: 'graph-hygiene.inspect',
    schemaVersion: '1.0',
    root: args.root,
    graphPath: args.graph,
    inspectedAt: new Date().toISOString(),
    summary: { rows, invalidRows, uniqueIds: idGroups.size, duplicateIds, supersededTrails, missingIds, pathReferences, missingPaths, sourceOnlyPaths, commaJoinedPaths, issues: issues.length },
    issues,
    ...(args.migrationPlan
      ? {
          migrationPlan: {
            legacySchemaRows: proposals.filter((p) => p.kind === 'legacy-schema-row').length,
            removedFrameworkRefs: proposals.filter((p) => p.kind === 'removed-framework-ref').length,
            recordJcodeMentions: proposals.filter((p) => p.kind === 'record-body-jcode-mention').length,
            proposals,
          },
        }
      : {}),
    nextActions: [
      'Fix invalid JSON and duplicate/missing IDs before relying on graph queries.',
      'Replace comma-joined path strings with separate graph records or explicit path arrays.',
      'For missing host paths, confirm whether the record belongs to the host copy or needs supersession; framework-source-only paths are counted separately.',
    ],
  }
}

function renderMd(result: GraphHygieneResult): string {
  const lines: string[] = []
  lines.push('# Graph hygiene')
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Graph: \`${result.graphPath}\``)
  lines.push(`- OK: ${result.ok ? 'yes' : 'no'}`)
  lines.push(`- Rows: ${result.summary.rows}`)
  lines.push(`- Issues: ${result.summary.issues}`)
  lines.push(`- Invalid rows: ${result.summary.invalidRows}`)
  lines.push(`- Duplicate IDs: ${result.summary.duplicateIds}`)
  lines.push(`- Superseded trails (1 active + superseded history, OK): ${result.summary.supersededTrails}`)
  lines.push(`- Missing IDs: ${result.summary.missingIds}`)
  lines.push(`- Path references: ${result.summary.pathReferences}`)
  lines.push(`- Missing paths: ${result.summary.missingPaths}`)
  lines.push(`- Source-only paths: ${result.summary.sourceOnlyPaths}`)
  lines.push(`- Comma-joined paths: ${result.summary.commaJoinedPaths}`)
  if (result.issues.length > 0) {
    lines.push('')
    lines.push('## Issues')
    for (const issue of result.issues.slice(0, 80)) {
      lines.push(`- [${issue.severity}] ${issue.code} line=${issue.line}${issue.id ? ` id=${issue.id}` : ''}${issue.path ? ` path=\`${issue.path}\`` : ''} — ${issue.message}`)
    }
    if (result.issues.length > 80) lines.push(`- ... ${result.issues.length - 80} more issue(s)`)
  }
  if (result.migrationPlan) {
    lines.push('')
    lines.push('## Migration plan (read-only proposals — apply via the lazy-graph-migrate guided skill, batch + user approval)')
    lines.push(`- Legacy-schema rows: ${result.migrationPlan.legacySchemaRows}`)
    lines.push(`- Removed-framework refs: ${result.migrationPlan.removedFrameworkRefs}`)
    lines.push(`- Record-body jcode mentions (detection only → lazy-record-quality): ${result.migrationPlan.recordJcodeMentions}`)
    for (const p of result.migrationPlan.proposals.slice(0, 80)) {
      lines.push(`- [${p.kind}] line=${p.line}${p.id ? ` id=${p.id}` : ''} — ${p.detail} → ${p.proposal}`)
    }
    if (result.migrationPlan.proposals.length > 80) lines.push(`- ... ${result.migrationPlan.proposals.length - 80} more proposal(s)`)
  }
  lines.push('')
  lines.push('## Next actions')
  for (const action of result.nextActions) lines.push(`- ${action}`)
  return lines.join('\n')
}

try {
  const args = parseArgs(process.argv.slice(2))
  const result = inspect(args)
  if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
  else console.log(renderMd(result))
  if (args.failOnIssues && result.issues.length > 0) process.exit(2)
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error))
  process.exit(1)
}
