#!/usr/bin/env bun
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'

const KINDS = new Set(['script', 'skill', 'prompt', 'hook', 'command', 'tool-adapter', 'validation', 'checklist', 'audit'])
const LEVELS = new Set(['discover', 'recommend', 'default', 'warn', 'block'])
const LEVEL_ORDER = ['block', 'warn', 'default', 'recommend', 'discover']
const REQUIRED = ['id', 'kind', 'level', 'sourceRecord', 'appliesWhen', 'description', 'owner']

type Format = 'json' | 'md'

type Capability = {
  id: string
  kind: string
  level: string
  sourceRecord: string
  appliesWhen: string[]
  actions?: string[]
  entrypoint?: string
  description: string
  owner: string
  tags?: string[]
  [key: string]: unknown
}

type Registry = {
  version: number
  capabilities: Capability[]
}

type AuditIssue = {
  severity: 'error' | 'warn'
  id?: string
  message: string
}

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Usage: lazy capability <command> [options]

Commands:
  add --id <id> --kind <kind> --level <level> --source-record <path> \
      --applies-when <intent[,intent]> --description <text> --owner <owner> [options]
  list [--format=json|md] [--kind=K] [--level=L]
  resolve --intent <intent> [--action <action>] [--format=json|md]
  resolve --action <action> [--format=json|md]
  audit [--format=json|md]

Phase 2 remains non-blocking: add/list/resolve/audit only.

Add options:
  --action <action[,action]>      Action labels used by resolve
  --entrypoint <command-or-path>  Script/command/hook entrypoint
  --tag <tag[,tag]>              Capability tag(s)
  --fallback <text>              Bypass/fallback note
  --allow-missing-source-record   Allow draft capability with missing source record
  --dry-run                       Print the updated registry without writing
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
      if (['format', 'id', 'kind', 'level', 'intent', 'action', 'target', 'source-record', 'applies-when', 'entrypoint', 'description', 'owner', 'tag', 'fallback', 'skill-name', 'template-path', 'tool', 'adapter', 'checklist-path', 'audit-command'].includes(k)) opts[k] = value(argv, i++, a)
      else opts[k] = true
    } else {
      console.error(`Unknown argument: ${a}`)
      usage(2)
    }
  }
  return opts
}

function hostRoot(opts: Record<string, string | boolean>): string {
  const explicit = typeof opts.target === 'string' ? opts.target : process.env.LAZY_HOST_ROOT
  return resolve(explicit || process.cwd())
}

function registryPath(root: string): string {
  return join(root, '.lazy-harness', 'ssot', 'capabilities.json')
}

function loadRegistry(root: string): Registry {
  const path = registryPath(root)
  if (!existsSync(path)) return { version: 1, capabilities: [] }
  const parsed = JSON.parse(readFileSync(path, 'utf8'))
  if (!parsed || typeof parsed !== 'object') throw new Error(`Capability registry is not an object: ${path}`)
  const caps = Array.isArray(parsed.capabilities) ? parsed.capabilities : []
  return { version: Number(parsed.version || 1), capabilities: caps as Capability[] }
}

function normalizeRegistry(registry: Registry): Registry {
  const normalized: Registry = {
    version: registry.version || 1,
    capabilities: [...registry.capabilities].sort((a, b) => a.id.localeCompare(b.id)),
  }
  return normalized
}

function saveRegistry(root: string, registry: Registry, dryRun: boolean): Registry {
  const path = registryPath(root)
  const normalized = normalizeRegistry(registry)
  const text = JSON.stringify(normalized, null, 2) + '\n'
  if (dryRun) return normalized
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, text)
  return normalized
}

function splitList(value: string | boolean | undefined): string[] {
  if (typeof value !== 'string') return []
  return value
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
}

function requireString(opts: Record<string, string | boolean>, key: string): string {
  const value = opts[key]
  if (typeof value !== 'string' || value.trim() === '') {
    console.error(`capability add requires --${key}`)
    process.exit(2)
  }
  return value.trim()
}

