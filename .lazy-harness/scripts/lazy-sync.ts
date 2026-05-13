#!/usr/bin/env bun
/**
 * lazy-sync — update framework 본체 (Category A) on an already-initialized host.
 *
 * Preserves Category B (institutional memory). Skips Category C as always.
 *
 * Drift detection:
 *   - Compares host's state/synced-from-commit vs source's HEAD
 *   - Equal: no-op
 *   - Behind: updates Category A files
 *   - Ahead/divergent: refuses unless --force
 *
 * Usage:
 *   bun .lazy-harness/scripts/lazy-sync.ts [--from <dir>] [--target <dir>] [--dry-run] [--force] [--quiet]
 *
 * Exit:
 *   0 success | 1 validation | 2 drift conflict | 3 IO
 */

import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  copyFileSync,
  statSync,
  readdirSync
} from 'node:fs'
import { join, dirname, resolve, relative } from 'node:path'
import { execSync } from 'node:child_process'

// ─────────────────────────────────────────────────────────────
// Args
// ─────────────────────────────────────────────────────────────

interface Args {
  target: string
  from: string
  dryRun: boolean
  force: boolean
  quiet: boolean
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    target: '',
    from: '',
    dryRun: false,
    force: false,
    quiet: false
  }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--target') args.target = argv[++i]
    else if (a === '--from') args.from = argv[++i]
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
  console.log(`lazy-sync — update framework 본체 on an already-initialized host.

Usage:
  bun lazy-sync.ts [options]

Options:
  --target <dir>   Host root (default: cwd)
  --from <dir>     Framework source (auto from state/synced-from-commit if omitted)
  --dry-run        Show changes only
  --force          Update despite drift
  --quiet          Suppress per-file logs

Exit:
  0 ok | 1 validation | 2 drift | 3 io`)
}

// ─────────────────────────────────────────────────────────────
// Logging
// ─────────────────────────────────────────────────────────────

let DRY = false
let QUIET = false

function log(msg: string): void {
  if (!QUIET) console.log(msg)
}

// ────────────────────────────────���────────────────────────────
// FS helpers
// ─────────────────────────────────────────────────────────────

function ensureDir(dir: string): void {
  if (DRY) return
  mkdirSync(dir, { recursive: true })
}

function copyFile(src: string, dest: string): void {
  if (DRY) {
    if (!existsSync(dest) || readFileSync(src).compare(readFileSync(dest)) !== 0) {
      log(`  [dry] would update: ${dest}`)
    }
    return
  }
  ensureDir(dirname(dest))
  copyFileSync(src, dest)
  try {
    const srcMode = statSync(src).mode
    if (srcMode & 0o111) execSync(`chmod +x ${JSON.stringify(dest)}`)
  } catch {
    /* ignore */
  }
}

function walkFiles(dir: string, baseDir: string = dir): string[] {
  const out: string[] = []
  if (!existsSync(dir)) return out
  const entries = readdirSync(dir, { withFileTypes: true })
  for (const e of entries) {
    const p = join(dir, e.name)
    if (e.isDirectory()) out.push(...walkFiles(p, baseDir))
    else if (e.isFile()) out.push(relative(baseDir, p))
  }
  return out
}

function matchGlob(name: string, glob: string): boolean {
  const re = new RegExp(
    '^' +
      glob
        .replace(/\./g, '\\.')
        .replace(/\*\*/g, '___DOUBLESTAR___')
        .replace(/\*/g, '[^/]*')
        .replace(/___DOUBLESTAR___/g, '.*') +
      '$'
  )
  return re.test(name)
}

function shouldInclude(relPath: string, glob?: string[], exclude?: string[]): boolean {
  if (exclude) {
    for (const ex of exclude) {
      if (matchGlob(relPath, ex) || relPath.startsWith(ex.replace(/\/$/, ''))) return false
    }
  }
  if (!glob || glob.length === 0) return true
  return glob.some((g) => matchGlob(relPath, g))
}

// ─────────────────────────────────────────────────────────────
// Drift detection
// ─────────────────────────────────────────────────────────────

