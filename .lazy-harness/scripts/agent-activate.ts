#!/usr/bin/env bun
import {
  chmodSync,
  existsSync,
  lstatSync,
  mkdirSync,
  readFileSync,
  renameSync,
  rmdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'

type Format = 'md' | 'json'

type Args = {
  target: string
  dryRun: boolean
  quiet: boolean
  format: Format
}

type FileAction = {
  path: string
  action: 'create' | 'update' | 'unchanged'
}

type FilePlan = FileAction & {
  next: string
}

type ExcludeAction = {
  path?: string
  added: string[]
  skipped?: string
}

type ExcludePlan = ExcludeAction & {
  next?: string
}

type FileSnapshot = {
  path: string
  existed: boolean
  content?: Buffer
  mode?: number
}


const START = '<!-- lazy-harness-agent-activation:start -->'
const END = '<!-- lazy-harness-agent-activation:end -->'
const EXCLUDE_LINES = ['.pi/', '.omp/']
const PROJECT_SKILL_PATHS = ['../.claude/skills', '../.codex/skills', '../.agents/skills']

function parseArgs(argv: string[]): Args {
  const args: Args = { target: process.cwd(), dryRun: false, quiet: false, format: 'md' }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--target') args.target = value(argv, i++, a)
    else if (a.startsWith('--target=')) args.target = a.slice('--target='.length)
    else if (a === '--dry-run') args.dryRun = true
    else if (a === '--quiet') args.quiet = true
    else if (a === '--format') args.format = parseFormat(value(argv, i++, a))
    else if (a.startsWith('--format=')) args.format = parseFormat(a.slice('--format='.length))
    else if (a === '-h' || a === '--help') usage(0)
    else {
      console.error(`Unknown argument: ${a}`)
      usage(2)
    }
  }
  return args
}

function value(argv: string[], index: number, flag: string): string {
  const v = argv[index + 1]
  if (!v || v.startsWith('--')) {
    console.error(`Missing value for ${flag}`)
    process.exit(2)
  }
  return v
}

function parseFormat(raw: string): Format {
  if (raw === 'md' || raw === 'json') return raw
  console.error(`Unsupported --format: ${raw}`)
  process.exit(2)
}

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Usage: lazy agent activate [--target DIR] [--dry-run] [--format=md|json]

Create project-local Pi/OMP activation files and skill settings for this exact root.

The target must already contain .lazy-harness/bin/lazy. Run lazy init first for new projects.`)
  process.exit(exitCode)
}

function resolveTarget(target: string): string {
  const abs = resolve(target)
  const git = spawnSync('git', ['-C', abs, 'rev-parse', '--show-toplevel'], { encoding: 'utf8' })
  if (git.status === 0 && git.stdout.trim()) return resolve(git.stdout.trim())
  return abs
}

function ensureActivatedProject(target: string): void {
  if (!existsSync(target)) {
    console.error(`lazy agent activate: target does not exist: ${target}`)
    process.exit(1)
  }
  if (!existsSync(join(target, '.lazy-harness', 'bin', 'lazy'))) {
    console.error(`lazy agent activate: ${target} is not initialized; missing .lazy-harness/bin/lazy`)
    process.exit(1)
  }
}

function activationBody(agent: 'Pi' | 'OMP'): string {
  return `${START}
# Lazy-Harness project activation (${agent})

This project is activated for the lazy-harness Pi/OMP runtime bootstrap.

Before host-specific claims or mutations:

1. Run \`.lazy-harness/bin/lazy map --overview --complete --format=md\`.
2. Drill into a concrete feature id, record path, graph id, source path, or test path with \`.lazy-harness/bin/lazy map <copied-node> --format=md --limit=8\`.
3. Read real \`.lazy-harness\` records/source/tests before editing.
4. Treat \`.lazy-harness/AGENTS.md\` and linked records as the project rule entrypoint.

Keep long project rules in \`.lazy-harness\` records. Do not paste a second full copy of the framework grammar here.
${END}
`
}

function mergeManagedBlock(existing: string, body: string): string {
  const start = existing.indexOf(START)
  const end = existing.indexOf(END)
  if (start >= 0 && end >= start) {
    const afterEnd = end + END.length
    const suffix = existing.slice(afterEnd).replace(/^\n?/, '')
    const prefix = existing.slice(0, start).replace(/\n?$/, '')
    return [prefix, body.trimEnd(), suffix].filter(Boolean).join('\n\n') + '\n'
  }
  if (!existing.trim()) return body
  return `${existing.replace(/\n?$/, '\n\n')}${body}`
}

function planPromptFile(target: string, relPath: string, body: string): FilePlan {
  const path = join(target, relPath)
  const existing = existsSync(path) ? readFileSync(path, 'utf8') : ''
  const next = mergeManagedBlock(existing, body)
  const action: FileAction['action'] = existing ? (existing === next ? 'unchanged' : 'update') : 'create'
  return { path, action, next }
}

function mergePiSettings(existing: string): string {
  const data = existing.trim() ? JSON.parse(existing) : {}
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new Error('project .pi/settings.json must be a JSON object')
  }
  const settings = data as Record<string, unknown>
  const existingSkills = Array.isArray(settings.skills) ? settings.skills.filter((value): value is string => typeof value === 'string') : []
  const skills = [...existingSkills]
  for (const skillPath of PROJECT_SKILL_PATHS) {
    if (!skills.includes(skillPath)) skills.push(skillPath)
  }
  settings.skills = skills
  settings.enableSkillCommands = true
  return `${JSON.stringify(settings, null, 2)}\n`
}