function validateCapabilityShape(root: string, cap: Capability, allowMissingSourceRecord = false): AuditIssue[] {
  const issues = auditRegistry(root, { version: 1, capabilities: [cap] })
  if (allowMissingSourceRecord) {
    return issues.filter((issue) => !issue.message.startsWith('missing sourceRecord:'))
  }
  return issues
}

function capabilityFromOptions(opts: Record<string, string | boolean>): Capability {
  const cap: Capability = {
    id: requireString(opts, 'id'),
    kind: requireString(opts, 'kind'),
    level: requireString(opts, 'level'),
    sourceRecord: requireString(opts, 'source-record'),
    appliesWhen: splitList(opts['applies-when']),
    description: requireString(opts, 'description'),
    owner: requireString(opts, 'owner'),
  }
  const actions = splitList(opts.action)
  const tags = splitList(opts.tag)
  if (actions.length) cap.actions = actions
  if (tags.length) cap.tags = tags
  const fieldMap: Record<string, keyof Capability> = {
    entrypoint: 'entrypoint',
    fallback: 'fallback',
    'skill-name': 'skillName',
    'template-path': 'templatePath',
    tool: 'tool',
    adapter: 'adapter',
    'checklist-path': 'checklistPath',
    'audit-command': 'auditCommand',
  }
  for (const [optKey, capKey] of Object.entries(fieldMap)) {
    const value = opts[optKey]
    if (typeof value === 'string' && value.trim()) cap[capKey] = value.trim()
  }
  return cap
}

function upsertCapability(registry: Registry, cap: Capability): 'created' | 'updated' | 'unchanged' {
  const index = registry.capabilities.findIndex((existing) => existing.id === cap.id)
  if (index === -1) {
    registry.capabilities.push(cap)
    return 'created'
  }
  const existing = registry.capabilities[index]
  if (JSON.stringify(existing) === JSON.stringify(cap)) return 'unchanged'
  registry.capabilities[index] = cap
  return 'updated'
}

function upsertGraphEntry(root: string, cap: Capability, status: string, dryRun: boolean): void {
  if (dryRun) return
  const path = join(root, '.lazy-harness', 'knowledge', 'graph.jsonl')
  const id = `capability_${cap.id.replace(/[^a-zA-Z0-9._-]/g, '_')}`
  const entry = {
    id,
    kind: 'capability',
    layer: 'SSOT',
    path: '.lazy-harness/ssot/capabilities.json',
    relation: status === 'created' ? 'registers' : 'updates',
    target: cap.id,
    source: `${cap.kind}/${cap.level}: ${cap.description}`,
    sourceRecord: cap.sourceRecord,
    appliesWhen: cap.appliesWhen,
    actions: cap.actions || [],
    updatedAt: new Date().toISOString(),
  }
  mkdirSync(dirname(path), { recursive: true })
  let lines = existsSync(path) ? readFileSync(path, 'utf8').split('\n').filter((line) => line.trim()) : []
  lines = lines.filter((line) => {
    try {
      return JSON.parse(line).id !== id
    } catch {
      return true
    }
  })
  lines.push(JSON.stringify(entry))
  writeFileSync(path, lines.join('\n') + '\n')
}

function fmt(opts: Record<string, string | boolean>): Format {
  const format = String(opts.format || 'md')
  if (format !== 'md' && format !== 'json') {
    console.error(`Unsupported format: ${format}`)
    process.exit(2)
  }
  return format
}

function levelRank(level: string): number {
  const i = LEVEL_ORDER.indexOf(level)
  return i === -1 ? LEVEL_ORDER.length : i
}

function actionMatches(needle: string, action: string): boolean {
  if (needle === action) return true
  if (action.includes(needle)) return true
  return false
}

