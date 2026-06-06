#!/usr/bin/env bun
/**
 * operational-state.ts — explicit/manual Operational State Packet prototype.
 *
 * Non-canonical. Does not store or emit raw --message text. Does not run from
 * message.received hooks by default.
 */
import { existsSync, readFileSync } from 'node:fs'
import * as path from 'node:path'
import { createHash } from 'node:crypto'
import { buildContextIndex, type ContextIndex } from './context-index.ts'

type Format = 'json' | 'md'
type TaskKind = 'unknown' | 'implementation' | 'planning' | 'validation' | 'recording'
type Risk = 'low' | 'medium' | 'high' | 'unknown'
type PointerKind = 'record' | 'plan' | 'project-profile' | 'source-file' | 'test' | 'schema' | 'fixture' | 'graph' | 'template' | 'directory' | 'generated-index'

interface Args {
  root: string
  message: string
  format: Format
  indexPath: string
}

interface Pointer {
  path: string
  kind: PointerKind
  reason: string
  featureIds?: string[]
}

interface CapabilityPointer {
  id: string
  kind: string
  level: string
  sourceRecord: string
  reason: string
  checklistPath?: string
}

interface OperationalStatePacket {
  schemaVersion: '1.0'
  generatedAt: string
  source: {
    root: string
    method: 'operational-state-v1'
    canonicalInputs: string[]
    generatedInputs: string[]
    fallbackNeeded: boolean
  }
  taskKind: TaskKind
  requiredReads: Pointer[]
  recommendedReads: Pointer[]
  capabilities: CapabilityPointer[]
  evidence: Pointer[]
  risk: Risk
  notes: string[]
}

