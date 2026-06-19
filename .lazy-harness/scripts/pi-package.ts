#!/usr/bin/env bun
import { existsSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

type Format = 'md' | 'json'
type Scope = 'local' | 'global'

type Options = {
  format: Format
  target?: string
  packagePath?: string
  dryRun: boolean
  scope?: Scope
  noSmoke: boolean
  strict: boolean
}

type CommandResult = {
  command: string[]
  exitCode: number | null
  stdout: string
  stderr: string
}

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Usage: lazy pi <command> [options]

Commands:
  install --local|--global [--dry-run] [--package <path>]
      Attach packages/lazy-harness-pi to official Pi settings.
  remove --local|--global [--dry-run] [--package <path>]
      Remove the lazy-harness Pi package from official Pi settings.
  list [--local|--global] [--format=md|json]
      Show Pi package settings through pi list. Default: --local/--approve.
  smoke [--dry-run] [--format=md|json]
      One-run load smoke: pi -e <package> --help. Never persists settings.
  doctor [--no-smoke] [--strict] [--format=md|json]
      Inspect pi binary, package layout, settings list, and optional one-run smoke.

Options:
  --local       Use project-local Pi settings: pi install/remove -l ... --approve
  --global      Use user-global Pi settings: pi install/remove ... --no-approve
  --dry-run     Print the pi command without executing install/remove/smoke
  --package P   Override package path. Default: <host>/packages/lazy-harness-pi
  --target DIR  Host root. Default: $LAZY_HOST_ROOT or this script's host root
  --format F    md or json. Default: md

Safety:
  install/remove require explicit --local or --global.
  smoke and doctor never mutate Pi settings.
  Under the hood: install maps to pi install; remove maps to pi remove; list maps to pi list; smoke maps to pi -e.
  npm/standalone publishing is intentionally out of scope until Pi/OMP smoke is stable.
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

function parseOptions(argv: string[]): Options {
  const opts: Options = { format: 'md', dryRun: false, noSmoke: false, strict: false }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '-h' || a === '--help') usage(0)
    if (a === '--local') opts.scope = 'local'
    else if (a === '--global') opts.scope = 'global'
    else if (a === '--dry-run') opts.dryRun = true
    else if (a === '--no-smoke') opts.noSmoke = true
    else if (a === '--strict') opts.strict = true
    else if (a === '--target') opts.target = value(argv, i++, a)
    else if (a.startsWith('--target=')) opts.target = a.slice('--target='.length)
    else if (a === '--package') opts.packagePath = value(argv, i++, a)
    else if (a.startsWith('--package=')) opts.packagePath = a.slice('--package='.length)
    else if (a === '--format') opts.format = parseFormat(value(argv, i++, a))
    else if (a.startsWith('--format=')) opts.format = parseFormat(a.slice('--format='.length))
    else {
      console.error(`Unknown argument: ${a}`)
      usage(2)
    }
  }
  return opts
}

function parseFormat(raw: string): Format {
  if (raw === 'md' || raw === 'json') return raw
  console.error(`Unsupported --format: ${raw}`)
  process.exit(2)
}

function hostRoot(opts: Options): string {
  return resolve(opts.target || process.env.LAZY_HOST_ROOT || scriptHostRoot())
}

function scriptHostRoot(): string {
  return resolve(import.meta.dir, '..', '..')
}

function packagePath(root: string, opts: Options): string {
  return resolve(opts.packagePath || join(root, 'packages', 'lazy-harness-pi'))
}

function requireScope(opts: Options, command: string): Scope {
  if (!opts.scope) {
    console.error(`lazy pi ${command} requires explicit --local or --global`)
    process.exit(2)
  }
  return opts.scope
}

function printJson(value: unknown): void {
  console.log(JSON.stringify(value, null, 2))
}

function commandForInstallLike(action: 'install' | 'remove', pkg: string, scope: Scope): string[] {
  const args = ['pi', action, pkg]
  if (scope === 'local') args.push('-l', '--approve')
  else args.push('--no-approve')
  return args
}

function commandForList(scope: Scope | undefined): string[] {
  return ['pi', 'list', scope === 'global' ? '--no-approve' : '--approve']
}

function commandForSmoke(pkg: string): string[] {
  return ['pi', '-e', pkg, '--help']
}

function run(command: string[], dryRun = false): CommandResult {
  if (dryRun) return { command, exitCode: 0, stdout: '', stderr: '' }
  const result = spawnSync(command[0], command.slice(1), { encoding: 'utf8' })
  return {
    command,
    exitCode: result.status,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
  }
}

function printCommandResult(title: string, result: CommandResult, fmt: Format, extra: Record<string, unknown> = {}): void {
  if (fmt === 'json') {
    printJson({ ok: result.exitCode === 0, title, ...extra, result })
    return
  }
  console.log(`# ${title}`)
  for (const [key, value] of Object.entries(extra)) {
    console.log(`- ${key}: ${String(value)}`)
  }
  console.log(`- command: ${result.command.map(shellQuote).join(' ')}`)
  console.log(`- exit_code: ${result.exitCode}`)
  if (result.stdout.trim()) {
    console.log('\n## stdout')
    console.log(result.stdout.trimEnd())
  }
  if (result.stderr.trim()) {
    console.log('\n## stderr')
    console.log(result.stderr.trimEnd())
  }
}