function planPiSettings(target: string): FilePlan {
  const path = join(target, '.pi', 'settings.json')
  const existing = existsSync(path) ? readFileSync(path, 'utf8') : ''
  const next = mergePiSettings(existing)
  const action: FileAction['action'] = existing ? (existing === next ? 'unchanged' : 'update') : 'create'
  return { path, action, next }
}

function gitExcludePath(target: string): string | undefined {
  const gitDirPath = join(target, '.git')
  if (!existsSync(gitDirPath)) return undefined
  let gitDir = gitDirPath
  const gitStat = statSync(gitDirPath)
  if (gitStat.isFile()) {
    const content = readFileSync(gitDirPath, 'utf8').trim()
    const match = content.match(/^gitdir:\s*(.+)$/)
    if (match) gitDir = match[1].startsWith('/') ? match[1] : resolve(target, match[1])
  }
  return join(gitDir, 'info', 'exclude')
}

function planGitExclude(target: string): ExcludePlan {
  const path = gitExcludePath(target)
  if (!path) return { added: [], skipped: 'target is not a git worktree' }
  const existing = existsSync(path) ? readFileSync(path, 'utf8') : ''
  const existingLines = new Set(existing.split(/\r?\n/).map((line) => line.trim()))
  const added = EXCLUDE_LINES.filter((line) => !existingLines.has(line))
  const prefix = existing && !existing.endsWith('\n') ? '\n' : ''
  const suffix = added.length > 0 ? `${prefix}# Added by lazy agent activate\n${added.join('\n')}\n` : ''
  return { path, added, next: `${existing}${suffix}` }
}

function atomicWrite(path: string, content: string): void {
  mkdirSync(dirname(path), { recursive: true })
  const tmp = `${path}.${process.pid}.tmp`
  writeFileSync(tmp, content, 'utf8')
  renameSync(tmp, path)
}

function snapshotFile(path: string): FileSnapshot {
  if (!existsSync(path)) return { path, existed: false }
  const stat = lstatSync(path)
  if (!stat.isFile()) throw new Error(`managed path is not a regular file: ${path}`)
  return { path, existed: true, content: readFileSync(path), mode: stat.mode & 0o777 }
}

function restoreSnapshots(snapshots: FileSnapshot[]): void {
  for (const snapshot of [...snapshots].reverse()) {
    if (!snapshot.existed) {
      rmSync(snapshot.path, { force: true })
      continue
    }
    mkdirSync(dirname(snapshot.path), { recursive: true })
    writeFileSync(snapshot.path, snapshot.content ?? Buffer.alloc(0))
    if (snapshot.mode !== undefined) chmodSync(snapshot.path, snapshot.mode)
  }
}

function removeCreatedDirs(paths: string[]): void {
  for (const path of [...paths].reverse()) {
    try {
      rmdirSync(path)
    } catch {
      // Preserve non-empty or concurrently reused directories.
    }
  }
}

function applyPlans(files: FilePlan[], exclude: ExcludePlan): void {
  for (const file of files) {
    if (file.action !== 'unchanged') atomicWrite(file.path, file.next)
  }
  if (exclude.path && exclude.added.length > 0 && exclude.next !== undefined) atomicWrite(exclude.path, exclude.next)
}


function printResult(target: string, files: FileAction[], exclude: ExcludeAction, args: Args): void {
  const ok = true
  const fileResults = files.map(({ path, action }) => ({ path, action }))
  const excludeResult = { path: exclude.path, added: exclude.added, skipped: exclude.skipped }
  if (args.format === 'json') {
    console.log(JSON.stringify({ ok, target, dryRun: args.dryRun, files: fileResults, gitInfoExclude: excludeResult }, null, 2))
    return
  }
  if (!args.quiet) {
    console.log('# lazy agent activate')
    console.log(`- ok: ${ok}`)
    console.log(`- target: ${target}`)
    console.log(`- dry_run: ${args.dryRun}`)
    for (const file of files) console.log(`- ${file.action}: ${file.path}`)
    if (exclude.path) console.log(`- git_info_exclude: ${exclude.path} added=${exclude.added.join(',') || 'none'}`)
    else console.log(`- git_info_exclude: skipped (${exclude.skipped})`)
    console.log('- runtimes: Pi (stable), OMP (Experimental)')
  }
}
function failResult(target: string, error: unknown, args: Args): void {
  const message = error instanceof Error ? error.message : String(error)
  if (args.format === 'json') {
    console.log(JSON.stringify({ ok: false, target, dryRun: args.dryRun, error: message }, null, 2))
  } else {
    console.error(`lazy agent activate: ${message}`)
  }
  process.exitCode = 1
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const target = resolveTarget(args.target)
  ensureActivatedProject(target)
  let files: FilePlan[]
  let exclude: ExcludePlan
  try {
    files = [
      planPromptFile(target, join('.pi', 'APPEND_SYSTEM.md'), activationBody('Pi')),
      planPromptFile(target, join('.omp', 'APPEND_SYSTEM.md'), activationBody('OMP')),
      planPiSettings(target),
    ]
    exclude = planGitExclude(target)
  } catch (error) {
    failResult(target, error, args)
    return
  }

  if (args.dryRun) {
    printResult(target, files, exclude, args)
    return
  }
  const managedPaths = files.filter((file) => file.action !== 'unchanged').map((file) => file.path)
  if (exclude.path && exclude.added.length > 0) managedPaths.push(exclude.path)
  const snapshots = managedPaths.map(snapshotFile)
  const candidateDirs = [join(target, '.pi'), join(target, '.omp')]
  const createdDirs = candidateDirs.filter((path) => !existsSync(path))
  try {
    applyPlans(files, exclude)
    printResult(target, files, exclude, args)
  } catch (error) {
    restoreSnapshots(snapshots)
    removeCreatedDirs(createdDirs)
    failResult(target, error, args)
  }
}

main()