function resolveCapabilities(caps: Capability[], intent?: string, action?: string): Capability[] {
  const matched = caps.filter((cap) => {
    const applies = Array.isArray(cap.appliesWhen) ? cap.appliesWhen : []
    const actions = Array.isArray(cap.actions) ? cap.actions : []
    return Boolean(
      (intent && applies.includes(intent)) ||
      (action && actions.some((a) => actionMatches(String(a), action)))
    )
  })
  return matched
    .map((cap, index) => ({ cap, index }))
    .sort((a, b) => levelRank(a.cap.level) - levelRank(b.cap.level) || a.index - b.index)
    .map((x) => x.cap)
}

function auditRegistry(root: string, registry: Registry): AuditIssue[] {
  const issues: AuditIssue[] = []
  const ids = new Set<string>()
  if (!Array.isArray(registry.capabilities)) {
    issues.push({ severity: 'error', message: 'capabilities must be an array' })
    return issues
  }
  registry.capabilities.forEach((cap: any, index) => {
    const id = typeof cap?.id === 'string' ? cap.id : `#${index}`
    for (const key of REQUIRED) {
      if (cap?.[key] === undefined || cap?.[key] === null || cap?.[key] === '') {
        issues.push({ severity: 'error', id, message: `missing required field: ${key}` })
      }
    }
    if (typeof cap?.id === 'string') {
      if (ids.has(cap.id)) issues.push({ severity: 'error', id: cap.id, message: 'duplicate id' })
      ids.add(cap.id)
    }
    if (cap?.kind && !KINDS.has(String(cap.kind))) issues.push({ severity: 'error', id, message: `unsupported kind: ${cap.kind}` })
    if (cap?.level && !LEVELS.has(String(cap.level))) issues.push({ severity: 'error', id, message: `unsupported level: ${cap.level}` })
    if (!Array.isArray(cap?.appliesWhen) || cap.appliesWhen.length === 0) issues.push({ severity: 'error', id, message: 'appliesWhen must be a non-empty array' })
    if (cap?.actions !== undefined && !Array.isArray(cap.actions)) issues.push({ severity: 'error', id, message: 'actions must be an array when present' })
    if (typeof cap?.sourceRecord === 'string') {
      const p = resolve(root, cap.sourceRecord)
      if (!existsSync(p)) issues.push({ severity: 'error', id, message: `missing sourceRecord: ${cap.sourceRecord}` })
    }
    if ((cap?.level === 'warn' || cap?.level === 'block') && !cap?.entrypoint && !Array.isArray(cap?.actions)) {
      issues.push({ severity: 'warn', id, message: `${cap.level} capability has no entrypoint/actions enforcement surface` })
    }
  })
  return issues
}

function printJson(data: unknown): void {
  console.log(JSON.stringify(data, null, 2))
}

function printCapabilityList(caps: Capability[], format: Format): void {
  if (format === 'json') return printJson({ capabilities: caps })
  if (caps.length === 0) {
    console.log('No capabilities registered.')
    return
  }
  console.log('# Capabilities')
  for (const cap of caps) {
    console.log(`\n## ${cap.id}`)
    console.log(`- kind: ${cap.kind}`)
    console.log(`- level: ${cap.level}`)
    console.log(`- appliesWhen: ${cap.appliesWhen.join(', ')}`)
    if (cap.actions?.length) console.log(`- actions: ${cap.actions.join(', ')}`)
    if (cap.entrypoint) console.log(`- entrypoint: ${cap.entrypoint}`)
    console.log(`- sourceRecord: ${cap.sourceRecord}`)
    console.log(`- owner: ${cap.owner}`)
    console.log(`- description: ${cap.description}`)
  }
}

function printResolve(caps: Capability[], intent: string | undefined, action: string | undefined, format: Format): void {
  if (format === 'json') return printJson({ intent, action, matches: caps })
  console.log(`# Capability resolution`)
  if (intent) console.log(`- intent: ${intent}`)
  if (action) console.log(`- action: ${action}`)
  if (caps.length === 0) {
    console.log('\nNo matching capabilities.')
    return
  }
  for (const cap of caps) {
    console.log(`\n## ${cap.id} (${cap.level})`)
    console.log(`- kind: ${cap.kind}`)
    if (cap.entrypoint) console.log(`- use: ${cap.entrypoint}`)
    console.log(`- sourceRecord: ${cap.sourceRecord}`)
    console.log(`- description: ${cap.description}`)
  }
}

