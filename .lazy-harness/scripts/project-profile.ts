#!/usr/bin/env bun
/**
 * Project Profile (SDD: spec/platform/project-profile.md)
 *
 * Safe-by-default profile bootstrap. Inspect and plan are read-only. Apply with
 * --confirm creates only needs-interview skeleton records, never silent
 * architecture decisions.
 */
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { appendJsonlStable, type JsonlAppendStatus } from './runtime-paths.ts'

type Mode = 'inspect' | 'plan' | 'apply' | 'interview' | 'interview-v2' | 'queue-v2' | 'promote-v2' | 'fill'
type Format = 'json' | 'md'
type ArtifactStatus = 'present' | 'missing'
type QueueStatus = 'pending' | 'accepted' | 'rejected' | 'promoted' | 'superseded'
type QueuePrimaryRoute = 'facts' | 'expectations' | 'contracts' | 'validation' | 'decisions' | 'ownership' | 'source-links' | 'policies' | 'event-ready-metadata' | 'queue-only'
type QueueFacet = 'DDD' | 'BDD' | 'SDD' | 'TDD' | 'ADR' | 'SSOT' | 'Policy' | 'Project' | 'Source' | 'Evidence'
type QueueSourceKind = 'question-group' | 'project-map-seed' | 'policy-candidate' | 'unresolved-ambiguity' | 'proposed-write' | 'update-loop'
type QueuePromotionKind = 'record' | 'project-map-branch' | 'rulebook' | 'capability-binding' | 'candidate-row' | 'update-loop-event' | 'queue-only'

interface Args {
  mode: Mode
  format: Format
  root: string
  dryRun: boolean
  confirm: boolean
  answers?: string
  item?: string
}

interface RequiredArtifact {
  path: string
  label: string
  layer: 'project' | 'tests'
  status: ArtifactStatus
  bytes: number | null
  mtime: string | null
}

interface ProjectProfileInspectResult {
  ok: true
  mode: 'project-profile.inspect'
  schemaVersion: '1.0'
  root: string
  inspectedAt: string
  requiredArtifacts: RequiredArtifact[]
  documentIngestion: {
    ledgerPath: string
    ledgerStatus: ArtifactStatus
    candidatesPath: string
    candidatesStatus: ArtifactStatus
    shouldOfferIngestion: boolean
    reason: string
  }
  summary: {
    present: number
    missing: number
    artifactsComplete: boolean
    needsInterviewFields: number
    confirmedFields: number
    answersComplete: boolean
    /** @deprecated Use artifactsComplete and answersComplete. Kept for older callers. */
    complete: boolean
  }
  optionGate: {
    prompt: string
    options: string[]
    recommended: string
  }
  nextActions: string[]
}

interface ProposedWrite {
  path: string
  action: 'create' | 'skip-existing'
  kind: 'project-profile-skeleton'
  content: string
  summary: string
}

interface PlanResult {
  ok: true
  mode: 'project-profile.plan' | 'project-profile.apply-dry-run' | 'project-profile.apply'
  schemaVersion: '1.0'
  root: string
  generatedAt: string
  dryRun: boolean
  inspect: ProjectProfileInspectResult
  proposedWrites: ProposedWrite[]
  appliedWrites?: Array<{ path: string; action: 'written' | 'skipped'; summary: string }>
  warnings: string[]
  optionGate: {
    prompt: string
    options: string[]
    recommended: string
  }
}

interface InterviewQuestion {
  id: string
  sourcePath: string
  target: string
  section: string
  prompt: string
  options: string[]
  recommended: string
}

interface InterviewResult {
  ok: true
  mode: 'project-profile.interview' | 'project-profile.interview-apply'
  schemaVersion: '1.0'
  root: string
  generatedAt: string
  dryRun: boolean
  inspect: ProjectProfileInspectResult
  questions: InterviewQuestion[]
  appliedWrites?: Array<{ path: string; action: 'written' | 'skipped'; summary: string }>
  warnings: string[]
  nextActions: string[]
}

interface ProfileAnswer {
  target: string
  value: string
  source?: string
}

interface FillProposedWrite {
  path: string
  action: 'update'
  matchedTargets: string[]
  content: string
  summary: string
}

interface FillResult {
  ok: true
  mode: 'project-profile.fill' | 'project-profile.fill-dry-run'
  schemaVersion: '1.0'
  root: string
  generatedAt: string
  dryRun: boolean
  answersPath: string
  answers: ProfileAnswer[]
  proposedWrites: FillProposedWrite[]
  appliedWrites?: Array<{ path: string; action: 'written' | 'skipped'; summary: string }>
  unmatchedAnswers: ProfileAnswer[]
  warnings: string[]
}

interface ProjectProfileInterviewV2Packet {
  schemaVersion: 'project-profile-interview-v2/v1'
  mode: 'interview-v2'
  root: string
  generatedAt: string
  adapterBoundary: {
    primary: 'pi'
    compatibility: ['omp']
    core: string
  }
  writes: {
    dryRun: true
    confirmedOnly: true
    noSilentDefaults: true
  }
  inspectContext: {
    schemaVersion: ProjectProfileInspectResult['schemaVersion']
    summary: ProjectProfileInspectResult['summary']
    requiredArtifacts: Array<Pick<RequiredArtifact, 'path' | 'label' | 'layer' | 'status'>>
    documentIngestion: ProjectProfileInspectResult['documentIngestion']
  }
  questionGroups: Array<{
    id: string
    title: string
    dimensions: string[]
  }>
  projectMapSeeds: Array<{
    id: string
    title: string
    primary: string
    facets: string[]
    status: 'draft'
    scope: 'host-project'
    cluster: {
      role: 'anchor'
      anchorId: string
      branchOf: null
      branches: Array<{ id: string; primary: string; facets: string[] }>
      edges: Array<{ from: string; to: string; relation: string }>
    }
    canonicalRecords: string[]
  }>
  policyCandidates: Array<{
    id: string
    dimension: string
    sourceQuestionGroup: string
    confirmed: false
    stages: Array<{ stage: string; level: 'discover' | 'recommend'; behavior: string }>
  }>
  unresolvedAmbiguities: Array<{
    id: string
    question: string
    options: string[]
  }>
  proposedWrites: Array<{ path: string; requiresConfirmation: true }>
  updateLoop: {
    schemaVersion: 'project-map-update-event/v1'
    eventType: 'project-profile-refresh'
    source: 'project-profile'
    target: {
      anchorId: string
      branch: string
      nodeId: string
      primary: string
      facets: string[]
    }
    transition: {
      from: 'observation'
      to: 'candidate'
      requiresConfirmation: true
      canonicalRecords: []
      candidateStore: '.lazy-harness/knowledge/candidates.jsonl'
    }
    evidence: Array<{ kind: 'project-profile'; path: string; summary: string; redaction: 'compact' }>
    effects: Array<{ action: 'append-candidate'; path: '.lazy-harness/knowledge/candidates.jsonl' }>
  }
  warnings: string[]
}

interface ProjectProfileQueueItem {
  id: string
  status: QueueStatus
  primaryRoute: QueuePrimaryRoute
  facets: QueueFacet[]
  relatedRoutes: QueuePrimaryRoute[]
  source: {
    kind: QueueSourceKind
    id: string
  }
  summary: string
  evidence: Array<{ kind: string; path?: string; summary: string }>
  promotionTarget: {
    kind: QueuePromotionKind
    path?: string
    requiresConfirmation: true
  }
  promotedAt?: string
  promotedTo?: string[]
  promotionEffects?: ProjectProfilePromotionTargetEffect[]
}

interface ProjectProfileQueueV1 {
  ok: true
  mode: 'project-profile.queue-v2' | 'project-profile.queue-v2-apply'
  schemaVersion: 'project-profile-queue/v1'
  root: string
  createdAt: string
  updatedAt: string
  dryRun: boolean
  dryRunSource: true
  queuePath: '.lazy-harness/project/profile-queue.json'
  sourcePacket: {
    schemaVersion: ProjectProfileInterviewV2Packet['schemaVersion']
    generatedAt: string
    mode: ProjectProfileInterviewV2Packet['mode']
  }
  items: ProjectProfileQueueItem[]
  summary: {
    total: number
    pending: number
    byPrimaryRoute: Record<string, number>
    pendingPolicyCandidates: number
    pendingEventReadyMetadata: number
  }
  warnings: string[]
  appliedWrites?: Array<{ path: string; action: 'written'; summary: string }>
}

interface ProjectProfilePromotionTargetEffect {
  kind: QueuePromotionKind
  path?: string
  status: 'applied' | 'deferred'
  action: 'create-record' | 'skip-existing-record' | 'append-project-map-branch' | 'skip-existing-project-map-branch' | 'append-candidate-row' | 'dedupe-candidate-row' | 'conflict-candidate-row' | 'create-rulebook' | 'skip-existing-rulebook' | 'upsert-capability' | 'append-update-loop-event' | 'dedupe-update-loop-event' | 'conflict-update-loop-event' | 'defer-target-writer'
  summary: string
  reason: string
}

interface ProjectProfileRecordPromotionWrite {
  kind: 'record'
  path: string
  action: 'create' | 'skip-existing'
  content: string
  summary: string
  effect: ProjectProfilePromotionTargetEffect
}

interface ProjectProfileCandidatePromotionWrite {
  kind: 'candidate-row'
  path: '.lazy-harness/knowledge/candidates.jsonl'
  row: Record<string, unknown>
  summary: string
}

interface ProjectProfileProjectMapBranchPromotionWrite {
  kind: 'project-map-branch'
  path: '.lazy-harness/project/feature-navigation.xml'
  action: 'append' | 'skip-existing'
  feature: Record<string, unknown>
  content: string
  summary: string
  effect: ProjectProfilePromotionTargetEffect
}

interface ProjectProfileRulebookPromotionWrite {
  kind: 'rulebook'
  path: string
  action: 'create' | 'skip-existing'
  content: string
  summary: string
  effect: ProjectProfilePromotionTargetEffect
}

interface ProjectProfileCapabilityPromotionWrite {
  kind: 'capability-binding'
  path: '.lazy-harness/ssot/capabilities.json'
  status: 'created' | 'updated' | 'unchanged'
  capability: Record<string, unknown>
  registry: { version: number; capabilities: Record<string, unknown>[] }
  summary: string
  effect: ProjectProfilePromotionTargetEffect
}

interface ProjectProfileUpdateLoopPromotionWrite {
  kind: 'update-loop-event'
  path: '.lazy-harness/knowledge/project-map-update-events.jsonl'
  row: Record<string, unknown>
  summary: string
}

interface ProjectProfilePromoteV2Preview {
  ok: true
  mode: 'project-profile.promote-v2'
  schemaVersion: 'project-profile-promote-preview/v1'
  root: string
  generatedAt: string
  dryRun: true
  queuePath: '.lazy-harness/project/profile-queue.json'
  item: ProjectProfileQueueItem
  plannedWrites: Array<{
    kind: QueuePromotionKind
    path?: string
    action: 'create-or-update' | 'append' | 'preview-only'
    requiresConfirmation: true
    summary: string
  }>
  queueUpdate: {
    id: string
    from: 'accepted'
    to: 'promoted'
    promotedAt: string
    promotedTo: string[]
    previewOnly: true
  }
  warnings: string[]
}

interface ProjectProfilePromoteV2Result {
  ok: true
  mode: 'project-profile.promote-v2-apply'
  schemaVersion: 'project-profile-promote-result/v1'
  root: string
  generatedAt: string
  dryRun: false
  queuePath: '.lazy-harness/project/profile-queue.json'
  item: ProjectProfileQueueItem
  targetEffects: ProjectProfilePromotionTargetEffect[]
  projectMapBranch?: Record<string, unknown>
  candidateRow?: Record<string, unknown>
  capability?: Record<string, unknown>
  updateEvent?: Record<string, unknown>
  queueUpdate: {
    id: string
    from: 'accepted'
    to: 'promoted'
    promotedAt: string
    promotedTo: string[]
    previewOnly: false
  }
  appliedWrites: Array<{ path: string; action: 'written' | 'skipped' | 'appended' | 'deduped-identical' | 'conflict-recorded' | 'created' | 'updated' | 'unchanged'; summary: string }>
  warnings: string[]
}

type ProjectProfilePromoteV2Output = ProjectProfilePromoteV2Preview | ProjectProfilePromoteV2Result

const REQUIRED_ARTIFACTS = [
  { path: '.lazy-harness/project/profile.xml', label: 'Project goal/profile root', layer: 'project' as const },
  { path: '.lazy-harness/project/stack.xml', label: 'Stack and platform choices', layer: 'project' as const },
  { path: '.lazy-harness/project/filesystem.xml', label: 'Filesystem/source/test/generated policy', layer: 'project' as const },
  { path: '.lazy-harness/project/feature-navigation.xml', label: 'Map-first feature navigation', layer: 'project' as const },
  { path: '.lazy-harness/tests/test-strategy.xml', label: 'Test strategy and validation commands', layer: 'tests' as const },
]

