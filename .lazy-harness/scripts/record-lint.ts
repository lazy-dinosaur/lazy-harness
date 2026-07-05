#!/usr/bin/env bun
/**
 * record-lint.ts — deterministic, read-only validator for canonical `.lazy-harness` records.
 *
 * Checks each canonical record (domain/spec/behavior/tests/decisions/ssot, excluding README):
 *   - a well-formed `## Rule digest` (Status/Layer/Scope enums valid, Layer matches path,
 *     Applies-when and Must bullets present),
 *   - no broken `.lazy-harness/...md` record references (outside fenced code blocks).
 *
 * Meant to be enforced at the commit/push gate via `lazy test`/self-test (blocking),
 * NOT as a dev-time tool.execute.before hard gate (ADR 0016/0041/0048).
 */
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import path from 'node:path'

type Format = 'json' | 'md'

const CANONICAL_LAYER: Record<string, string> = {
  domain: 'DDD',
  spec: 'SDD',
  behavior: 'BDD',
  tests: 'TDD',
  decisions: 'ADR',
  ssot: 'SSOT',
}
const VALID_STATUS: Record<string, true> = {
  active: true,
  advisory: true,
  deprecated: true,
  reverted: true,
  'needs-review': true,
}
const VALID_SCOPE: Record<string, true> = {
  'framework-global': true,
  'host-project': true,
  'team-policy': true,
  'layer-fact': true,
  'transient-plan': true,
  'local-only': true,
}
const VALID_LAYER: Record<string, true> = {
  DDD: true,
  SDD: true,
  BDD: true,
  TDD: true,
  ADR: true,
  SSOT: true,
  Planning: true,
}

interface Issue {
  recordPath: string
  code: string
  detail: string
}

interface Args {
  root: string
  format: Format
  failOnIssues: boolean
}

function usage(code = 2): never {
  const out = code === 0 ? console.log : console.error
  out(`Record Lint\n\nUsage:\n  .lazy-harness/bin/lazy record-lint [--format=json|md] [--fail-on-issues]\n\nRead-only validator: every canonical record (domain/spec/behavior/tests/decisions/ssot) must carry a well-formed \`## Rule digest\` and must not cite missing .lazy-harness records. Meant for the commit/push gate via lazy test, not a dev-time block.`)
  process.exit(code)
}

function normalizeFormat(value: string): Format {
  if (value === 'markdown') return 'md'
  if (value === 'json' || value === 'md') return value
  throw new Error(`Unsupported --format: ${value}`)
}

function parseArgs(argv: string[]): Args {
  const args: Args = { root: process.env.LAZY_HOST_ROOT || process.cwd(), format: 'md', failOnIssues: false }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '--help' || arg === '-h') usage(0)
    else if (arg === '--fail-on-issues') args.failOnIssues = true
    else if ((arg === '--root' || arg === '--host') && next) { args.root = next; i += 1 }
    else if (arg.startsWith('--root=')) args.root = arg.slice('--root='.length)
    else if (arg.startsWith('--host=')) args.root = arg.slice('--host='.length)
    else if ((arg === '--format' || arg === '-f') && next) { args.format = normalizeFormat(next); i += 1 }
    else if (arg.startsWith('--format=')) args.format = normalizeFormat(arg.slice('--format='.length))
    else throw new Error(`Unknown argument: ${arg}`)
  }
  args.root = path.resolve(args.root)
  if (!existsSync(path.join(args.root, '.lazy-harness'))) throw new Error(`Host root missing .lazy-harness: ${args.root}`)
  return args
}

function walkRecords(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const entry of readdirSync(dir).sort()) {
    const full = path.join(dir, entry)
    if (statSync(full).isDirectory()) out.push(...walkRecords(full))
    else if (entry.endsWith('.md') && entry.toLowerCase() !== 'readme.md') out.push(full)
  }
  return out
}

// 3 call sites (Status/Layer/Scope) need lockstep `- Name: value` extraction.
function digestField(block: string, name: string): string | null {
  const match = block.match(new RegExp(`(?:^|\\n)\\s*-\\s*${name}\\s*:\\s*([^\\n]+)`))
  return match ? match[1].trim() : null
}

