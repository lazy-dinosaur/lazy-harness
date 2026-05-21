#!/usr/bin/env bun
/**
 * Graph Hygiene (SDD: spec/platform/graph-hygiene.md)
 *
 * Read-only lint for .lazy-harness/knowledge/graph.jsonl path/id hygiene.
 */
import { existsSync, readFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { join, resolve } from 'node:path'

interface Args {
  root: string
  graph: string
  source?: string
  format: 'json' | 'md'
  failOnIssues: boolean
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
    missingIds: number
    pathReferences: number
    missingPaths: number
    sourceOnlyPaths: number
    commaJoinedPaths: number
    issues: number
  }
  issues: Issue[]
  nextActions: string[]
}

function parseArgs(argv: string[]): Args {
  const root = process.env.LAZY_HOST_ROOT || process.cwd()
  const args: Args = {
    root,
    graph: join(root, '.lazy-harness', 'knowledge', 'graph.jsonl'),
    source: process.env.LAZY_FRAMEWORK_SOURCE,
    format: 'md',
    failOnIssues: false,
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
  console.log(`Graph Hygiene\n\nUsage:\n  bun .lazy-harness/scripts/graph-hygiene.ts [--format md|json] [--root <host>] [--source <framework>] [--graph <path>] [--fail-on-issues]\n  .lazy-harness/bin/lazy graph-hygiene --format=md\n\nRead-only lint for .lazy-harness/knowledge/graph.jsonl. Reports invalid JSON, missing IDs, duplicate IDs, comma-joined path strings, missing host-relative paths, and source-only paths that exist in the framework source but not the host.`)
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
      summary: { rows: 0, invalidRows: 0, uniqueIds: 0, duplicateIds: 0, missingIds: 0, pathReferences: 0, missingPaths: 0, sourceOnlyPaths: 0, commaJoinedPaths: 0, issues: 0 },
      issues: [],
      nextActions: ['No graph.jsonl found. Create graph records through implementation maps or knowledge intake before relying on graph navigation.'],
    }
  }
  const seen = new Map<string, number>()
  let rows = 0
  let invalidRows = 0
  let pathReferences = 0
  let missingPaths = 0
  let sourceOnlyPaths = 0
  let commaJoinedPaths = 0
  let missingIds = 0
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
    } else if (seen.has(id)) {
      addIssue(issues, { code: 'duplicate-id', severity: 'error', line: lineNumber, id, message: `Duplicate id also appeared on line ${seen.get(id)}.` })
    } else {
      seen.set(id, lineNumber)
    }
    for (const path of extractPaths(row)) {
      pathReferences += 1
      if (path.includes(',')) {
        commaJoinedPaths += 1
        addIssue(issues, { code: 'comma-joined-path', severity: 'warning', line: lineNumber, id: id || undefined, path, message: 'Path field appears to contain multiple comma-joined paths; use one graph row per path or an explicit path array.' })
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
  const duplicateIds = issues.filter((issue) => issue.code === 'duplicate-id').length
  return {
    ok: issues.filter((issue) => issue.severity === 'error').length === 0,
    mode: 'graph-hygiene.inspect',
    schemaVersion: '1.0',
    root: args.root,
    graphPath: args.graph,
    inspectedAt: new Date().toISOString(),
    summary: { rows, invalidRows, uniqueIds: seen.size, duplicateIds, missingIds, pathReferences, missingPaths, sourceOnlyPaths, commaJoinedPaths, issues: issues.length },
    issues,
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