function parseArgs(argv: string[]): Args {
  const args: Args = {
    mode: 'inspect',
    format: 'md',
    root: process.env.LAZY_HOST_ROOT || process.cwd(),
    dryRun: false,
    confirm: false,
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '--mode' && next && ['inspect', 'plan', 'apply', 'interview', 'interview-v2', 'queue-v2', 'promote-v2', 'fill'].includes(next)) {
      args.mode = next as Mode
      i += 1
    } else if (arg.startsWith('--mode=')) {
      const value = arg.slice('--mode='.length)
      if (!['inspect', 'plan', 'apply', 'interview', 'interview-v2', 'queue-v2', 'promote-v2', 'fill'].includes(value)) throw new Error(`Unsupported --mode: ${value}`)
      args.mode = value as Mode
    } else if (arg === '--format' && (next === 'json' || next === 'md' || next === 'markdown')) {
      args.format = next === 'markdown' ? 'md' : next
      i += 1
    } else if (arg.startsWith('--format=')) {
      const value = arg.slice('--format='.length)
      if (value !== 'json' && value !== 'md' && value !== 'markdown') throw new Error(`Unsupported --format: ${value}`)
      args.format = value === 'markdown' ? 'md' : value
    } else if (arg === '--root' && next) {
      args.root = next
      i += 1
    } else if (arg.startsWith('--root=')) {
      args.root = arg.slice('--root='.length)
    } else if (arg === '--dry-run') {
      args.dryRun = true
    } else if (arg === '--confirm' || arg === '--yes') {
      args.confirm = true
    } else if (arg === '--answers' && next) {
      args.answers = next
      i += 1
    } else if (arg.startsWith('--answers=')) {
      args.answers = arg.slice('--answers='.length)
    } else if (arg === '--item' && next) {
      args.item = next
      i += 1
    } else if (arg.startsWith('--item=')) {
      args.item = arg.slice('--item='.length)
    } else if (arg === '--help' || arg === '-h') {
      printHelp()
      process.exit(0)
    } else {
      throw new Error(`Unknown or incomplete flag: ${arg}`)
    }
  }
  return args
}

function printHelp(): void {
  console.log(`Project Profile\n\nUsage:\n  bun .lazy-harness/scripts/project-profile.ts --mode inspect [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode plan [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode apply --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode apply --confirm [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode interview --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode interview --confirm [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode interview-v2 --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode queue-v2 --confirm [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <queue-item-id> --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode promote-v2 --item <queue-item-id> --confirm [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode fill --answers answers.json --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode fill --answers answers.json --confirm [--format md|json] [--root <path>]\n\nInspect mode is read-only. Plan mode proposes missing skeleton profile records. Apply with --confirm writes only needs-interview skeletons and never makes architecture decisions. Interview mode emits structured questions for needs-interview fields; --confirm writes only the open-question transcript. Interview V2 emits a read-only Project Map/policy discovery packet and requires --dry-run. Queue V2 converts the Interview V2 packet into a typed queue; --confirm writes only .lazy-harness/project/profile-queue.json. Promote V2 previews or confirms one accepted queue item; --confirm always writes queue status/promoted metadata and applies only the writer for that item's target kind (record skeleton, feature-navigation cue, candidate row, draft rulebook, discover/checklist capability, or non-canonical update-loop event). Fill mode applies only explicit answers from an answers file and requires --dry-run or --confirm.`)
}

function artifact(root: string, item: (typeof REQUIRED_ARTIFACTS)[number]): RequiredArtifact {
  const abs = join(root, item.path)
  if (!existsSync(abs)) {
    return { ...item, status: 'missing', bytes: null, mtime: null }
  }
  const st = statSync(abs)
  return { ...item, status: 'present', bytes: st.size, mtime: st.mtime.toISOString() }
}

function statusFor(root: string, path: string): ArtifactStatus {
  return existsSync(join(root, path)) ? 'present' : 'missing'
}

function statusCount(root: string, artifacts: RequiredArtifact[], status: 'needs-interview' | 'confirmed'): number {
  let count = 0
  const pattern = new RegExp(`status="${status}"`, 'g')
  for (const artifact of artifacts) {
    if (artifact.status !== 'present') continue
    const content = readFileSync(join(root, artifact.path), 'utf8')
    count += (content.match(pattern) || []).length
  }
  return count
}

function inspect(args: Args): ProjectProfileInspectResult {
  if (!existsSync(args.root)) throw new Error(`Root does not exist: ${args.root}`)
  const requiredArtifacts = REQUIRED_ARTIFACTS.map((item) => artifact(args.root, item))
  const present = requiredArtifacts.filter((item) => item.status === 'present').length
  const missing = requiredArtifacts.length - present
  const ledgerPath = '.lazy-harness/project/document-intake.xml'
  const candidatesPath = '.lazy-harness/knowledge/candidates.jsonl'
  const ledgerStatus = statusFor(args.root, ledgerPath)
  const candidatesStatus = statusFor(args.root, candidatesPath)
  const shouldOfferIngestion = ledgerStatus === 'missing'
  const artifactsComplete = missing === 0
  const needsInterviewFields = statusCount(args.root, requiredArtifacts, 'needs-interview')
  const confirmedFields = statusCount(args.root, requiredArtifacts, 'confirmed')
  const answersComplete = artifactsComplete && needsInterviewFields === 0
  const complete = answersComplete
  const prompt = !artifactsComplete
    ? 'Project Profile artifacts are incomplete. How should setup proceed?'
    : !answersComplete
      ? 'Project Profile artifacts exist, but interview answers are incomplete. What should happen next?'
      : 'Project Profile is complete. What should happen next?'
  const options = !artifactsComplete
    ? [
      'A. Create missing needs-interview skeleton records (Recommended)',
      'B. Run /lazy-doc-ingest first if docs may contain durable facts',
      'C. Start interview-only Project Profile setup',
      'D. Custom instruction',
    ]
    : !answersComplete
      ? [
        'A. Generate/review Project Profile interview questions (Recommended)',
        'B. Apply explicit confirmed answers with --mode fill',
        'C. Defer; keep status="needs-interview" fields visible',
        'D. Custom instruction',
      ]
      : [
        'A. Review existing profile only (Recommended)',
        'B. Refresh profile using document-ingestion outputs',
        'C. Start interview to update architecture decisions',
        'D. Custom instruction',
      ]
  const nextActions = !artifactsComplete
    ? ['Do not silently invent profile defaults.', 'Create missing skeletons or ask interview option gates before making architecture decisions.']
    : !answersComplete
      ? ['Run `project-profile --mode interview` to see open questions.', 'Use `project-profile --mode fill --answers <file> --confirm` only with explicit confirmed answers.']
      : ['Review profile artifacts before feature work.', 'Use map-first navigation from profile to records/code/tests.']
  return {
    ok: true,
    mode: 'project-profile.inspect',
    schemaVersion: '1.0',
    root: args.root,
    inspectedAt: new Date().toISOString(),
    requiredArtifacts,
    documentIngestion: {
      ledgerPath,
      ledgerStatus,
      candidatesPath,
      candidatesStatus,
      shouldOfferIngestion,
      reason: shouldOfferIngestion
        ? 'No document-intake ledger found; offer /lazy-doc-ingest before interview if outside docs may contain durable facts.'
        : 'Document-intake ledger exists; Project Profile may ask whether to use it as evidence.',
    },
    summary: { present, missing, artifactsComplete, needsInterviewFields, confirmedFields, answersComplete, complete },
    optionGate: {
      prompt,
      options,
      recommended: 'A',
    },
    nextActions,
  }
}

function xmlEscape(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function skeletonContent(path: string, generatedAt: string, inspectResult: ProjectProfileInspectResult): string {
  const ingestionAttrs = `documentIntake="${inspectResult.documentIngestion.ledgerStatus}" candidates="${inspectResult.documentIngestion.candidatesStatus}"`
  if (path.endsWith('/profile.xml')) {
    return `<?xml version="1.0" encoding="UTF-8"?>\n<projectProfile version="1" status="needs-interview" generatedAt="${xmlEscape(generatedAt)}" ${ingestionAttrs}>\n  <purpose status="needs-interview" />\n  <users status="needs-interview" />\n  <qualityPriorities status="needs-interview" />\n  <constraints status="needs-interview" />\n  <notes>No project goals or architecture decisions were inferred automatically.</notes>\n</projectProfile>\n`
  }
  if (path.endsWith('/stack.xml')) {
    return `<?xml version="1.0" encoding="UTF-8"?>\n<projectStack version="1" status="needs-interview" generatedAt="${xmlEscape(generatedAt)}" ${ingestionAttrs}>\n  <frontend status="needs-interview" />\n  <backend status="needs-interview" />\n  <database status="needs-interview" />\n  <runtime status="needs-interview" />\n  <validation status="needs-interview" />\n</projectStack>\n`
  }
  if (path.endsWith('/filesystem.xml')) {
    return `<?xml version="1.0" encoding="UTF-8"?>\n<projectFilesystem version="1" status="needs-interview" generatedAt="${xmlEscape(generatedAt)}" ${ingestionAttrs}>\n  <sourceRoots status="needs-interview" />\n  <testRoots status="needs-interview" />\n  <generatedRoots status="needs-interview" />\n  <forbiddenEditPaths status="needs-interview" />\n</projectFilesystem>\n`
  }
  if (path.endsWith('/feature-navigation.xml')) {
    return `<?xml version="1.0" encoding="UTF-8"?>\n<featureNavigation version="1" status="needs-interview" generatedAt="${xmlEscape(generatedAt)}" ${ingestionAttrs}>\n  <lookupOrder>\n    <step layer="DDD" status="needs-interview" />\n    <step layer="SDD" status="needs-interview" />\n    <step layer="BDD" status="needs-interview" />\n    <step layer="TDD" status="needs-interview" />\n    <step layer="ADR" status="needs-interview" />\n    <step layer="SSOT" status="needs-interview" />\n  </lookupOrder>\n  <sideEffectPolicy status="needs-interview" />\n  <regressionPolicy status="needs-interview" />\n  <domainInvariantPolicy status="needs-interview" />\n</featureNavigation>\n`
  }
  throw new Error(`No skeleton template for ${path}`)
}

function buildPlanResult(args: Args): PlanResult {
  if (args.mode === 'apply' && !args.dryRun && !args.confirm) {
    throw new Error('apply mode requires --dry-run for preview or --confirm to write needs-interview skeleton records')
  }
  const inspectResult = inspect(args)
  const generatedAt = new Date().toISOString()
  const proposedWrites = inspectResult.requiredArtifacts
    .filter((artifact) => artifact.status === 'missing' && artifact.path.startsWith('.lazy-harness/project/'))
    .map((artifact): ProposedWrite => ({
      path: artifact.path,
      action: 'create',
      kind: 'project-profile-skeleton',
      content: skeletonContent(artifact.path, generatedAt, inspectResult),
      summary: `Create needs-interview skeleton for ${artifact.label}`,
    }))
  return {
    ok: true,
    mode: args.mode === 'apply' ? (args.dryRun ? 'project-profile.apply-dry-run' : 'project-profile.apply') : 'project-profile.plan',
    schemaVersion: '1.0',
    root: args.root,
    generatedAt,
    dryRun: args.mode === 'apply' ? args.dryRun : args.dryRun,
    inspect: inspectResult,
    proposedWrites,
    warnings: [
      'Project Profile skeleton apply does not decide architecture, stack, filesystem, or navigation policy.',
      'Generated records are status="needs-interview" and must be completed by interview or confirmed evidence.',
    ],
    optionGate: {
      prompt: 'How should Project Profile setup proceed?',
      options: [
        'A. Create missing needs-interview skeleton records (Recommended)',
        'B. Run or review Document Resource Ingestion first',
        'C. Start full interview before creating skeletons',
        'D. Custom instruction',
      ],
      recommended: 'A',
    },
  }
}

function ensureParent(path: string): void {
  mkdirSync(path.slice(0, path.lastIndexOf('/')), { recursive: true })
}

function applyConfirmed(result: PlanResult): PlanResult {
  const appliedWrites: NonNullable<PlanResult['appliedWrites']> = []
  for (const write of result.proposedWrites) {
    const abs = join(result.root, write.path)
    if (existsSync(abs)) {
      appliedWrites.push({ path: write.path, action: 'skipped', summary: 'Already exists' })
      continue
    }
    ensureParent(abs)
    writeFileSync(abs, write.content, 'utf8')
    appliedWrites.push({ path: write.path, action: 'written', summary: write.summary })
  }
  return { ...result, appliedWrites }
}

function renderInspectMd(result: ProjectProfileInspectResult): string {
  const lines: string[] = []
  lines.push('# Project Profile inspect report')
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Artifacts complete: ${result.summary.artifactsComplete ? 'yes' : 'no'}`)
  lines.push(`- Answers complete: ${result.summary.answersComplete ? 'yes' : 'no'}`)
  lines.push(`- Needs-interview fields: ${result.summary.needsInterviewFields}`)
  lines.push(`- Confirmed fields: ${result.summary.confirmedFields}`)
  lines.push(`- Required artifacts: present=${result.summary.present}, missing=${result.summary.missing}`)
  lines.push('')
  lines.push('## Required artifacts')
  for (const artifact of result.requiredArtifacts) {
    lines.push(`- ${artifact.status === 'present' ? '✓' : '✗'} \`${artifact.path}\` — ${artifact.label}`)
  }
  lines.push('')
  lines.push('## Document Resource Ingestion handoff')
  lines.push(`- Ledger: ${result.documentIngestion.ledgerStatus} — \`${result.documentIngestion.ledgerPath}\``)
  lines.push(`- Candidates: ${result.documentIngestion.candidatesStatus} — \`${result.documentIngestion.candidatesPath}\``)
  lines.push(`- Recommendation: ${result.documentIngestion.reason}`)
  lines.push('')
  lines.push('## Option gate')
  lines.push(result.optionGate.prompt)
  for (const option of result.optionGate.options) lines.push(`- ${option}`)
  lines.push('')
  lines.push('## Next actions')
  for (const action of result.nextActions) lines.push(`- ${action}`)
  return lines.join('\n')
}

