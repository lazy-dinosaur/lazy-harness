#!/usr/bin/env bun

import { resolve } from 'node:path'
import { hostRoot } from './runtime-paths.ts'
import {
  applyArchitecturePlan,
  ArchitectureContractError,
  type ArchitectureApplyResult,
  type ArchitectureInspectResult,
  type ArchitecturePlanResult,
  buildArchitecturePlan,
  inspectArchitecture,
} from './architecture-profile-core.ts'

type Command = 'inspect' | 'plan' | 'apply' | 'help'
type Format = 'json' | 'md'

interface Args {
  command: Command
  root: string
  format: Format
  proposal?: string
  confirm?: string
  confirmationRef?: string
}

function valueArg(argv: string[], index: number, name: string): {
  value: string
  consumed: number
} | null {
  const token = argv[index]
  if (token === name) {
    const value = argv[index + 1]
    if (!value || value.startsWith('--')) {
      throw new ArchitectureContractError(`${name} requires a value`)
    }
    return { value, consumed: 2 }
  }
  if (token.startsWith(`${name}=`)) {
    const value = token.slice(name.length + 1)
    if (!value) throw new ArchitectureContractError(`${name} requires a value`)
    return { value, consumed: 1 }
  }
  return null
}

function parseArgs(argv: string[]): Args {
  const commandToken = argv[0] || 'help'
  if (!['inspect', 'plan', 'apply', 'help', '-h', '--help'].includes(commandToken)) {
    throw new ArchitectureContractError(`Unknown architecture command: ${commandToken}`)
  }
  const command: Command = ['-h', '--help'].includes(commandToken)
    ? 'help'
    : commandToken as Command
  let root = hostRoot()
  let format: Format = 'md'
  let proposal: string | undefined
  let confirm: string | undefined
  let confirmationRef: string | undefined

  for (let index = 1; index < argv.length;) {
    const token = argv[index]
    const rootArg = valueArg(argv, index, '--root')
    if (rootArg) {
      root = resolve(rootArg.value)
      index += rootArg.consumed
      continue
    }
    const formatArg = valueArg(argv, index, '--format')
    if (formatArg) {
      if (!['json', 'md'].includes(formatArg.value)) {
        throw new ArchitectureContractError('--format must be json or md')
      }
      format = formatArg.value as Format
      index += formatArg.consumed
      continue
    }
    const proposalArg = valueArg(argv, index, '--proposal')
    if (proposalArg) {
      proposal = proposalArg.value
      index += proposalArg.consumed
      continue
    }
    const confirmArg = valueArg(argv, index, '--confirm')
    if (confirmArg) {
      confirm = confirmArg.value
      index += confirmArg.consumed
      continue
    }
    const confirmationRefArg = valueArg(argv, index, '--confirmation-ref')
    if (confirmationRefArg) {
      confirmationRef = confirmationRefArg.value
      index += confirmationRefArg.consumed
      continue
    }
    throw new ArchitectureContractError(`Unknown architecture option: ${token}`)
  }

  if (command === 'plan' && !proposal) {
    throw new ArchitectureContractError('architecture plan requires --proposal <file>')
  }
  if (command === 'apply') {
    if (!proposal) throw new ArchitectureContractError('architecture apply requires --proposal <file>')
    if (!confirm) {
      throw new ArchitectureContractError(
        'architecture apply requires --confirm <plan digest>; a bare flag is rejected',
      )
    }
    if (!confirmationRef) {
      throw new ArchitectureContractError(
        'architecture apply requires --confirmation-ref <reference>',
      )
    }
  }
  return { command, root, format, proposal, confirm, confirmationRef }
}

function printHelp(): void {
  console.log(`Usage: lazy architecture <command> [options]

Commands:
  inspect [--root DIR] [--format=md|json]
      Validate the framework catalog and optional confirmed host map. Read-only.

  plan --proposal FILE [--root DIR] [--format=md|json]
      Validate and normalize an explicit host-map proposal. Read-only.

  apply --proposal FILE --confirm PLAN_DIGEST
        --confirmation-ref REFERENCE [--root DIR] [--format=md|json]
      Recompute the exact plan and atomically write the confirmed host map.

Value flags accept both --flag value and --flag=value forms.
Inspect and plan never write. Apply changes only
.lazy-harness/project/architecture-map.json.`)
}

