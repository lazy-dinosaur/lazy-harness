#!/usr/bin/env bun
/**
 * task-router — read-only workflow compression router (ADR 0037).
 *
 * This script classifies a user request into finite routing axes. By default it
 * is read-only. With --log it appends telemetry only; it never writes records,
 * mutates question queues, or selects a Recommended option.
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'

type Intent = 'feature' | 'fix' | 'refactor' | 'investigation' | 'docs' | 'release' | 'unknown'
type Scope = 'trivial' | 'code-local' | 'behavior' | 'contract' | 'ownership' | 'unknown'
type Risk = 'low' | 'medium' | 'high'
type Confidence = 'low' | 'medium' | 'high'
type Layer = 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr' | 'ssot'
type RecordSearchMode = 'none' | 'recommended' | 'required'
type RecordCaptureMode = 'none' | 'candidate' | 'canonical'
type ImplMapTier = 'none' | 'file-map' | 'symbol-flow' | 'full-graph'
type GateMode = 'none' | 'narrow-confirm' | 'option-gate'
type OutputFormat = 'json' | 'md'

interface Args {
  message: string
  changedFiles: string[]
  format: OutputFormat
  log: boolean
  summary: boolean
  audit: boolean
  commits: number
  messageId: string
}

interface Evidence {
  matchedSignals: string[]
  riskEvidence: string[]
  scopeEvidence: string[]
  pathEvidence: string[]
  gateReasonCode: string
  truncatedLikely: boolean
  changedFileCount: number
  changedFileKinds: string[]
}

interface RouteOutput {
  ok: true
  mode: 'workflow-route'
  schemaVersion: '1.0'
  message: string
  changedFiles: string[]
  route: {
    intent: Intent
    scope: Scope
    risk: Risk
    confidence: Confidence
    affectedLayers: Layer[]
    recordSearch: { mode: RecordSearchMode; targets: string[]; reason: string }
    recordCapture: { mode: RecordCaptureMode; target: string | null; reason: string }
    implementationMap: { tier: ImplMapTier; reason: string }
    gate: { mode: GateMode; reason: string | null }
    validation: string[]
    nonNegotiables: string[]
    evidence: Evidence
  }
  rationale: string[]
  warnings: string[]
}

const LAYER_TARGETS: Record<Layer, string> = {
  ddd: '.lazy-harness/domain/',
  sdd: '.lazy-harness/spec/',
  bdd: '.lazy-harness/behavior/',
  tdd: '.lazy-harness/tests/',
  adr: '.lazy-harness/decisions/',
  ssot: '.lazy-harness/ssot/'
}

function parseArgs(argv: string[]): Args {
  const args: Args = { message: '', changedFiles: [], format: 'json', log: false, summary: false, audit: false, commits: 12, messageId: '' }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if ((arg === '--message' || arg === '-m') && next) {
      args.message = next
      i += 1
    } else if (arg.startsWith('--message=')) {
      args.message = arg.slice('--message='.length)
    } else if (arg === '--format' && (next === 'json' || next === 'md' || next === 'markdown')) {
      args.format = next === 'markdown' ? 'md' : next
      i += 1
    } else if (arg.startsWith('--format=')) {
      const value = arg.slice('--format='.length)
      if (value !== 'json' && value !== 'md' && value !== 'markdown') throw new Error(`Invalid --format: ${value}`)
      args.format = value === 'markdown' ? 'md' : value
    } else if ((arg === '--changed-files' || arg === '--files') && next) {
      args.changedFiles.push(...splitFiles(next))
      i += 1
    } else if (arg.startsWith('--changed-files=')) {
      args.changedFiles.push(...splitFiles(arg.slice('--changed-files='.length)))
    } else if (arg.startsWith('--files=')) {
      args.changedFiles.push(...splitFiles(arg.slice('--files='.length)))
    } else if (arg === '--file' && next) {
      args.changedFiles.push(next)
      i += 1
    } else if (arg === '--log') {
      args.log = true
    } else if (arg === '--message-id' && next) {
      args.messageId = next
      i += 1
    } else if (arg.startsWith('--message-id=')) {
      args.messageId = arg.slice('--message-id='.length)
    } else if (arg === '--summary' || arg === 'summary') {
      args.summary = true
    } else if (arg === '--audit' || arg === 'audit') {
      args.audit = true
    } else if (arg === '--commits' && next) {
      args.commits = Number.parseInt(next, 10) || 12
      i += 1
    } else if (arg.startsWith('--commits=')) {
      args.commits = Number.parseInt(arg.slice('--commits='.length), 10) || 12
    } else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown or incomplete flag: ${arg}`)
    }
  }
  args.changedFiles = [...new Set(args.changedFiles.map(normalizePath).filter(Boolean))]
  return args
}

function splitFiles(value: string): string[] {
  return value.split(',').map((entry) => entry.trim()).filter(Boolean)
}

function normalizePath(value: string): string {
  return value.replace(/\\/g, '/').replace(/^\.\//, '')
}

function printHelp(): void {
  console.log(`task-router — workflow compression router\n\nUsage:\n  lazy route --message "..." [--format=json|md] [--changed-files a,b] [--log] [--message-id id]\n  lazy route-summary [--format=json|md]\n  lazy route-audit [--commits=12] [--format=json|md]\n\nDefault route mode is advisory and read-only. --log appends telemetry only; it never writes records, mutates queues, or chooses Recommended options.`)
}

function has(text: string, pattern: RegExp): boolean {
  return pattern.test(text)
}

function addLayer(layers: Set<Layer>, ...values: Layer[]): void {
  values.forEach((value) => layers.add(value))
}

function add(values: string[], ...items: string[]): void {
  for (const item of items) {
    if (item && !values.includes(item)) values.push(item)
  }
}

function maxRisk(a: Risk, b: Risk): Risk {
  const order: Record<Risk, number> = { low: 0, medium: 1, high: 2 }
  return order[b] > order[a] ? b : a
}

function strongerScope(current: Scope, next: Scope): Scope {
  const order: Record<Scope, number> = { trivial: 0, 'code-local': 1, behavior: 2, contract: 3, ownership: 4, unknown: -1 }
  if (current === 'unknown') return next
  if (next === 'unknown') return current
  return order[next] > order[current] ? next : current
}

function textSignal(text: string, regex: RegExp): boolean {
  return regex.test(text)
}

function fileKind(file: string): string {
  if (/prisma\/schema\//.test(file)) return 'prisma-schema'
  if (/src\/main\/trpc\/routers\//.test(file)) return 'trpc-router'
  if (/auth|permission|PermissionsTab|AuthProvider/i.test(file)) return 'auth-permission'
  if (/src\/renderer\/src\/screens\//.test(file)) return 'renderer-screen'
  if (/src\/renderer\/src\/components\//.test(file)) return 'renderer-component'
  if (/tests?\//.test(file) || /\.test\./.test(file) || /\.spec\./.test(file)) return 'test'
  if (/docs?\//.test(file) || /\.(md|mdx|txt)$/.test(file)) return 'docs'
  if (/schema|config|env|hooks?\//i.test(file)) return 'contract-config'
  return 'code'
}

function classify(args: Args): RouteOutput {
  const raw = args.message.trim()
  const text = raw.toLowerCase()
  const files = args.changedFiles
  const layers = new Set<Layer>()
  const rationale: string[] = []
  const warnings: string[] = []
  const evidence: Evidence = {
    matchedSignals: [],
    riskEvidence: [],
    scopeEvidence: [],
    pathEvidence: [],
    gateReasonCode: 'none',
    truncatedLikely: raw.length >= 500,
    changedFileCount: files.length,
    changedFileKinds: []
  }

  let intent: Intent = 'unknown'
  let scope: Scope = 'unknown'
  let risk: Risk = 'low'
  let confidence: Confidence = raw ? 'medium' : 'low'
  let gate: GateMode = 'none'

  const shortOrPronoun = !raw || raw.length < 12 || has(text, /\b(그거|이거|저거|그 부분|that|this|it)\b/i)
  if (shortOrPronoun) {
    add(evidence.matchedSignals, 'short-or-pronoun')
    evidence.gateReasonCode = 'short-reference'
    scope = 'unknown'
    risk = 'medium'
    confidence = 'low'
    gate = 'option-gate'
    rationale.push('Request is short or referential; default-unknown requires clarification or record lookup.')
  }

  if (has(text, /\b(release|deploy|publish|hotfix|version|build|릴리즈|배포|publish|버전|핫픽스)\b/i)) {
    add(evidence.matchedSignals, 'release-word')
    add(evidence.riskEvidence, 'release-deploy')
    intent = 'release'
    risk = 'high'
    scope = 'contract'
    gate = 'option-gate'
    addLayer(layers, 'adr', 'ssot', 'tdd')
    rationale.push('Release/deploy/build wording implies high-risk workflow.')
  }

  if (has(text, /\b(delete|drop|destroy|wipe|force push|force-push|truncate|db push|migration|migrate|auth|permission|secret|token)\b/i) || textSignal(text, /(삭제|제거|초기화|드랍|강제|마이그레이션|권한|인증|보안)/)) {
    add(evidence.matchedSignals, 'risk-word')
    if (textSignal(text, /(삭제|제거|delete|drop|destroy|wipe|truncate)/i)) add(evidence.riskEvidence, 'destructive-word')
    if (textSignal(text, /(auth|permission|secret|token|권한|인증|보안)/i)) add(evidence.riskEvidence, 'auth-permission-word')
    if (textSignal(text, /(migration|migrate|마이그레이션)/i)) add(evidence.riskEvidence, 'migration-word')
    risk = 'high'
    gate = 'option-gate'
    addLayer(layers, 'ssot', 'adr', 'tdd')
    rationale.push('Destructive/security/database wording requires explicit gate.')
  }

  if (has(text, /\b(api|ipc|rpc|schema|contract|config|env|hook|cli|props?|component interface|endpoint|migration|스키마|계약|설정|환경변수|훅)\b/i)) {
    add(evidence.matchedSignals, 'contract-word')
    add(evidence.scopeEvidence, 'contract-word')
    if (scope !== 'ownership') scope = 'contract'
    if (risk === 'low') risk = 'medium'
    addLayer(layers, 'sdd', 'ssot', 'tdd')
    rationale.push('Contract/config/API wording maps to SDD/SSOT/TDD.')
  }

  if (has(text, /\b(ui|screen|button|click|flow|behavior|scenario|user)\b/i) || textSignal(text, /(사용자|화면|버튼|클릭|동작|흐름|시나리오|우클릭|드롭다운|모드|상세|표시)/)) {
    add(evidence.matchedSignals, 'behavior-word')
    add(evidence.scopeEvidence, 'behavior-word')
    if (scope === 'unknown' || scope === 'code-local' || scope === 'trivial') scope = 'behavior'
    if (risk === 'low') risk = 'medium'
    addLayer(layers, 'bdd', 'sdd', 'tdd')
    rationale.push('User-visible behavior wording maps to BDD/SDD/TDD.')
  }

  if (has(text, /\b(source of truth|source-of-truth|ownership|owner|upstream|downstream|project identity|rule placement|canonical|ssot|소스오브트루스|소유권|업스트림|다운스트림|프로젝트 정체성)\b/i)) {
    add(evidence.matchedSignals, 'ownership-word')
    add(evidence.scopeEvidence, 'ownership-word')
    add(evidence.riskEvidence, 'ownership-boundary')
    scope = 'ownership'
    risk = 'high'
    gate = 'option-gate'
    addLayer(layers, 'ssot', 'adr')
    rationale.push('Ownership/source-of-truth wording maps to SSOT/ADR and high risk.')
  }

  if (has(text, /\b(fix|bug|regression|broken|error|fail|고쳐|버그|회귀|실패|에러)\b/i)) {
    add(evidence.matchedSignals, 'fix-word')
    intent = 'fix'
    if (scope === 'unknown') scope = 'code-local'
    if (risk === 'low') risk = 'medium'
    addLayer(layers, 'tdd')
    rationale.push('Bug/fix wording requires TDD consideration.')
  }

  if (has(text, /\b(refactor|cleanup|rename|move|internal|리팩터|정리|이름 변경)\b/i)) {
    add(evidence.matchedSignals, 'refactor-word')
    if (intent === 'unknown') intent = 'refactor'
    if (scope === 'unknown') scope = 'code-local'
    addLayer(layers, 'tdd')
    rationale.push('Refactor wording maps to local code validation.')
  }

  if (has(text, /\b(investigate|evaluate|assess|plan|review|analy[sz]e|research|검토|평가|계획|분석|조사)\b/i)) {
    add(evidence.matchedSignals, 'investigation-word')
    if (intent === 'unknown') intent = 'investigation'
    if (scope === 'unknown') scope = 'code-local'
    rationale.push('Investigation/planning wording maps to advisory capture.')
  }

  if (has(text, /\b(doc|docs|readme|comment|copy|typo|text|문서|주석|오타|문구)\b/i)) {
    add(evidence.matchedSignals, 'docs-word')
    if (intent === 'unknown') intent = 'docs'
    if (scope === 'unknown') scope = 'trivial'
    rationale.push('Docs/copy wording is trivial unless host-specific policy terms override it.')
  }

  if ((has(text, /\b(feat|feature|add|create|implement|change|update|make)\b/i) || textSignal(text, /(만들|추가|구현|변경|수정)/)) && intent === 'unknown') {
    add(evidence.matchedSignals, 'implementation-word')
    intent = 'feature'
    if (scope === 'unknown') scope = 'code-local'
    if (risk === 'low') risk = 'medium'
    rationale.push('Implementation wording defaults to feature/code-local unless stronger scope matched.')
  }

  for (const file of files) {
    const kind = fileKind(file)
    add(evidence.changedFileKinds, kind)
    if (kind !== 'code') add(evidence.pathEvidence, kind)
    if (/\.(md|mdx|txt)$/.test(file)) {
      if (intent === 'unknown') intent = 'docs'
      if (scope === 'unknown') scope = 'trivial'
    } else if (/\.(ts|tsx|js|jsx|py|sh)$/.test(file)) {
      if (scope === 'unknown' || scope === 'trivial') scope = 'code-local'
      if (intent === 'unknown') intent = 'refactor'
      if (risk === 'low') risk = 'medium'
      addLayer(layers, 'tdd')
    }
    if (kind === 'prisma-schema' || kind === 'trpc-router' || kind === 'contract-config' || file.includes('/api/') || file.includes('/ipc') || file.includes('/schema') || file.includes('/config') || file.includes('/hooks/')) {
      scope = strongerScope(scope, 'contract')
      risk = maxRisk(risk, 'medium')
      addLayer(layers, 'sdd', 'ssot', 'tdd')
      add(evidence.scopeEvidence, `${kind}-path`)
      add(evidence.riskEvidence, `${kind}-path`)
    }
    if (kind === 'auth-permission') {
      scope = strongerScope(scope, 'ownership')
      risk = maxRisk(risk, 'high')
      gate = 'option-gate'
      addLayer(layers, 'ssot', 'adr', 'tdd')
      add(evidence.scopeEvidence, 'auth-permission-path')
      add(evidence.riskEvidence, 'auth-permission-path')
    }
    if (kind === 'renderer-screen' || kind === 'renderer-component') {
      scope = strongerScope(scope, 'behavior')
      risk = maxRisk(risk, 'medium')
      addLayer(layers, 'bdd', 'sdd', 'tdd')
      add(evidence.scopeEvidence, `${kind}-path`)
    }
  }

  if (intent === 'unknown' && raw) intent = 'investigation'
  if (scope === 'unknown' && raw && !shortOrPronoun) scope = 'code-local'

  if (scope === 'trivial' && risk === 'low' && layers.size === 0 && gate === 'none') {
    confidence = 'high'
  } else if (risk === 'high' || gate === 'option-gate') {
    confidence = shortOrPronoun ? 'low' : 'medium'
  }

  if (risk === 'high') gate = 'option-gate'
  else if (gate === 'none' && (scope === 'contract' || scope === 'behavior') && confidence !== 'high') gate = 'narrow-confirm'
  if (gate === 'option-gate' && evidence.gateReasonCode === 'none') evidence.gateReasonCode = risk === 'high' ? 'high-risk' : (scope === 'unknown' ? 'unknown' : scope)
  if (gate === 'narrow-confirm' && evidence.gateReasonCode === 'none') evidence.gateReasonCode = scope
  if (evidence.truncatedLikely) {
    add(evidence.matchedSignals, 'truncated-likely')
    warnings.push('Message length suggests possible lifecycle payload truncation; route confidence may be incomplete.')
  }

  const affectedLayers = [...layers]
  const recordSearch = routeRecordSearch(scope, risk, confidence, affectedLayers)
  const recordCapture = routeRecordCapture(scope, risk, intent)
  const implementationMap = routeImplMap(scope, risk, files)
  const validation = routeValidation(scope, risk, intent)

  if (recordCapture.mode === 'candidate') {
    warnings.push('Candidate capture is durable but non-canonical; it cannot satisfy canonical record obligations.')
  }
  if (gate !== 'none') {
    warnings.push('Router is advisory only; unresolved gates still require normal lazy-harness option/confirmation discipline.')
  }

  return {
    ok: true,
    mode: 'workflow-route',
    schemaVersion: '1.0',
    message: raw,
    changedFiles: files,
    route: {
      intent,
      scope,
      risk,
      confidence,
      affectedLayers,
      recordSearch,
      recordCapture,
      implementationMap,
      gate: { mode: gate, reason: gateReason(gate, scope, risk, confidence) },
      validation,
      nonNegotiables: nonNegotiables(gate, risk, recordSearch.mode),
      evidence
    },
    rationale,
    warnings
  }
}

function routeRecordSearch(scope: Scope, risk: Risk, confidence: Confidence, layers: Layer[]): RouteOutput['route']['recordSearch'] {
  if (risk === 'high' || scope === 'contract' || scope === 'behavior' || scope === 'ownership' || scope === 'unknown' || confidence === 'low') {
    const targets = layers.length > 0 ? layers.map((layer) => LAYER_TARGETS[layer]) : ['.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/']
    return { mode: 'required', targets, reason: 'Host-dependent, risky, ambiguous, behavior, contract, or ownership work requires record-first search.' }
  }
  if (scope === 'code-local') {
    return { mode: 'recommended', targets: ['.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/'], reason: 'Local code work often benefits from nearby records.' }
  }
  return { mode: 'none', targets: [], reason: 'No host-dependent detail detected by router.' }
}

function routeRecordCapture(scope: Scope, risk: Risk, intent: Intent): RouteOutput['route']['recordCapture'] {
  if (risk === 'high' || scope === 'contract' || scope === 'behavior' || scope === 'ownership' || intent === 'fix') {
    return { mode: 'canonical', target: canonicalTarget(scope, intent), reason: 'Confirmed behavior/contract/ownership/risk/fix work must converge to canonical records when facts change.' }
  }
  if (intent === 'investigation' || scope === 'code-local') {
    return { mode: 'candidate', target: '.lazy-harness/knowledge/candidates.jsonl or .lazy-harness/planning/**', reason: 'Use durable non-canonical capture for discoveries or local planning.' }
  }
  return { mode: 'none', target: null, reason: 'Trivial/no-impact work needs no durable capture.' }
}

function canonicalTarget(scope: Scope, intent: Intent): string {
  if (scope === 'ownership') return '.lazy-harness/ssot/** or .lazy-harness/decisions/NNNN-*.md'
  if (scope === 'contract') return '.lazy-harness/spec/** or .lazy-harness/ssot/**'
  if (scope === 'behavior') return '.lazy-harness/behavior/** and related .lazy-harness/tests/**'
  if (intent === 'fix') return '.lazy-harness/tests/** plus impacted layers'
  return '.lazy-harness/{domain,spec,behavior,tests,decisions,ssot}/**'
}

function routeImplMap(scope: Scope, risk: Risk, files: string[]): RouteOutput['route']['implementationMap'] {
  if (risk === 'high' || scope === 'ownership') return { tier: 'full-graph', reason: 'High-risk or ownership work requires full graph-level mapping.' }
  if (scope === 'contract' || scope === 'behavior') return { tier: 'symbol-flow', reason: 'Behavior/contract implementation changes need key symbols, flow, and tests.' }
  if (scope === 'code-local' || files.length > 0) return { tier: 'file-map', reason: 'Local implementation work needs file roles and validation.' }
  return { tier: 'none', reason: 'No implementation impact detected.' }
}

function routeValidation(scope: Scope, risk: Risk, intent: Intent): string[] {
  const values = new Set<string>(['commit-time-lazy-test'])
  if (scope === 'code-local' || scope === 'behavior' || scope === 'contract' || intent === 'fix') values.add('focused-test-if-obvious')
  if (scope === 'behavior' || scope === 'contract' || risk === 'high') values.add('lazy-test')
  if (risk === 'high') {
    values.add('explicit-confirmation')
    values.add('doctor-smoke')
  }
  return [...values]
}

function gateReason(gate: GateMode, scope: Scope, risk: Risk, confidence: Confidence): string | null {
  if (gate === 'none') return null
  if (gate === 'option-gate') return `Gate required because scope=${scope}, risk=${risk}, confidence=${confidence}.`
  return `One likely route exists, but confirmation is useful because scope=${scope}, confidence=${confidence}.`
}

function nonNegotiables(gate: GateMode, risk: Risk, recordSearch: RecordSearchMode): string[] {
  const values = ['router-read-only', 'no-recommended-auto-select', 'candidate-is-not-canonical']
  if (recordSearch === 'required') values.push('record-first-search')
  if (gate !== 'none') values.push('unresolved-gate-blocks-progress')
  if (risk === 'high') values.push('explicit-confirmation-before-risk')
  return values
}

function toMarkdown(result: RouteOutput): string {
  const r = result.route
  return [
    '# lazy route',
    '',
    `- intent: ${r.intent}`,
    `- scope: ${r.scope}`,
    `- risk: ${r.risk}`,
    `- confidence: ${r.confidence}`,
    `- affected layers: ${r.affectedLayers.length ? r.affectedLayers.join(', ') : 'none'}`,
    `- record search: ${r.recordSearch.mode} (${r.recordSearch.reason})`,
    `- record capture: ${r.recordCapture.mode}${r.recordCapture.target ? ` → ${r.recordCapture.target}` : ''}`,
    `- implementation map: ${r.implementationMap.tier}`,
    `- gate: ${r.gate.mode}${r.gate.reason ? ` (${r.gate.reason})` : ''}`,
    `- validation: ${r.validation.join(', ')}`,
    `- evidence: signals=${r.evidence.matchedSignals.join(',') || 'none'} risk=${r.evidence.riskEvidence.join(',') || 'none'} path=${r.evidence.pathEvidence.join(',') || 'none'} gateReason=${r.evidence.gateReasonCode}`,
    '',
    '## Non-negotiables',
    ...r.nonNegotiables.map((entry) => `- ${entry}`),
    '',
    '## Rationale',
    ...(result.rationale.length ? result.rationale.map((entry) => `- ${entry}`) : ['- No specific heuristic rationale.']),
    ...(result.warnings.length ? ['', '## Warnings', ...result.warnings.map((entry) => `- ${entry}`)] : [])
  ].join('\n')
}

function hostRoot(): string {
  return process.env.LAZY_HOST_ROOT || process.cwd()
}

function telemetryPath(name: string): string {
  return join(hostRoot(), '.lazy-harness', 'logs', name)
}

function stableHash(value: string): string {
  return createHash('sha256').update(value).digest('hex').slice(0, 16)
}

function appendTelemetry(result: RouteOutput, messageId = ''): void {
  const logsDir = join(hostRoot(), '.lazy-harness', 'logs')
  mkdirSync(logsDir, { recursive: true })
  const path = telemetryPath('route-decisions.jsonl')
  const messageIdHash = messageId ? stableHash(messageId) : ''
  if (messageIdHash && existsSync(path)) {
    const alreadyLogged = readFileSync(path, 'utf8')
      .split('\n')
      .filter((line) => line.trim())
      .some((line) => {
        try {
          return JSON.parse(line).messageIdHash === messageIdHash
        } catch {
          return false
        }
      })
    if (alreadyLogged) return
  }
  const r = result.route
  const entry = {
    timestamp: new Date().toISOString(),
    source: 'lazy-route',
    schemaVersion: result.schemaVersion,
    messageHash: stableHash(result.message),
    messageIdHash: messageIdHash || undefined,
    messageLength: result.message.length,
    changedFiles: result.changedFiles,
    intent: r.intent,
    scope: r.scope,
    risk: r.risk,
    confidence: r.confidence,
    affectedLayers: r.affectedLayers,
    recordSearchMode: r.recordSearch.mode,
    recordCaptureMode: r.recordCapture.mode,
    implementationMapTier: r.implementationMap.tier,
    gateMode: r.gate.mode,
    routeVersion: '1.1',
    matchedSignals: r.evidence.matchedSignals,
    riskEvidence: r.evidence.riskEvidence,
    scopeEvidence: r.evidence.scopeEvidence,
    pathEvidence: r.evidence.pathEvidence,
    gateReasonCode: r.evidence.gateReasonCode,
    truncatedLikely: r.evidence.truncatedLikely,
    changedFileCount: r.evidence.changedFileCount,
    changedFileKinds: r.evidence.changedFileKinds,
    validation: r.validation,
    nonNegotiables: r.nonNegotiables,
    warningCount: result.warnings.length
  }
  appendFileSync(path, `${JSON.stringify(entry)}\n`, 'utf8')
}

function loadJsonl(path: string): any[] {
  if (!existsSync(path)) return []
  return readFileSync(path, 'utf8')
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line))
}

function countBy(entries: any[], key: string): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const entry of entries) {
    const value = String(entry[key] ?? 'unknown')
    counts[value] = (counts[value] || 0) + 1
  }
  return counts
}

function summarizeTelemetry(): any {
  const decisions = loadJsonl(telemetryPath('route-decisions.jsonl'))
  const feedback = loadJsonl(telemetryPath('route-feedback.jsonl'))
  const total = decisions.length
  const optionGate = decisions.filter((entry) => entry.gateMode === 'option-gate').length
  const highRisk = decisions.filter((entry) => entry.risk === 'high').length
  const lowConfidence = decisions.filter((entry) => entry.confidence === 'low').length
  const candidate = decisions.filter((entry) => entry.recordCaptureMode === 'candidate').length
  const canonical = decisions.filter((entry) => entry.recordCaptureMode === 'canonical').length
  const truncated = decisions.filter((entry) => entry.truncatedLikely).length
  const recommendations: string[] = []
  if (total === 0) recommendations.push('No route telemetry yet. Use lazy route --log during real work.')
  if (total >= 5 && optionGate / total > 0.45) recommendations.push('High option-gate ratio; inspect false positives and consider narrower gate heuristics.')
  if (total >= 5 && lowConfidence / total > 0.35) recommendations.push('High low-confidence ratio; inspect ambiguous input handling or add better context inputs.')
  if (total >= 5 && canonical / total > 0.55) recommendations.push('High canonical capture ratio; inspect whether router is over-prescribing full records.')
  if (feedback.length === 0 && total >= 10) recommendations.push('No route feedback logged yet; ask user/agent to label false positives or false negatives when noticed.')
  return {
    ok: true,
    mode: 'route-summary',
    schemaVersion: '1.0',
    totalRoutes: total,
    feedbackCount: feedback.length,
    counts: {
      intent: countBy(decisions, 'intent'),
      scope: countBy(decisions, 'scope'),
      risk: countBy(decisions, 'risk'),
      confidence: countBy(decisions, 'confidence'),
      gateMode: countBy(decisions, 'gateMode'),
      recordSearchMode: countBy(decisions, 'recordSearchMode'),
      recordCaptureMode: countBy(decisions, 'recordCaptureMode'),
      implementationMapTier: countBy(decisions, 'implementationMapTier')
      , gateReasonCode: countBy(decisions, 'gateReasonCode')
    },
    evidenceCounts: {
      riskEvidence: countArrayValues(decisions, 'riskEvidence'),
      scopeEvidence: countArrayValues(decisions, 'scopeEvidence'),
      pathEvidence: countArrayValues(decisions, 'pathEvidence'),
      changedFileKinds: countArrayValues(decisions, 'changedFileKinds')
    },
    ratios: total === 0 ? {} : {
      optionGate: optionGate / total,
      highRisk: highRisk / total,
      lowConfidence: lowConfidence / total,
      candidateCapture: candidate / total,
      canonicalCapture: canonical / total,
      truncatedLikely: truncated / total
    },
    recommendations
  }
}

function countArrayValues(entries: any[], key: string): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const entry of entries) {
    const values = Array.isArray(entry[key]) ? entry[key] : []
    for (const value of values) counts[String(value)] = (counts[String(value)] || 0) + 1
  }
  return counts
}

function summaryMarkdown(summary: any): string {
  return [
    '# lazy route summary',
    '',
    `- total routes: ${summary.totalRoutes}`,
    `- feedback count: ${summary.feedbackCount}`,
    `- option-gate ratio: ${summary.ratios.optionGate ?? 0}`,
    `- low-confidence ratio: ${summary.ratios.lowConfidence ?? 0}`,
    `- canonical-capture ratio: ${summary.ratios.canonicalCapture ?? 0}`,
    `- truncated-likely ratio: ${summary.ratios.truncatedLikely ?? 0}`,
    '',
    '## Counts',
    `- scope: ${JSON.stringify(summary.counts.scope)}`,
    `- risk: ${JSON.stringify(summary.counts.risk)}`,
    `- gate: ${JSON.stringify(summary.counts.gateMode)}`,
    `- record capture: ${JSON.stringify(summary.counts.recordCaptureMode)}`,
    `- gate reasons: ${JSON.stringify(summary.counts.gateReasonCode)}`,
    `- risk evidence: ${JSON.stringify(summary.evidenceCounts.riskEvidence)}`,
    `- path evidence: ${JSON.stringify(summary.evidenceCounts.pathEvidence)}`,
    '',
    '## Recommendations',
    ...(summary.recommendations.length ? summary.recommendations.map((item: string) => `- ${item}`) : ['- No recommendations.'])
  ].join('\n')
}

function gitOutput(args: string[]): string {
  try {
    return execFileSync('git', args, { cwd: hostRoot(), encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
  } catch {
    return ''
  }
}

function auditRecentCommits(count: number): any {
  const lines = gitOutput(['log', `-${Math.max(1, count)}`, '--format=%H%x00%s']).split('\n').filter(Boolean)
  const commits = lines.map((line) => {
    const [sha, subject = ''] = line.split('\x00')
    const files = gitOutput(['show', '--name-only', '--format=', sha]).split('\n').map((f) => f.trim()).filter(Boolean)
    const route = classify({ message: subject, changedFiles: files, format: 'json', log: false, summary: false, audit: false, commits: count, messageId: '' }).route
    const flags: string[] = []
    if (route.risk === 'high') flags.push('risk-review-required')
    if (route.evidence.riskEvidence.includes('destructive-word')) flags.push('destructive-evidence')
    if (route.evidence.pathEvidence.some((p) => ['prisma-schema', 'trpc-router', 'auth-permission'].includes(p))) flags.push('contract-risk-path')
    if (route.risk === 'low' && (route.evidence.riskEvidence.length || route.evidence.pathEvidence.some((p) => ['prisma-schema', 'trpc-router', 'auth-permission'].includes(p)))) flags.push('possible-risk-undercall')
    if (route.gate.mode === 'none' && route.evidence.riskEvidence.includes('destructive-word')) flags.push('destructive-without-gate')
    if (route.scope === 'code-local' && route.evidence.pathEvidence.some((p) => ['trpc-router', 'prisma-schema', 'auth-permission', 'renderer-screen'].includes(p))) flags.push('path-scope-undercall')
    if (route.recordCapture.mode === 'candidate' && (route.scope === 'contract' || route.scope === 'behavior' || route.risk === 'high')) flags.push('candidate-for-contract-behavior-risk')
    return { sha: sha.slice(0, 8), subjectHash: stableHash(subject), subjectLength: subject.length, fileCount: files.length, route, flags }
  })
  return {
    ok: true,
    mode: 'route-audit',
    schemaVersion: '1.0',
    commitCount: commits.length,
    flaggedCount: commits.filter((c) => c.flags.length > 0).length,
    commits
  }
}

function auditMarkdown(audit: any): string {
  return [
    '# lazy route audit',
    '',
    `- commits: ${audit.commitCount}`,
    `- flagged: ${audit.flaggedCount}`,
    '',
    ...audit.commits.map((c: any) => [
      `## ${c.sha}`,
      `- subjectHash: ${c.subjectHash}`,
      `- files: ${c.fileCount}`,
      `- route: intent=${c.route.intent} scope=${c.route.scope} risk=${c.route.risk} gate=${c.route.gate.mode} capture=${c.route.recordCapture.mode} map=${c.route.implementationMap.tier}`,
      `- evidence: risk=${c.route.evidence.riskEvidence.join(',') || 'none'} path=${c.route.evidence.pathEvidence.join(',') || 'none'}`,
      `- flags: ${c.flags.join(', ') || 'none'}`,
      ''
    ].join('\n'))
  ].join('\n')
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    if (args.summary) {
      const summary = summarizeTelemetry()
      if (args.format === 'json') console.log(JSON.stringify(summary, null, 2))
      else console.log(summaryMarkdown(summary))
      return
    }
    if (args.audit) {
      const audit = auditRecentCommits(args.commits)
      if (args.format === 'json') console.log(JSON.stringify(audit, null, 2))
      else console.log(auditMarkdown(audit))
      return
    }
    if (!args.message.trim()) throw new Error('Missing --message')
    const result = classify(args)
    if (args.log) appendTelemetry(result, args.messageId)
    if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
    else console.log(toMarkdown(result))
  } catch (error) {
    console.error(`task-router: ${(error as Error).message}`)
    printHelp()
    process.exit(2)
  }
}

main()