function renderPlanMd(result: PlanResult): string {
  const title = result.mode === 'project-profile.apply-dry-run'
    ? 'Project Profile apply dry-run'
    : result.mode === 'project-profile.apply'
      ? 'Project Profile apply'
      : 'Project Profile plan'
  const lines: string[] = []
  lines.push(`# ${title}`)
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Dry run: ${result.dryRun ? 'yes' : 'no'}`)
  lines.push(`- Proposed writes: ${result.proposedWrites.length}`)
  lines.push('')
  lines.push('## Proposed writes')
  for (const write of result.proposedWrites) lines.push(`- \`${write.path}\`: ${write.summary}`)
  if (result.appliedWrites?.length) {
    lines.push('')
    lines.push('## Applied writes')
    for (const write of result.appliedWrites) lines.push(`- ${write.action}: \`${write.path}\` — ${write.summary}`)
  }
  lines.push('')
  lines.push('## Warnings')
  for (const warning of result.warnings) lines.push(`- ${warning}`)
  lines.push('')
  lines.push('## Option gate')
  lines.push(result.optionGate.prompt)
  for (const option of result.optionGate.options) lines.push(`- ${option}`)
  return lines.join('\n')
}

function stableId(value: string): string {
  return `PPQ-${createHash('sha256').update(value).digest('hex').slice(0, 12)}`
}

function slugify(value: string): string {
  const slug = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'project-profile-record'
}

function titleCase(value: string): string {
  return value
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((part) => part.slice(0, 1).toUpperCase() + part.slice(1))
    .join(' ')
}

function layerForRecordPath(path: string, fallback: QueuePrimaryRoute): 'DDD' | 'BDD' | 'SDD' | 'TDD' | 'ADR' | 'SSOT' | 'Planning' {
  if (path.includes('/domain/')) return 'DDD'
  if (path.includes('/behavior/')) return 'BDD'
  if (path.includes('/spec/')) return 'SDD'
  if (path.includes('/tests/')) return 'TDD'
  if (path.includes('/decisions/')) return 'ADR'
  if (path.includes('/ssot/')) return 'SSOT'
  if (path.includes('/planning/') || path.includes('/plans/')) return 'Planning'
  if (fallback === 'facts') return 'DDD'
  if (fallback === 'expectations') return 'BDD'
  if (fallback === 'contracts') return 'SDD'
  if (fallback === 'validation') return 'TDD'
  if (fallback === 'decisions') return 'ADR'
  if (fallback === 'ownership') return 'SSOT'
  return 'Planning'
}

function recordPathForPromotion(item: ProjectProfileQueueItem): string {
  const base = item.promotionTarget.path || '.lazy-harness/planning/'
  if (base.endsWith('.md')) return base
  const normalizedBase = base.endsWith('/') ? base : `${base}/`
  const sourceId = item.source.id || item.id
  return `${normalizedBase}${slugify(sourceId)}.md`
}

function rulebookPathForPromotion(item: ProjectProfileQueueItem): string {
  const base = item.promotionTarget.path || '.lazy-harness/rules/'
  if (base.endsWith('.md')) return base
  const normalizedBase = base.endsWith('/') ? base : `${base}/`
  return `${normalizedBase}${slugify(item.source.id || item.id)}.md`
}

function labelForTarget(path: string, elementName: string, attrs: string): string {
  const layer = attrs.match(/layer="([^"]+)"/)?.[1]
  if (layer) return `${elementName}[layer=${layer}]`
  if (path.endsWith('/profile.xml')) return `profile.${elementName}`
  if (path.endsWith('/stack.xml')) return `stack.${elementName}`
  if (path.endsWith('/filesystem.xml')) return `filesystem.${elementName}`
  if (path.endsWith('/feature-navigation.xml')) return `featureNavigation.${elementName}`
  if (path.endsWith('/test-strategy.xml')) return `testStrategy.${elementName}`
  return elementName
}

function sectionPrompt(target: string): string {
  if (target.startsWith('profile.')) return 'Confirm this project profile field. What should future agents treat as durable project truth?'
  if (target.startsWith('stack.')) return 'Confirm this stack/platform field. What existing or desired technology should future agents follow?'
  if (target.startsWith('filesystem.')) return 'Confirm this filesystem policy field. Which paths are source, tests, generated, or forbidden?'
  if (target.startsWith('featureNavigation.') || target.includes('[layer=')) return 'Confirm this map-first navigation field. How should future agents find records, risks, and tests before editing?'
  if (target.startsWith('testStrategy.')) return 'Confirm this validation field. Which command or policy proves correctness for this host?'
  return 'Confirm this Project Profile field.'
}

function questionsFromArtifact(root: string, artifact: RequiredArtifact): InterviewQuestion[] {
  if (artifact.status !== 'present') return []
  const abs = join(root, artifact.path)
  const content = readFileSync(abs, 'utf8')
  const questions: InterviewQuestion[] = []
  const regex = /<([A-Za-z][\w:-]*)([^>]*\sstatus="needs-interview"[^>]*)\/?\s*>/g
  let match: RegExpExecArray | null
  while ((match = regex.exec(content)) !== null) {
    const elementName = match[1]
    const attrs = match[2]
    if (!elementName || ['projectProfile', 'projectStack', 'projectFilesystem', 'featureNavigation', 'testStrategy'].includes(elementName)) continue
    const target = labelForTarget(artifact.path, elementName, attrs)
    const id = stableId(`${artifact.path}:${target}`)
    questions.push({
      id,
      sourcePath: artifact.path,
      target,
      section: artifact.label,
      prompt: sectionPrompt(target),
      options: [
        'A. Answer now with confirmed project truth (Recommended)',
        'B. Use existing document-ingestion candidate evidence before answering',
        'C. Defer explicitly; keep status="needs-interview"',
        'D. Custom answer / different framing',
      ],
      recommended: 'A',
    })
  }
  return questions
}

function buildInterviewResult(args: Args): InterviewResult {
  const inspectResult = inspect(args)
  const generatedAt = new Date().toISOString()
  const questions = inspectResult.requiredArtifacts.flatMap((artifact) => questionsFromArtifact(args.root, artifact))
  const warnings = [
    'Interview mode does not infer or fill profile values without confirmed answers.',
    'Use document-ingestion candidates only as evidence; Project Profile remains interview-first.',
  ]
  if (inspectResult.summary.missing > 0) warnings.push('Some Project Profile artifacts are missing; run plan/apply skeleton before completing the interview.')
  return {
    ok: true,
    mode: args.confirm && !args.dryRun ? 'project-profile.interview-apply' : 'project-profile.interview',
    schemaVersion: '1.0',
    root: args.root,
    generatedAt,
    dryRun: args.dryRun || !args.confirm,
    inspect: inspectResult,
    questions,
    warnings,
    nextActions: questions.length === 0
      ? ['No open needs-interview fields found. Review profile records for status="confirmed" completeness.']
      : ['Ask/answer each Project Profile question, then apply confirmed answers in a future fill step.', 'Do not edit architecture, stack, filesystem, or test policy silently.'],
  }
}

function renderQuestionXml(result: InterviewResult): string {
  const lines = [`<?xml version="1.0" encoding="UTF-8"?>`, `<projectProfileInterview version="1" status="open" generatedAt="${xmlEscape(result.generatedAt)}">`]
  for (const question of result.questions) {
    lines.push(`  <question id="${xmlEscape(question.id)}" sourcePath="${xmlEscape(question.sourcePath)}" target="${xmlEscape(question.target)}" recommended="${xmlEscape(question.recommended)}">`)
    lines.push(`    <prompt>${xmlEscape(question.prompt)}</prompt>`)
    lines.push('    <options>')
    for (const option of question.options) lines.push(`      <option>${xmlEscape(option)}</option>`)
    lines.push('    </options>')
    lines.push('  </question>')
  }
  lines.push('</projectProfileInterview>')
  return `${lines.join('\n')}\n`
}

function applyInterviewQueue(result: InterviewResult): InterviewResult {
  const outPath = '.lazy-harness/project/profile-interview.xml'
  const abs = join(result.root, outPath)
  ensureParent(abs)
  writeFileSync(abs, renderQuestionXml(result), 'utf8')
  return { ...result, appliedWrites: [{ path: outPath, action: 'written', summary: `Wrote ${result.questions.length} open Project Profile questions` }] }
}

function renderInterviewMd(result: InterviewResult): string {
  const lines: string[] = []
  lines.push(result.mode === 'project-profile.interview-apply' ? '# Project Profile interview apply' : '# Project Profile interview')
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Dry run: ${result.dryRun ? 'yes' : 'no'}`)
  lines.push(`- Open questions: ${result.questions.length}`)
  if (result.appliedWrites?.length) {
    lines.push('')
    lines.push('## Applied writes')
    for (const write of result.appliedWrites) lines.push(`- ${write.action}: \`${write.path}\` — ${write.summary}`)
  }
  lines.push('')
  lines.push('## Questions')
  for (const question of result.questions) {
    lines.push(`- ${question.id} \`${question.target}\` from \`${question.sourcePath}\``)
    lines.push(`  - ${question.prompt}`)
    for (const option of question.options) lines.push(`  - ${option}`)
  }
  lines.push('')
  lines.push('## Warnings')
  for (const warning of result.warnings) lines.push(`- ${warning}`)
  lines.push('')
  lines.push('## Next actions')
  for (const action of result.nextActions) lines.push(`- ${action}`)
  return lines.join('\n')
}

