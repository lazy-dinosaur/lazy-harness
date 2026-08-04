#!/usr/bin/env bun
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'

const SCOPES = new Set(['framework-global', 'host-project', 'team-policy', 'adapter'])
const STAGES = new Set(['turn', 'edit', 'commit', 'push', 'release', 'high-risk-mutation'])
const LEVELS = new Set(['discover', 'recommend', 'default', 'warn', 'block'])
const LEVEL_ORDER = ['block', 'warn', 'default', 'recommend', 'discover']
const ADVISORY_LEVEL_ORDER = ['default', 'recommend', 'discover']
const ADVISORY_LEVELS = new Set(ADVISORY_LEVEL_ORDER)
const WARN_LEVEL_ORDER = ['warn', 'default', 'recommend', 'discover']
const WARN_LEVELS = new Set(WARN_LEVEL_ORDER)
const EVIDENCE_KINDS = new Set(['record', 'validation-output', 'user-confirmation', 'update-event'])
const EVENT_TYPES = new Set(['policy-candidate', 'policy-promotion', 'policy-demotion'])
const FORBIDDEN_KEYS = new Set(['confidence', 'intent', 'risk', 'requiredRead', 'optionalRead', 'gate', 'nextAction', 'candidateMeaning'])

type Format = 'json' | 'md'
type Severity = 'error' | 'warn'

type PolicyEvidence = {
  kind: string
  path?: string
  summary: string
}

type Policy = {
  id: string
  title: string
  scope: string
  stage: string
  level: string
  appliesTo: string[]
  sourceRecord: string
  capabilityIds?: string[]
  evidence: PolicyEvidence[]
  promotion: {
    requiresConfirmation: boolean
    allowedTargetLevels: string[]
  }
  rollback: {
    criteria: string[]
    demotionTarget: string
  }
  updateLoop: {
    eventType: string
    canonicalByPacketAlone: boolean
  }
  explain?: {
    summary?: string
    nonCanonicalViews?: string[]
  }
  [key: string]: unknown
}

type PolicyRegistry = {
  version: number
  policies: Policy[]
}

type Capability = {
  id: string
  sourceRecord?: string
  rulebookRecord?: string
  policyIds?: string[]
  [key: string]: unknown
}

type CapabilityRegistry = {
  version: number
  capabilities: Capability[]
}

type RulebookEntry = {
  path: string
  title: string
  status: string
  level: string
  relatedCapability?: string
}

type ReadinessFinding = {
  severity: 'blocker' | 'info'
  path?: string
  capabilityId?: string
  policyId?: string
  message: string
}

type HardStopPromotion = {
  recordPath: string
  startLine: number
  fields: Record<string, string>
  problems: string[]
}

type AuditIssue = {
  severity: Severity
  id?: string
  message: string
}

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Usage: lazy policy <command> [options]

Commands:
  list [--format=json|md] [--stage=STAGE] [--level=LEVEL]
  audit [--format=json|md]
  explain --id <policy-id> [--format=json|md]
  resolve [--format=json|md] [--stage=STAGE] [--applies-to=A,B] [--max-level=default|recommend|discover|warn] [--runtime=advisory|warn]
  render-rulebook [--format=json|md] [--write] [--output=.lazy-harness/generated/policy-rulebook.md]
  upsert --from-json <policy.json> [--confirm] [--format=json|md]
  retire-readiness [--format=json|md] [--strict]
  block-readiness [--format=json|md] [--strict]

Policy Machinery Option B: .lazy-harness/ssot/policies.json is canonical.
Resolve defaults to advisory-only. Warn runtime requires --runtime=warn and never blocks.
Block runtime requires block-readiness evidence first and is not installed by this CLI.
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
      if (['format', 'id', 'stage', 'level', 'target', 'applies-to', 'max-level', 'runtime', 'output', 'from-json'].includes(k)) opts[k] = value(argv, i++, a)
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

function registryPath(root: string): string {
  return join(root, '.lazy-harness', 'ssot', 'policies.json')
}

function loadRegistry(root: string): PolicyRegistry {
  const path = registryPath(root)
  if (!existsSync(path)) return { version: 1, policies: [] }
  const parsed = JSON.parse(readFileSync(path, 'utf8'))
  if (!parsed || typeof parsed !== 'object') throw new Error(`Policy registry is not an object: ${path}`)
  return { version: Number(parsed.version || 1), policies: Array.isArray(parsed.policies) ? parsed.policies as Policy[] : [] }
}

function writeRegistry(root: string, registry: PolicyRegistry): void {
  const path = registryPath(root)
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, `${JSON.stringify(registry, null, 2)}\n`, 'utf8')
}

function printJson(data: unknown): void {
  console.log(JSON.stringify(data, null, 2))
}