function shellQuote(value: string): string {
  if (/^[A-Za-z0-9_./:@=-]+$/.test(value)) return value
  return `'${value.replace(/'/g, `'\\''`)}'`
}

function ensurePackageLayout(pkg: string): { ok: boolean; errors: string[]; manifestName?: string } {
  const errors: string[] = []
  const manifest = join(pkg, 'package.json')
  const extension = join(pkg, 'extensions', 'lazy-harness', 'index.ts')
  const readme = join(pkg, 'README.md')
  for (const path of [manifest, extension, readme]) {
    if (!existsSync(path)) errors.push(`missing ${path}`)
  }
  let manifestName: string | undefined
  if (existsSync(manifest)) {
    try {
      const parsed = JSON.parse(readFileSync(manifest, 'utf8'))
      manifestName = typeof parsed?.name === 'string' ? parsed.name : undefined
      const pi = parsed?.pi
      if (!pi || !Array.isArray(pi.extensions) || !pi.extensions.includes('./extensions')) errors.push('package.json missing pi.extensions ./extensions')
      if (!pi || !Array.isArray(pi.skills) || !pi.skills.includes('./skills')) errors.push('package.json missing pi.skills ./skills')
      if (!pi || !Array.isArray(pi.prompts) || !pi.prompts.includes('./prompts')) errors.push('package.json missing pi.prompts ./prompts')
    } catch (error) {
      errors.push(`package.json parse failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }
  return { ok: errors.length === 0, errors, manifestName }
}

function printDryRun(title: string, command: string[], fmt: Format, extra: Record<string, unknown> = {}): void {
  const result = run(command, true)
  printCommandResult(`${title} dry-run`, result, fmt, { ...extra, dryRun: true })
}

function installOrRemove(action: 'install' | 'remove', opts: Options): void {
  const root = hostRoot(opts)
  const pkg = packagePath(root, opts)
  const scope = requireScope(opts, action)
  const layout = ensurePackageLayout(pkg)
  if (!layout.ok) {
    if (opts.format === 'json') printJson({ ok: false, packagePath: pkg, layout })
    else {
      console.error(`lazy pi ${action}: invalid package path ${pkg}`)
      for (const err of layout.errors) console.error(`- ${err}`)
    }
    process.exit(1)
  }
  const command = commandForInstallLike(action, pkg, scope)
  if (opts.dryRun) {
    printDryRun(`Pi ${action}`, command, opts.format, { scope, packagePath: pkg })
    return
  }
  const result = run(command)
  printCommandResult(`Pi ${action}`, result, opts.format, { scope, packagePath: pkg })
  process.exit(result.exitCode === 0 ? 0 : 1)
}

function list(opts: Options): void {
  const command = commandForList(opts.scope)
  const result = run(command)
  printCommandResult('Pi package list', result, opts.format, { scope: opts.scope || 'local' })
  process.exit(result.exitCode === 0 ? 0 : 1)
}

function smoke(opts: Options): void {
  const root = hostRoot(opts)
  const pkg = packagePath(root, opts)
  const layout = ensurePackageLayout(pkg)
  const command = commandForSmoke(pkg)
  if (!layout.ok) {
    if (opts.format === 'json') printJson({ ok: false, packagePath: pkg, layout, command })
    else {
      console.error(`lazy pi smoke: invalid package path ${pkg}`)
      for (const err of layout.errors) console.error(`- ${err}`)
    }
    process.exit(1)
  }
  if (opts.dryRun) {
    printDryRun('Pi one-run smoke', command, opts.format, { packagePath: pkg })
    return
  }
  const result = run(command)
  printCommandResult('Pi one-run smoke', result, opts.format, { packagePath: pkg })
  process.exit(result.exitCode === 0 ? 0 : 1)
}

function doctor(opts: Options): void {
  const root = hostRoot(opts)
  const pkg = packagePath(root, opts)
  const layout = ensurePackageLayout(pkg)
  const piVersion = run(['pi', '--version'])
  const listResult = run(commandForList(opts.scope))
  const smokeResult = opts.noSmoke ? null : run(commandForSmoke(pkg))
  const ok = layout.ok && piVersion.exitCode === 0 && listResult.exitCode === 0 && (!smokeResult || smokeResult.exitCode === 0)
  const payload = {
    ok,
    strict: opts.strict,
    hostRoot: root,
    packagePath: pkg,
    packageLayout: layout,
    piVersion,
    list: listResult,
    smoke: smokeResult,
    note: 'doctor/smoke never mutate Pi settings; install/remove require explicit commands',
  }
  if (opts.format === 'json') printJson(payload)
  else {
    console.log('# Lazy Pi doctor')
    console.log(`- ok: ${ok}`)
    console.log(`- host_root: ${root}`)
    console.log(`- package_path: ${pkg}`)
    console.log(`- package_layout: ${layout.ok ? 'ok' : 'failed'}`)
    if (layout.manifestName) console.log(`- package_name: ${layout.manifestName}`)
    for (const err of layout.errors) console.log(`  - layout_error: ${err}`)
    console.log(`- pi_version_exit: ${piVersion.exitCode}`)
    if (piVersion.stdout.trim()) console.log(`- pi_version: ${piVersion.stdout.trim()}`)
    console.log(`- list_exit: ${listResult.exitCode}`)
    console.log(`- smoke_exit: ${smokeResult ? smokeResult.exitCode : 'skipped'}`)
    console.log('- note: doctor/smoke never mutate Pi settings; install/remove require explicit commands')
  }
  if (opts.strict && !ok) process.exit(1)
}

function main(): void {
  const [cmd, ...rest] = process.argv.slice(2)
  if (!cmd || cmd === '-h' || cmd === '--help') usage(cmd ? 0 : 2)
  const opts = parseOptions(rest)
  if (cmd === 'install') return installOrRemove('install', opts)
  if (cmd === 'remove' || cmd === 'uninstall') return installOrRemove('remove', opts)
  if (cmd === 'list') return list(opts)
  if (cmd === 'smoke') return smoke(opts)
  if (cmd === 'doctor') return doctor(opts)
  console.error(`Unknown lazy pi command: ${cmd}`)
  usage(2)
}

main()