function buildInterviewV2Result(args: Args): ProjectProfileInterviewV2Packet {
  if (!args.dryRun || args.confirm) {
    throw new Error('interview-v2 mode is read-only and requires --dry-run; --confirm is intentionally unsupported')
  }
  const inspectResult = inspect(args)
  return {
    schemaVersion: 'project-profile-interview-v2/v1',
    mode: 'interview-v2',
    root: args.root,
    generatedAt: new Date().toISOString(),
    adapterBoundary: {
      primary: 'pi',
      compatibility: ['omp'],
      core: 'Project Profile V2 output is agent-neutral project map and policy discovery data',
    },
    writes: { dryRun: true, confirmedOnly: true, noSilentDefaults: true },
    inspectContext: {
      schemaVersion: inspectResult.schemaVersion,
      summary: inspectResult.summary,
      requiredArtifacts: inspectResult.requiredArtifacts.map((item) => ({ path: item.path, label: item.label, layer: item.layer, status: item.status })),
      documentIngestion: inspectResult.documentIngestion,
    },
    questionGroups: [
      { id: 'project-purpose', title: 'Project purpose and constraints', dimensions: ['facts', 'expectations'] },
      { id: 'source-ownership', title: 'Source ownership and filesystem boundaries', dimensions: ['ownership', 'source-links', 'policies'] },
      { id: 'system-design', title: 'System design and architecture boundaries', dimensions: ['contracts', 'decisions', 'policies'] },
      { id: 'domain-vocabulary', title: 'Domain vocabulary and invariants', dimensions: ['facts', 'ownership', 'validation'] },
      { id: 'frontend-design', title: 'Frontend design system and accessibility baseline', dimensions: ['contracts', 'expectations', 'policies'] },
      { id: 'backend-data', title: 'Backend API, persistence, auth, error, and migration boundaries', dimensions: ['contracts', 'ownership', 'validation'] },
      { id: 'validation-policy', title: 'Validation and testing policy', dimensions: ['validation', 'policies'] },
      { id: 'workflow-policy', title: 'Commit, push, PR, review, and release workflow', dimensions: ['policies', 'expectations'] },
      { id: 'dependency-policy', title: 'Dependency and tool policy', dimensions: ['policies', 'ownership', 'contracts'] },
      { id: 'security-privacy', title: 'Security, privacy, and compliance boundaries', dimensions: ['ownership', 'policies', 'validation'] },
      { id: 'documentation-policy', title: 'Documentation and record update expectations', dimensions: ['policies', 'source-links'] },
      { id: 'human-confirmation', title: 'Human confirmation and autonomy boundaries', dimensions: ['policies', 'ownership'] },
      { id: 'agent-autonomy', title: 'Agent autonomy and refactor boundaries', dimensions: ['policies', 'decisions'] },
    ],
    projectMapSeeds: [{
      id: 'project-policy-discovery',
      title: 'Project/team policy discovery',
      primary: 'policies',
      facets: ['Policy', 'Project', 'BDD', 'SDD'],
      status: 'draft',
      scope: 'host-project',
      cluster: {
        role: 'anchor',
        anchorId: 'project-policy-discovery',
        branchOf: null,
        branches: [
          { id: 'project-validation-policy', primary: 'validation', facets: ['TDD', 'Policy'] },
          { id: 'project-dependency-policy', primary: 'policies', facets: ['Policy', 'SSOT'] },
          { id: 'project-design-boundary', primary: 'contracts', facets: ['SDD', 'ADR'] },
          { id: 'project-human-confirmation', primary: 'ownership', facets: ['SSOT', 'Policy'] },
          { id: 'project-domain-vocabulary', primary: 'facts', facets: ['DDD', 'Project'] },
        ],
        edges: [
          { from: 'project-policy-discovery', to: 'project-validation-policy', relation: 'has-validation' },
          { from: 'project-policy-discovery', to: 'project-dependency-policy', relation: 'has-policy' },
          { from: 'project-policy-discovery', to: 'project-design-boundary', relation: 'has-contract' },
          { from: 'project-policy-discovery', to: 'project-human-confirmation', relation: 'has-ownership' },
          { from: 'project-policy-discovery', to: 'project-domain-vocabulary', relation: 'has-fact' },
        ],
      },
      canonicalRecords: ['.lazy-harness/spec/platform/project-profile-v2.md', '.lazy-harness/spec/platform/project-map-v2.md'],
    }],
    policyCandidates: [
      {
        id: 'project-validation-stage-policy',
        dimension: 'validation',
        sourceQuestionGroup: 'validation-policy',
        confirmed: false,
        stages: [
          { stage: 'turn', level: 'recommend', behavior: 'ask project whether focused validation is expected for changed code' },
          { stage: 'push', level: 'discover', behavior: 'ask project whether broad validation should run before push' },
        ],
      },
      {
        id: 'dependency-addition-review-policy',
        dimension: 'dependency-change',
        sourceQuestionGroup: 'dependency-policy',
        confirmed: false,
        stages: [
          { stage: 'edit', level: 'recommend', behavior: 'ask project whether new runtime dependencies require record-backed justification' },
          { stage: 'high-risk-mutation', level: 'discover', behavior: 'ask project whether supply-chain-sensitive dependency changes require explicit confirmation' },
        ],
      },
      {
        id: 'human-confirmation-boundary-policy',
        dimension: 'human-confirmation',
        sourceQuestionGroup: 'human-confirmation',
        confirmed: false,
        stages: [
          { stage: 'high-risk-mutation', level: 'recommend', behavior: 'ask project which irreversible or externally visible actions need explicit confirmation' },
          { stage: 'release', level: 'discover', behavior: 'ask project whether release actions require a human approval checkpoint' },
        ],
      },
    ],
    unresolvedAmbiguities: [
      {
        id: 'policy-storage-target',
        question: 'Should confirmed project policies be written first as Project Map candidates, .lazy-harness/rules records, or capabilities.json bindings?',
        options: ['project-map-candidate', 'rules-record', 'capability-binding', 'decide-per-policy'],
      },
      {
        id: 'project-profile-refresh-event-shape',
        question: 'Should future confirmed Project Profile refresh write update-loop event packets immediately or keep event-ready metadata until a later apply mode?',
        options: ['event-ready-metadata', 'append-update-event', 'ask-each-refresh', 'decide-after-policy-machinery'],
      },
    ],
    proposedWrites: [
      { path: '.lazy-harness/project/profile.xml', requiresConfirmation: true },
      { path: '.lazy-harness/project/feature-navigation.xml', requiresConfirmation: true },
      { path: '.lazy-harness/tests/test-strategy.xml', requiresConfirmation: true },
      { path: '.lazy-harness/rules/', requiresConfirmation: true },
      { path: '.lazy-harness/ssot/capabilities.json', requiresConfirmation: true },
    ],
    updateLoop: {
      schemaVersion: 'project-map-update-event/v1',
      eventType: 'project-profile-refresh',
      source: 'project-profile',
      target: { anchorId: 'project-profile-v2', branch: 'ownership', nodeId: 'project-profile-refresh-candidate', primary: 'ownership', facets: ['SSOT', 'Project'] },
      transition: { from: 'observation', to: 'candidate', requiresConfirmation: true, canonicalRecords: [], candidateStore: '.lazy-harness/knowledge/candidates.jsonl' },
      evidence: [{ kind: 'project-profile', path: '.lazy-harness/project/profile.xml', summary: 'Project Profile V2 dry-run output is candidate/event-ready metadata only.', redaction: 'compact' }],
      effects: [{ action: 'append-candidate', path: '.lazy-harness/knowledge/candidates.jsonl' }],
    },
    warnings: [
      'interview-v2 is read-only and requires --dry-run.',
      'Project Map seeds and policy candidates are candidates, not canonical truth.',
      'No files are written and no Project Map update event is appended by this mode.',
      'Use confirmed answers plus a future apply mode before promoting profile data to canonical records.',
    ],
  }
}

function renderInterviewV2Md(result: ProjectProfileInterviewV2Packet): string {
  return [
    '# Project Profile Interview V2',
    '',
    `Generated: ${result.generatedAt}`,
    `Adapter boundary: primary=${result.adapterBoundary.primary}, compatibility=${result.adapterBoundary.compatibility.join(', ')}`,
    `Writes: dryRun=${result.writes.dryRun}, confirmedOnly=${result.writes.confirmedOnly}, noSilentDefaults=${result.writes.noSilentDefaults}`,
    '',
    '## Question groups',
    ...result.questionGroups.map((group) => `- ${group.id}: ${group.title}`),
    '',
    '## Project Map seeds',
    ...result.projectMapSeeds.map((seed) => `- ${seed.id}: ${seed.primary} [${seed.facets.join(', ')}]`),
    '',
    '## Policy candidates',
    ...result.policyCandidates.map((policy) => `- ${policy.id}: ${policy.dimension} (${policy.stages.map((stage) => `${stage.stage}:${stage.level}`).join(', ')})`),
    '',
    '## Unresolved ambiguities',
    ...result.unresolvedAmbiguities.map((item) => `- ${item.id}: ${item.question}`),
    '',
    '## Warnings',
    ...result.warnings.map((warning) => `- ${warning}`),
    '',
  ].join('\n')
}

function queueItemId(sourceKind: QueueSourceKind, id: string): string {
  return stableId(`project-profile-queue-v1:${sourceKind}:${id}`)
}

function queueRouteForQuestionGroup(id: string): Pick<ProjectProfileQueueItem, 'primaryRoute' | 'facets' | 'relatedRoutes' | 'promotionTarget'> {
  if (id === 'project-purpose') return { primaryRoute: 'facts', facets: ['DDD', 'BDD', 'Project'], relatedRoutes: ['expectations'], promotionTarget: { kind: 'record', path: '.lazy-harness/domain/', requiresConfirmation: true } }
  if (id === 'domain-vocabulary') return { primaryRoute: 'facts', facets: ['DDD', 'SSOT'], relatedRoutes: ['ownership'], promotionTarget: { kind: 'record', path: '.lazy-harness/domain/', requiresConfirmation: true } }
  if (id === 'frontend-design') return { primaryRoute: 'expectations', facets: ['BDD', 'SDD', 'TDD'], relatedRoutes: ['contracts', 'validation'], promotionTarget: { kind: 'record', path: '.lazy-harness/behavior/', requiresConfirmation: true } }
  if (id === 'backend-data') return { primaryRoute: 'contracts', facets: ['SDD', 'SSOT', 'TDD'], relatedRoutes: ['ownership', 'validation'], promotionTarget: { kind: 'record', path: '.lazy-harness/spec/', requiresConfirmation: true } }
  if (id === 'system-design') return { primaryRoute: 'contracts', facets: ['SDD', 'ADR', 'Policy'], relatedRoutes: ['decisions', 'policies'], promotionTarget: { kind: 'record', path: '.lazy-harness/spec/', requiresConfirmation: true } }
  if (id === 'validation-policy') return { primaryRoute: 'validation', facets: ['TDD', 'Policy'], relatedRoutes: ['policies'], promotionTarget: { kind: 'record', path: '.lazy-harness/tests/', requiresConfirmation: true } }
  if (id === 'source-ownership') return { primaryRoute: 'ownership', facets: ['SSOT', 'Policy', 'Source'], relatedRoutes: ['source-links', 'policies'], promotionTarget: { kind: 'record', path: '.lazy-harness/ssot/', requiresConfirmation: true } }
  if (id === 'security-privacy') return { primaryRoute: 'ownership', facets: ['SSOT', 'Policy', 'TDD'], relatedRoutes: ['policies', 'validation'], promotionTarget: { kind: 'record', path: '.lazy-harness/ssot/', requiresConfirmation: true } }
  if (id === 'agent-autonomy') return { primaryRoute: 'decisions', facets: ['ADR', 'Policy'], relatedRoutes: ['policies'], promotionTarget: { kind: 'record', path: '.lazy-harness/decisions/', requiresConfirmation: true } }
  if (id === 'workflow-policy' || id === 'dependency-policy' || id === 'documentation-policy' || id === 'human-confirmation') return { primaryRoute: 'policies', facets: ['Policy', 'SSOT'], relatedRoutes: ['ownership'], promotionTarget: { kind: 'rulebook', path: '.lazy-harness/rules/', requiresConfirmation: true } }
  return { primaryRoute: 'expectations', facets: ['BDD', 'Project'], relatedRoutes: ['source-links'], promotionTarget: { kind: 'record', path: '.lazy-harness/behavior/', requiresConfirmation: true } }
}

function routeForProposedWrite(path: string): Pick<ProjectProfileQueueItem, 'primaryRoute' | 'facets' | 'relatedRoutes' | 'promotionTarget'> {
  if (path.includes('/rules/')) return { primaryRoute: 'policies', facets: ['Policy'], relatedRoutes: [], promotionTarget: { kind: 'rulebook', path, requiresConfirmation: true } }
  if (path.endsWith('capabilities.json')) return { primaryRoute: 'policies', facets: ['Policy', 'SSOT'], relatedRoutes: ['ownership'], promotionTarget: { kind: 'capability-binding', path, requiresConfirmation: true } }
  if (path.includes('/tests/')) return { primaryRoute: 'validation', facets: ['TDD'], relatedRoutes: [], promotionTarget: { kind: 'record', path, requiresConfirmation: true } }
  if (path.includes('/project/')) return { primaryRoute: 'ownership', facets: ['SSOT', 'Project'], relatedRoutes: ['source-links'], promotionTarget: { kind: 'record', path, requiresConfirmation: true } }
  return { primaryRoute: 'queue-only', facets: ['Project'], relatedRoutes: [], promotionTarget: { kind: 'queue-only', path, requiresConfirmation: true } }
}

