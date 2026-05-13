#!/usr/bin/env bun
/**
 * lazy-update — update the local framework source clone and sync Category A
 * into the current host.
 *
 * Public-safe wrapper around lazy-sync:
 *   1. Determine persistent source checkout from state/synced-from-commit,
 *      --source, or ~/.cache/lazy-harness/source.
 *   2. Fetch/checkout the requested ref from the public repo.
 *   3. Run this host's lazy-sync.ts against that source.
 */

import { existsSync, mkdirSync, readFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { spawnSync } from 'node:child_process'
import { homedir } from 'node:os'

const DEFAULT_REPO = `${'https'}://github.com/lazy-dinosaur/lazy-harness.git`
const DEFAULT_REF = 'main'

interface Args {
  target: string
  source: string
  repo: string
  ref: string
  cacheDir: string
  dryRun: boolean
  force: boolean
  quiet: boolean
}

function defaultCacheSource(): string {
  const base = process.env.XDG_CACHE_HOME || join(homedir(), '.cache')
  return join(base, 'lazy-harness', 'source')
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    target: '',
    source: '',
    repo: DEFAULT_REPO,
    ref: DEFAULT_REF,
    cacheDir: defaultCacheSource(),
    dryRun: false,
    force: false,
    quiet: false
  }

  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--target') args.target = argv[++i]
    else if (a.startsWith('--target=')) args.target = a.slice('--target='.length)
    else if (a === '--source') args.source = argv[++i]
    else if (a.startsWith('--source=')) args.source = a.slice('--source='.length)
    else if (a === '--repo') args.repo = argv[++i]
    else if (a.startsWith('--repo=')) args.repo = a.slice('--repo='.length)
    else if (a === '--ref') args.ref = argv[++i]
    else if (a.startsWith('--ref=')) args.ref = a.slice('--ref='.length)
    else if (a === '--cache-dir') args.cacheDir = argv[++i]
    else if (a.startsWith('--cache-dir=')) args.cacheDir = a.slice('--cache-dir='.length)
    else if (a === '--dry-run') args.dryRun = true
    else if (a === '--force') args.force = true
    else if (a === '--quiet') args.quiet = true
    else if (a === '--help' || a === '-h') {
      printHelp()
      process.exit(0)
    } else {
      console.error(`Unknown flag: ${a}`)
      process.exit(1)
    }
  }
  return args
}

function printHelp(): void {
  console.log(`lazy-update — update lazy-harness source and sync this host.

Usage:
  lazy update [options]

Options:
  --target <dir>     Host project root (default: cwd)
  --source <dir>     Existing lazy-harness source checkout
  --repo <url>       Source repo URL (default: ${DEFAULT_REPO})
  --ref <ref>        Branch, tag, or commit to update to (default: ${DEFAULT_REF})
  --cache-dir <dir>  Clone location when source is missing (default: ${defaultCacheSource()})
  --dry-run          Update/check source, then show host sync changes only
  --force            Pass --force to lazy-sync for divergent host marker history
  --quiet            Suppress non-essential logs

Exit:
  0 ok | 1 validation/io | 2 sync drift conflict`)
}

let QUIET = false
function log(msg: string): void {
  if (!QUIET) console.log(msg)
}

function run(cmd: string, args: string[], opts: { cwd?: string; quiet?: boolean } = {}): string {
  const res = spawnSync(cmd, args, {
    cwd: opts.cwd,
    encoding: 'utf8',
    stdio: opts.quiet ? ['ignore', 'pipe', 'pipe'] : ['ignore', 'inherit', 'inherit']
  })
  if (res.status !== 0) {
    const detail = opts.quiet ? `${res.stderr || res.stdout || ''}`.trim() : ''
    throw new Error(`${cmd} ${args.join(' ')} failed${detail ? `: ${detail}` : ''}`)
  }
  return `${res.stdout || ''}`.trim()
}

function markerSource(targetRoot: string): string {
  const marker = join(targetRoot, '.lazy-harness', 'state', 'synced-from-commit')
  if (!existsSync(marker)) return ''
  try {
    const data = JSON.parse(readFileSync(marker, 'utf8'))
    const value = typeof data.sourceRoot === 'string' ? data.sourceRoot : ''
    return value
  } catch {
    return ''
  }
}