interface DriftStatus {
  status: 'equal' | 'behind' | 'ahead' | 'divergent' | 'unknown'
  hostSha: string
  sourceSha: string
  message: string
}

function getCommitSha(repoRoot: string): string {
  try {
    return execSync('git rev-parse HEAD', { cwd: repoRoot, encoding: 'utf8' }).trim()
  } catch {
    return ''
  }
}

function detectDrift(sourceRoot: string, targetRoot: string): DriftStatus {
  const markerPath = join(targetRoot, '.lazy-harness', 'state', 'synced-from-commit')
  let hostSha = ''
  if (existsSync(markerPath)) {
    try {
      const data = JSON.parse(readFileSync(markerPath, 'utf8'))
      hostSha = (data.syncedFromCommit as string) ?? ''
    } catch {
      /* ignore */
    }
  }
  const sourceSha = getCommitSha(sourceRoot)

  if (!sourceSha) {
    return { status: 'unknown', hostSha, sourceSha, message: 'Could not determine source HEAD sha' }
  }
  if (!hostSha) {
    return {
      status: 'unknown',
      hostSha,
      sourceSha,
      message: 'Host has no state/synced-from-commit (was this initialized by lazy-init?)'
    }
  }
  if (hostSha === sourceSha) {
    return { status: 'equal', hostSha, sourceSha, message: 'Already in sync' }
  }
  // Try to use git to determine relationship
  try {
    const isAncestor = (a: string, b: string): boolean => {
      try {
        execSync(`git merge-base --is-ancestor ${a} ${b}`, { cwd: sourceRoot, stdio: 'ignore' })
        return true
      } catch {
        return false
      }
    }
    if (isAncestor(hostSha, sourceSha)) {
      return { status: 'behind', hostSha, sourceSha, message: `Host is behind by N commits` }
    }
    if (isAncestor(sourceSha, hostSha)) {
      return { status: 'ahead', hostSha, sourceSha, message: 'Host is ahead of source' }
    }
    return { status: 'divergent', hostSha, sourceSha, message: 'Host and source diverged' }
  } catch {
    return { status: 'unknown', hostSha, sourceSha, message: 'Could not compute ancestry' }
  }
}

// ─────────────────────────────────────────────────────────────
// Source detection
// ─────────────────────────────────────────────────────────────

function detectSourceFromMarker(targetRoot: string): string {
  const markerPath = join(targetRoot, '.lazy-harness', 'state', 'synced-from-commit')
  if (!existsSync(markerPath)) return ''
  try {
    const data = JSON.parse(readFileSync(markerPath, 'utf8'))
    return (data.sourceRoot as string) ?? ''
  } catch {
    return ''
  }
}

// ─────────────────────────────────────────────────────────────
// Manifest
// ─────────────────────────────────────────────────────────────

interface ManifestItem {
  path: string
  kind?: 'file' | 'directory'
  glob?: string[]
  exclude?: string[]
}

interface InitManifest {
  categories: {
    A: { items: ManifestItem[] }
  }
}

function loadManifest(sourceRoot: string): InitManifest {
  const p = join(sourceRoot, '.lazy-harness', 'manifests', 'init-categories.json')
  return JSON.parse(readFileSync(p, 'utf8')) as InitManifest
}

// ─────────────────────────────────────────────────────────────
// Category A sync (same logic as lazy-init but with diff awareness)
// ─────────────────────────────────────────────────────────────

