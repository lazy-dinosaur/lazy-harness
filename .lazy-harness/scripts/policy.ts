#!/usr/bin/env bun
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
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

Policy Machinery Option B: .lazy-harness/ssot/policies.json is canonical.
Resolve defaults to advisory-only. Warn runtime requires --runtime=warn and never blocks.
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
      if (['format', 'id', 'stage', 'level', 'target', 'applies-to', 'max-level', 'runtime', 'output'].includes(k)) opts[k] = value(argv, i++, a)
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

function printJson(data: unknown): void {
  console.log(JSON.stringify(data, null, 2))
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
  if (policy.level === 'block') return 'block (not implemented by current runtime)'
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