function rel(root: string, path: string): string {
  return relative(root, path).split('\\').join('/')
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

function loadRulebookEntries(root: string): RulebookEntry[] {
  const dir = join(root, '.lazy-harness', 'rules')
  return walkMarkdown(dir).map((path) => {
    const text = readFileSync(path, 'utf8')
    const metadata = parseMetadata(text)
    const titleMatch = text.match(/^#\s+(.+)$/m)
    return {
      path: rel(root, path),
      title: titleMatch ? titleMatch[1].trim() : rel(root, path),
      status: metadata.status || '',
      level: metadata.level || '',
      relatedCapability: metadata['related-capability'],
    }
  })
}

function loadCapabilityRegistry(root: string): CapabilityRegistry {
  const path = join(root, '.lazy-harness', 'ssot', 'capabilities.json')
  if (!existsSync(path)) return { version: 1, capabilities: [] }
  const parsed = JSON.parse(readFileSync(path, 'utf8'))
  return { version: Number(parsed.version || 1), capabilities: Array.isArray(parsed.capabilities) ? parsed.capabilities as Capability[] : [] }
}

function capabilityForRulebookEntry(rule: RulebookEntry, capabilities: Capability[]): Capability | undefined {
  return capabilities.find((cap) => cap.id === rule.relatedCapability || cap.rulebookRecord === rule.path || cap.sourceRecord === rule.path)
}

const HARD_STOP_REQUIRED_FIELDS = ['Status', 'Boundary', 'Scope', 'User confirmation', 'Evidence', 'Existing softer coverage', 'Fixture', 'Narrowness', 'Rollback']
const HARD_STOP_ACTIVE_STATUSES = new Set(['active', 'proposed'])
const HARD_STOP_ALLOWED_SCOPES = new Set(['framework-global', 'host-project', 'team-policy'])

function extractHardStopPromotions(text: string, recordPath: string, root: string): HardStopPromotion[] {
  const lines = text.split('\n')
  const sections: Array<{ startLine: number, lines: string[] }> = []
  let inFence = false
  let currentStart = -1
  let current: string[] = []
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    if (line.trim().startsWith('```')) inFence = !inFence
    if (!inFence && /^##\s+Hard-stop promotion\s*$/i.test(line.trim())) {
      if (currentStart !== -1) sections.push({ startLine: currentStart, lines: current })
      currentStart = i + 1
      current = []
      continue
    }
    if (currentStart !== -1) {
      if (!inFence && /^##\s+/.test(line.trim())) {
        sections.push({ startLine: currentStart, lines: current })
        currentStart = -1
        current = []
      } else {
        current.push(line)
      }
    }
  }
  if (currentStart !== -1) sections.push({ startLine: currentStart, lines: current })
  return sections.map((section) => {
    const fields: Record<string, string> = {}
    for (const line of section.lines) {
      const m = line.trim().match(/^-\s+([A-Za-z][A-Za-z\s]+):\s*(.*)$/)
      if (!m) continue
      fields[m[1].trim().replace(/\s+/g, ' ')] = m[2].trim()
    }
    return { recordPath, startLine: section.startLine, fields, problems: validateHardStopPromotion(root, fields) }
  })
}

function validateHardStopPromotion(root: string, fields: Record<string, string>): string[] {
  const problems: string[] = []
  const status = String(fields.Status || '').trim().toLowerCase()
  if (status && !new Set(['active', 'proposed', 'retired']).has(status)) problems.push(`invalid Status ${fields.Status}`)
  if (status === 'retired') return problems
  for (const field of HARD_STOP_REQUIRED_FIELDS) {
    const value = String(fields[field] || '').trim()
    if (!value || ['<todo>', 'TODO', 'todo', 'n/a', 'N/A'].includes(value)) problems.push(`missing ${field}`)
  }
  const scope = String(fields.Scope || '').trim()
  if (scope && !HARD_STOP_ALLOWED_SCOPES.has(scope)) problems.push(`invalid Scope ${scope}`)
  const fixture = String(fields.Fixture || '').trim().replace(/^`|`$/g, '')
  if (fixture) {
    if (!isRootRelativeLazyPath(fixture)) problems.push(`Fixture must be root-relative .lazy-harness path ${fixture}`)
    else if (!existsSync(join(root, fixture))) problems.push(`Fixture does not exist ${fixture}`)
  }
  return problems
}

function objectValue(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : undefined
}

function nonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0
}

function isRootRelativeLazyPath(path: unknown): path is string {
  return typeof path === 'string' && path.startsWith('.lazy-harness/') && !path.split('/').includes('..') && !path.startsWith('/')
}

function generatedOutputPath(root: string, opts: Record<string, string | boolean>): string {
  const requested = typeof opts.output === 'string' ? opts.output : '.lazy-harness/generated/policy-rulebook.md'
  if (requested.startsWith('/') || requested.split('/').includes('..') || !requested.startsWith('.lazy-harness/generated/')) {
    console.error('policy render-rulebook --output must be a root-relative .lazy-harness/generated/ path')
    process.exit(2)
  }
  return join(root, requested)
}

function walkForbidden(value: unknown, issues: AuditIssue[], id: string, path = '$'): void {
  if (Array.isArray(value)) {
    value.forEach((child, idx) => walkForbidden(child, issues, id, `${path}[${idx}]`))
    return
  }
  if (!value || typeof value !== 'object') return
  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
    if (FORBIDDEN_KEYS.has(key)) issues.push({ severity: 'error', id, message: `forbidden semantic-authority key at ${path}.${key}` })
    walkForbidden(child, issues, id, `${path}.${key}`)
  }
}

