#!/usr/bin/env bun
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

const LEVELS = new Set(['discover', 'recommend', 'default', 'warn', 'block'])
const LEVEL_ORDER = ['block', 'warn', 'default', 'recommend', 'discover']
const SCOPES = new Set(['framework-global', 'host-project', 'team-policy', 'jcode-local'])
const STATUSES = new Set(['active', 'draft', 'retired'])

type Format = 'json' | 'md'
type Severity = 'error' | 'warn'

type Capability = {
  id: string
  kind: string
  level: string
  sourceRecord: string
  appliesWhen: string[]
  actions?: string[]
  preferredActions?: string[]
  discouragedActions?: string[]
  entrypoint?: string
  rulebookRecord?: string
  requiresReasonForBypass?: boolean
  description: string
  owner: string
  tags?: string[]
  [key: string]: unknown
}

type Registry = {
  version: number
  capabilities: Capability[]
}

type RuleDigest = {
  appliesWhen: string[]
  prefer: string[]
  avoid: string[]
  requires: string[]
  bypass: string[]
  recordCompletion: string[]
}

type RuleEntry = {
  path: string
  title: string
  status: string
  layer: string
  scope: string
  owner: string
  level: string
  relatedCapability?: string
  relatedRecords: string[]
  digest: RuleDigest
  sections: string[]
  text: string
}

type RuleIssue = {
  severity: Severity
  path?: string
  id?: string
  message: string
}

type RuleMatch = {
  rule: RuleEntry
  capability?: Capability
  matchType: 'rule-intent' | 'capability-intent' | 'preferred-action' | 'discouraged-action' | 'action' | 'entrypoint'
  matchedValue: string
}

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Usage: lazy rules <command> [options]

Commands:
  list [--format=json|md]
  resolve --intent <intent> [--format=json|md]
  resolve --action <command-or-action> [--format=json|md]
  audit [--format=json|md] [--strict]