// ADR 0026 markers (same signal as self-test _detect_scope / doctor standalone detection):
// the framework dev repo carries BOTH; hosts carry neither. Do NOT use
// state/synced-from-commit absence (see check_standalone_source_detection_uses_markers).
function isFrameworkSourceRoot(root: string): boolean {
  const lazy = path.join(root, '.lazy-harness')
  return (
    existsSync(path.join(lazy, 'framework', 'framework-contract.md')) &&
    existsSync(path.join(lazy, 'planning', 'phase-5-plan.xml'))
  )
}

// Category-A canonical records are framework-owned: synced from source and enforced at the
// framework commit gate. On a host the full record graph is a superset of the synced subset,
// so a synced framework record legitimately cross-references records the host never carries —
// those structural dangling refs are not host defects. Host-context lint therefore skips
// framework-owned records; host-authored records (outside Category A) stay fully strict so
// genuine host typos are still caught.
function loadFrameworkOwnedRecords(root: string): Set<string> {
  const owned = new Set<string>()
  const manifestPath = path.join(root, '.lazy-harness', 'manifests', 'init-categories.json')
  if (!existsSync(manifestPath)) return owned
  let manifest: unknown
  try {
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
  } catch {
    return owned
  }
  const items = (manifest as { categories?: { A?: { items?: unknown[] } } })?.categories?.A?.items
  if (!Array.isArray(items)) return owned
  for (const item of items) {
    const entry = item as { path?: string; targetPath?: string; kind?: string }
    if (entry?.kind !== 'file') continue
    const rel = entry.targetPath || entry.path
    if (typeof rel !== 'string') continue
    if (!(rel.split('/')[0] in CANONICAL_LAYER)) continue
    owned.add(`.lazy-harness/${rel}`)
  }
  return owned
}