function auditPolicy(root: string, policy: Policy): AuditIssue[] {
  const issues: AuditIssue[] = []
  const id = typeof policy.id === 'string' ? policy.id : '<missing-id>'
  if (!/^[a-z][a-z0-9._-]{1,127}$/.test(String(policy.id || ''))) issues.push({ severity: 'error', id, message: 'invalid or missing id' })
  if (typeof policy.title !== 'string' || !policy.title.trim()) issues.push({ severity: 'error', id, message: 'missing title' })
  if (!SCOPES.has(policy.scope)) issues.push({ severity: 'error', id, message: `invalid scope: ${policy.scope}` })
  if (!STAGES.has(policy.stage)) issues.push({ severity: 'error', id, message: `invalid stage: ${policy.stage}` })
  if (!LEVELS.has(policy.level)) issues.push({ severity: 'error', id, message: `invalid level: ${policy.level}` })
  if (!Array.isArray(policy.appliesTo) || policy.appliesTo.length === 0) issues.push({ severity: 'error', id, message: 'appliesTo must be non-empty' })
  if (!isRootRelativeLazyPath(policy.sourceRecord)) issues.push({ severity: 'error', id, message: 'sourceRecord must be root-relative .lazy-harness path' })
  else if (!existsSync(join(root, policy.sourceRecord))) issues.push({ severity: 'error', id, message: `sourceRecord missing: ${policy.sourceRecord}` })

  if (!Array.isArray(policy.evidence) || policy.evidence.length === 0) issues.push({ severity: 'error', id, message: 'evidence must be non-empty' })
  else {
    for (const evidence of policy.evidence) {
      if (!EVIDENCE_KINDS.has(evidence.kind)) issues.push({ severity: 'error', id, message: `invalid evidence kind: ${evidence.kind}` })
      if (typeof evidence.summary !== 'string' || !evidence.summary.trim()) issues.push({ severity: 'error', id, message: 'evidence summary required' })
      if (evidence.path && (!isRootRelativeLazyPath(evidence.path) || !existsSync(join(root, evidence.path)))) issues.push({ severity: 'error', id, message: `evidence path invalid or missing: ${evidence.path}` })
    }
  }

  if (!policy.promotion || policy.promotion.requiresConfirmation !== true) issues.push({ severity: 'error', id, message: 'promotion.requiresConfirmation must be true' })
  if (!policy.rollback || !Array.isArray(policy.rollback.criteria) || policy.rollback.criteria.length === 0) issues.push({ severity: 'error', id, message: 'rollback.criteria must be non-empty' })
  if (!policy.updateLoop || !EVENT_TYPES.has(policy.updateLoop.eventType)) issues.push({ severity: 'error', id, message: 'updateLoop.eventType invalid' })
  if (!policy.updateLoop || policy.updateLoop.canonicalByPacketAlone !== false) issues.push({ severity: 'error', id, message: 'updateLoop.canonicalByPacketAlone must be false' })
  if ((policy.level === 'warn' || policy.level === 'block') && policy.promotion?.requiresConfirmation !== true) issues.push({ severity: 'error', id, message: 'warn/block policies require explicit confirmation' })
  walkForbidden(policy, issues, id)
  return issues
}

function auditRegistry(root: string, registry: PolicyRegistry): AuditIssue[] {
  const issues: AuditIssue[] = []
  const seen = new Set<string>()
  for (const policy of registry.policies) {
    if (seen.has(policy.id)) issues.push({ severity: 'error', id: policy.id, message: 'duplicate policy id' })
    seen.add(policy.id)
    issues.push(...auditPolicy(root, policy))
  }
  return issues
}

function sortedPolicies(policies: Policy[]): Policy[] {
  return [...policies].sort((a, b) => a.id.localeCompare(b.id))
}

function loadPolicyInput(pathValue: unknown): Policy {
  if (typeof pathValue !== 'string' || !pathValue) {
    console.error('policy upsert requires --from-json <policy.json>')
    process.exit(2)
  }
  const path = resolve(pathValue)
  const parsed = JSON.parse(readFileSync(path, 'utf8'))
  const policy = parsed && typeof parsed === 'object' && 'policy' in parsed ? (parsed as Record<string, unknown>).policy : parsed
  if (!policy || typeof policy !== 'object' || Array.isArray(policy)) {
    console.error('policy upsert --from-json must contain a policy object or { policy: object }')
    process.exit(2)
  }
  return policy as Policy
}

function upsertPolicy(root: string, opts: Record<string, string | boolean>, format: Format): void {
  const registry = loadRegistry(root)
  const policy = loadPolicyInput(opts['from-json'])
  const existingIndex = registry.policies.findIndex((item) => item.id === policy.id)
  const action = existingIndex === -1 ? 'insert' : 'replace'
  const policies = [...registry.policies]
  if (existingIndex === -1) policies.push(policy)
  else policies[existingIndex] = policy
  const nextRegistry: PolicyRegistry = {
    ...registry,
    version: registry.version || 1,
    policies: sortedPolicies(policies),
  }
  const issues = auditRegistry(root, nextRegistry)
  const ok = !issues.some((issue) => issue.severity === 'error')
  const confirmed = opts.confirm === true
  if (!ok) {
    const result = {
      schemaVersion: 'policy-upsert/v1',
      ok: false,
      action,
      wrote: false,
      confirmed,
      policyId: policy.id,
      issues,
    }
    if (format === 'json') printJson(result)
    else {
      console.log('# Policy upsert failed')
      console.log('')
      for (const issue of issues) console.log(`- ${issue.severity}${issue.id ? ` ${issue.id}` : ''}: ${issue.message}`)
    }
    process.exit(1)
  }
  if (confirmed) writeRegistry(root, nextRegistry)
  const result = {
    schemaVersion: 'policy-upsert/v1',
    ok: true,
    action,
    wrote: confirmed,
    dryRun: !confirmed,
    confirmRequiredToWrite: !confirmed,
    canonicalTarget: '.lazy-harness/ssot/policies.json',
    policyId: policy.id,
    policies: nextRegistry.policies.length,
  }
  if (format === 'json') return printJson(result)
  console.log('# Policy upsert')
  console.log('')
  console.log(`- ok: ${result.ok}`)
  console.log(`- action: ${action}`)
  console.log(`- policy: ${policy.id}`)
  console.log(`- wrote: ${confirmed}`)
  console.log(`- canonical target: ${result.canonicalTarget}`)
  if (!confirmed) console.log('- dry-run: pass `--confirm` to write')
}