function buildProfileQueueV1FromInterviewV2(packet: ProjectProfileInterviewV2Packet, args: Args): ProjectProfileQueueV1 {
  const now = new Date().toISOString()
  const items: ProjectProfileQueueItem[] = []

  for (const group of packet.questionGroups) {
    const route = queueRouteForQuestionGroup(group.id)
    items.push({
      id: queueItemId('question-group', group.id),
      status: 'pending',
      ...route,
      source: { kind: 'question-group', id: group.id },
      summary: `${group.title}: ${group.dimensions.join(', ')}`,
      evidence: [{ kind: 'project-profile-question-group', summary: `Derived from interview-v2 question group ${group.id}` }],
    })
  }

  for (const seed of packet.projectMapSeeds) {
    items.push({
      id: queueItemId('project-map-seed', seed.id),
      status: 'pending',
      primaryRoute: 'source-links',
      facets: ['Project', 'Evidence'],
      relatedRoutes: ['expectations', 'contracts'],
      source: { kind: 'project-map-seed', id: seed.id },
      summary: `${seed.title}: ${seed.cluster.branches.length} branch(es), ${seed.cluster.edges.length} edge(s)`,
      evidence: [{ kind: 'project-map-seed', summary: `Derived from interview-v2 Project Map seed ${seed.id}` }],
      promotionTarget: { kind: 'project-map-branch', path: '.lazy-harness/project/feature-navigation.xml', requiresConfirmation: true },
    })
  }

  for (const policy of packet.policyCandidates) {
    items.push({
      id: queueItemId('policy-candidate', policy.id),
      status: 'pending',
      primaryRoute: 'policies',
      facets: ['Policy', 'SSOT'],
      relatedRoutes: ['ownership'],
      source: { kind: 'policy-candidate', id: policy.id },
      summary: `${policy.dimension}: ${policy.stages.map((stage) => `${stage.stage}/${stage.level}`).join(', ')}`,
      evidence: [{ kind: 'policy-candidate', summary: `Derived from interview-v2 policy candidate ${policy.id}` }],
      promotionTarget: { kind: 'rulebook', path: '.lazy-harness/rules/', requiresConfirmation: true },
    })
  }

  for (const ambiguity of packet.unresolvedAmbiguities) {
    const policyLike = ambiguity.id.includes('policy')
    items.push({
      id: queueItemId('unresolved-ambiguity', ambiguity.id),
      status: 'pending',
      primaryRoute: policyLike ? 'policies' : 'queue-only',
      facets: policyLike ? ['SSOT', 'Policy'] : ['Project'],
      relatedRoutes: policyLike ? ['ownership'] : [],
      source: { kind: 'unresolved-ambiguity', id: ambiguity.id },
      summary: ambiguity.question,
      evidence: [{ kind: 'unresolved-ambiguity', summary: `Options: ${ambiguity.options.join(', ')}` }],
      promotionTarget: { kind: 'record', path: policyLike ? '.lazy-harness/ssot/' : '.lazy-harness/planning/', requiresConfirmation: true },
    })
  }

  for (const proposedWrite of packet.proposedWrites) {
    const route = routeForProposedWrite(proposedWrite.path)
    items.push({
      id: queueItemId('proposed-write', proposedWrite.path),
      status: 'pending',
      ...route,
      source: { kind: 'proposed-write', id: proposedWrite.path },
      summary: `Future confirmed write target: ${proposedWrite.path}`,
      evidence: [{ kind: 'proposed-write', path: proposedWrite.path, summary: 'Interview V2 proposed write target requiring confirmation' }],
    })
  }

  items.push({
    id: queueItemId('update-loop', packet.updateLoop.target.nodeId),
    status: 'pending',
    primaryRoute: 'event-ready-metadata',
    facets: ['Project', 'Evidence'],
    relatedRoutes: ['source-links'],
    source: { kind: 'update-loop', id: packet.updateLoop.target.nodeId },
    summary: `${packet.updateLoop.eventType} event-ready metadata for ${packet.updateLoop.target.anchorId}`,
    evidence: packet.updateLoop.evidence.map((item) => ({ kind: item.kind, path: item.path, summary: item.summary })),
    promotionTarget: { kind: 'update-loop-event', requiresConfirmation: true },
  })

  const byPrimaryRoute = items.reduce<Record<string, number>>((acc, item) => {
    acc[item.primaryRoute] = (acc[item.primaryRoute] || 0) + 1
    return acc
  }, {})
  return {
    ok: true,
    mode: args.confirm ? 'project-profile.queue-v2-apply' : 'project-profile.queue-v2',
    schemaVersion: 'project-profile-queue/v1',
    root: args.root,
    createdAt: now,
    updatedAt: now,
    dryRun: !args.confirm,
    dryRunSource: true,
    queuePath: '.lazy-harness/project/profile-queue.json',
    sourcePacket: { schemaVersion: packet.schemaVersion, generatedAt: packet.generatedAt, mode: packet.mode },
    items,
    summary: {
      total: items.length,
      pending: items.filter((item) => item.status === 'pending').length,
      byPrimaryRoute,
      pendingPolicyCandidates: items.filter((item) => item.status === 'pending' && item.source.kind === 'policy-candidate').length,
      pendingEventReadyMetadata: items.filter((item) => item.status === 'pending' && item.primaryRoute === 'event-ready-metadata').length,
    },
    warnings: [
      'queue-v2 is a typed inbox/router; it does not promote records by itself.',
      'queue-v2 --confirm writes only .lazy-harness/project/profile-queue.json.',
      'candidates/rules/capabilities/update-loop events require later explicit promotion.',
    ],
  }
}

function buildProfileQueueV1(args: Args): ProjectProfileQueueV1 {
  if (!args.dryRun && !args.confirm) throw new Error('queue-v2 mode requires --dry-run or --confirm')
  const packet = buildInterviewV2Result({ ...args, dryRun: true, confirm: false })
  return buildProfileQueueV1FromInterviewV2(packet, args)
}

function applyProfileQueue(queue: ProjectProfileQueueV1): ProjectProfileQueueV1 {
  const abs = join(queue.root, queue.queuePath)
  ensureParent(abs)
  const content = JSON.stringify({ ...queue, appliedWrites: undefined }, null, 2) + '\n'
  writeFileSync(abs, content, 'utf8')
  return { ...queue, appliedWrites: [{ path: queue.queuePath, action: 'written', summary: `Wrote ${queue.items.length} Project Profile queue item(s)` }] }
}

function readProfileQueue(root: string): ProjectProfileQueueV1 {
  const queuePath = join(root, '.lazy-harness/project/profile-queue.json')
  if (!existsSync(queuePath)) throw new Error('promote-v2 requires .lazy-harness/project/profile-queue.json; run queue-v2 --confirm first')
  const queue = JSON.parse(readFileSync(queuePath, 'utf8')) as ProjectProfileQueueV1
  if (queue.schemaVersion !== 'project-profile-queue/v1' || !Array.isArray(queue.items)) {
    throw new Error('profile-queue.json is not a project-profile-queue/v1 queue')
  }
  return queue
}

function summarizeProfileQueueItems(items: ProjectProfileQueueItem[]): ProjectProfileQueueV1['summary'] {
  const byPrimaryRoute: Record<string, number> = {}
  for (const item of items) byPrimaryRoute[item.primaryRoute] = (byPrimaryRoute[item.primaryRoute] || 0) + 1
  return {
    total: items.length,
    pending: items.filter((item) => item.status === 'pending').length,
    byPrimaryRoute,
    pendingPolicyCandidates: items.filter((item) => item.status === 'pending' && item.source.kind === 'policy-candidate').length,
    pendingEventReadyMetadata: items.filter((item) => item.status === 'pending' && item.primaryRoute === 'event-ready-metadata').length,
  }
}

function actionForPromotionKind(kind: QueuePromotionKind): 'create-or-update' | 'append' | 'preview-only' {
  if (kind === 'candidate-row' || kind === 'update-loop-event') return 'append'
  if (kind === 'queue-only') return 'preview-only'
  return 'create-or-update'
}

function pathForPromotionTarget(target: ProjectProfileQueueItem['promotionTarget']): string | undefined {
  if (target.path) return target.path
  if (target.kind === 'update-loop-event') return '.lazy-harness/knowledge/project-map-update-events.jsonl'
  return undefined
}

function buildPromotionTargetEffect(item: ProjectProfileQueueItem): ProjectProfilePromotionTargetEffect {
  const target = item.promotionTarget
  const path = pathForPromotionTarget(target)
  return {
    kind: target.kind,
    path,
    status: 'deferred',
    action: 'defer-target-writer',
    summary: path
      ? `Deferred ${target.kind} target writer for ${item.id} to ${path}`
      : `Deferred ${target.kind} target writer for ${item.id}`,
    reason: 'This promote-v2 --confirm slice writes only queue status/promoted metadata; canonical target writers are implemented separately by target kind.',
  }
}

function buildRecordPromotionWrite(item: ProjectProfileQueueItem, generatedAt: string, root: string): ProjectProfileRecordPromotionWrite | null {
  if (item.promotionTarget.kind !== 'record') return null
  const path = recordPathForPromotion(item)
  const abs = join(root, path)
  const exists = existsSync(abs)
  const layer = layerForRecordPath(path, item.primaryRoute)
  const sourceLabel = titleCase(item.source.id || item.primaryRoute)
  const title = `${layer} — Project Profile: ${sourceLabel}`
  const nodeId = slugify(item.source.id || item.id)
  const facets = item.facets.join(', ')
  const relatedRoutes = item.relatedRoutes.length ? item.relatedRoutes.join(', ') : 'none'
  const evidence = item.evidence.length
    ? item.evidence.map((entry) => `- ${entry.path ? `\`${entry.path}\` — ` : ''}${entry.summary}`).join('\n')
    : '- none'
  const content = `# ${title}

Status: needs-interview
Date: ${generatedAt.slice(0, 10)}
Layer: ${layer}
Source: Project Profile V2 queue item \`${item.id}\`

## Rule digest

- Status: needs-review
- Layer: ${layer}
- Scope: host-project
- Applies when:
  - completing Project Profile V2 queue item \`${item.id}\`
  - filling ${item.primaryRoute} information discovered by Project Interview V2
- Must:
  - replace needs-interview placeholders with explicit confirmed project facts before relying on this record
  - keep Project Profile queue evidence linked until the record is completed
- Must not:
  - treat this generated skeleton as confirmed project truth
- Record completion:
  - update this record when the corresponding Project Profile answers are confirmed
- Related records:
  - \`.lazy-harness/spec/platform/project-profile-v2.md\`
  - \`.lazy-harness/tests/project-profile-v2.md\`

## Project Profile queue promotion

- Queue item: \`${item.id}\`
- Source: ${item.source.kind} / \`${item.source.id}\`
- Primary route: ${item.primaryRoute}
- Facets: ${facets}
- Related routes: ${relatedRoutes}
- Summary: ${item.summary}
- Promoted at: ${generatedAt}
- Completion status: needs-interview

## Evidence

${evidence}

## Project Map branch

- Anchor: \`project-profile-v2\`
- Branch: \`${item.primaryRoute}\`
- Node: \`${nodeId}\`
- Primary: \`${item.primaryRoute}\`
- Facets: ${facets}
- Edges:
  - \`project-profile-v2 --seeds--> ${nodeId}\`
- Related records:
  - \`.lazy-harness/spec/platform/project-profile-v2.md\`
  - \`.lazy-harness/tests/project-profile-v2.md\`

## Implementation map

- Status: planned
- Primary files:
  - \`${path}\` — generated needs-interview record target.
  - \`.lazy-harness/scripts/project-profile.ts\` — record target writer.
  - \`.lazy-harness/project/profile-queue.json\` — queue source when present.
- Key symbols:
  - \`project-profile.ts#buildRecordPromotionWrite\`
  - \`project-profile.ts#applyPromoteV2\`
- Protection:
  - \`self-test.py#check_project_profile_v2_queue_runtime\`
- Ownership boundaries:
  - This generated record is not confirmed domain/project truth until a user fills it.
  - Do not escalate this skeleton to active guidance without explicit confirmation.

## Discovery capture

- DDD: ${layer === 'DDD' ? 'candidate needs-interview record created' : 'none'}.
- BDD: ${layer === 'BDD' ? 'candidate needs-interview record created' : 'none'}.
- SDD: ${layer === 'SDD' ? 'candidate needs-interview record created' : 'updated, Project Profile V2 record writer created this skeleton'}.
- TDD: ${layer === 'TDD' ? 'candidate needs-interview record created' : 'covered by Project Profile V2 queue runtime self-test'}.
- ADR: ${layer === 'ADR' ? 'candidate needs-interview record created' : 'none'}.
- SSOT: ${layer === 'SSOT' ? 'candidate needs-interview record created' : 'none'}.
- Planning: Project Profile V2 queue item promoted to a needs-interview record skeleton.
`
  return {
    kind: 'record',
    path,
    action: exists ? 'skip-existing' : 'create',
    content,
    summary: exists ? `Record target already exists for ${item.id}` : `Create needs-interview record target for ${item.id}`,
    effect: {
      kind: 'record',
      path,
      status: 'applied',
      action: exists ? 'skip-existing-record' : 'create-record',
      summary: exists ? `Record target already existed for ${item.id}` : `Created needs-interview record target for ${item.id}`,
      reason: 'Record target writer creates only needs-interview skeletons and does not assert confirmed project facts.',
    },
  }
}

function candidateRowId(item: ProjectProfileQueueItem): string {
  return `cand_project_profile_v2_${createHash('sha256').update(`${item.id}\0${item.source.kind}\0${item.source.id}\0${item.summary}`).digest('hex').slice(0, 16)}`
}

function buildCandidatePromotionWrite(item: ProjectProfileQueueItem): ProjectProfileCandidatePromotionWrite | null {
  if (item.promotionTarget.kind !== 'candidate-row') return null
  const row = {
    id: candidateRowId(item),
    kind: 'project-profile-v2-candidate-row',
    status: 'candidate',
    source: 'project-profile-v2',
    candidateType: 'project-profile-v2-promotion',
    topic: item.source.id,
    summary: item.summary,
    candidate: item.summary,
    primaryRoute: item.primaryRoute,
    facets: item.facets,
    relatedRoutes: item.relatedRoutes,
    promotion: {
      queueItemId: item.id,
      source: item.source,
      targetKind: item.promotionTarget.kind,
      requiresConfirmation: item.promotionTarget.requiresConfirmation,
    },
    evidence: item.evidence,
    rawMessageStored: false,
  }
  return {
    kind: 'candidate-row',
    path: '.lazy-harness/knowledge/candidates.jsonl',
    row,
    summary: `Append stable candidate row for ${item.id}`,
  }
}

