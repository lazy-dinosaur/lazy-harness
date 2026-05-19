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
  const args: Args = { message: '', changedFiles: [], format: 'json', log: false, summary: false }
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
    } else if (arg === '--summary' || arg === 'summary') {
      args.summary = true
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
  console.log(`task-router — workflow compression router\n\nUsage:\n  lazy route --message "..." [--format=json|md] [--changed-files a,b] [--log]\n  lazy route-summary [--format=json|md]\n\nDefault route mode is advisory and read-only. --log appends telemetry only; it never writes records, mutates queues, or chooses Recommended options.`)
}

function has(text: string, pattern: RegExp): boolean {
  return pattern.test(text)
}

function addLayer(layers: Set<Layer>, ...values: Layer[]): void {
  values.forEach((value) => layers.add(value))
}

function classify(args: Args): RouteOutput {
  const raw = args.message.trim()
  const text = raw.toLowerCase()
  const files = args.changedFiles
  const layers = new Set<Layer>()
  const rationale: string[] = []
  const warnings: string[] = []

  let intent: Intent = 'unknown'
  let scope: Scope = 'unknown'
  let risk: Risk = 'low'
  let confidence: Confidence = raw ? 'medium' : 'low'
  let gate: GateMode = 'none'

  const shortOrPronoun = !raw || raw.length < 12 || has(text, /\b(그거|이거|저거|그 부분|that|this|it)\b/i)
  if (shortOrPronoun) {
    scope = 'unknown'
    risk = 'medium'
    confidence = 'low'
    gate = 'option-gate'
    rationale.push('Request is short or referential; default-unknown requires clarification or record lookup.')
  }

  if (has(text, /\b(release|deploy|publish|hotfix|version|build|릴리즈|배포|publish|버전|핫픽스)\b/i)) {
    intent = 'release'
    risk = 'high'
    scope = 'contract'
    gate = 'option-gate'
    addLayer(layers, 'adr', 'ssot', 'tdd')
    rationale.push('Release/deploy/build wording implies high-risk workflow.')
  }

  if (has(text, /\b(delete|drop|destroy|wipe|force push|force-push|truncate|db push|migration|migrate|auth|permission|secret|token|삭제|드랍|강제|마이그레이션|권한|인증|보안)\b/i)) {
    risk = 'high'
    gate = 'option-gate'
    addLayer(layers, 'ssot', 'adr', 'tdd')
    rationale.push('Destructive/security/database wording requires explicit gate.')
  }

  if (has(text, /\b(api|ipc|rpc|schema|contract|config|env|hook|cli|props?|component interface|endpoint|migration|스키마|계약|설정|환경변수|훅)\b/i)) {
    if (scope !== 'ownership') scope = 'contract'
    if (risk === 'low') risk = 'medium'
    addLayer(layers, 'sdd', 'ssot', 'tdd')
    rationale.push('Contract/config/API wording maps to SDD/SSOT/TDD.')
  }

  if (has(text, /\b(ui|screen|button|click|flow|behavior|scenario|user|사용자|화면|버튼|클릭|동작|흐름|시나리오)\b/i)) {
    if (scope === 'unknown' || scope === 'code-local' || scope === 'trivial') scope = 'behavior'
    if (risk === 'low') risk = 'medium'
    addLayer(layers, 'bdd', 'sdd', 'tdd')
    rationale.push('User-visible behavior wording maps to BDD/SDD/TDD.')
  }

  if (has(text, /\b(source of truth|source-of-truth|ownership|owner|upstream|downstream|project identity|rule placement|canonical|ssot|소스오브트루스|소유권|업스트림|다운스트림|프로젝트 정체성)\b/i)) {
    scope = 'ownership'
    risk = 'high'
    gate = 'option-gate'
    addLayer(layers, 'ssot', 'adr')
    rationale.push('Ownership/source-of-truth wording maps to SSOT/ADR and high risk.')
  }

  if (has(text, /\b(fix|bug|regression|broken|error|fail|고쳐|버그|회귀|실패|에러)\b/i)) {
    intent = 'fix'
    if (scope === 'unknown') scope = 'code-local'
    if (risk === 'low') risk = 'medium'
    addLayer(layers, 'tdd')
    rationale.push('Bug/fix wording requires TDD consideration.')
  }

  if (has(text, /\b(refactor|cleanup|rename|move|internal|리팩터|정리|이름 변경)\b/i)) {
    if (intent === 'unknown') intent = 'refactor'
    if (scope === 'unknown') scope = 'code-local'
    addLayer(layers, 'tdd')
    rationale.push('Refactor wording maps to local code validation.')
  }

  if (has(text, /\b(investigate|evaluate|assess|plan|review|analy[sz]e|research|검토|평가|계획|분석|조사)\b/i)) {
    if (intent === 'unknown') intent = 'investigation'
    if (scope === 'unknown') scope = 'code-local'
    rationale.push('Investigation/planning wording maps to advisory capture.')
  }

  if (has(text, /\b(doc|docs|readme|comment|copy|typo|text|문서|주석|오타|문구)\b/i)) {
    if (intent === 'unknown') intent = 'docs'
    if (scope === 'unknown') scope = 'trivial'
    rationale.push('Docs/copy wording is trivial unless host-specific policy terms override it.')
  }

  if (has(text, /\b(add|create|implement|change|update|make|만들|추가|구현|변경|수정)\b/i) && intent === 'unknown') {
    intent = 'feature'
    if (scope === 'unknown') scope = 'code-local'
    if (risk === 'low') risk = 'medium'
    rationale.push('Implementation wording defaults to feature/code-local unless stronger scope matched.')
  }

  for (const file of files) {
    if (/\.(md|mdx|txt)$/.test(file)) {
      if (intent === 'unknown') intent = 'docs'
      if (scope === 'unknown') scope = 'trivial'
    } else if (/\.(ts|tsx|js|jsx|py|sh)$/.test(file)) {
      if (scope === 'unknown' || scope === 'trivial') scope = 'code-local'
      if (intent === 'unknown') intent = 'refactor'
      if (risk === 'low') risk = 'medium'
      addLayer(layers, 'tdd')
    }
    if (file.includes('/api/') || file.includes('/ipc') || file.includes('/schema') || file.includes('/config') || file.includes('/hooks/')) {
      scope = 'contract'
      risk = risk === 'high' ? 'high' : 'medium'
      addLayer(layers, 'sdd', 'ssot', 'tdd')
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
      nonNegotiables: nonNegotiables(gate, risk, recordSearch.mode)
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

function appendTelemetry(result: RouteOutput): void {
  const logsDir = join(hostRoot(), '.lazy-harness', 'logs')
  mkdirSync(logsDir, { recursive: true })
  const r = result.route
  const entry = {
    timestamp: new Date().toISOString(),
    source: 'lazy-route',
    schemaVersion: result.schemaVersion,
    messageHash: stableHash(result.message),
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
    validation: r.validation,
    nonNegotiables: r.nonNegotiables,
    warningCount: result.warnings.length
  }
  appendFileSync(telemetryPath('route-decisions.jsonl'), `${JSON.stringify(entry)}\n`, 'utf8')
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
    },
    ratios: total === 0 ? {} : {
      optionGate: optionGate / total,
      highRisk: highRisk / total,
      lowConfidence: lowConfidence / total,
      candidateCapture: candidate / total,
      canonicalCapture: canonical / total
    },
    recommendations
  }
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
    '',
    '## Counts',
    `- scope: ${JSON.stringify(summary.counts.scope)}`,
    `- risk: ${JSON.stringify(summary.counts.risk)}`,
    `- gate: ${JSON.stringify(summary.counts.gateMode)}`,
    `- record capture: ${JSON.stringify(summary.counts.recordCaptureMode)}`,
    '',
    '## Recommendations',
    ...(summary.recommendations.length ? summary.recommendations.map((item: string) => `- ${item}`) : ['- No recommendations.'])
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
    if (!args.message.trim()) throw new Error('Missing --message')
    const result = classify(args)
    if (args.log) appendTelemetry(result)
    if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
    else console.log(toMarkdown(result))
  } catch (error) {
    console.error(`task-router: ${(error as Error).message}`)
    printHelp()
    process.exit(2)
  }
}

main()