function listPolicies(root: string, opts: Record<string, string | boolean>, format: Format): void {
  const registry = loadRegistry(root)
  const stage = typeof opts.stage === 'string' ? opts.stage : ''
  const level = typeof opts.level === 'string' ? opts.level : ''
  const policies = registry.policies
    .filter((p) => !stage || p.stage === stage)
    .filter((p) => !level || p.level === level)
    .sort((a, b) => LEVEL_ORDER.indexOf(a.level) - LEVEL_ORDER.indexOf(b.level) || a.id.localeCompare(b.id))
  if (format === 'json') return printJson({ schemaVersion: 'policy-registry/v1', ok: true, policies })
  console.log('# Policy registry')
  console.log('')
  if (!policies.length) {
    console.log('_No policies matched._')
    return
  }
  for (const policy of policies) {
    console.log(`- **${policy.id}** (${policy.level}, ${policy.stage}) — ${policy.title}`)
  }
}

function parseList(value: unknown): string[] {
  if (typeof value !== 'string') return []
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function advisoryRank(level: string): number {
  const idx = ADVISORY_LEVEL_ORDER.indexOf(level)
  return idx === -1 ? Number.POSITIVE_INFINITY : idx
}

function runtimeRank(level: string, runtime: 'advisory' | 'warn'): number {
  const order = runtime === 'warn' ? WARN_LEVEL_ORDER : ADVISORY_LEVEL_ORDER
  const idx = order.indexOf(level)
  return idx === -1 ? Number.POSITIVE_INFINITY : idx
}

function resolvePolicies(root: string, opts: Record<string, string | boolean>, format: Format): void {
  const registry = loadRegistry(root)
  const stage = typeof opts.stage === 'string' ? opts.stage : ''
  const appliesTo = parseList(opts['applies-to'])
  const runtime = (typeof opts.runtime === 'string' ? opts.runtime : 'advisory') as string
  if (runtime !== 'advisory' && runtime !== 'warn') {
    console.error('policy resolve --runtime must be one of: advisory, warn')
    process.exit(2)
  }
  const levelOrder = runtime === 'warn' ? WARN_LEVEL_ORDER : ADVISORY_LEVEL_ORDER
  const levelSet = runtime === 'warn' ? WARN_LEVELS : ADVISORY_LEVELS
  const maxLevel = typeof opts['max-level'] === 'string' ? opts['max-level'] : (runtime === 'warn' ? 'warn' : 'default')
  if (!levelSet.has(maxLevel)) {
    console.error(`policy resolve --max-level must be one of: ${levelOrder.join(', ')} for runtime=${runtime}`)
    process.exit(2)
  }
  const allowedLevels = new Set(levelOrder.slice(runtimeRank(maxLevel, runtime)))
  const skipped = {
    nonAdvisoryLevel: 0,
    stageMismatch: 0,
    appliesToMismatch: 0,
  }
  const matches = registry.policies
    .filter((policy) => {
      if (!levelSet.has(policy.level)) {
        skipped.nonAdvisoryLevel++
        return false
      }
      if (!allowedLevels.has(policy.level)) {
        skipped.nonAdvisoryLevel++
        return false
      }
      if (stage && policy.stage !== stage) {
        skipped.stageMismatch++
        return false
      }
      if (appliesTo.length && !appliesTo.some((item) => policy.appliesTo.includes(item))) {
        skipped.appliesToMismatch++
        return false
      }
      return true
    })
    .sort((a, b) => runtimeRank(a.level, runtime) - runtimeRank(b.level, runtime) || a.id.localeCompare(b.id))
    .map((policy) => ({
      id: policy.id,
      title: policy.title,
      stage: policy.stage,
      level: policy.level,
      appliesTo: policy.appliesTo,
      sourceRecord: policy.sourceRecord,
      capabilities: policy.capabilityIds || [],
      summary: policy.explain?.summary || policy.title,
      recommendedAction: runtime === 'warn' && policy.level === 'warn' ? 'emit-warning' : 'surface-guidance',
      enforcement: runtime === 'warn' && policy.level === 'warn' ? 'warn-only' : 'advisory-only',
    }))

  const result = {
    schemaVersion: 'policy-resolve/v1',
    ok: true,
    runtime,
    enforcement: runtime === 'warn' ? 'warn-only' : 'advisory-only',
    stage: stage || null,
    appliesTo,
    maxLevel,
    matches,
    skipped,
    policyBoundary: runtime === 'warn'
      ? 'Warn-only resolver; block runtime enforcement remains a future promoted slice.'
      : 'Advisory resolver only; warn/block runtime enforcement remains a future promoted slice.',
  }
  if (format === 'json') return printJson(result)
  console.log('# Policy resolve')
  console.log('')
  console.log(`- enforcement: ${result.enforcement}`)
  console.log(`- stage: ${result.stage || 'any'}`)
  console.log(`- appliesTo: ${appliesTo.length ? appliesTo.join(', ') : 'any'}`)
  console.log(`- maxLevel: ${maxLevel}`)
  console.log(`- boundary: ${result.policyBoundary}`)
  console.log('')
  if (!matches.length) {
    console.log('_No advisory policies matched._')
    return
  }
  console.log('## Matches')
  for (const match of matches) {
    console.log(`- **${match.id}** (${match.level}, ${match.stage}) — ${match.summary}`)
    if (match.capabilities.length) console.log(`  - capabilities: ${match.capabilities.join(', ')}`)
    console.log(`  - action: ${match.recommendedAction}`)
  }
}

function explainPolicy(policy: Policy, format: Format): void {
  const explanation = {
    schemaVersion: 'policy-explain/v1',
    id: policy.id,
    title: policy.title,
    canonicalSource: '.lazy-harness/ssot/policies.json',
    sourceRecord: policy.sourceRecord,
    summary: policy.explain?.summary || policy.title,
    scope: policy.scope,
    stage: policy.stage,
    level: policy.level,
    appliesTo: policy.appliesTo,
    capabilities: policy.capabilityIds || [],
    evidence: policy.evidence,
    promotion: policy.promotion,
    rollback: policy.rollback,
    updateLoop: policy.updateLoop,
    nonCanonicalViews: policy.explain?.nonCanonicalViews || [],
    policyBoundary: 'Generated/explain view only; canonical policy semantics live in .lazy-harness/ssot/policies.json.',
  }
  if (format === 'json') return printJson(explanation)
  console.log(`# Policy: ${policy.id}`)
  console.log('')
  console.log(`- Title: ${policy.title}`)
  console.log(`- Canonical source: \`.lazy-harness/ssot/policies.json\``)
  console.log(`- Source record: \`${policy.sourceRecord}\``)
  console.log(`- Scope/stage/level: ${policy.scope} / ${policy.stage} / ${policy.level}`)
  console.log(`- Summary: ${explanation.summary}`)
  console.log(`- Boundary: ${explanation.policyBoundary}`)
  if (policy.capabilityIds?.length) console.log(`- Capabilities: ${policy.capabilityIds.join(', ')}`)
  console.log('')
  console.log('## Applies to')
  for (const item of policy.appliesTo) console.log(`- ${item}`)
  console.log('')
  console.log('## Evidence')
  for (const item of policy.evidence) console.log(`- ${item.kind}${item.path ? ` \`${item.path}\`` : ''}: ${item.summary}`)
  console.log('')
  console.log('## Promotion / rollback')
  console.log(`- Requires confirmation: ${policy.promotion.requiresConfirmation}`)
  console.log(`- Allowed target levels: ${policy.promotion.allowedTargetLevels.join(', ')}`)
  console.log(`- Rollback target: ${policy.rollback.demotionTarget}`)
  for (const criterion of policy.rollback.criteria) console.log(`  - ${criterion}`)
}

function policyRuntimeDescription(policy: Policy): string {
  if (policy.level === 'warn') return 'warn-only (explicit policy_context required)'
  if (policy.level === 'block') {
    const runtime = objectValue(policy.runtime)
    if (runtime?.mode === 'command-boundary' && runtime.blocks === true) return 'block (command-boundary configured; verify installation with block-readiness)'
    if (runtime?.mode === 'typed-agent-routing' && runtime.blocks === true) return 'block (typed-agent-routing configured; verify installation with block-readiness)'
    return 'block (readiness/preflight only; no lifecycle runtime declared)'
  }
  return 'advisory-only'
}

function renderPolicyRulebook(registry: PolicyRegistry): string {
  const policies = [...registry.policies].sort((a, b) => a.id.localeCompare(b.id))
  const lines: string[] = []
  lines.push('# Generated Policy Rulebook')
  lines.push('')
  lines.push('> GENERATED VIEW, NON-CANONICAL.')
  lines.push('> Canonical behavior policy source: `.lazy-harness/ssot/policies.json`.')
  lines.push('> Regenerate with: `.lazy-harness/bin/lazy policy render-rulebook --write`.')
  lines.push('')
  lines.push('This file explains typed behavior policies for humans/LLMs. Do not edit it as source of truth.')
  lines.push('')
  lines.push('## Summary')
  lines.push('')
  lines.push(`- Policy count: ${policies.length}`)
  lines.push('- Canonical source: `.lazy-harness/ssot/policies.json`')
  lines.push('- Generated/explain view only: yes')
  lines.push('')
  lines.push('| Policy | Level | Stage | Runtime | Summary |')
  lines.push('|---|---|---|---|---|')
  for (const policy of policies) {
    const summary = (policy.explain?.summary || policy.title).replace(/\|/g, '\\|')
    lines.push(`| \`${policy.id}\` | ${policy.level} | ${policy.stage} | ${policyRuntimeDescription(policy)} | ${summary} |`)
  }
  for (const policy of policies) {
    lines.push('')
    lines.push(`## ${policy.id}`)
    lines.push('')
    lines.push(`- Title: ${policy.title}`)
    lines.push(`- Scope: ${policy.scope}`)
    lines.push(`- Stage: ${policy.stage}`)
    lines.push(`- Level: ${policy.level}`)
    lines.push(`- Runtime: ${policyRuntimeDescription(policy)}`)
    lines.push(`- Source record: \`${policy.sourceRecord}\``)
    if (policy.capabilityIds?.length) lines.push(`- Capabilities: ${policy.capabilityIds.join(', ')}`)
    lines.push(`- Summary: ${policy.explain?.summary || policy.title}`)
    lines.push('')
    lines.push('### Applies to')
    for (const item of policy.appliesTo) lines.push(`- ${item}`)
    lines.push('')
    lines.push('### Evidence')
    for (const item of policy.evidence) lines.push(`- ${item.kind}${item.path ? ` \`${item.path}\`` : ''}: ${item.summary}`)
    lines.push('')
    lines.push('### Promotion / rollback')
    lines.push(`- Requires confirmation: ${policy.promotion.requiresConfirmation}`)
    lines.push(`- Allowed target levels: ${policy.promotion.allowedTargetLevels.join(', ')}`)
    lines.push(`- Rollback target: ${policy.rollback.demotionTarget}`)
    for (const criterion of policy.rollback.criteria) lines.push(`  - ${criterion}`)
  }
  lines.push('')
  return lines.join('\n')
}

function renderRulebook(root: string, opts: Record<string, string | boolean>, format: Format): void {
  const registry = loadRegistry(root)
  const content = renderPolicyRulebook(registry)
  const outputPath = generatedOutputPath(root, opts)
  const relOutput = relative(root, outputPath).split('\\').join('/')
  if (opts.write === true) {
    mkdirSync(dirname(outputPath), { recursive: true })
    writeFileSync(outputPath, content, 'utf8')
  }
  const result = {
    schemaVersion: 'policy-rulebook-render/v1',
    ok: true,
    canonicalSource: '.lazy-harness/ssot/policies.json',
    generatedView: true,
    nonCanonical: true,
    outputPath: relOutput,
    wrote: opts.write === true,
    policyCount: registry.policies.length,
    content,
  }
  if (format === 'json') return printJson(result)
  if (opts.write === true) {
    console.log(`Wrote generated policy rulebook: ${relOutput}`)
    console.log('Canonical source: .lazy-harness/ssot/policies.json')
    return
  }
  process.stdout.write(content)
}

function policyIdsForCapability(policyRegistry: PolicyRegistry, capability: Capability): string[] {
  const ids = new Set<string>()
  for (const id of Array.isArray(capability.policyIds) ? capability.policyIds : []) ids.add(String(id))
  for (const policy of policyRegistry.policies) {
    if (Array.isArray(policy.capabilityIds) && policy.capabilityIds.includes(capability.id)) ids.add(policy.id)
  }
  return [...ids].sort()
}

function retireReadiness(root: string, opts: Record<string, string | boolean>, format: Format): void {
  const policyRegistry = loadRegistry(root)
  const capabilityRegistry = loadCapabilityRegistry(root)
  const rules = loadRulebookEntries(root)
  const activeRules = rules.filter((rule) => rule.status === 'active')
  const policyIds = new Set(policyRegistry.policies.map((policy) => policy.id))
  const rulePaths = new Set(rules.map((rule) => rule.path))
  const findings: ReadinessFinding[] = []
  const coveredRulePaths = new Set<string>()

  for (const rule of activeRules) {
    const capability = capabilityForRulebookEntry(rule, capabilityRegistry.capabilities)
    if (!capability) {
      findings.push({ severity: 'blocker', path: rule.path, message: 'active rulebook entry has no capability binding, so typed policy migration cannot prove compatibility' })
      continue
    }
    const linkedPolicyIds = policyIdsForCapability(policyRegistry, capability)
    if (linkedPolicyIds.length === 0) {
      findings.push({ severity: 'blocker', path: rule.path, capabilityId: capability.id, message: 'capability has no typed policy link through capability.policyIds or policy.capabilityIds' })
      continue
    }
    let ruleCovered = true
    for (const policyId of linkedPolicyIds) {
      if (!policyIds.has(policyId)) {
        findings.push({ severity: 'blocker', path: rule.path, capabilityId: capability.id, policyId, message: 'capability references missing typed policy id' })
        ruleCovered = false
      }
    }
    if (ruleCovered) {
      coveredRulePaths.add(rule.path)
      findings.push({ severity: 'info', path: rule.path, capabilityId: capability.id, policyId: linkedPolicyIds.join(','), message: 'active rulebook entry has typed policy coverage' })
    }
  }

  for (const capability of capabilityRegistry.capabilities) {
    const rulebookPath = typeof capability.rulebookRecord === 'string' ? capability.rulebookRecord : ''
    const sourcePath = typeof capability.sourceRecord === 'string' ? capability.sourceRecord : ''
    const referencedRule = rulebookPath || (sourcePath.startsWith('.lazy-harness/rules/') ? sourcePath : '')
    if (referencedRule && !rulePaths.has(referencedRule)) {
      findings.push({ severity: 'blocker', path: referencedRule, capabilityId: capability.id, message: 'capability references missing rulebook compatibility surface' })
    }
  }

  const blockers = findings.filter((finding) => finding.severity === 'blocker')
  const result = {
    schemaVersion: 'policy-rulebook-retire-readiness/v1',
    ok: true,
    ready: blockers.length === 0,
    strict: opts.strict === true,
    canonicalSource: '.lazy-harness/ssot/policies.json',
    compatibilitySurface: '.lazy-harness/rules/**',
    boundary: 'Readiness/preflight only; does not delete .lazy-harness/rules/** or change lazy rules compatibility behavior.',
    counts: {
      activeRulebookEntries: activeRules.length,
      coveredRulebookEntries: coveredRulePaths.size,
      policies: policyRegistry.policies.length,
      capabilities: capabilityRegistry.capabilities.length,
      blockers: blockers.length,
    },
    findings,
  }
  if (format === 'json') printJson(result)
  else {
    console.log('# Policy rulebook retire readiness')
    console.log('')
    console.log(`- ready: ${result.ready ? 'yes' : 'no'}`)
    console.log(`- canonical source: ${result.canonicalSource}`)
    console.log(`- compatibility surface: ${result.compatibilitySurface}`)
    console.log(`- boundary: ${result.boundary}`)
    console.log(`- active rulebook entries: ${result.counts.activeRulebookEntries}`)
    console.log(`- covered rulebook entries: ${result.counts.coveredRulebookEntries}`)
    console.log(`- blockers: ${result.counts.blockers}`)
    console.log('')
    console.log('## Findings')
    if (!findings.length) console.log('- none')
    for (const finding of findings) {
      console.log(`- ${finding.severity}${finding.path ? ` ${finding.path}` : ''}${finding.capabilityId ? ` capability=${finding.capabilityId}` : ''}${finding.policyId ? ` policy=${finding.policyId}` : ''}: ${finding.message}`)
    }
  }
  if (opts.strict === true && blockers.length > 0) process.exitCode = 1
}

function blockReadiness(root: string, opts: Record<string, string | boolean>, format: Format): void {
  const registry = loadRegistry(root)
  const auditIssues = auditRegistry(root, registry).filter((issue) => issue.severity === 'error')
  const blockPolicies = registry.policies.filter((policy) => policy.level === 'block')
  const commandBoundaryPolicies = blockPolicies.filter((policy) => objectValue(policy.runtime)?.mode === 'command-boundary')
  const commandBoundaryHelper = join(root, '.lazy-harness/hooks/lifecycle/helpers/check-project-command-boundary.py')
  const commandBoundaryHook = join(root, '.lazy-harness/hooks/lifecycle/on-tool-execute-before.sh')
  const commandBoundaryInstalled = commandBoundaryPolicies.length > 0
    && existsSync(commandBoundaryHelper)
    && existsSync(commandBoundaryHook)
    && readFileSync(commandBoundaryHook, 'utf8').includes('check-project-command-boundary.py')
  const typedAgentRoutingPolicies = blockPolicies.filter((policy) => objectValue(policy.runtime)?.mode === 'typed-agent-routing')
  const typedAgentRoutingHelper = join(root, '.lazy-harness/hooks/lifecycle/helpers/check-agent-model-routing.py')
  const typedAgentRoutingInstalled = typedAgentRoutingPolicies.length > 0
    && existsSync(typedAgentRoutingHelper)
    && existsSync(commandBoundaryHook)
    && readFileSync(commandBoundaryHook, 'utf8').includes('check-agent-model-routing.py')
  const findings: ReadinessFinding[] = []
  const readyPolicyIds = new Set<string>()

  if (auditIssues.length) {
    for (const issue of auditIssues) findings.push({ severity: 'blocker', policyId: issue.id, message: `policy registry audit error: ${issue.message}` })
  }
  if (!blockPolicies.length) {
    findings.push({ severity: 'blocker', message: 'no block-level policies exist; block runtime has no promoted boundary to install' })
  }

  for (const policy of blockPolicies) {
    let policyReady = true
    const addBlocker = (message: string, path?: string): void => {
      policyReady = false
      findings.push({ severity: 'blocker', policyId: policy.id, path, message })
    }
    if (!policy.promotion?.allowedTargetLevels?.includes('block')) addBlocker('block policy promotion.allowedTargetLevels must include block')
    if (!policy.evidence?.some((item) => item.kind === 'user-confirmation')) addBlocker('block policy requires user-confirmation evidence')
    if (!policy.evidence?.some((item) => item.kind === 'validation-output')) addBlocker('block policy requires validation-output evidence proving block and allow cases')
    if (!policy.rollback?.criteria?.length) addBlocker('block policy requires rollback criteria')

    const runtime = objectValue(policy.runtime)
    if (!runtime) addBlocker('block policy requires runtime metadata')
    else {
      if (runtime.blocks !== true) addBlocker('runtime.blocks must be true for block readiness')
      if (runtime.requiresExplicitContext !== true) addBlocker('runtime.requiresExplicitContext must be true for block readiness')
      if (!nonEmptyString(runtime.bypass)) addBlocker('runtime.bypass must document bypass or acknowledgement behavior')
      if (!nonEmptyString(runtime.fixture)) addBlocker('runtime.fixture must point to a block/allow regression fixture')
      else if (!isRootRelativeLazyPath(runtime.fixture) || !existsSync(join(root, runtime.fixture))) addBlocker(`runtime.fixture missing or invalid: ${runtime.fixture}`, String(runtime.fixture))
      if (runtime.mode === 'command-boundary') {
        const boundary = objectValue(runtime.commandBoundary)
        if (!boundary || !nonEmptyString(boundary.guard)) addBlocker('command-boundary policy requires runtime.commandBoundary.guard')
        if (!commandBoundaryInstalled) addBlocker('command-boundary policy requires the shared helper to be chained from on-tool-execute-before.sh')
      }
      if (runtime.mode === 'typed-agent-routing') {
        const routes = objectValue(runtime.typedAgentRouting)
        if (!routes || !Object.keys(routes).length) addBlocker('typed-agent-routing policy requires runtime.typedAgentRouting route configuration')
        if (!typedAgentRoutingInstalled) addBlocker('typed-agent-routing policy requires the shared helper to be chained from on-tool-execute-before.sh')
      }
    }

    if (!isRootRelativeLazyPath(policy.sourceRecord) || !existsSync(join(root, policy.sourceRecord))) {
      addBlocker(`sourceRecord missing or invalid: ${policy.sourceRecord}`, policy.sourceRecord)
    } else {
      const sourceText = readFileSync(join(root, policy.sourceRecord), 'utf8')
      const promotions = extractHardStopPromotions(sourceText, policy.sourceRecord, root)
      const activePromotions = promotions.filter((promotion) => HARD_STOP_ACTIVE_STATUSES.has(String(promotion.fields.Status || '').trim().toLowerCase()))
      if (!activePromotions.length) addBlocker('sourceRecord must include active/proposed ## Hard-stop promotion section', policy.sourceRecord)
      for (const promotion of activePromotions) {
        if (promotion.problems.length) {
          for (const problem of promotion.problems) addBlocker(`hard-stop promotion problem at line ${promotion.startLine}: ${problem}`, policy.sourceRecord)
        }
      }
    }

    if (policyReady) {
      readyPolicyIds.add(policy.id)
      findings.push({ severity: 'info', policyId: policy.id, path: policy.sourceRecord, message: 'block policy has promotion evidence, fixture, explicit-context runtime, bypass behavior, and rollback path' })
    }
  }

  const blockers = findings.filter((finding) => finding.severity === 'blocker')
  const result = {
    schemaVersion: 'policy-block-readiness/v1',
    ok: true,
    ready: blockers.length === 0 && blockPolicies.length > 0,
    strict: opts.strict === true,
    runtime: 'block-preflight-only',
    hardStopHookInstalled: false,
    lifecycleMutation: false,
    commandBoundaryInstalled,
    commandBoundaryPolicyIds: commandBoundaryPolicies.map((policy) => policy.id),
    typedAgentRoutingInstalled,
    typedAgentRoutingPolicyIds: typedAgentRoutingPolicies.map((policy) => policy.id),
    boundary: 'Generic response/turn block runtime: Readiness/preflight only; does not install or enable lifecycle hard-stop hooks. Promoted project command boundaries are reported separately.',
    criteria: [
      'block policy level',
      'user-confirmation evidence',
      'validation-output evidence proving block and allow cases',
      'active/proposed hard-stop promotion section in sourceRecord',
      'runtime.blocks=true',
      'runtime.requiresExplicitContext=true',
      'runtime.bypass documented',
      'runtime.fixture exists',
      'rollback criteria documented',
    ],
    counts: {
      policies: registry.policies.length,
      blockPolicies: blockPolicies.length,
      readyBlockPolicies: readyPolicyIds.size,
      commandBoundaryPolicies: commandBoundaryPolicies.length,
      typedAgentRoutingPolicies: typedAgentRoutingPolicies.length,
      blockers: blockers.length,
    },
    findings,
  }
  if (format === 'json') printJson(result)
  else {
    console.log('# Policy block readiness')
    console.log('')
    console.log(`- ready: ${result.ready ? 'yes' : 'no'}`)
    console.log(`- runtime: ${result.runtime}`)
    console.log(`- hard-stop hook installed: ${result.hardStopHookInstalled ? 'yes' : 'no'}`)
    console.log(`- project command boundary installed: ${result.commandBoundaryInstalled ? 'yes' : 'no'}`)
    console.log(`- typed agent routing installed: ${result.typedAgentRoutingInstalled ? 'yes' : 'no'}`)
    console.log(`- boundary: ${result.boundary}`)
    console.log(`- block policies: ${result.counts.blockPolicies}`)
    console.log(`- ready block policies: ${result.counts.readyBlockPolicies}`)
    console.log(`- blockers: ${result.counts.blockers}`)
    console.log('')
    console.log('## Findings')
    for (const finding of findings) console.log(`- ${finding.severity}${finding.policyId ? ` policy=${finding.policyId}` : ''}${finding.path ? ` path=${finding.path}` : ''}: ${finding.message}`)
  }
  if (opts.strict === true && blockers.length > 0) process.exitCode = 1
}

function audit(root: string, format: Format): void {
  const registry = loadRegistry(root)
  const issues = auditRegistry(root, registry)
  const ok = !issues.some((issue) => issue.severity === 'error')
  if (format === 'json') return printJson({ schemaVersion: 'policy-audit/v1', ok, issues, policies: registry.policies.length })
  console.log('# Policy audit')
  console.log('')
  console.log(`- ok: ${ok}`)
  console.log(`- policies: ${registry.policies.length}`)
  if (issues.length) {
    console.log('')
    console.log('## Issues')
    for (const issue of issues) console.log(`- ${issue.severity}${issue.id ? ` ${issue.id}` : ''}: ${issue.message}`)
  }
  if (!ok) process.exitCode = 1
}

function main(): void {
  const [command = 'help', ...rest] = process.argv.slice(2)
  if (command === 'help' || command === '--help' || command === '-h') usage(0)
  const opts = parseOptions(rest)
  const root = hostRoot(opts)
  const format = fmt(opts)
  if (command === 'list') return listPolicies(root, opts, format)
  if (command === 'audit') return audit(root, format)
  if (command === 'resolve') return resolvePolicies(root, opts, format)
  if (command === 'render-rulebook') return renderRulebook(root, opts, format)
  if (command === 'upsert') return upsertPolicy(root, opts, format)
  if (command === 'retire-readiness') return retireReadiness(root, opts, format)
  if (command === 'block-readiness') return blockReadiness(root, opts, format)
  if (command === 'explain') {
    const id = typeof opts.id === 'string' ? opts.id : ''
    if (!id) {
      console.error('policy explain requires --id <policy-id>')
      process.exit(2)
    }
    const registry = loadRegistry(root)
    const policy = registry.policies.find((item) => item.id === id)
    if (!policy) {
      console.error(`policy not found: ${id}`)
      process.exit(1)
    }
    return explainPolicy(policy, format)
  }
  console.error(`Unknown policy command: ${command}`)
  usage(2)
}

main()
