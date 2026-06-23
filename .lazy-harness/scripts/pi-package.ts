#!/usr/bin/env bun
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

type Format = 'md' | 'json'
type Scope = 'local' | 'global'
type Runtime = 'pi' | 'omp'

type Options = {
  format: Format
  sourceRoot?: string
  targetRepo?: string
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

const RUNTIME: Runtime = process.env.LAZY_AGENT_RUNTIME === 'omp' ? 'omp' : 'pi'

type RuntimeInfo = {
  id: Runtime
  label: string
  binary: string
  sourceEnv: string
  targetEnv: string
}

function runtimeInfo(runtime: Runtime = RUNTIME): RuntimeInfo {
  if (runtime === 'omp') {
    return {
      id: 'omp',
      label: 'OMP',
      binary: 'omp',
      sourceEnv: 'LAZY_OMP_SOURCE_ROOT',
      targetEnv: 'LAZY_OMP_TARGET_REPO',
    }
  }
  return {
    id: 'pi',
    label: 'Pi',
    binary: 'pi',
    sourceEnv: 'LAZY_PI_SOURCE_ROOT',
    targetEnv: 'LAZY_PI_TARGET_REPO',
  }
}

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  const info = runtimeInfo()
  if (info.id === 'omp') {
    out(`Usage: lazy omp <command> [options]

Commands:
  install [--dry-run] [--package <path>]
      Link packages/lazy-harness-pi into OMP via: omp plugin install <package>.
  remove [--dry-run] [--package <path>]
      Remove the shared package from OMP via: omp plugin uninstall <package-name>.
  list [--format=md|json]
      Show OMP plugin settings through omp plugin list.
  smoke [--dry-run] [--format=md|json]
      One-run load smoke: omp -e <package> --help. Never persists settings.
  doctor [--no-smoke] [--strict] [--format=md|json]
      Inspect omp binary, package layout, plugin list, and optional one-run smoke.

Options:
  --dry-run     Print the omp command without executing install/remove/smoke
  --package P   Override source package path. Default: <source-root>/packages/lazy-harness-pi
  --source-root DIR
                Lazy-harness source root. Default: this script's host root
  --target-repo DIR
                Repo/cwd for list/smoke diagnostics. Default: $LAZY_OMP_TARGET_REPO or cwd
  --target DIR  Deprecated alias for --source-root
  --format F    md or json. Default: md

Safety:
  OMP local path installs use official OMP plugin link semantics and persist in OMP's plugin registry.
  Use smoke for one-run non-persistent OMP loading.
  The source package path and target repo are intentionally separate to avoid cross-repo contamination.
  Under the hood: install maps to omp plugin install; remove maps to omp plugin uninstall; list maps to omp plugin list; smoke maps to omp -e.
  npm/standalone publishing is intentionally out of scope until Pi/OMP smoke is stable.
`)
    process.exit(exitCode)
  }

  out(`Usage: lazy pi <command> [options]

Commands:
  install [--local|--global] [--dry-run] [--package <path>]
      Attach packages/lazy-harness-pi to official Pi settings. Default: --global bootstrap.
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
  --package P   Override source package path. Default: <source-root>/packages/lazy-harness-pi
  --source-root DIR
                Lazy-harness source root. Default: this script's host root
  --target-repo DIR
                Repo/settings target for --local/list. Default: $LAZY_PI_TARGET_REPO or cwd
  --target DIR  Deprecated alias for --source-root
  --format F    md or json. Default: md

Safety:
  install defaults to --global bootstrap; remove still requires explicit --local or --global.
  --local writes target repo .pi/settings.json; --global writes user-global Pi settings.
  Project activation remains local: use lazy agent activate or lazy init to create .pi/.omp APPEND_SYSTEM.md pointers.
  The source package path and target repo are intentionally separate to avoid cross-repo contamination.
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
    else if (a === '--source-root') opts.sourceRoot = value(argv, i++, a)
    else if (a.startsWith('--source-root=')) opts.sourceRoot = a.slice('--source-root='.length)
    else if (a === '--target-repo') opts.targetRepo = value(argv, i++, a)
    else if (a.startsWith('--target-repo=')) opts.targetRepo = a.slice('--target-repo='.length)
    else if (a === '--target') opts.sourceRoot = value(argv, i++, a)
    else if (a.startsWith('--target=')) opts.sourceRoot = a.slice('--target='.length)
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

function sourceRoot(opts: Options): string {
  const info = runtimeInfo()
  return resolve(opts.sourceRoot || process.env[info.sourceEnv] || process.env.LAZY_PI_SOURCE_ROOT || scriptHostRoot())
}

function scriptHostRoot(): string {
  return resolve(import.meta.dir, '..', '..')
}

function packagePath(root: string, opts: Options): string {
  return resolve(opts.packagePath || join(root, 'packages', 'lazy-harness-pi'))
}

function targetRepo(opts: Options): string {
  const info = runtimeInfo()
  return resolveGitRoot(opts.targetRepo || process.env[info.targetEnv] || process.env.LAZY_PI_TARGET_REPO || process.cwd())
}

function resolveGitRoot(dir: string): string {
  const abs = resolve(dir)
  const result = spawnSync('git', ['-C', abs, 'rev-parse', '--show-toplevel'], { encoding: 'utf8' })
  if (result.status === 0 && result.stdout.trim()) return resolve(result.stdout.trim())
  return abs
}

function requireScope(opts: Options, command: string): Scope {
  if (!opts.scope) {
    console.error(`lazy ${runtimeInfo().id} ${command} requires explicit --local or --global`)
    process.exit(2)
  }
  return opts.scope
}

function printJson(value: unknown): void {
  console.log(JSON.stringify(value, null, 2))
}

function commandForInstallLike(action: 'install' | 'remove', pkg: string, scope: Scope | undefined, manifestName?: string): string[] {
  const info = runtimeInfo()
  if (info.id === 'omp') {
    if (action === 'install') return [info.binary, 'plugin', 'install', pkg]
    return [info.binary, 'plugin', 'uninstall', manifestName || '@lazy-dinosaur/lazy-harness-pi']
  }
  if (!scope) throw new Error('internal error: Pi install/remove requires scope')
  const args = [info.binary, action, pkg]
  if (scope === 'local') args.push('-l', '--approve')
  else args.push('--no-approve')
  return args
}

function commandForList(scope: Scope | undefined): string[] {
  const info = runtimeInfo()
  if (info.id === 'omp') return [info.binary, 'plugin', 'list']
  return [info.binary, 'list', scope === 'global' ? '--no-approve' : '--approve']
}

function commandForSmoke(pkg: string): string[] {
  return [runtimeInfo().binary, '-e', pkg, '--help']
}

function run(command: string[], dryRun = false, cwd?: string): CommandResult {
  if (dryRun) return { command, exitCode: 0, stdout: '', stderr: '' }
  const result = spawnSync(command[0], command.slice(1), { cwd, encoding: 'utf8' })
  return {
    command,
    exitCode: result.status,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
  }
}

function gitExcludePath(repo: string): string | undefined {
  const result = spawnSync('git', ['-C', repo, 'rev-parse', '--git-path', 'info/exclude'], { encoding: 'utf8' })
  if (result.status !== 0 || !result.stdout.trim()) return undefined
  const raw = result.stdout.trim()
  return resolve(repo, raw)
}

function ensureLocalPiIgnored(repo: string, dryRun = false): { path?: string; changed: boolean; skipped?: string } {
  const exclude = gitExcludePath(repo)
  if (!exclude) return { changed: false, skipped: 'target repo is not a git worktree' }
  if (dryRun) return { path: exclude, changed: false }
  mkdirSync(dirname(exclude), { recursive: true })
  const current = existsSync(exclude) ? readFileSync(exclude, 'utf8') : ''
  if (/^\.pi\/\s*$/m.test(current) || /^\.pi\s*$/m.test(current)) return { path: exclude, changed: false }
  const prefix = current && !current.endsWith('\n') ? '\n' : ''
  appendFileSync(exclude, `${prefix}.pi/\n`, 'utf8')
  return { path: exclude, changed: true }
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
      for (const key of ['pi', 'omp']) {
        const manifest = parsed?.[key]
        if (!manifest || !Array.isArray(manifest.extensions) || !manifest.extensions.includes('./extensions')) errors.push(`package.json missing ${key}.extensions ./extensions`)
        if (!manifest || !Array.isArray(manifest.skills) || !manifest.skills.includes('./skills')) errors.push(`package.json missing ${key}.skills ./skills`)
        if (!manifest || !Array.isArray(manifest.prompts) || !manifest.prompts.includes('./prompts')) errors.push(`package.json missing ${key}.prompts ./prompts`)
      }
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
  const info = runtimeInfo()
  const root = sourceRoot(opts)
  const repo = targetRepo(opts)
  const pkg = packagePath(root, opts)
  const scope = info.id === 'pi'
    ? (action === 'install' ? opts.scope || 'global' : requireScope(opts, action))
    : opts.scope
  const layout = ensurePackageLayout(pkg)
  if (!layout.ok) {
    if (opts.format === 'json') printJson({ ok: false, packagePath: pkg, layout })
    else {
      console.error(`lazy ${info.id} ${action}: invalid package path ${pkg}`)
      for (const err of layout.errors) console.error(`- ${err}`)
    }
    process.exit(1)
  }
  const command = commandForInstallLike(action, pkg, scope, layout.manifestName)
  const localIgnore = info.id === 'pi' && scope === 'local' && action === 'install'
    ? ensureLocalPiIgnored(repo, opts.dryRun)
    : undefined
  const extra = { runtime: info.id, scope, sourceRoot: root, targetRepo: repo, packagePath: pkg, localPiGitExclude: localIgnore }
  if (opts.dryRun) {
    printDryRun(`${info.label} ${action}`, command, opts.format, extra)
    return
  }
  const result = run(command, false, repo)
  printCommandResult(`${info.label} ${action}`, result, opts.format, extra)
  process.exit(result.exitCode === 0 ? 0 : 1)
}

function list(opts: Options): void {
  const info = runtimeInfo()
  const repo = targetRepo(opts)
  const command = commandForList(opts.scope)
  const result = run(command, false, repo)
  printCommandResult(`${info.label} package list`, result, opts.format, { runtime: info.id, scope: opts.scope || (info.id === 'pi' ? 'local' : undefined), targetRepo: repo })
  process.exit(result.exitCode === 0 ? 0 : 1)
}

function smoke(opts: Options): void {
  const info = runtimeInfo()
  const root = sourceRoot(opts)
  const repo = targetRepo(opts)
  const pkg = packagePath(root, opts)
  const layout = ensurePackageLayout(pkg)
  const command = commandForSmoke(pkg)
  if (!layout.ok) {
    if (opts.format === 'json') printJson({ ok: false, packagePath: pkg, layout, command })
    else {
      console.error(`lazy ${info.id} smoke: invalid package path ${pkg}`)
      for (const err of layout.errors) console.error(`- ${err}`)
    }
    process.exit(1)
  }
  if (opts.dryRun) {
    printDryRun(`${info.label} one-run smoke`, command, opts.format, { runtime: info.id, sourceRoot: root, targetRepo: repo, packagePath: pkg })
    return
  }
  const result = run(command, false, repo)
  printCommandResult(`${info.label} one-run smoke`, result, opts.format, { runtime: info.id, sourceRoot: root, targetRepo: repo, packagePath: pkg })
  process.exit(result.exitCode === 0 ? 0 : 1)
}

function doctor(opts: Options): void {
  const info = runtimeInfo()
  const root = sourceRoot(opts)
  const repo = targetRepo(opts)
  const pkg = packagePath(root, opts)
  const layout = ensurePackageLayout(pkg)
  const agentVersion = run([info.binary, '--version'])
  const listResult = run(commandForList(opts.scope), false, repo)
  const smokeResult = opts.noSmoke ? null : run(commandForSmoke(pkg), false, repo)
  const localPiGitExclude = info.id === 'pi' ? ensureLocalPiIgnored(repo, true) : undefined
  const ok = layout.ok && agentVersion.exitCode === 0 && listResult.exitCode === 0 && (!smokeResult || smokeResult.exitCode === 0)
  const payload = {
    ok,
    runtime: info.id,
    strict: opts.strict,
    sourceRoot: root,
    targetRepo: repo,
    packagePath: pkg,
    packageLayout: layout,
    localPiGitExclude,
    agentVersion,
    list: listResult,
    smoke: smokeResult,
    note: info.id === 'pi'
      ? 'doctor/smoke never mutate Pi settings; install/remove require explicit commands'
      : 'doctor/smoke never mutate OMP plugin settings; install/remove require explicit commands',
  }
  if (opts.format === 'json') printJson(payload)
  else {
    console.log(`# Lazy ${info.label} doctor`)
    console.log(`- ok: ${ok}`)
    console.log(`- runtime: ${info.id}`)
    console.log(`- source_root: ${root}`)
    console.log(`- target_repo: ${repo}`)
    console.log(`- package_path: ${pkg}`)
    if (localPiGitExclude) console.log(`- local_pi_git_exclude: ${localPiGitExclude.path || localPiGitExclude.skipped || 'unknown'}`)
    console.log(`- package_layout: ${layout.ok ? 'ok' : 'failed'}`)
    if (layout.manifestName) console.log(`- package_name: ${layout.manifestName}`)
    for (const err of layout.errors) console.log(`  - layout_error: ${err}`)
    console.log(`- ${info.id}_version_exit: ${agentVersion.exitCode}`)
    if (agentVersion.stdout.trim()) console.log(`- ${info.id}_version: ${agentVersion.stdout.trim()}`)
    console.log(`- list_exit: ${listResult.exitCode}`)
    console.log(`- smoke_exit: ${smokeResult ? smokeResult.exitCode : 'skipped'}`)
    console.log(`- note: doctor/smoke never mutate ${info.label} settings; install/remove require explicit commands`)
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
  console.error(`Unknown lazy ${runtimeInfo().id} command: ${cmd}`)
  usage(2)
}

main()