function looksLikeSource(path: string): boolean {
  return existsSync(join(path, '.lazy-harness', 'scripts', 'lazy-sync.ts')) &&
    existsSync(join(path, '.lazy-harness', 'AGENTS.md'))
}

function ensureSource(args: Args, targetRoot: string): string {
  let source = args.source || markerSource(targetRoot) || args.cacheDir
  source = resolve(source)

  if (existsSync(source) && looksLikeSource(source)) {
    log(`[Source] update existing checkout: ${source}`)
    if (existsSync(join(source, '.git'))) {
      try {
        run('git', ['remote', 'set-url', 'origin', args.repo], { cwd: source, quiet: true })
      } catch {
        // Some local dogfooding sources may not have origin. Keep going.
      }
      run('git', ['fetch', 'origin', '--tags'], { cwd: source })
      checkoutRef(source, args.ref)
    } else {
      log('  source is not a git checkout; skipping fetch/checkout')
    }
    return source
  }

  log(`[Source] clone ${args.repo} → ${source}`)
  mkdirSync(dirname(source), { recursive: true })
  run('git', ['clone', args.repo, source])
  checkoutRef(source, args.ref)
  return source
}

function gitOutput(source: string, args: string[]): string {
  const res = spawnSync('git', args, { cwd: source, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })
  if (res.status !== 0) {
    throw new Error(`git ${args.join(' ')} failed: ${`${res.stderr || res.stdout || ''}`.trim()}`)
  }
  return `${res.stdout || ''}`.trim()
}

function assertCleanGitWorktree(source: string): void {
  const status = gitOutput(source, ['status', '--porcelain'])
  if (status) {
    throw new Error(
      `source checkout has uncommitted changes: ${source}\n` +
        `Commit/stash them, or use --source pointing at a clean cache checkout. Current changes:\n${status}`
    )
  }
}

function checkoutRef(source: string, ref: string): void {
  assertCleanGitWorktree(source)
  const remoteRef = `origin/${ref}`
  const hasRemote = spawnSync('git', ['show-ref', '--verify', '--quiet', `refs/remotes/${remoteRef}`], {
    cwd: source,
    stdio: 'ignore'
  }).status === 0

  if (hasRemote) {
    const current = gitOutput(source, ['branch', '--show-current'])
    if (current !== ref) {
      const hasLocal = spawnSync('git', ['show-ref', '--verify', '--quiet', `refs/heads/${ref}`], {
        cwd: source,
        stdio: 'ignore'
      }).status === 0
      if (hasLocal) run('git', ['checkout', ref], { cwd: source })
      else run('git', ['checkout', '-b', ref, remoteRef], { cwd: source })
    }
    run('git', ['merge', '--ff-only', remoteRef], { cwd: source })
  } else {
    run('git', ['checkout', ref], { cwd: source })
  }
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  QUIET = args.quiet

  const targetRoot = resolve(args.target || process.cwd())
  if (!existsSync(join(targetRoot, '.lazy-harness'))) {
    console.error(`Error: target has no .lazy-harness/: ${targetRoot}`)
    process.exit(1)
  }
  if (!existsSync(join(targetRoot, '.git'))) {
    console.error(`Error: target is not a git repo: ${targetRoot}`)
    process.exit(1)
  }

  try {
    log('lazy-update')
    log(`  target: ${targetRoot}`)
    log(`  ref:    ${args.ref}`)
    if (args.dryRun) log('  mode:   DRY-RUN target sync')

    const sourceRoot = ensureSource(args, targetRoot)
    if (!looksLikeSource(sourceRoot)) {
      console.error(`Error: source does not look like lazy-harness: ${sourceRoot}`)
      process.exit(1)
    }

    const syncScript = join(targetRoot, '.lazy-harness', 'scripts', 'lazy-sync.ts')
    const syncArgs = [syncScript, '--from', sourceRoot, '--target', targetRoot]
    if (args.dryRun) syncArgs.push('--dry-run')
    if (args.force) syncArgs.push('--force')
    if (args.quiet) syncArgs.push('--quiet')

    log('\n[Sync]')
    const res = spawnSync('bun', syncArgs, { stdio: 'inherit' })
    process.exit(res.status ?? 1)
  } catch (error) {
    console.error(`Error: ${(error as Error).message}`)
    process.exit(1)
  }
}

main()