function candidateEffectForStatus(item: ProjectProfileQueueItem, write: ProjectProfileCandidatePromotionWrite, status: JsonlAppendStatus): ProjectProfilePromotionTargetEffect {
  const action = status === 'appended'
    ? 'append-candidate-row'
    : status === 'deduped-identical'
      ? 'dedupe-candidate-row'
      : 'conflict-candidate-row'
  return {
    kind: 'candidate-row',
    path: write.path,
    status: status === 'conflict-recorded' ? 'deferred' : 'applied',
    action,
    summary: `${status} candidate row for ${item.id}`,
    reason: status === 'conflict-recorded'
      ? 'A candidate row with the same id but different content already exists; conflict was recorded for review.'
      : 'Candidate-row target writer appends only stable candidates.jsonl rows and does not promote them to canonical records.',
  }
}

function uniqueSortedStrings(values: string[]): string[] {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))].sort((a, b) => a.localeCompare(b))
}

function xmlList(tag: string, values: string[], indent = '      '): string {
  return values.map((value) => `${indent}<${tag}>${xmlEscape(value)}</${tag}>`).join('\n')
}

function projectMapBranchFeatureId(item: ProjectProfileQueueItem): string {
  return slugify(item.source.id || item.id)
}

function projectMapBranchFeatureLabel(item: ProjectProfileQueueItem): string {
  const [prefix] = item.summary.split(':')
  return (prefix || titleCase(item.source.id || item.id)).trim()
}

function buildProjectMapBranchFeature(item: ProjectProfileQueueItem): Record<string, unknown> {
  const id = projectMapBranchFeatureId(item)
  const label = projectMapBranchFeatureLabel(item)
  return {
    id,
    status: 'candidate',
    label,
    aliases: uniqueSortedStrings([label, item.source.id, item.primaryRoute, ...item.relatedRoutes]),
    routes: uniqueSortedStrings([`project-profile:${item.source.kind}:${item.source.id}`, `primary:${item.primaryRoute}`]),
    components: uniqueSortedStrings(['Project Profile V2 queue item', `Project Map seed ${item.source.id}`]),
    records: [
      { layer: 'SDD', path: '.lazy-harness/spec/platform/project-profile-v2.md' },
      { layer: 'SDD', path: '.lazy-harness/spec/platform/project-map-v2.md' },
      { layer: 'TDD', path: '.lazy-harness/tests/project-profile-v2.md' },
    ],
    sourceFiles: ['.lazy-harness/scripts/project-profile.ts', '.lazy-harness/project/feature-navigation.xml'],
    tests: ['.lazy-harness/scripts/self-test.py', '.lazy-harness/tests/project-profile-v2.md'],
    note: 'Candidate retrieval/navigation entry created from an accepted Project Profile V2 project-map-branch queue item. Use it as a cue only until linked canonical records are confirmed.',
  }
}

function renderProjectMapBranchFeatureXml(feature: Record<string, unknown>): string {
  const aliases = feature.aliases as string[]
  const routes = feature.routes as string[]
  const components = feature.components as string[]
  const records = feature.records as Array<{ layer: string; path: string }>
  const sourceFiles = feature.sourceFiles as string[]
  const tests = feature.tests as string[]
  const note = String(feature.note || '')
  return `  <feature id="${xmlEscape(String(feature.id))}" status="${xmlEscape(String(feature.status))}">
    <label>${xmlEscape(String(feature.label))}</label>
    <aliases>
${aliases.map((alias) => `      <alias lang="${alias === feature.id ? 'symbol' : 'en'}">${xmlEscape(alias)}</alias>`).join('\n')}
    </aliases>
    <routes>
${xmlList('route', routes)}
    </routes>
    <components>
${xmlList('component', components)}
    </components>
    <records>
${records.map((record) => `      <record layer="${xmlEscape(record.layer)}">${xmlEscape(record.path)}</record>`).join('\n')}
    </records>
    <sourceFiles>
${xmlList('path', sourceFiles)}
    </sourceFiles>
    <tests>
${xmlList('path', tests)}
    </tests>
    <risk>${xmlEscape(note)}</risk>
  </feature>`
}

function featureNavigationWithEntry(existing: string | null, featureXml: string): string {
  if (!existing || !existing.trim()) {
    return `<?xml version="1.0" encoding="UTF-8"?>
<featureNavigation id="project-profile-v2-promotions" status="candidate">
  <purpose>Project Profile V2 promoted feature navigation candidates.</purpose>
  <scope>Host-local retrieval/navigation map; candidate entries are cues and not canonical project truth by themselves.</scope>

${featureXml}
</featureNavigation>
`
  }
  if (!existing.includes('</featureNavigation>')) throw new Error('feature-navigation.xml must contain a closing </featureNavigation> tag before project-map-branch promotion')
  return existing.replace(/\s*<\/featureNavigation>\s*$/, `\n\n${featureXml}\n</featureNavigation>\n`)
}

function buildProjectMapBranchPromotionWrite(item: ProjectProfileQueueItem, root: string): ProjectProfileProjectMapBranchPromotionWrite | null {
  if (item.promotionTarget.kind !== 'project-map-branch') return null
  const path = '.lazy-harness/project/feature-navigation.xml' as const
  const abs = join(root, path)
  const existing = existsSync(abs) ? readFileSync(abs, 'utf8') : null
  const feature = buildProjectMapBranchFeature(item)
  const featureId = String(feature.id)
  const exists = Boolean(existing && new RegExp(`<feature\\b[^>]*\\bid=["']${featureId.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}["']`).test(existing))
  const featureXml = renderProjectMapBranchFeatureXml(feature)
  const content = exists ? (existing || '') : featureNavigationWithEntry(existing, featureXml)
  return {
    kind: 'project-map-branch',
    path,
    action: exists ? 'skip-existing' : 'append',
    feature,
    content,
    summary: exists ? `Project Map feature-navigation entry already exists for ${featureId}` : `Append candidate feature-navigation entry for ${featureId}`,
    effect: {
      kind: 'project-map-branch',
      path,
      status: 'applied',
      action: exists ? 'skip-existing-project-map-branch' : 'append-project-map-branch',
      summary: exists ? `Feature-navigation entry already existed for ${featureId}` : `Appended candidate feature-navigation entry for ${featureId}`,
      reason: 'Project-map-branch writer updates only feature-navigation retrieval cues and does not write canonical layer truth by itself.',
    },
  }
}

function updateLoopEventId(item: ProjectProfileQueueItem, queue: ProjectProfileQueueV1): string {
  const occurredAt = queue.sourcePacket?.generatedAt || queue.createdAt || queue.updatedAt
  return `evt_project_profile_v2_${createHash('sha256').update(`${item.id}\0${item.source.kind}\0${item.source.id}\0${occurredAt}`).digest('hex').slice(0, 16)}`
}

function buildUpdateLoopPromotionWrite(item: ProjectProfileQueueItem, queue: ProjectProfileQueueV1): ProjectProfileUpdateLoopPromotionWrite | null {
  if (item.promotionTarget.kind !== 'update-loop-event') return null
  const path = '.lazy-harness/knowledge/project-map-update-events.jsonl' as const
  const occurredAt = queue.sourcePacket?.generatedAt || queue.createdAt || queue.updatedAt
  const row = {
    schemaVersion: 'project-map-update-event/v1',
    id: updateLoopEventId(item, queue),
    eventType: 'project-profile-refresh',
    source: 'project-profile',
    occurredAt,
    scope: 'framework-global',
    summary: item.summary,
    target: {
      anchorId: 'project-profile-v2',
      branch: 'ownership',
      nodeId: item.source.id || item.id,
      primary: 'ownership',
      facets: ['SSOT', 'Project'],
    },
    transition: {
      from: 'observation',
      to: 'candidate',
      requiresConfirmation: true,
      canonicalRecords: [],
      candidateStore: '.lazy-harness/knowledge/candidates.jsonl',
    },
    evidence: item.evidence.map((entry) => ({
      kind: entry.kind,
      ...(entry.path ? { path: entry.path } : {}),
      summary: entry.summary,
      redaction: 'compact',
    })),
    effects: [
      { action: 'append-candidate', path: '.lazy-harness/knowledge/candidates.jsonl' },
    ],
    promotion: {
      queueItemId: item.id,
      source: item.source,
      targetKind: item.promotionTarget.kind,
      targetStore: path,
      requiresConfirmation: item.promotionTarget.requiresConfirmation,
    },
  }
  return {
    kind: 'update-loop-event',
    path,
    row,
    summary: `Append stable Project Map update event for ${item.id}`,
  }
}

function updateLoopEffectForStatus(item: ProjectProfileQueueItem, write: ProjectProfileUpdateLoopPromotionWrite, status: JsonlAppendStatus): ProjectProfilePromotionTargetEffect {
  const action = status === 'appended'
    ? 'append-update-loop-event'
    : status === 'deduped-identical'
      ? 'dedupe-update-loop-event'
      : 'conflict-update-loop-event'
  return {
    kind: 'update-loop-event',
    path: write.path,
    status: status === 'conflict-recorded' ? 'deferred' : 'applied',
    action,
    summary: `${status} update-loop event for ${item.id}`,
    reason: status === 'conflict-recorded'
      ? 'An update-loop event with the same id but different content already exists; conflict was recorded for review.'
      : 'Update-loop target writer appends only non-canonical Project Map update-event rows and does not write canonical records by itself.',
  }
}

function buildRulebookPromotionWrite(item: ProjectProfileQueueItem, generatedAt: string, root: string): ProjectProfileRulebookPromotionWrite | null {
  if (item.promotionTarget.kind !== 'rulebook') return null
  const path = rulebookPathForPromotion(item)
  const abs = join(root, path)
  const exists = existsSync(abs)
  const sourceId = item.source.id || item.id
  const title = `Project Profile Rule Candidate: ${titleCase(sourceId)}`
  const facets = item.facets.join(', ')
  const relatedRoutes = item.relatedRoutes.length ? item.relatedRoutes.join(', ') : 'none'
  const evidence = item.evidence.length
    ? item.evidence.map((entry) => `- ${entry.path ? `\`${entry.path}\` — ` : ''}${entry.summary}`).join('\n')
    : '- none'
  const content = `# ${title}

Status: draft
Layer: Rulebook
Scope: host-project
Owner: project-profile-v2
Level: discover
Related records:
- \`.lazy-harness/spec/platform/project-profile-v2.md\`
- \`.lazy-harness/tests/project-profile-v2.md\`
- \`.lazy-harness/decisions/0044-project-operating-rulebook.md\`

## Rule digest

- Applies when:
  - reviewing_project_profile_rulebook_candidate
  - completing Project Profile V2 queue item \`${item.id}\`
- Prefer:
  - review and edit this draft rule before relying on it
  - add an explicit capability binding only after human confirmation
- Avoid:
  - treating this generated draft as active project policy
  - promoting it directly to default, warn, or block behavior
- Requires:
  - explicit human confirmation before changing Status to active
  - explicit capability design before adding Related capability or machine-readable action guidance
- Bypass:
  - no bypass needed; draft/discover entries are advisory only
- Record completion:
  - update Project Profile V2 records, capability binding records, and tests if this generated draft becomes an active operating rule

## Operating rule

This is a generated Project Profile V2 rulebook draft. It captures a possible project operating policy discovered from queue item \`${item.id}\`.

- Source: ${item.source.kind} / \`${sourceId}\`
- Primary route: ${item.primaryRoute}
- Facets: ${facets}
- Related routes: ${relatedRoutes}
- Summary: ${item.summary}
- Promoted at: ${generatedAt}

Do not treat this entry as confirmed project operating policy until a human reviews and updates it.

## Examples

- Good: review this draft, decide whether it should become an active rule, then add explicit capability binding if it should steer actions.
- Bad: treat this generated draft as a default/warn/block rule without confirmation.
- Bad: this generated draft must not be treated as active default/warn/block behavior.

## Capability binding

- Capability id: none yet
- Enforcement level: discover
- Preferred actions: none yet
- Discouraged actions: none yet
- Intent labels: reviewing_project_profile_rulebook_candidate

## Evidence

${evidence}

## Implementation map

- Source records:
  - \`.lazy-harness/spec/platform/project-profile-v2.md\`
  - \`.lazy-harness/decisions/0044-project-operating-rulebook.md\`
- Source queue:
  - \`.lazy-harness/project/profile-queue.json\`
- Key symbols:
  - \`project-profile.ts#buildRulebookPromotionWrite\`
  - \`project-profile.ts#applyPromoteV2\`
- Validation:
  - \`.lazy-harness/bin/lazy rules audit --strict\`
- Tests:
  - \`self-test.py#check_project_profile_v2_queue_runtime\`

## Discovery capture

- DDD: none.
- BDD: candidate operating behavior captured as draft rulebook, not a confirmed scenario.
- SDD: updated by Project Profile V2 rulebook writer contract.
- TDD: protected by Project Profile V2 queue runtime self-test.
- ADR: follows ADR 0044 project operating rulebook storage.
- SSOT: rule placement follows \`.lazy-harness/ssot/rule-sources.md\`; no capability binding added yet.
- Planning: Project Profile V2 queue item promoted to a draft/discover rulebook entry.
`
  return {
    kind: 'rulebook',
    path,
    action: exists ? 'skip-existing' : 'create',
    content,
    summary: exists ? `Rulebook target already exists for ${item.id}` : `Create draft/discover rulebook target for ${item.id}`,
    effect: {
      kind: 'rulebook',
      path,
      status: 'applied',
      action: exists ? 'skip-existing-rulebook' : 'create-rulebook',
      summary: exists ? `Rulebook target already existed for ${item.id}` : `Created draft/discover rulebook target for ${item.id}`,
      reason: 'Rulebook target writer creates only draft/discover entries and does not add capability bindings or active enforcement levels.',
    },
  }
}

