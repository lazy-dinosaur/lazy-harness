#!/usr/bin/env bun
/**
 * record-decision-broker.ts — deterministic post-turn Record Decision Packet generator.
 *
 * This is an explicit CLI tool only. It does not integrate with response.completed,
 * does not mutate records, and does not write journals. It converts safe evidence
 * flags into the Phase 8 RecordDecisionPacket contract.
 */
import * as path from 'node:path'

type Format = 'json' | 'md'
type Disposition = 'record-updated' | 'candidate-needed' | 'no-record-needed' | 'option-gate-needed' | 'deferred'
type Trigger =
  | 'new-alias-found'
  | 'user-correction'
  | 'source-change'
  | 'test-change'
  | 'contract-change'
  | 'behavior-change'
  | 'architecture-decision'
  | 'response-audit-advisory'
  | 'validation-only'
  | 'explanation-only'
  | 'ambiguous-placement'
  | 'user-deferred'
type EvidenceKind =
  | 'user-confirmation'
  | 'user-correction'
  | 'changed-file'
  | 'changed-record'
  | 'changed-test'
  | 'context-delivery-required-read'
  | 'response-audit-advisory'
  | 'tool-call'
  | 'validation'
  | 'no-op'
type RecordAction = 'update' | 'create' | 'append' | 'candidate' | 'none' | 'ask-option-gate'
type Layer = 'DDD' | 'SDD' | 'BDD' | 'TDD' | 'ADR' | 'SSOT' | 'Planning' | 'Knowledge'

interface Args {
  root: string
  message: string
  format: Format
  changedFiles: string[]
  changedRecords: string[]
  changedTests: string[]
  requiredReads: string[]
  toolCalls: string[]
  validations: string[]
  userConfirmations: string[]
  userCorrections: string[]
  responseAuditAdvisories: string[]
  readOnly: boolean
  validationOnly: boolean
  ambiguous: boolean
  deferred: boolean
  recordUpdated: boolean
  noRecordNeeded: boolean
}

interface Evidence {
  kind: EvidenceKind
  summary: string
  path?: string
  toolName?: string
  hash?: string
  confidence: number
}

interface RecommendedRecord {
  path?: string
  layer?: Layer
  action: RecordAction
  reason: string
  confidence: number
}

interface RecordDecision {
  disposition: Disposition
  confidence: number
  trigger: Trigger
  summary: string
  evidence: Evidence[]
  recommendedRecords: RecommendedRecord[]
  instructions: string[]
}

interface RecordDecisionPacket {
  schemaVersion: '1.0'
  generatedAt: string
  recordDecision: RecordDecision
  notes?: string[]
}

function usage(): never {
  console.error(`Usage: record-decision-broker [options]

Options:
  --root DIR                         Host root (default: LAZY_HOST_ROOT or cwd)
  --message TEXT                     Compact current request/turn summary
  --format json|md                   Output format (default json)
  --changed-file PATH                Source/config file changed (repeatable)
  --changed-record PATH              .lazy-harness record/graph file changed (repeatable)
  --changed-test PATH                Test file changed (repeatable)
  --required-read PATH               Context Delivery requiredRead path observed (repeatable)
  --tool-call NAME                   Tool name observed (repeatable)
  --validation TEXT                  Validation evidence summary (repeatable)
  --user-confirmation TEXT           Confirmed user fact/choice (repeatable)
  --user-correction TEXT             User correction/source-of-truth update (repeatable)
  --response-audit-advisory TEXT     Response audit advisory evidence (repeatable)
  --read-only                        Turn was read-only/inspection-only
  --validation-only                  Turn only ran validation
  --ambiguous                        Layer/path/meaning is ambiguous; option gate needed
  --deferred                         User deferred record/action to later
  --record-updated                   Canonical record was already updated
  --no-record-needed                 Force no-record-needed when evidence is intentionally clean
  --help                             Show this help

Examples:
  .lazy-harness/bin/lazy record-decision --message="상태 요약" --read-only --format=md
  .lazy-harness/bin/lazy record-decision --message="예약시트는 reservation sheet" --user-confirmation="예약시트 alias confirmed"
  .lazy-harness/bin/lazy record-decision --message="layer unclear" --changed-file=src/app.ts --ambiguous
`)
  process.exit(2)
}