function usage(): never {
  console.error(`Usage: operational-state [options]

Options:
  --root DIR              Host root (default: LAZY_HOST_ROOT or cwd)
  --message TEXT          Optional request text used only for coarse classification; never emitted raw
  --format json|md        Output format (default json)
  --index PATH            Generated context-index path (default .lazy-harness/generated/context-index.json)
  --help                  Show this help

Examples:
  .lazy-harness/bin/lazy operational-state --message="validate evidence" --format=json
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
  const root = process.env.LAZY_HOST_ROOT || process.cwd()
  const args: Args = { root, message: '', format: 'json', indexPath: '' }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    let parsed = valueFor(argv, i, '--root')
    if (parsed.value !== null) { args.root = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--message')
    if (parsed.value !== null) { args.message = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--format')
    if (parsed.value !== null) {
      if (!['json', 'md', 'markdown'].includes(parsed.value)) usage()
      args.format = parsed.value === 'markdown' ? 'md' : parsed.value as Format
      i += parsed.consumed
      continue
    }
    parsed = valueFor(argv, i, '--index')
    if (parsed.value !== null) { args.indexPath = parsed.value; i += parsed.consumed; continue }
    if (arg === '--help' || arg === '-h') usage()
    usage()
  }
  args.root = path.resolve(args.root)
  if (!args.indexPath) args.indexPath = path.join(args.root, '.lazy-harness', 'generated', 'context-index.json')
  else args.indexPath = path.resolve(args.root, args.indexPath)
  return args
}

function rel(root: string, p: string): string {
  const absolute = path.resolve(root, p)
  const relative = path.relative(root, absolute).replace(/\\/g, '/')
  return relative || '.'
}

function existsRel(root: string, p: string): boolean {
  return existsSync(path.join(root, p))
}

function unique<T>(items: T[], key: (item: T) => string): T[] {
  const seen = new Set<string>()
  const out: T[] = []
  for (const item of items) {
    const k = key(item)
    if (seen.has(k)) continue
    seen.add(k)
    out.push(item)
  }
  return out
}

function classifyTask(message: string): TaskKind {
  const m = message.toLowerCase()
  if (/\b(test|validate|validation|verify|doctor|lint|evidence|benchmark|measure|검증)\b/.test(m)) return 'validation'
  if (/\b(plan|roadmap|design|proposal|phase|계획)\b/.test(m)) return 'planning'
  if (/\b(record|document|docs|capsule|write[- ]?up|기록)\b/.test(m)) return 'recording'
  if (/\b(implement|fix|build|change|edit|refactor|코드|수정|구현)\b/.test(m)) return 'implementation'
  return 'unknown'
}

function classifyRisk(message: string, taskKind: TaskKind): Risk {
  const m = message.toLowerCase()
  if (/\b(delete|drop|force|migration|database|secret|token|credential|security|release|deploy|production|db|삭제|배포)\b/.test(m)) return 'high'
  if (taskKind === 'implementation' || taskKind === 'validation' || taskKind === 'recording') return 'medium'
  if (taskKind === 'planning') return 'low'
  return 'unknown'
}

function readRegistry(root: string): any[] {
  const p = path.join(root, '.lazy-harness', 'ssot', 'capabilities.json')
  if (!existsSync(p)) return []
  try {
    const parsed = JSON.parse(readFileSync(p, 'utf8'))
    return Array.isArray(parsed.capabilities) ? parsed.capabilities : []
  } catch {
    return []
  }
}

function capabilityIntent(taskKind: TaskKind): string {
  if (taskKind === 'validation') return 'making_validation_claims'
  if (taskKind === 'recording') return 'recording_reproducible_evidence'
  if (taskKind === 'planning') return 'finding_project_capabilities'
  return ''
}

function matchingCapabilities(root: string, taskKind: TaskKind): CapabilityPointer[] {
  const intent = capabilityIntent(taskKind)
  const caps = readRegistry(root)
  const matches = caps.filter((cap) => {
    const applies = Array.isArray(cap.appliesWhen) ? cap.appliesWhen : []
    return intent ? applies.includes(intent) : false
  })
  return matches.map((cap) => ({
    id: String(cap.id || ''),
    kind: String(cap.kind || ''),
    level: String(cap.level || ''),
    sourceRecord: String(cap.sourceRecord || ''),
    reason: `Capability applies to ${intent}. Review sourceRecord before use.`,
    ...(typeof cap.checklistPath === 'string' ? { checklistPath: cap.checklistPath } : {}),
  })).filter((cap) => cap.id && cap.sourceRecord)
}

function pointer(pathValue: string, kind: PointerKind, reason: string, featureIds: string[] = []): Pointer {
  return { path: pathValue, kind, reason, ...(featureIds.length ? { featureIds } : {}) }
}

function findRecordFeatureIds(index: ContextIndex, recordPath: string): string[] {
  return index.records.find((record) => record.recordPath === recordPath)?.projectProfileFeatureIds || []
}

function buildReads(root: string, index: ContextIndex, taskKind: TaskKind): { requiredReads: Pointer[]; recommendedReads: Pointer[]; evidence: Pointer[] } {
  const required: Pointer[] = [
    pointer('.lazy-harness/spec/platform/operational-state-packet.md', 'record', 'Confirm explicit/manual Operational State Packet constraints before relying on output.', findRecordFeatureIds(index, '.lazy-harness/spec/platform/operational-state-packet.md')),
    pointer('.lazy-harness/spec/platform/context-delivery-contract.md', 'record', 'Confirm Context Delivery non-canonical and required-read semantics.', findRecordFeatureIds(index, '.lazy-harness/spec/platform/context-delivery-contract.md')),
  ].filter((p) => existsRel(root, p.path))

  const recommended: Pointer[] = [
    pointer('.lazy-harness/project/feature-navigation.xml', 'project-profile', 'Source/host feature navigation map for projectProfile retrieval hints.'),
    pointer('.lazy-harness/project/context-tiers.yaml', 'project-profile', 'Advisory context tier pointers, if present.'),
    pointer('.lazy-harness/ssot/capabilities.json', 'record', 'Capability registry for recommend/default/warn/block affordances.'),
  ].filter((p) => existsRel(root, p.path))

  if (taskKind === 'planning') {
    recommended.push(pointer('.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md', 'plan', 'Active rollout plan and acceptance criteria.', findRecordFeatureIds(index, '.lazy-harness/plans/prompt-runtime-compression-implementation-plan.md')))
  }
  if (taskKind === 'validation' || taskKind === 'recording') {
    recommended.push(pointer('.lazy-harness/spec/platform/evidence-capsule-standard.md', 'record', 'Evidence capsule checklist for non-trivial validation claims.', findRecordFeatureIds(index, '.lazy-harness/spec/platform/evidence-capsule-standard.md')))
    recommended.push(pointer('.lazy-harness/tests/evidence-capsule-standard.md', 'test', 'Regression record for evidence capsule behavior.', findRecordFeatureIds(index, '.lazy-harness/tests/evidence-capsule-standard.md')))
  }
  if (taskKind === 'implementation') {
    recommended.push(pointer('.lazy-harness/spec/platform/project-profile.md', 'record', 'Project Profile retrieval/feature-navigation contract.', findRecordFeatureIds(index, '.lazy-harness/spec/platform/project-profile.md')))
  }

  const evidence: Pointer[] = [
    pointer('.lazy-harness/evidence/README.md', 'directory', 'Evidence capsule storage and privacy guidance.'),
    pointer('.lazy-harness/templates/evidence-capsule.md', 'template', 'Manual evidence capsule template/checklist.'),
  ].filter((p) => existsRel(root, p.path))

  return {
    requiredReads: unique(required, (p) => p.path),
    recommendedReads: unique(recommended.filter((p) => existsRel(root, p.path)), (p) => p.path),
    evidence: unique(evidence, (p) => p.path),
  }
}

export function buildOperationalState(root: string, message: string, indexPath = path.join(root, '.lazy-harness', 'generated', 'context-index.json')): OperationalStatePacket {
  const index = buildContextIndex(root)
  const generatedInputs = existsSync(indexPath) ? [rel(root, indexPath)] : []
  const fallbackNeeded = generatedInputs.length === 0
  const taskKind = classifyTask(message)
  const risk = classifyRisk(message, taskKind)
  const reads = buildReads(root, index, taskKind)
  const capabilities = matchingCapabilities(root, taskKind)
  const notes = [
    'advisory-only: read canonical records/source before acting',
    'manual-only: not wired into message.received or response hooks by default',
    'raw-message-omitted: --message is used only for coarse taskKind/risk heuristics',
  ]
  if (fallbackNeeded) notes.push('fallback-needed: .lazy-harness/generated/context-index.json missing; used source-scan context-index builder in memory')
  if (message.trim()) {
    const fingerprint = createHash('sha256').update(message).digest('hex').slice(0, 12)
    notes.push(`message-fingerprint: sha256:${fingerprint}`)
  }
  return {
    schemaVersion: '1.0',
    generatedAt: '1970-01-01T00:00:00.000Z',
    source: {
      root,
      method: 'operational-state-v1',
      canonicalInputs: index.source.canonicalInputs,
      generatedInputs,
      fallbackNeeded,
    },
    taskKind,
    requiredReads: reads.requiredReads,
    recommendedReads: reads.recommendedReads,
    capabilities,
    evidence: reads.evidence,
    risk,
    notes,
  }
}

function renderMarkdown(packet: OperationalStatePacket): string {
  const lines = [
    '# Operational State Packet',
    '',
    `- taskKind: ${packet.taskKind}`,
    `- risk: ${packet.risk}`,
    `- fallbackNeeded: ${packet.source.fallbackNeeded}`,
    `- canonicalInputs: ${packet.source.canonicalInputs.length}`,
    `- generatedInputs: ${packet.source.generatedInputs.length}`,
  ]
  if (packet.requiredReads.length) {
    lines.push('', '## Required reads')
    for (const item of packet.requiredReads) lines.push(`- ${item.path} — ${item.reason}`)
  }
  if (packet.recommendedReads.length) {
    lines.push('', '## Recommended reads')
    for (const item of packet.recommendedReads) lines.push(`- ${item.path} — ${item.reason}`)
  }
  if (packet.capabilities.length) {
    lines.push('', '## Capabilities')
    for (const item of packet.capabilities) lines.push(`- ${item.id} (${item.kind}/${item.level}) — ${item.reason}`)
  }
  if (packet.evidence.length) {
    lines.push('', '## Evidence pointers')
    for (const item of packet.evidence) lines.push(`- ${item.path} — ${item.reason}`)
  }
  if (packet.notes.length) {
    lines.push('', '## Notes')
    for (const note of packet.notes) lines.push(`- ${note}`)
  }
  return `${lines.join('\n')}\n`
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const packet = buildOperationalState(args.root, args.message, args.indexPath)
  if (args.format === 'md') process.stdout.write(renderMarkdown(packet))
  else process.stdout.write(`${JSON.stringify(packet, null, 2)}\n`)
}

if (import.meta.main) main()