function syncCategoryA(
  sourceRoot: string,
  targetRoot: string,
  items: ManifestItem[]
): { updated: number; unchanged: number; missing: number } {
  const sourceLazy = join(sourceRoot, '.lazy-harness')
  const targetLazy = join(targetRoot, '.lazy-harness')

  let updated = 0
  let unchanged = 0
  let missing = 0

  log('\n[Category A] Framework 본체 sync')

  for (const item of items) {
    if (
      item.path === 'AGENTS.md' ||
      item.path === 'JCODE-INTEGRATION.md' ||
      item.path === 'README.md' ||
      item.kind === 'file'
    ) {
      const src = join(sourceLazy, item.path)
      const dest = join(targetLazy, item.path)
      if (!existsSync(src)) {
        missing++
        continue
      }
      if (existsSync(dest) && readFileSync(src).compare(readFileSync(dest)) === 0) {
        unchanged++
      } else {
        copyFile(src, dest)
        updated++
      }
      continue
    }

    const srcDir = join(sourceLazy, item.path)
    if (!existsSync(srcDir)) {
      missing++
      continue
    }
    const files = walkFiles(srcDir)
    for (const f of files) {
      if (!shouldInclude(f, item.glob, item.exclude)) continue
      const src = join(srcDir, f)
      const dest = join(targetLazy, item.path, f)
      if (existsSync(dest) && readFileSync(src).compare(readFileSync(dest)) === 0) {
        unchanged++
      } else {
        copyFile(src, dest)
        updated++
      }
    }
  }

  log(`  → ${updated} updated, ${unchanged} unchanged, ${missing} missing`)
  return { updated, unchanged, missing }
}

// ─────────────────────────────────────────────────────────────
// Version marker update
// ─────────────────────────────────────────────────────────────

function updateMarker(sourceRoot: string, targetRoot: string): void {
  const sha = getCommitSha(sourceRoot)
  const content =
    JSON.stringify(
      {
        syncedFromCommit: sha,
        syncedAt: new Date().toISOString(),
        sourceRoot,
        manifestVersion: '1.0'
      },
      null,
      2
    ) + '\n'
  const p = join(targetRoot, '.lazy-harness', 'state', 'synced-from-commit')
  if (DRY) {
    log(`  [dry] would update marker → ${sha.slice(0, 12)}`)
    return
  }
  ensureDir(dirname(p))
  writeFileSync(p, content)
  log(`  ✓ marker updated → ${sha.slice(0, 12)}`)
}

// ─────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  DRY = args.dryRun
  QUIET = args.quiet

  const targetRoot = resolve(args.target || process.cwd())

  // Pre-flight
  if (!existsSync(join(targetRoot, '.lazy-harness'))) {
    console.error(`Error: target has no .lazy-harness/ — run lazy-init first.`)
    process.exit(1)
  }

  let sourceRoot = args.from ? resolve(args.from) : detectSourceFromMarker(targetRoot)
  if (!sourceRoot) {
    console.error(
      `Error: could not determine source. Pass --from or ensure state/synced-from-commit has sourceRoot.`
    )
    process.exit(1)
  }
  sourceRoot = resolve(sourceRoot)

  if (!existsSync(join(sourceRoot, '.lazy-harness', 'AGENTS.md'))) {
    console.error(`Error: source does not look like a framework worktree: ${sourceRoot}`)
    process.exit(1)
  }

  log(`lazy-sync`)
  log(`  source: ${sourceRoot}`)
  log(`  target: ${targetRoot}`)
  if (DRY) log(`  mode:   DRY-RUN`)

  // Drift detection
  const drift = detectDrift(sourceRoot, targetRoot)
  log(`\n[Drift] ${drift.status}: ${drift.message}`)
  log(`  host:   ${drift.hostSha.slice(0, 12) || '(none)'}`)
  log(`  source: ${drift.sourceSha.slice(0, 12) || '(none)'}`)

  if (drift.status === 'equal') {
    log('\n✓ Already in sync. Nothing to do.')
    process.exit(0)
  }
  if ((drift.status === 'ahead' || drift.status === 'divergent') && !args.force) {
    console.error(`\nError: drift detected (${drift.status}). Use --force to proceed.`)
    process.exit(2)
  }

  // Sync
  const manifest = loadManifest(sourceRoot)
  const result = syncCategoryA(sourceRoot, targetRoot, manifest.categories.A.items)

  // Update marker
  log('\n[Marker]')
  updateMarker(sourceRoot, targetRoot)

  // Summary
  log('\n[Summary]')
  log(`  updated:   ${result.updated}`)
  log(`  unchanged: ${result.unchanged}`)
  log(`  missing:   ${result.missing}`)
  log('')
  if (DRY) {
    log('Dry run complete. Re-run without --dry-run to apply.')
  } else {
    log(`✓ Synced. Next: python3 .lazy-harness/scripts/self-test.py`)
  }
}

main()