function loadCapabilityRegistryForPromotion(root: string, path: string): { version: number; capabilities: Record<string, unknown>[] } {
  const abs = join(root, path)
  if (!existsSync(abs)) return { version: 1, capabilities: [] }
  const parsed = JSON.parse(readFileSync(abs, 'utf8'))
  return {
    version: Number(parsed?.version || 1),
    capabilities: Array.isArray(parsed?.capabilities) ? parsed.capabilities : [],
  }
}

function capabilityIdForPromotion(item: ProjectProfileQueueItem): string {
  return `project-profile-v2-${slugify(item.source.id || item.id)}`.slice(0, 128)
}

function buildCapabilityForPromotion(item: ProjectProfileQueueItem): Record<string, unknown> {
  const sourceId = item.source.id || item.id
  return {
    id: capabilityIdForPromotion(item),
    kind: 'checklist',
    level: 'discover',
    sourceRecord: '.lazy-harness/project/profile-queue.json',
    appliesWhen: [
      'reviewing_project_profile_capability_candidate',
      'completing_project_profile_v2_queue_item',
    ],
    actions: [
      'Review Project Profile V2 capability binding candidate',
      'lazy capability audit',
    ],
    checklistPath: '.lazy-harness/project/profile-queue.json',
    description: `Discover Project Profile V2 capability binding candidate from ${sourceId}.`,
    owner: 'host-project',
    tags: ['project-profile-v2', 'capability-binding', 'discover'],
    preferredActions: ['lazy capability audit', '.lazy-harness/ssot/capabilities.json'],
    requiresReasonForBypass: false,
    projectProfileQueueItemId: item.id,
    projectProfileSource: item.source,
  }
}

function upsertCapabilityForPromotion(registry: { version: number; capabilities: Record<string, unknown>[] }, capability: Record<string, unknown>): { status: 'created' | 'updated' | 'unchanged'; registry: { version: number; capabilities: Record<string, unknown>[] } } {
  const id = String(capability.id)
  const capabilities = registry.capabilities.slice()
  const index = capabilities.findIndex((candidate) => candidate?.id === id)
  let status: 'created' | 'updated' | 'unchanged' = 'created'
  if (index >= 0) {
    if (JSON.stringify(capabilities[index]) === JSON.stringify(capability)) status = 'unchanged'
    else {
      capabilities[index] = capability
      status = 'updated'
    }
  } else {
    capabilities.push(capability)
  }
  capabilities.sort((a, b) => String(a.id).localeCompare(String(b.id)))
  return { status, registry: { version: registry.version || 1, capabilities } }
}

function buildCapabilityPromotionWrite(item: ProjectProfileQueueItem, root: string): ProjectProfileCapabilityPromotionWrite | null {
  if (item.promotionTarget.kind !== 'capability-binding') return null
  const path = '.lazy-harness/ssot/capabilities.json' as const
  const capability = buildCapabilityForPromotion(item)
  const { status, registry } = upsertCapabilityForPromotion(loadCapabilityRegistryForPromotion(root, path), capability)
  return {
    kind: 'capability-binding',
    path,
    status,
    capability,
    registry,
    summary: `${status} discover/checklist capability for ${item.id}`,
    effect: {
      kind: 'capability-binding',
      path,
      status: 'applied',
      action: 'upsert-capability',
      summary: `${status} discover/checklist capability for ${item.id}`,
      reason: 'Capability-binding writer creates only discover/checklist registry entries and does not create hooks or warn/block/default enforcement.',
    },
  }
}

function selectAcceptedPromotionItem(root: string, itemId?: string): { queue: ProjectProfileQueueV1; item: ProjectProfileQueueItem; index: number } {
  if (!itemId) throw new Error('promote-v2 requires --item <queue-item-id>')
  const queue = readProfileQueue(root)
  const index = queue.items.findIndex((candidate) => candidate.id === itemId)
  if (index < 0) throw new Error(`Queue item not found: ${itemId}`)
  const item = queue.items[index]
  if (item.status !== 'accepted') throw new Error(`promote-v2 only promotes status=accepted items; ${item.id} is status=${item.status}`)
  return { queue, item, index }
}

function buildPromoteV2Preview(args: Args): ProjectProfilePromoteV2Preview {
  if (!args.dryRun || args.confirm) throw new Error('promote-v2 --dry-run preview requires --dry-run without --confirm')
  const { item } = selectAcceptedPromotionItem(args.root, args.item)
  const generatedAt = new Date().toISOString()
  const target = item.promotionTarget
  const targetPath = pathForPromotionTarget(target)
  const plannedWrites = [{
    kind: target.kind,
    path: targetPath,
    action: actionForPromotionKind(target.kind),
    requiresConfirmation: true as const,
    summary: targetPath
      ? `Preview ${target.kind} promotion for ${item.id} to ${targetPath}`
      : `Preview ${target.kind} promotion for ${item.id}`,
  }]
  const promotedTo = plannedWrites.map((write) => write.path || write.kind)
  return {
    ok: true,
    mode: 'project-profile.promote-v2',
    schemaVersion: 'project-profile-promote-preview/v1',
    root: args.root,
    generatedAt,
    dryRun: true,
    queuePath: '.lazy-harness/project/profile-queue.json',
    item,
    plannedWrites,
    queueUpdate: {
      id: item.id,
      from: 'accepted',
      to: 'promoted',
      promotedAt: generatedAt,
      promotedTo,
      previewOnly: true,
    },
    warnings: [
      'promote-v2 --dry-run is preview only.',
      'No queue status is changed and no canonical record/rule/capability/update-loop event is written.',
      'promote-v2 --confirm must re-check status=accepted before mutating the queue file.',
    ],
  }
}

function applyPromoteV2(args: Args): ProjectProfilePromoteV2Result {
  if (!args.confirm || args.dryRun) throw new Error('promote-v2 --confirm requires --confirm without --dry-run')
  const { queue, item, index } = selectAcceptedPromotionItem(args.root, args.item)
  const generatedAt = new Date().toISOString()
  const recordWrite = buildRecordPromotionWrite(item, generatedAt, args.root)
  const projectMapBranchWrite = buildProjectMapBranchPromotionWrite(item, args.root)
  const candidateWrite = buildCandidatePromotionWrite(item)
  const rulebookWrite = buildRulebookPromotionWrite(item, generatedAt, args.root)
  const capabilityWrite = buildCapabilityPromotionWrite(item, args.root)
  const updateLoopWrite = buildUpdateLoopPromotionWrite(item, queue)
  const appliedWrites: ProjectProfilePromoteV2Result['appliedWrites'] = []
  let candidateAppendStatus: JsonlAppendStatus | null = null
  let updateLoopAppendStatus: JsonlAppendStatus | null = null
  if (candidateWrite) {
    const candidateAbs = join(args.root, candidateWrite.path)
    candidateAppendStatus = appendJsonlStable(candidateAbs, candidateWrite.row, 'id', args.root)
    appliedWrites.push({ path: candidateWrite.path, action: candidateAppendStatus, summary: `${candidateWrite.summary} (${candidateAppendStatus})` })
  }
  if (updateLoopWrite) {
    const updateLoopAbs = join(args.root, updateLoopWrite.path)
    updateLoopAppendStatus = appendJsonlStable(updateLoopAbs, updateLoopWrite.row, 'id', args.root)
    appliedWrites.push({ path: updateLoopWrite.path, action: updateLoopAppendStatus, summary: `${updateLoopWrite.summary} (${updateLoopAppendStatus})` })
  }
  const targetEffects = [recordWrite?.effect || projectMapBranchWrite?.effect || rulebookWrite?.effect || capabilityWrite?.effect || (candidateWrite && candidateAppendStatus ? candidateEffectForStatus(item, candidateWrite, candidateAppendStatus) : updateLoopWrite && updateLoopAppendStatus ? updateLoopEffectForStatus(item, updateLoopWrite, updateLoopAppendStatus) : buildPromotionTargetEffect(item))]
  const promotedTo = targetEffects.map((effect) => effect.path || effect.kind)
  const promotedItem: ProjectProfileQueueItem = {
    ...item,
    status: 'promoted',
    promotedAt: generatedAt,
    promotedTo,
    promotionEffects: targetEffects,
  }
  const items = queue.items.slice()
  items[index] = promotedItem
  const nextQueue: ProjectProfileQueueV1 = {
    ...queue,
    root: args.root,
    mode: 'project-profile.queue-v2-apply',
    dryRun: false,
    updatedAt: generatedAt,
    items,
    summary: summarizeProfileQueueItems(items),
    warnings: [
      ...queue.warnings.filter((warning) => !warning.includes('candidates/rules/capabilities/update-loop events require later explicit promotion')),
      'promote-v2 --confirm wrote queue status/promoted metadata and applied only the selected target-kind writer when implemented.',
      'Unimplemented target writers remain deferred by target kind.',
    ],
  }
  if (recordWrite) {
    const recordAbs = join(args.root, recordWrite.path)
    if (recordWrite.action === 'create') {
      ensureParent(recordAbs)
      writeFileSync(recordAbs, recordWrite.content, 'utf8')
      appliedWrites.push({ path: recordWrite.path, action: 'written', summary: recordWrite.summary })
    } else {
      appliedWrites.push({ path: recordWrite.path, action: 'skipped', summary: recordWrite.summary })
    }
  }
  if (projectMapBranchWrite) {
    const featureNavAbs = join(args.root, projectMapBranchWrite.path)
    if (projectMapBranchWrite.action === 'append') {
      ensureParent(featureNavAbs)
      writeFileSync(featureNavAbs, projectMapBranchWrite.content, 'utf8')
      appliedWrites.push({ path: projectMapBranchWrite.path, action: 'written', summary: projectMapBranchWrite.summary })
    } else {
      appliedWrites.push({ path: projectMapBranchWrite.path, action: 'skipped', summary: projectMapBranchWrite.summary })
    }
  }
  if (rulebookWrite) {
    const rulebookAbs = join(args.root, rulebookWrite.path)
    if (rulebookWrite.action === 'create') {
      ensureParent(rulebookAbs)
      writeFileSync(rulebookAbs, rulebookWrite.content, 'utf8')
      appliedWrites.push({ path: rulebookWrite.path, action: 'written', summary: rulebookWrite.summary })
    } else {
      appliedWrites.push({ path: rulebookWrite.path, action: 'skipped', summary: rulebookWrite.summary })
    }
  }
  if (capabilityWrite) {
    const capabilityAbs = join(args.root, capabilityWrite.path)
    ensureParent(capabilityAbs)
    writeFileSync(capabilityAbs, JSON.stringify(capabilityWrite.registry, null, 2) + '\n', 'utf8')
    appliedWrites.push({ path: capabilityWrite.path, action: capabilityWrite.status, summary: capabilityWrite.summary })
  }
  const abs = join(args.root, nextQueue.queuePath)
  ensureParent(abs)
  writeFileSync(abs, JSON.stringify({ ...nextQueue, appliedWrites: undefined }, null, 2) + '\n', 'utf8')
  appliedWrites.push({ path: nextQueue.queuePath, action: 'written', summary: `Promoted ${item.id} in Project Profile queue${recordWrite ? ' and applied record target writer' : projectMapBranchWrite ? ' and applied project-map-branch writer' : rulebookWrite ? ' and applied rulebook writer' : capabilityWrite ? ' and applied capability-binding writer' : candidateWrite ? ' and applied candidate-row writer' : updateLoopWrite ? ' and applied update-loop event writer' : ' only'}` })
  return {
    ok: true,
    mode: 'project-profile.promote-v2-apply',
    schemaVersion: 'project-profile-promote-result/v1',
    root: args.root,
    generatedAt,
    dryRun: false,
    queuePath: nextQueue.queuePath,
    item: promotedItem,
    targetEffects,
    projectMapBranch: projectMapBranchWrite?.feature,
    candidateRow: candidateWrite?.row,
    capability: capabilityWrite?.capability,
    updateEvent: updateLoopWrite?.row,
    queueUpdate: {
      id: item.id,
      from: 'accepted',
      to: 'promoted',
      promotedAt: generatedAt,
      promotedTo,
      previewOnly: false,
    },
    appliedWrites,
    warnings: recordWrite
      ? [
        'promote-v2 --confirm updated .lazy-harness/project/profile-queue.json and a needs-interview record target.',
        'The generated record target is a skeleton and must not be treated as confirmed project truth.',
        'No rulebook, capability, candidate row, or update-loop event was written.',
      ]
      : projectMapBranchWrite
        ? [
          'promote-v2 --confirm updated .lazy-harness/project/profile-queue.json and .lazy-harness/project/feature-navigation.xml.',
          'The generated feature-navigation entry is a retrieval cue and must not be treated as canonical project truth by itself.',
          'No canonical record, rulebook, capability, candidate row, or update-loop event was written.',
        ]
      : candidateWrite
        ? [
          'promote-v2 --confirm updated .lazy-harness/project/profile-queue.json and .lazy-harness/knowledge/candidates.jsonl.',
          'The generated candidate row is not canonical project truth until promoted separately.',
          'No rulebook, capability, or update-loop event was written.',
        ]
      : rulebookWrite
        ? [
          'promote-v2 --confirm updated .lazy-harness/project/profile-queue.json and a draft/discover rulebook entry.',
          'The generated rulebook entry is draft/discover and must not be treated as active default/warn/block behavior.',
          'No capability binding or update-loop event was written.',
        ]
      : capabilityWrite
        ? [
          'promote-v2 --confirm updated .lazy-harness/project/profile-queue.json and .lazy-harness/ssot/capabilities.json.',
          'The generated capability is discover/checklist only and must not be treated as default/warn/block enforcement.',
          'No update-loop event was written.',
        ]
      : updateLoopWrite
        ? [
          'promote-v2 --confirm updated .lazy-harness/project/profile-queue.json and .lazy-harness/knowledge/project-map-update-events.jsonl.',
          'The generated update-loop event is non-canonical and must not be treated as confirmed project truth by itself.',
          'No canonical record, rulebook, capability, or candidate row was written.',
        ]
      : [
        'promote-v2 --confirm updated only .lazy-harness/project/profile-queue.json.',
        'Target-specific canonical writers were separated as deferred effects.',
        'No canonical record, rulebook, capability, candidate row, or update-loop event was written.',
      ],
  }
}