function valueFor(argv: string[], index: number, flag: string): { value: string | null; consumed: number } {
  const current = argv[index]
  if (current === flag) {
    const value = argv[index + 1]
    if (!value) usage()
    return { value, consumed: 1 }
  }
  const prefix = `${flag}=`
  if (current.startsWith(prefix)) {
    const value = current.slice(prefix.length)
    if (!value) usage()
    return { value, consumed: 0 }
  }
  return { value: null, consumed: 0 }
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    root: process.env.LAZY_HOST_ROOT || process.cwd(),
    message: '',
    format: 'json',
    changedFiles: [],
    changedRecords: [],
    changedTests: [],
    requiredReads: [],
    toolCalls: [],
    validations: [],
    userConfirmations: [],
    userCorrections: [],
    responseAuditAdvisories: [],
    readOnly: false,
    validationOnly: false,
    ambiguous: false,
    deferred: false,
    recordUpdated: false,
    noRecordNeeded: false,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    let parsed = valueFor(argv, i, '--root')
    if (parsed.value !== null) { args.root = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--message')
    if (parsed.value !== null) { args.message = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--format')
    if (parsed.value !== null) {
      if (parsed.value !== 'json' && parsed.value !== 'md' && parsed.value !== 'markdown') usage()
      args.format = parsed.value === 'markdown' ? 'md' : parsed.value
      i += parsed.consumed
      continue
    }
    parsed = valueFor(argv, i, '--changed-file')
    if (parsed.value !== null) { args.changedFiles.push(normalizePath(args.root, parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--changed-record')
    if (parsed.value !== null) { args.changedRecords.push(normalizePath(args.root, parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--changed-test')
    if (parsed.value !== null) { args.changedTests.push(normalizePath(args.root, parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--required-read')
    if (parsed.value !== null) { args.requiredReads.push(normalizePath(args.root, parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--tool-call')
    if (parsed.value !== null) { args.toolCalls.push(compact(parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--validation')
    if (parsed.value !== null) { args.validations.push(compact(parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--user-confirmation')
    if (parsed.value !== null) { args.userConfirmations.push(compact(parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--user-correction')
    if (parsed.value !== null) { args.userCorrections.push(compact(parsed.value)); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--response-audit-advisory')
    if (parsed.value !== null) { args.responseAuditAdvisories.push(compact(parsed.value)); i += parsed.consumed; continue }
    if (arg === '--read-only') { args.readOnly = true; continue }
    if (arg === '--validation-only') { args.validationOnly = true; continue }
    if (arg === '--ambiguous') { args.ambiguous = true; continue }
    if (arg === '--deferred') { args.deferred = true; continue }
    if (arg === '--record-updated') { args.recordUpdated = true; continue }
    if (arg === '--no-record-needed') { args.noRecordNeeded = true; continue }
    if (arg === '--help' || arg === '-h') usage()
    usage()
  }
  args.root = path.resolve(args.root)
  return args
}

function compact(value: string, max = 180): string {
  const single = String(value || '').replace(/\s+/g, ' ').trim()
  return single.length > max ? `${single.slice(0, max - 1)}…` : single
}

function normalizePath(root: string, value: string): string {
  const raw = String(value || '').trim()
  if (!raw) return raw
  const absolute = path.isAbsolute(raw) ? raw : path.resolve(root, raw)
  const relative = path.relative(root, absolute).replace(/\\/g, '/')
  if (!relative || relative.startsWith('..')) return raw.replace(/\\/g, '/')
  return relative
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values.map((v) => compact(v)).filter(Boolean)))
}

function inferLayer(recordPath: string): Layer | undefined {
  const normalized = recordPath.replace(/\\/g, '/')
  if (normalized.includes('/domain/')) return 'DDD'
  if (normalized.includes('/spec/')) return 'SDD'
  if (normalized.includes('/behavior/')) return 'BDD'
  if (normalized.includes('/tests/') || normalized.includes('/regression/')) return 'TDD'
  if (normalized.includes('/decisions/')) return 'ADR'
  if (normalized.includes('/ssot/')) return 'SSOT'
  if (normalized.includes('/planning/') || normalized.includes('/plans/')) return 'Planning'
  if (normalized.includes('/knowledge/')) return 'Knowledge'
  return undefined
}

function inferChangeTrigger(args: Args): Trigger {
  const firstRecord = args.changedRecords[0] || ''
  const firstFile = args.changedFiles[0] || ''
  const combined = `${firstRecord} ${firstFile}`
  if (/decisions\//.test(combined)) return 'architecture-decision'
  if (/tests\//.test(combined) || args.changedTests.length) return 'test-change'
  if (/spec\//.test(combined) || /schema|contract/i.test(combined)) return 'contract-change'
  if (/behavior\//.test(combined) || /component|ui|screen|flow|route/i.test(combined)) return 'behavior-change'
  return 'source-change'
}

function baseEvidence(args: Args): Evidence[] {
  const evidence: Evidence[] = []
  for (const summary of args.userConfirmations) evidence.push({ kind: 'user-confirmation', summary: `User confirmation: ${summary}`, confidence: 0.9 })
  for (const summary of args.userCorrections) evidence.push({ kind: 'user-correction', summary: `User correction: ${summary}`, confidence: 0.92 })
  for (const path of args.changedFiles) evidence.push({ kind: 'changed-file', path, summary: `Changed file: ${path}`, confidence: 0.78 })
  for (const path of args.changedRecords) evidence.push({ kind: 'changed-record', path, summary: `Changed record: ${path}`, confidence: 0.9 })
  for (const path of args.changedTests) evidence.push({ kind: 'changed-test', path, summary: `Changed test: ${path}`, confidence: 0.84 })
  for (const path of args.requiredReads) evidence.push({ kind: 'context-delivery-required-read', path, summary: `Required-read evidence: ${path}`, confidence: 0.74 })
  for (const toolName of args.toolCalls) evidence.push({ kind: 'tool-call', toolName, summary: `Tool call evidence: ${toolName}`, confidence: 0.62 })
  for (const summary of args.validations) evidence.push({ kind: 'validation', summary: `Validation: ${summary}`, confidence: 0.8 })
  for (const summary of args.responseAuditAdvisories) evidence.push({ kind: 'response-audit-advisory', summary: `Response audit advisory: ${summary}`, confidence: 0.76 })
  if (!evidence.length) evidence.push({ kind: 'no-op', summary: 'No durable record evidence was provided.', confidence: 0.8 })
  return evidence
}

function chooseDisposition(args: Args): { disposition: Disposition; trigger: Trigger; confidence: number } {
  if (args.deferred) return { disposition: 'deferred', trigger: 'user-deferred', confidence: 0.86 }
  if (args.recordUpdated || args.changedRecords.length) return { disposition: 'record-updated', trigger: inferChangeTrigger(args), confidence: 0.88 }
  if (args.ambiguous) return { disposition: 'option-gate-needed', trigger: 'ambiguous-placement', confidence: 0.66 }
  if (args.userCorrections.length) return { disposition: 'candidate-needed', trigger: 'user-correction', confidence: 0.84 }
  if (args.userConfirmations.length) return { disposition: 'candidate-needed', trigger: 'new-alias-found', confidence: 0.82 }
  if (args.responseAuditAdvisories.length) return { disposition: 'candidate-needed', trigger: 'response-audit-advisory', confidence: 0.72 }
  if (args.changedTests.length) return { disposition: 'candidate-needed', trigger: 'test-change', confidence: 0.72 }
  if (args.changedFiles.length) return { disposition: 'candidate-needed', trigger: inferChangeTrigger(args), confidence: 0.7 }
  if (args.validationOnly || args.validations.length) return { disposition: 'no-record-needed', trigger: 'validation-only', confidence: 0.86 }
  if (args.readOnly || args.noRecordNeeded || looksExplanationOnly(args.message)) return { disposition: 'no-record-needed', trigger: 'explanation-only', confidence: 0.84 }
  return { disposition: 'no-record-needed', trigger: 'explanation-only', confidence: 0.7 }
}

function looksExplanationOnly(message: string): boolean {
  return /(status|summary|explain|what is|차이|설명|요약|상태|뭐야|무엇|왜)/i.test(message || '')
}

function recommendedRecords(args: Args, disposition: Disposition, trigger: Trigger): RecommendedRecord[] {
  if (disposition === 'no-record-needed') {
    return [{ action: 'none', reason: 'No durable record action is justified by the supplied evidence.', confidence: 0.86 }]
  }
  if (disposition === 'option-gate-needed') {
    return [{ action: 'ask-option-gate', reason: 'Canonical layer/path/meaning is ambiguous; ask 3-5 options before mutating records.', confidence: 0.78 }]
  }
  if (disposition === 'deferred') {
    return [{ path: '.lazy-harness/planning/native-context-broker-implementation-plan.md', layer: 'Planning', action: 'append', reason: 'User deferred the next action; capture the pause or backlog pointer in planning when durable.', confidence: 0.72 }]
  }
  if (disposition === 'record-updated') {
    return unique(args.changedRecords).map((recordPath) => ({ path: recordPath, layer: inferLayer(recordPath), action: 'update', reason: 'Canonical record was already updated in this turn.', confidence: 0.9 }))
  }
  const recs: RecommendedRecord[] = []
  if (trigger === 'user-correction') {
    recs.push({ path: '.lazy-harness/ssot/project-identity.md', layer: 'SSOT', action: 'update', reason: 'User correction may change source-of-truth, ownership, or project identity.', confidence: 0.76 })
  }
  if (trigger === 'new-alias-found' || trigger === 'behavior-change') {
    recs.push({ path: '.lazy-harness/behavior/', layer: 'BDD', action: 'candidate', reason: 'User-facing alias or behavior may need a BDD record update.', confidence: 0.72 })
  }
  if (trigger === 'contract-change') {
    recs.push({ path: '.lazy-harness/spec/', layer: 'SDD', action: 'candidate', reason: 'Contract/schema evidence may need SDD capture.', confidence: 0.72 })
  }
  if (trigger === 'test-change') {
    recs.push({ path: '.lazy-harness/tests/', layer: 'TDD', action: 'candidate', reason: 'Test/regression evidence may need TDD capture.', confidence: 0.72 })
  }
  if (trigger === 'architecture-decision') {
    recs.push({ path: '.lazy-harness/decisions/', layer: 'ADR', action: 'candidate', reason: 'Architecture/trade-off evidence may need ADR capture.', confidence: 0.72 })
  }
  recs.push({ path: '.lazy-harness/knowledge/candidates.jsonl', layer: 'Knowledge', action: 'candidate', reason: 'Evidence is useful but should not become a blind canonical write.', confidence: 0.7 })
  return recs
}

function summaryFor(args: Args, disposition: Disposition, trigger: Trigger): string {
  if (disposition === 'no-record-needed') return 'Turn evidence indicates no durable record action is needed.'
  if (disposition === 'option-gate-needed') return 'Turn evidence suggests a record may be needed, but layer/path/meaning is ambiguous.'
  if (disposition === 'deferred') return 'User deferred record/action follow-up to a later turn.'
  if (disposition === 'record-updated') return 'Durable record update evidence is already present in this turn.'
  if (trigger === 'new-alias-found') return 'User confirmation suggests a new alias or surface term may need durable capture.'
  if (trigger === 'user-correction') return 'User correction suggests source-of-truth or ownership records may need durable capture.'
  return 'Turn evidence suggests candidate record capture may be needed, but not an automatic canonical write.'
}

function instructionsFor(disposition: Disposition): string[] {
  if (disposition === 'no-record-needed') return ['Keep response.completed silent.', 'Do not create or update records from this packet.']
  if (disposition === 'option-gate-needed') return ['Ask a 3-5 option gate before mutating records.', 'Do not write automatically from this packet alone.']
  if (disposition === 'record-updated') return ['Verify the changed record path is canonical.', 'No additional record action is needed unless validation reveals a gap.']
  if (disposition === 'deferred') return ['Respect the user deferral boundary.', 'Capture a planning pointer only when durable backlog is useful.']
  return ['Append candidate evidence or ask before canonical record write.', 'Do not write automatically from this packet alone.']
}

function buildPacket(args: Args): RecordDecisionPacket {
  const choice = chooseDisposition(args)
  const evidence = baseEvidence(args)
  return {
    schemaVersion: '1.0',
    generatedAt: new Date().toISOString(),
    recordDecision: {
      disposition: choice.disposition,
      confidence: choice.confidence,
      trigger: choice.trigger,
      summary: summaryFor(args, choice.disposition, choice.trigger),
      evidence,
      recommendedRecords: recommendedRecords(args, choice.disposition, choice.trigger),
      instructions: instructionsFor(choice.disposition),
    },
    notes: [
      'generator=record-decision-broker.ts',
      'mutationAllowed=false',
      'runtimeMutationIntegration=false',
      'runtimeDefaultOutput=false',
    ],
  }
}

function renderMarkdown(packet: RecordDecisionPacket): string {
  const d = packet.recordDecision
  const lines = [
    '# Record Decision Packet',
    '',
    `- Disposition: ${d.disposition}`,
    `- Trigger: ${d.trigger}`,
    `- Confidence: ${d.confidence.toFixed(2)}`,
    `- Summary: ${d.summary}`,
    '',
    '## Evidence',
  ]
  for (const item of d.evidence) {
    const pathPart = item.path ? ` (${item.path})` : ''
    const toolPart = item.toolName ? ` [${item.toolName}]` : ''
    lines.push(`- ${item.kind}${pathPart}${toolPart}: ${item.summary} (${item.confidence.toFixed(2)})`)
  }
  lines.push('', '## Recommended records')
  for (const rec of d.recommendedRecords) {
    const pathPart = rec.path ? ` ${rec.path}` : ''
    const layerPart = rec.layer ? ` [${rec.layer}]` : ''
    lines.push(`- ${rec.action}${pathPart}${layerPart}: ${rec.reason} (${rec.confidence.toFixed(2)})`)
  }
  lines.push('', '## Instructions')
  for (const instruction of d.instructions) lines.push(`- ${instruction}`)
  lines.push('')
  return lines.join('\n')
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const packet = buildPacket(args)
  if (args.format === 'md') process.stdout.write(renderMarkdown(packet))
  else process.stdout.write(`${JSON.stringify(packet, null, 2)}\n`)
}

main()