Project operating rules live in .lazy-harness/rules/** and may link to
.lazy-harness/ssot/capabilities.json for preferred/discouraged actions.
`)
  process.exit(exitCode)
}

function value(argv: string[], index: number, flag: string): string {
  const v = argv[index + 1]
  if (!v || v.startsWith('--')) {
    console.error(`Missing value for ${flag}`)
    process.exit(2)
  }
  return v
}

function parseOptions(argv: string[]): Record<string, string | boolean> {
  const opts: Record<string, string | boolean> = {}
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '-h' || a === '--help') usage(0)
    if (a.startsWith('--') && a.includes('=')) {
      const [k, ...rest] = a.slice(2).split('=')
      opts[k] = rest.join('=')
    } else if (a.startsWith('--')) {
      const k = a.slice(2)
      if (['format', 'intent', 'action', 'target'].includes(k)) opts[k] = value(argv, i++, a)
      else opts[k] = true
    } else {
      console.error(`Unknown argument: ${a}`)
      usage(2)
    }
  }
  return opts
}

function fmt(opts: Record<string, string | boolean>): Format {
  const format = String(opts.format || 'md')
  if (format !== 'md' && format !== 'json') {
    console.error(`Unsupported format: ${format}`)
    process.exit(2)
  }
  return format
}

function hostRoot(opts: Record<string, string | boolean>): string {
  const explicit = typeof opts.target === 'string' ? opts.target : process.env.LAZY_HOST_ROOT
  return resolve(explicit || process.cwd())
}

function printJson(data: unknown): void {
  console.log(JSON.stringify(data, null, 2))
}

function walkMarkdown(dir: string): string[] {
  if (!existsSync(dir)) return []
  const out: string[] = []
  for (const item of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, item.name)
    if (item.isDirectory()) out.push(...walkMarkdown(p))
    else if (item.isFile() && item.name.endsWith('.md')) out.push(p)
  }
  return out.sort()
}

function rel(root: string, path: string): string {
  return relative(root, path).split('\\').join('/')
}

function parseMetadata(text: string): Record<string, string> {
  const metadata: Record<string, string> = {}
  for (const line of text.split('\n')) {
    if (line.startsWith('## ')) break
    const m = line.match(/^([A-Za-z][A-Za-z -]*):\s*(.+?)\s*$/)
    if (!m) continue
    metadata[m[1].trim().toLowerCase().replace(/\s+/g, '-')] = m[2].trim()
  }
  return metadata
}

function parseSections(text: string): Map<string, string> {
  const sections = new Map<string, string>()
  const matches = [...text.matchAll(/^##\s+(.+)$/gm)]
  for (let i = 0; i < matches.length; i++) {
    const title = matches[i][1].trim()
    const start = (matches[i].index || 0) + matches[i][0].length
    const end = i + 1 < matches.length ? matches[i + 1].index || text.length : text.length
    sections.set(title, text.slice(start, end).trim())
  }
  return sections
}

function parseNestedList(section: string, heading: string): string[] {
  const lines = section.split('\n')
  const values: string[] = []
  let active = false
  for (const line of lines) {
    const top = line.match(/^-\s+(.+?):\s*$/)
    if (top) {
      active = top[1].trim().toLowerCase() === heading.toLowerCase()
      continue
    }
    if (active) {
      const nested = line.match(/^\s{2,}-\s+(.+?)\s*$/)
      if (nested) values.push(nested[1].trim())
      else if (line.startsWith('- ')) active = false
    }
  }
  return values
}

function parseRelatedRecords(text: string): string[] {
  const lines = text.split('\n')
  const records: string[] = []
  let active = false
  for (const line of lines) {
    if (/^Related records:\s*$/i.test(line.trim())) {
      active = true
      continue
    }
    if (line.startsWith('## ')) active = false
    if (active) {
      const item = line.match(/^-\s+`?([^`\s].*?)`?\s*$/)
      if (item) records.push(item[1].trim())
      else if (/^[A-Za-z][A-Za-z -]*:\s+/.test(line)) active = false
    }
  }
  return records
}

function loadRulebook(root: string): RuleEntry[] {
  const dir = join(root, '.lazy-harness', 'rules')
  return walkMarkdown(dir).map((path) => {
    const text = readFileSync(path, 'utf8')
    const metadata = parseMetadata(text)
    const sections = parseSections(text)
    const ruleDigest = sections.get('Rule digest') || ''
    const titleMatch = text.match(/^#\s+(.+)$/m)
    const digest: RuleDigest = {
      appliesWhen: parseNestedList(ruleDigest, 'Applies when'),
      prefer: parseNestedList(ruleDigest, 'Prefer'),
      avoid: parseNestedList(ruleDigest, 'Avoid'),
      requires: parseNestedList(ruleDigest, 'Requires'),
      bypass: parseNestedList(ruleDigest, 'Bypass'),
      recordCompletion: parseNestedList(ruleDigest, 'Record completion'),
    }
    return {
      path: rel(root, path),
      title: titleMatch ? titleMatch[1].trim() : rel(root, path),
      status: metadata.status || '',
      layer: metadata.layer || '',
      scope: metadata.scope || '',
      owner: metadata.owner || '',
      level: metadata.level || '',
      relatedCapability: metadata['related-capability'],
      relatedRecords: parseRelatedRecords(text),
      digest,
      sections: [...sections.keys()],
      text,
    }
  })
}

function loadRegistry(root: string): Registry {
  const path = join(root, '.lazy-harness', 'ssot', 'capabilities.json')
  if (!existsSync(path)) return { version: 1, capabilities: [] }
  const parsed = JSON.parse(readFileSync(path, 'utf8'))
  return { version: Number(parsed.version || 1), capabilities: Array.isArray(parsed.capabilities) ? parsed.capabilities : [] }
}

function capabilityForRule(rule: RuleEntry, caps: Capability[]): Capability | undefined {
  return caps.find((cap) => cap.id === rule.relatedCapability || cap.rulebookRecord === rule.path || cap.sourceRecord === rule.path)
}

function levelRank(level: string): number {
  const i = LEVEL_ORDER.indexOf(level)
  return i === -1 ? LEVEL_ORDER.length : i
}

function actionMatches(needle: string, action: string): boolean {
  if (needle === action) return true
  return action.includes(needle)
}

function actionLabels(cap: Capability): { type: RuleMatch['matchType']; value: string }[] {
  const labels: { type: RuleMatch['matchType']; value: string }[] = []
  for (const value of Array.isArray(cap.discouragedActions) ? cap.discouragedActions : []) labels.push({ type: 'discouraged-action', value: String(value) })
  for (const value of Array.isArray(cap.preferredActions) ? cap.preferredActions : []) labels.push({ type: 'preferred-action', value: String(value) })
  for (const value of Array.isArray(cap.actions) ? cap.actions : []) labels.push({ type: 'action', value: String(value) })
  if (typeof cap.entrypoint === 'string' && cap.entrypoint) labels.push({ type: 'entrypoint', value: cap.entrypoint })
  return labels
}

function resolveRules(rules: RuleEntry[], caps: Capability[], intent?: string, action?: string): RuleMatch[] {
  const matches: RuleMatch[] = []
  const seen = new Set<string>()
  for (const rule of rules) {
    const cap = capabilityForRule(rule, caps)
    if (intent && rule.digest.appliesWhen.includes(intent)) {
      const key = `${rule.path}:rule-intent:${intent}`
      if (!seen.has(key)) matches.push({ rule, capability: cap, matchType: 'rule-intent', matchedValue: intent }), seen.add(key)
    }
    if (cap && intent && Array.isArray(cap.appliesWhen) && cap.appliesWhen.includes(intent)) {
      const key = `${rule.path}:capability-intent:${intent}`
      if (!seen.has(key)) matches.push({ rule, capability: cap, matchType: 'capability-intent', matchedValue: intent }), seen.add(key)
    }
    if (cap && action) {
      for (const label of actionLabels(cap)) {
        if (actionMatches(label.value, action)) {
          const key = `${rule.path}:${label.type}:${label.value}`
          if (!seen.has(key)) matches.push({ rule, capability: cap, matchType: label.type, matchedValue: label.value }), seen.add(key)
        }
      }
    }
  }
  return matches.sort((a, b) => levelRank(a.capability?.level || a.rule.level) - levelRank(b.capability?.level || b.rule.level) || a.rule.path.localeCompare(b.rule.path))
}

function auditRules(root: string, rules: RuleEntry[], registry: Registry, strict: boolean): RuleIssue[] {
  const issues: RuleIssue[] = []
  const caps = registry.capabilities
  const capIds = new Set(caps.map((cap) => cap.id))
  const rulePaths = new Set(rules.map((rule) => rule.path))

  for (const rule of rules) {
    if (!STATUSES.has(rule.status)) issues.push({ severity: 'error', path: rule.path, message: `invalid or missing Status: ${rule.status || '(missing)'}` })
    if (rule.layer !== 'Rulebook') issues.push({ severity: 'error', path: rule.path, message: `Layer must be Rulebook, got ${rule.layer || '(missing)'}` })
    if (!SCOPES.has(rule.scope)) issues.push({ severity: 'error', path: rule.path, message: `invalid or missing Scope: ${rule.scope || '(missing)'}` })
    if (!LEVELS.has(rule.level)) issues.push({ severity: 'error', path: rule.path, message: `invalid or missing Level: ${rule.level || '(missing)'}` })
    if (!rule.sections.includes('Rule digest')) issues.push({ severity: 'error', path: rule.path, message: 'missing ## Rule digest' })
    if (rule.status === 'active' && ['default', 'warn', 'block'].includes(rule.level) && !rule.relatedCapability) {
      issues.push({ severity: 'error', path: rule.path, message: `${rule.level} active rule requires Related capability` })
    }
    if (rule.relatedCapability && !capIds.has(rule.relatedCapability)) {
      issues.push({ severity: 'error', path: rule.path, id: rule.relatedCapability, message: 'Related capability not found in capabilities.json' })
    }
    if (strict && rule.status === 'active') {
      for (const required of ['Operating rule', 'Capability binding', 'Implementation map']) {
        if (!rule.sections.includes(required)) issues.push({ severity: 'error', path: rule.path, message: `missing ## ${required}` })
      }
    }
    const cap = capabilityForRule(rule, caps)
    if (cap) {
      const discouraged = Array.isArray(cap.discouragedActions) ? cap.discouragedActions : []
      if (strict && rule.digest.avoid.length > 0 && discouraged.length === 0) {
        issues.push({ severity: 'error', path: rule.path, id: cap.id, message: 'rule has Avoid entries but linked capability lacks discouragedActions' })
      }
      if (strict && ['warn', 'block'].includes(cap.level) && rule.digest.bypass.length === 0) {
        issues.push({ severity: 'error', path: rule.path, id: cap.id, message: `${cap.level} rule/capability requires Bypass entry` })
      }
    }
  }

  for (const cap of caps) {
    const source = typeof cap.sourceRecord === 'string' ? cap.sourceRecord : ''
    const rulebook = typeof cap.rulebookRecord === 'string' ? cap.rulebookRecord : ''
    if (rulebook) {
      if (!rulePaths.has(rulebook)) issues.push({ severity: 'error', id: cap.id, message: `missing rulebookRecord: ${rulebook}` })
    }
    if (source.startsWith('.lazy-harness/rules/') && !rulePaths.has(source)) {
      issues.push({ severity: 'error', id: cap.id, message: `missing sourceRecord rulebook entry: ${source}` })
    }
    const preferred = Array.isArray(cap.preferredActions) ? cap.preferredActions : []
    const discouraged = Array.isArray(cap.discouragedActions) ? cap.discouragedActions : []
    if (strict && discouraged.length > 0 && preferred.length === 0) {
      issues.push({ severity: 'error', id: cap.id, message: 'discouragedActions require preferredActions guidance' })
    }
  }

  return issues
}

function printList(rules: RuleEntry[], format: Format): void {
  if (format === 'json') return printJson({ rules })
  console.log('# Project operating rules')
  if (rules.length === 0) {
    console.log('\nNo rulebook entries found.')
    return
  }
  for (const rule of rules) {
    console.log(`\n## ${rule.title}`)
    console.log(`- path: ${rule.path}`)
    console.log(`- status: ${rule.status}`)
    console.log(`- level: ${rule.level}`)
    console.log(`- scope: ${rule.scope}`)
    if (rule.relatedCapability) console.log(`- relatedCapability: ${rule.relatedCapability}`)
  }
}

function printResolve(matches: RuleMatch[], intent: string | undefined, action: string | undefined, format: Format): void {
  if (format === 'json') return printJson({ intent, action, matches })
  console.log('# Project operating rule resolution')
  if (intent) console.log(`- intent: ${intent}`)
  if (action) console.log(`- action: ${action}`)
  if (matches.length === 0) {
    console.log('\nNo matching operating rules.')
    return
  }
  for (const match of matches) {
    const cap = match.capability
    console.log(`\n## ${match.rule.title} (${cap?.level || match.rule.level})`)
    console.log(`- path: ${match.rule.path}`)
    console.log(`- match: ${match.matchType} -> ${match.matchedValue}`)
    if (cap?.preferredActions?.length) console.log(`- prefer: ${cap.preferredActions.join(', ')}`)
    if (cap?.discouragedActions?.length) console.log(`- avoid: ${cap.discouragedActions.join(', ')}`)
    if (cap?.entrypoint) console.log(`- use: ${cap.entrypoint}`)
    if (cap?.id) console.log(`- capability: ${cap.id}`)
  }
}

function printAudit(issues: RuleIssue[], rules: RuleEntry[], format: Format): void {
  const ok = !issues.some((issue) => issue.severity === 'error')
  if (format === 'json') return printJson({ ok, count: rules.length, issues })
  console.log('# Project operating rulebook audit')
  console.log(`- ok: ${ok ? 'yes' : 'no'}`)
  console.log(`- rules: ${rules.length}`)
  console.log(`- issues: ${issues.length}`)
  for (const issue of issues) console.log(`  - [${issue.severity}]${issue.path ? ` ${issue.path}:` : ''}${issue.id ? ` ${issue.id}:` : ''} ${issue.message}`)
}

function main(): void {
  const [cmd, ...rest] = process.argv.slice(2)
  if (!cmd || cmd === '-h' || cmd === '--help') usage(cmd ? 0 : 2)
  if (!['list', 'resolve', 'audit'].includes(cmd)) {
    console.error(`Unknown rules command: ${cmd}`)
    usage(2)
  }
  const opts = parseOptions(rest)
  const root = hostRoot(opts)
  const rules = loadRulebook(root)
  const registry = loadRegistry(root)

  if (cmd === 'list') {
    printList(rules, fmt(opts))
    return
  }
  if (cmd === 'resolve') {
    const intent = typeof opts.intent === 'string' ? opts.intent : undefined
    const action = typeof opts.action === 'string' ? opts.action : undefined
    if (!intent && !action) {
      console.error('rules resolve requires --intent and/or --action')
      process.exit(2)
    }
    printResolve(resolveRules(rules, registry.capabilities, intent, action), intent, action, fmt(opts))
    return
  }
  if (cmd === 'audit') {
    const strict = opts.strict === true
    const issues = auditRules(root, rules, registry, strict)
    printAudit(issues, rules, fmt(opts))
    if (issues.some((issue) => issue.severity === 'error')) process.exit(1)
    return
  }
}

main()