function renderPromoteV2Md(result: ProjectProfilePromoteV2Output): string {
  return [
    result.dryRun ? '# Project Profile promote V2 dry-run' : '# Project Profile promote V2 apply',
    '',
    `- Item: \`${result.item.id}\``,
    `- Status: ${result.item.status}`,
    `- Primary route: ${result.item.primaryRoute}`,
    `- Facets: ${result.item.facets.join(', ')}`,
    `- Queue update: ${result.queueUpdate.from} → ${result.queueUpdate.to}${result.queueUpdate.previewOnly ? ' (preview)' : ''}`,
    '',
    ...('plannedWrites' in result ? [
      '## Planned writes',
      ...result.plannedWrites.map((write) => `- ${write.action}: ${write.kind}${write.path ? ` → \`${write.path}\`` : ''}`),
      '',
    ] : []),
    ...('targetEffects' in result ? [
      '## Target effects',
      ...result.targetEffects.map((effect) => `- ${effect.status}: ${effect.kind}${effect.path ? ` → \`${effect.path}\`` : ''}`),
      '',
    ] : []),
    ...('appliedWrites' in result ? [
      '## Applied writes',
      ...result.appliedWrites.map((write) => `- ${write.action}: \`${write.path}\` — ${write.summary}`),
      '',
    ] : []),
    '',
    '## Warnings',
    ...result.warnings.map((warning) => `- ${warning}`),
    '',
  ].join('\n')
}

function renderProfileQueueMd(queue: ProjectProfileQueueV1): string {
  const lines: string[] = []
  lines.push(queue.mode === 'project-profile.queue-v2-apply' ? '# Project Profile queue V2 apply' : '# Project Profile queue V2')
  lines.push('')
  lines.push(`- Root: \`${queue.root}\``)
  lines.push(`- Dry run: ${queue.dryRun ? 'yes' : 'no'}`)
  lines.push(`- Queue path: \`${queue.queuePath}\``)
  lines.push(`- Items: ${queue.summary.total}`)
  lines.push(`- Pending policy candidates: ${queue.summary.pendingPolicyCandidates}`)
  lines.push(`- Pending event-ready metadata: ${queue.summary.pendingEventReadyMetadata}`)
  lines.push('')
  lines.push('## Items')
  for (const item of queue.items) {
    lines.push(`- ${item.id}: ${item.primaryRoute} [${item.facets.join(', ')}] — ${item.summary}`)
  }
  if (queue.appliedWrites?.length) {
    lines.push('')
    lines.push('## Applied writes')
    for (const write of queue.appliedWrites) lines.push(`- ${write.action}: \`${write.path}\` — ${write.summary}`)
  }
  lines.push('')
  lines.push('## Warnings')
  for (const warning of queue.warnings) lines.push(`- ${warning}`)
  return lines.join('\n')
}

function parseAnswers(args: Args): ProfileAnswer[] {
  if (!args.answers) throw new Error('fill mode requires --answers <answers.json>')
  const raw = JSON.parse(readFileSync(args.answers, 'utf8')) as unknown
  const entries: unknown = Array.isArray(raw)
    ? raw
    : raw && typeof raw === 'object' && Array.isArray((raw as { answers?: unknown }).answers)
      ? (raw as { answers: unknown[] }).answers
      : raw && typeof raw === 'object'
        ? Object.entries(raw as Record<string, unknown>).map(([target, value]) => ({ target, value }))
        : []
  if (!Array.isArray(entries)) throw new Error('answers file must be an array, an {answers: []} object, or a target/value object')
  return entries.map((entry, index): ProfileAnswer => {
    if (!entry || typeof entry !== 'object') throw new Error(`answers[${index}] must be an object`)
    const target = String((entry as { target?: unknown }).target ?? '').trim()
    const value = String((entry as { value?: unknown }).value ?? '').trim()
    const sourceValue = (entry as { source?: unknown }).source
    const source = sourceValue === undefined ? undefined : String(sourceValue).trim()
    if (!target) throw new Error(`answers[${index}] missing target`)
    if (!value) throw new Error(`answers[${index}] missing value`)
    return { target, value, ...(source ? { source } : {}) }
  })
}

function confirmedAttrs(attrs: string, answer: ProfileAnswer, confirmedAt: string): string {
  const sourceAttr = answer.source ? ` source="${xmlEscape(answer.source)}"` : ''
  return attrs.replace(/status="needs-interview"/, `status="confirmed" confirmedAt="${xmlEscape(confirmedAt)}"${sourceAttr}`)
}

function fillArtifact(root: string, artifact: RequiredArtifact, answers: ProfileAnswer[], generatedAt: string): { write?: FillProposedWrite; matched: Set<string> } {
  if (artifact.status !== 'present') return { matched: new Set() }
  const abs = join(root, artifact.path)
  const original = readFileSync(abs, 'utf8')
  const answersByTarget = new Map(answers.map((answer) => [answer.target, answer]))
  const matched = new Set<string>()
  const updated = original.replace(/<([A-Za-z][\w:-]*)([^>]*\sstatus="needs-interview"[^>]*)\/\s*>/g, (full, elementName: string, attrs: string) => {
    if (['projectProfile', 'projectStack', 'projectFilesystem', 'featureNavigation', 'testStrategy'].includes(elementName)) return full
    const target = labelForTarget(artifact.path, elementName, attrs)
    const answer = answersByTarget.get(target)
    if (!answer) return full
    matched.add(target)
    return `<${elementName}${confirmedAttrs(attrs, answer, generatedAt)}>${xmlEscape(answer.value)}</${elementName}>`
  })
  if (updated === original) return { matched }
  return {
    matched,
    write: {
      path: artifact.path,
      action: 'update',
      matchedTargets: [...matched],
      content: updated,
      summary: `Confirm ${matched.size} Project Profile field(s) from explicit answers`,
    },
  }
}

function buildFillResult(args: Args): FillResult {
  if (!args.dryRun && !args.confirm) throw new Error('fill mode requires --dry-run for preview or --confirm to write explicit confirmed answers')
  const answers = parseAnswers(args)
  const inspectResult = inspect(args)
  const generatedAt = new Date().toISOString()
  const proposedWrites: FillProposedWrite[] = []
  const matchedTargets = new Set<string>()
  for (const artifact of inspectResult.requiredArtifacts) {
    const result = fillArtifact(args.root, artifact, answers, generatedAt)
    for (const target of result.matched) matchedTargets.add(target)
    if (result.write) proposedWrites.push(result.write)
  }
  const unmatchedAnswers = answers.filter((answer) => !matchedTargets.has(answer.target))
  return {
    ok: true,
    mode: args.confirm && !args.dryRun ? 'project-profile.fill' : 'project-profile.fill-dry-run',
    schemaVersion: '1.0',
    root: args.root,
    generatedAt,
    dryRun: args.dryRun || !args.confirm,
    answersPath: args.answers ?? '',
    answers,
    proposedWrites,
    unmatchedAnswers,
    warnings: [
      'Fill mode only updates status="needs-interview" self-closing fields that match explicit answer targets.',
      'Unmatched answers are not written; rerun interview to inspect current open targets.',
    ],
  }
}

function applyFill(result: FillResult): FillResult {
  const appliedWrites: NonNullable<FillResult['appliedWrites']> = []
  for (const write of result.proposedWrites) {
    const abs = join(result.root, write.path)
    writeFileSync(abs, write.content, 'utf8')
    appliedWrites.push({ path: write.path, action: 'written', summary: write.summary })
  }
  return { ...result, appliedWrites }
}

function renderFillMd(result: FillResult): string {
  const lines: string[] = []
  lines.push(result.mode === 'project-profile.fill' ? '# Project Profile fill' : '# Project Profile fill dry-run')
  lines.push('')
  lines.push(`- Root: \`${result.root}\``)
  lines.push(`- Dry run: ${result.dryRun ? 'yes' : 'no'}`)
  lines.push(`- Answers: ${result.answers.length}`)
  lines.push(`- Proposed writes: ${result.proposedWrites.length}`)
  lines.push(`- Unmatched answers: ${result.unmatchedAnswers.length}`)
  lines.push('')
  lines.push('## Proposed writes')
  for (const write of result.proposedWrites) lines.push(`- \`${write.path}\`: ${write.summary} (${write.matchedTargets.join(', ')})`)
  if (result.appliedWrites?.length) {
    lines.push('')
    lines.push('## Applied writes')
    for (const write of result.appliedWrites) lines.push(`- ${write.action}: \`${write.path}\` — ${write.summary}`)
  }
  if (result.unmatchedAnswers.length) {
    lines.push('')
    lines.push('## Unmatched answers')
    for (const answer of result.unmatchedAnswers) lines.push(`- \`${answer.target}\``)
  }
  lines.push('')
  lines.push('## Warnings')
  for (const warning of result.warnings) lines.push(`- ${warning}`)
  return lines.join('\n')
}

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    if (args.mode === 'inspect') {
      const result = inspect(args)
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderInspectMd(result))
      return
    }
    if (args.mode === 'interview') {
      const interview = buildInterviewResult(args)
      const result = args.confirm && !args.dryRun ? applyInterviewQueue(interview) : interview
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderInterviewMd(result))
      return
    }
    if (args.mode === 'interview-v2') {
      const result = buildInterviewV2Result(args)
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderInterviewV2Md(result))
      return
    }
    if (args.mode === 'queue-v2') {
      const queue = buildProfileQueueV1(args)
      const result = args.confirm && !args.dryRun ? applyProfileQueue(queue) : queue
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderProfileQueueMd(result))
      return
    }
    if (args.mode === 'promote-v2') {
      if (!args.dryRun && !args.confirm) throw new Error('promote-v2 requires --dry-run for preview or --confirm to update queue status')
      const result = args.confirm && !args.dryRun ? applyPromoteV2(args) : buildPromoteV2Preview(args)
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderPromoteV2Md(result))
      return
    }
    if (args.mode === 'fill') {
      const fill = buildFillResult(args)
      const result = args.confirm && !args.dryRun ? applyFill(fill) : fill
      if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
      else console.log(renderFillMd(result))
      return
    }
    const plan = buildPlanResult(args)
    const result = args.mode === 'apply' && args.confirm && !args.dryRun ? applyConfirmed(plan) : plan
    if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
    else console.log(renderPlanMd(result))
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