function lint(root: string): { issues: Issue[]; advisories: Issue[]; inspected: number; cleanRecords: number; frameworkOwned: number } {
  const issues: Issue[] = []
  const advisories: Issue[] = []
  let inspected = 0
  let cleanRecords = 0
  let frameworkOwned = 0
  const hostContext = !isFrameworkSourceRoot(root)
  const ownedRecords = hostContext ? loadFrameworkOwnedRecords(root) : new Set<string>()
  for (const [dir, expectedLayer] of Object.entries(CANONICAL_LAYER)) {
    for (const file of walkRecords(path.join(root, '.lazy-harness', dir))) {
      inspected += 1
      const recordPath = `.lazy-harness/${path.relative(path.join(root, '.lazy-harness'), file).split(path.sep).join('/')}`
      if (hostContext && ownedRecords.has(recordPath)) {
        frameworkOwned += 1
        continue
      }
      const body = readFileSync(file, 'utf8')
      const before = issues.length

      const digestMatch = body.match(/(?:^|\n)##\s+Rule digest\s*\n([\s\S]*?)(?:\n#{1,2}\s|$)/)
      const block = digestMatch ? digestMatch[1] : null
      if (!block) {
        issues.push({ recordPath, code: 'missing-rule-digest', detail: 'no `## Rule digest` section' })
      } else {
        const status = digestField(block, 'Status')
        if (!status) issues.push({ recordPath, code: 'digest-missing-status', detail: 'Status field missing' })
        else if (!VALID_STATUS[status]) issues.push({ recordPath, code: 'digest-bad-status', detail: `Status='${status}' not a valid status` })

        const layer = digestField(block, 'Layer')
        if (!layer) issues.push({ recordPath, code: 'digest-missing-layer', detail: 'Layer field missing' })
        else if (!VALID_LAYER[layer]) issues.push({ recordPath, code: 'digest-bad-layer', detail: `Layer='${layer}' not a valid layer` })
        else if (layer !== expectedLayer) issues.push({ recordPath, code: 'digest-layer-path-mismatch', detail: `Layer='${layer}' but path implies '${expectedLayer}'` })

        const scope = digestField(block, 'Scope')
        if (!scope) issues.push({ recordPath, code: 'digest-missing-scope', detail: 'Scope field missing' })
        else if (!VALID_SCOPE[scope]) issues.push({ recordPath, code: 'digest-bad-scope', detail: `Scope='${scope}' not a valid scope` })

        if (!/(?:^|\n)\s*-\s*Applies when\s*:/.test(block)) issues.push({ recordPath, code: 'digest-missing-applies-when', detail: 'Applies when bullet missing' })
        if (!/(?:^|\n)\s*-\s*Must\s*:/.test(block)) issues.push({ recordPath, code: 'digest-missing-must', detail: 'Must bullet missing' })

        // ADR 0053 advisory (never exit-affecting): surface terms are the grep bait
        // for bridging user vocabulary to records; coverage is advisory until dogfood
        // evidence justifies promotion.
        const hasAliases = /(?:^|\n)\s*-\s*Aliases\s*:\s*\n\s+-\s*\S/.test(block)
        const hasSurfaceTerms = /(?:^|\n)\s*-\s*Surface terms\s*:\s*\n\s+-\s*\S/.test(block)
        if (!hasAliases && !hasSurfaceTerms && status !== 'deprecated' && status !== 'reverted') {
          advisories.push({ recordPath, code: 'advisory-missing-surface-terms', detail: 'digest has no non-empty Aliases/Surface terms (ADR 0053 grep-bait rule)' })
        }
      }

      const scan = body.replace(/```[\s\S]*?```/g, '')
      const seen = new Set<string>()
      for (const match of scan.matchAll(/\.lazy-harness\/[A-Za-z0-9_./-]+\.md/g)) {
        const ref = match[0]
        if (seen.has(ref) || ref === recordPath || ref.includes('...')) continue
        seen.add(ref)
        if (!existsSync(path.join(root, ref))) issues.push({ recordPath, code: 'broken-record-ref', detail: `cites missing ${ref}` })
      }

      if (issues.length === before) cleanRecords += 1
    }
  }
  return { issues, advisories, inspected, cleanRecords, frameworkOwned }
}

function renderMarkdown(payload: Record<string, unknown>): string {
  const lines: string[] = []
  lines.push('# Record lint')
  lines.push('')
  lines.push('- mode: `record-lint`')
  lines.push(`- inspected canonical records: ${payload.inspected}`)
  lines.push(`- clean records: ${payload.cleanRecords}`)
  lines.push(`- framework-owned (host-skipped): ${payload.frameworkOwned ?? 0}`)
  lines.push(`- issues: ${payload.issueCount}`)
  const counts = payload.counts as Record<string, number>
  if (Object.keys(counts).length) {
    lines.push('', '## Counts')
    for (const [code, count] of Object.entries(counts).sort()) lines.push(`- ${code}: ${count}`)
  }
  const issues = payload.issues as Issue[]
  if (issues.length) {
    lines.push('', '## Issues')
    for (const issue of issues) lines.push(`- [${issue.code}] \`${issue.recordPath}\` — ${issue.detail}`)
  } else {
    lines.push('', 'All canonical records pass digest-format and reference checks.')
  }
  const advisories = (payload.advisories as Issue[] | undefined) ?? []
  lines.push('', `- advisories (non-blocking): ${advisories.length}`)
  if (advisories.length) {
    const byCode: Record<string, number> = {}
    for (const advisory of advisories) byCode[advisory.code] = (byCode[advisory.code] || 0) + 1
    for (const [code, count] of Object.entries(byCode).sort()) lines.push(`  - ${code}: ${count}`)
  }
  return `${lines.join('\n')}\n`
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    const { issues, advisories, inspected, cleanRecords, frameworkOwned } = lint(args.root)
    const counts: Record<string, number> = {}
    for (const issue of issues) counts[issue.code] = (counts[issue.code] || 0) + 1
    const payload = {
      schemaVersion: '1.0',
      mode: 'record-lint',
      root: args.root,
      inspected,
      cleanRecords,
      frameworkOwned,
      issueCount: issues.length,
      counts,
      issues,
      advisoryCount: advisories.length,
      advisories,
      note: 'Read-only canonical-record validator (digest format + broken record refs). Enforce at the commit/push gate via lazy test, not a dev-time block.',
    }
    if (args.format === 'json') console.log(JSON.stringify(payload, null, 2))
    else process.stdout.write(renderMarkdown(payload))
    if (args.failOnIssues && issues.length > 0) process.exit(2)
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