function printAudit(issues: AuditIssue[], registry: Registry, format: Format): void {
  const ok = issues.filter((i) => i.severity === 'error').length === 0
  if (format === 'json') return printJson({ ok, count: registry.capabilities.length, issues })
  console.log('# Capability audit')
  console.log(`- ok: ${ok ? 'yes' : 'no'}`)
  console.log(`- capabilities: ${registry.capabilities.length}`)
  console.log(`- issues: ${issues.length}`)
  for (const issue of issues) {
    console.log(`  - [${issue.severity}]${issue.id ? ` ${issue.id}:` : ''} ${issue.message}`)
  }
}

function addCapability(root: string, registry: Registry, opts: Record<string, string | boolean>, format: Format): void {
  const dryRun = opts['dry-run'] === true
  const allowMissingSourceRecord = opts['allow-missing-source-record'] === true
  const cap = capabilityFromOptions(opts)
  const issues = validateCapabilityShape(root, cap, allowMissingSourceRecord)
  const errors = issues.filter((issue) => issue.severity === 'error')
  if (errors.length) {
    if (format === 'json') printJson({ ok: false, issues })
    else {
      console.error('Capability add failed:')
      for (const issue of errors) console.error(`- ${issue.message}`)
    }
    process.exit(1)
  }
  const status = upsertCapability(registry, cap)
  const normalized = saveRegistry(root, registry, dryRun)
  upsertGraphEntry(root, cap, status, dryRun)
  if (format === 'json') {
    printJson({ ok: true, status: dryRun ? 'dry-run' : status, capability: cap, registry: dryRun ? normalized : undefined, issues })
  } else if (dryRun) {
    console.log(JSON.stringify(normalized, null, 2))
  } else {
    console.log(`✓ capability ${status}: ${cap.id}`)
  }
}

function main(): void {
  const [cmd, ...rest] = process.argv.slice(2)
  if (!cmd || cmd === '-h' || cmd === '--help') usage(cmd ? 0 : 2)
  if (!['add', 'list', 'resolve', 'audit'].includes(cmd)) {
    console.error(`Unknown capability command: ${cmd}`)
    usage(2)
  }
  const opts = parseOptions(rest)
  const root = hostRoot(opts)
  let registry: Registry
  try {
    registry = loadRegistry(root)
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    if (fmt(opts) === 'json') printJson({ ok: false, issues: [{ severity: 'error', message }] })
    else console.error(`Capability registry error: ${message}`)
    process.exit(1)
  }
  if (cmd === 'list') {
    let caps = registry.capabilities
    if (typeof opts.kind === 'string') caps = caps.filter((c) => c.kind === opts.kind)
    if (typeof opts.level === 'string') caps = caps.filter((c) => c.level === opts.level)
    printCapabilityList(caps, fmt(opts))
    return
  }
  if (cmd === 'add') {
    addCapability(root, registry, opts, fmt(opts))
    return
  }
  if (cmd === 'resolve') {
    const intent = typeof opts.intent === 'string' ? opts.intent : undefined
    const action = typeof opts.action === 'string' ? opts.action : undefined
    if (!intent && !action) {
      console.error('capability resolve requires --intent and/or --action')
      process.exit(2)
    }
    printResolve(resolveCapabilities(registry.capabilities, intent, action), intent, action, fmt(opts))
    return
  }
  if (cmd === 'audit') {
    const issues = auditRegistry(root, registry)
    printAudit(issues, registry, fmt(opts))
    if (issues.some((i) => i.severity === 'error')) process.exit(1)
    return
  }
}

main()
