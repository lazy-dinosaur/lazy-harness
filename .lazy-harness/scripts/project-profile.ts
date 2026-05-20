#!/usr/bin/env bun
/**
 * Project Profile — inspect skeleton (SDD: spec/platform/project-profile.md)
 *
 * Current slice is read-only. It reports whether host Project Profile records
 * exist and whether Document Resource Ingestion outputs are available to use as
 * evidence before an interview/apply flow.
 */
import { existsSync, statSync } from 'node:fs'
import { join } from 'node:path'

type Mode = 'inspect'
type Format = 'json' | 'md'
type ArtifactStatus = 'present' | 'missing'

interface Args {
  mode: Mode
  format: Format
  root: string
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
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    const next = argv[i + 1]
    if (arg === '--mode' && next === 'inspect') {
      args.mode = 'inspect'
      i += 1
    } else if (arg.startsWith('--mode=')) {
      const value = arg.slice('--mode='.length)
      if (value !== 'inspect') throw new Error(`Unsupported --mode: ${value}`)
      args.mode = 'inspect'
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
  console.log(`Project Profile\n\nUsage:\n  bun .lazy-harness/scripts/project-profile.ts --mode inspect [--format md|json] [--root <path>]\n\nInspect mode is read-only. It checks required Project Profile artifacts and document-ingestion handoff state.`)
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
          'A. Run /lazy-doc-ingest first if docs may contain durable facts (Recommended)',
          'B. Start interview-only Project Profile setup',
          'C. Create only missing skeleton records',
          'D. Custom instruction',
        ],
      recommended: 'A',
    },
    nextActions: complete
      ? ['Review profile artifacts before feature work.', 'Use map-first navigation from profile to records/code/tests.']
      : ['Do not silently invent profile defaults.', 'Run document ingestion or interview option gate before creating profile records.'],
  }
}

function renderMd(result: ProjectProfileInspectResult): string {
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

function main(): void {
  try {
    const args = parseArgs(process.argv.slice(2))
    const result = inspect(args)
    if (args.format === 'json') console.log(JSON.stringify(result, null, 2))
    else console.log(renderMd(result))
  } catch (error) {
    console.error(error instanceof Error ? error.message : String(error))
    process.exit(1)
  }
}

main()