function renderFindings(
  findings: Array<{ severity: string; code: string; message: string; path?: string }>,
): string[] {
  if (!findings.length) return ['- Findings: none']
  return [
    `- Findings: ${findings.length}`,
    ...findings.map((finding) =>
      `  - [${finding.severity}] ${finding.code}${finding.path ? ` (${finding.path})` : ''}: ${finding.message}`),
  ]
}

function renderInspect(result: ArchitectureInspectResult): string {
  return [
    '# Architecture inspect',
    '',
    `- OK: ${result.ok}`,
    `- Root: ${result.root}`,
    `- Catalog: ${result.catalog.id || 'unknown'}@${result.catalog.version || 'unknown'}`,
    `- Values/Aliases/Relations: ${result.catalog.valueCount}/${result.catalog.aliasCount}/${result.catalog.relationCount}`,
    `- Host map: ${result.hostMap.status}`,
    `- Notice: ${result.notice}`,
    ...renderFindings(result.findings),
    '- Writes: none',
  ].join('\n')
}

function renderPlan(result: ArchitecturePlanResult): string {
  return [
    '# Architecture plan',
    '',
    `- OK: ${result.ok}`,
    `- Root: ${result.root}`,
    `- Proposal: ${result.proposalPath}`,
    `- Baseline digest: ${result.baselineDigest}`,
    `- Catalog digest: ${result.catalogDigest}`,
    `- Proposal digest: ${result.proposalDigest}`,
    `- Plan digest: ${result.planDigest}`,
    `- Planned write: ${result.writes[0]?.path || 'none'}`,
    ...renderFindings(result.findings),
    result.ok
      ? `- Apply: lazy architecture apply --proposal ${result.proposalPath} --confirm ${result.planDigest} --confirmation-ref <reference>`
      : '- Apply: blocked until every error is resolved and the plan is rerun.',
  ].join('\n')
}

function renderApply(result: ArchitectureApplyResult): string {
  return [
    '# Architecture apply',
    '',
    '- OK: true',
    `- Root: ${result.root}`,
    `- Plan digest: ${result.planDigest}`,
    `- Map: ${result.mapPath}`,
    `- Map digest: ${result.mapDigest}`,
    `- Confirmation: ${result.confirmationRef}`,
    '- Writes: 1',
  ].join('\n')
}

function printResult(
  result: ArchitectureInspectResult | ArchitecturePlanResult | ArchitectureApplyResult,
  format: Format,
): void {
  if (format === 'json') {
    console.log(JSON.stringify(result, null, 2))
    return
  }
  if (result.mode === 'architecture.inspect') console.log(renderInspect(result))
  else if (result.mode === 'architecture.plan') console.log(renderPlan(result))
  else console.log(renderApply(result))
}

function printError(error: unknown, format: Format): void {
  const contract = error instanceof ArchitectureContractError
    ? error
    : new ArchitectureContractError(
      error instanceof Error ? error.message : String(error),
      [],
      1,
    )
  if (format === 'json') {
    console.error(JSON.stringify({
      ok: false,
      mode: 'architecture.error',
      schemaVersion: 'architecture-error/v1',
      error: contract.message,
      findings: contract.findings,
    }, null, 2))
  } else {
    console.error(`Error: ${contract.message}`)
    for (const finding of contract.findings) {
      console.error(`- [${finding.severity}] ${finding.code}: ${finding.message}`)
    }
  }
  process.exitCode = contract.exitCode
}

function main(): void {
  let format: Format = 'md'
  try {
    const args = parseArgs(process.argv.slice(2))
    format = args.format
    if (args.command === 'help') {
      printHelp()
      return
    }
    if (args.command === 'inspect') {
      const result = inspectArchitecture(args.root)
      printResult(result, args.format)
      if (!result.ok) process.exitCode = 2
      return
    }
    if (args.command === 'plan') {
      const result = buildArchitecturePlan(args.root, args.proposal as string)
      printResult(result, args.format)
      if (!result.ok) process.exitCode = 2
      return
    }
    const result = applyArchitecturePlan(
      args.root,
      args.proposal as string,
      args.confirm as string,
      args.confirmationRef as string,
    )
    printResult(result, args.format)
  } catch (error) {
    printError(error, format)
  }
}

main()
