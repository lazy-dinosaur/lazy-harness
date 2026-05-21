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

type Mode = 'inspect' | 'plan' | 'apply' | 'interview'
type Format = 'json' | 'md'
type ArtifactStatus = 'present' | 'missing'

interface Args {
  mode: Mode
  format: Format
  root: string
  dryRun: boolean
  confirm: boolean
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
    if (arg === '--mode' && next && ['inspect', 'plan', 'apply', 'interview'].includes(next)) {
      args.mode = next as Mode
      i += 1
    } else if (arg.startsWith('--mode=')) {
      const value = arg.slice('--mode='.length)
      if (!['inspect', 'plan', 'apply', 'interview'].includes(value)) throw new Error(`Unsupported --mode: ${value}`)
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
  console.log(`Project Profile\n\nUsage:\n  bun .lazy-harness/scripts/project-profile.ts --mode inspect [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode plan [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode apply --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode apply --confirm [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode interview --dry-run [--format md|json] [--root <path>]\n  bun .lazy-harness/scripts/project-profile.ts --mode interview --confirm [--format md|json] [--root <path>]\n\nInspect mode is read-only. Plan mode proposes missing skeleton profile records. Apply with --confirm writes only needs-interview skeletons and never makes architecture decisions. Interview mode emits structured questions for needs-interview fields; --confirm writes only the open-question transcript.`)
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
  const complete = missing === 0
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
    summary: { present, missing, complete },
    optionGate: {
      prompt: complete ? 'Project Profile exists. What should happen next?' : 'Project Profile is incomplete. How should setup proceed?',
      options: complete
        ? [
          'A. Review existing profile only (Recommended)',
          'B. Refresh profile using document-ingestion outputs',
          'C. Start interview to update architecture decisions',
          'D. Custom instruction',
        ]
        : [
          'A. Create missing needs-interview skeleton records (Recommended)',
          'B. Run /lazy-doc-ingest first if docs may contain durable facts',
          'C. Start interview-only Project Profile setup',
          'D. Custom instruction',
        ],
      recommended: 'A',
    },
    nextActions: complete
      ? ['Review profile artifacts before feature work.', 'Use map-first navigation from profile to records/code/tests.']
      : ['Do not silently invent profile defaults.', 'Create missing skeletons or ask interview option gates before making architecture decisions.'],
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
  lines.push(`- Complete: ${result.summary.complete ? 'yes' : 'no'}`)
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
