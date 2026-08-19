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
 *   bun .lazy-harness/scripts/lazy-sync.ts [--from <dir>] [--target <dir>] [--dry-run] [--force] [--skip-knowledge-seeds] [--quiet]
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
  readdirSync,
  unlinkSync,
  rmSync
} from 'node:fs'
import { join, dirname, resolve, relative } from 'node:path'
import { execSync, spawnSync } from 'node:child_process'
import { appendJsonlStable } from './runtime-paths.ts'
import { isTrustedRoot } from './jcode-trust.ts'
import { shouldIncludeManifestPath } from './manifest-path-matcher.ts'

// ─────────────────────────────────────────────────────────────
// Args
// ─────────────────────────────────────────────────────────────

interface Args {
  target: string
  from: string
  dryRun: boolean
  force: boolean
  skipKnowledgeSeeds: boolean
  quiet: boolean
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    target: '',
    from: '',
    dryRun: false,
    force: false,
    skipKnowledgeSeeds: false,
    quiet: false
  }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--target') args.target = argv[++i]
    else if (a === '--from') args.from = argv[++i]
    else if (a === '--dry-run') args.dryRun = true
    else if (a === '--force') args.force = true
    else if (a === '--skip-knowledge-seeds') args.skipKnowledgeSeeds = true
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
  --target <dir>             Host root (default: cwd)
  --from <dir>               Framework source (auto from state/synced-from-commit if omitted)
  --dry-run                  Show changes only
  --force                    Update despite drift
  --skip-knowledge-seeds     Do not merge knowledge/*.jsonl; other Category A and registry seeds still sync
  --quiet                    Suppress per-file logs

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

// ─────────────────────────────────────────────────────────────
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

function mergeJsonlSeed(src: string, dest: string, targetRoot: string): 'updated' | 'unchanged' {
  if (!existsSync(dest)) {
    copyFile(src, dest)
    return 'updated'
  }
  const srcLines = readFileSync(src, 'utf8').split(/\n/).filter((line) => line.trim().length > 0)
  const destText = readFileSync(dest, 'utf8')
  const destLines = destText.split(/\n/).filter((line) => line.trim().length > 0)
  const seen = new Set(destLines)
  const missing = srcLines.filter((line) => !seen.has(line))
  if (missing.length === 0) return 'unchanged'
  if (DRY) {
    log(`  [dry] would merge ${missing.length} seed JSONL rows into: ${dest}`)
    return 'updated'
  }
  ensureDir(dirname(dest))
  let appended = 0
  let conflicts = 0
  let plain = 0
  for (const line of missing) {
    try {
      const row = JSON.parse(line)
      const status = appendJsonlStable(dest, row, 'id', targetRoot)
      if (status === 'appended') appended += 1
      else if (status === 'conflict-recorded') conflicts += 1
    } catch {
      const current = readFileSync(dest, 'utf8')
      const prefix = current.endsWith('\n') || current.length === 0 ? '' : '\n'
      writeFileSync(dest, `${current}${prefix}${line}\n`)
      plain += 1
    }
  }
  log(`  merged ${missing.length} seed JSONL rows into: ${dest} (${appended} appended, ${conflicts} conflicts, ${plain} plain)`)
  return 'updated'
}

function isKnowledgeSeedItem(item: ManifestItem): boolean {
  return item.path === 'knowledge/' || item.path === 'knowledge'
}

function isCapabilitiesSeedItem(item: ManifestItem): boolean {
  return item.path === 'ssot/capabilities.json'
}

function isPoliciesSeedItem(item: ManifestItem): boolean {
  return item.path === 'ssot/policies.json'
}

function mergeCapabilitiesSeed(src: string, dest: string): 'updated' | 'unchanged' {
  if (!existsSync(dest)) {
    copyFile(src, dest)
    return 'updated'
  }

  let srcData: Record<string, unknown>
  let destData: Record<string, unknown>
  try {
    srcData = JSON.parse(readFileSync(src, 'utf8')) as Record<string, unknown>
    destData = JSON.parse(readFileSync(dest, 'utf8')) as Record<string, unknown>
  } catch (err) {
    log(`  ⚠ could not merge capabilities seed: ${(err as Error).message}`)
    return 'unchanged'
  }

  const srcCaps = Array.isArray(srcData.capabilities) ? srcData.capabilities : []
  const destCaps = Array.isArray(destData.capabilities) ? destData.capabilities : []
  const existingIds = new Set(
    destCaps
      .map((cap) => (cap && typeof cap === 'object' ? (cap as Record<string, unknown>).id : undefined))
      .filter((id): id is string => typeof id === 'string' && id.length > 0)
  )
  const missing = srcCaps.filter((cap) => {
    if (!cap || typeof cap !== 'object') return false
    const id = (cap as Record<string, unknown>).id
    return typeof id === 'string' && id.length > 0 && !existingIds.has(id)
  })

  if (missing.length === 0) return 'unchanged'
  if (DRY) {
    log(`  [dry] would merge ${missing.length} seed capabilities into: ${dest}`)
    return 'updated'
  }

  const merged: Record<string, unknown> = { ...destData }
  if (!('$schema' in merged) && '$schema' in srcData) merged.$schema = srcData.$schema
  if (!('version' in merged) && 'version' in srcData) merged.version = srcData.version
  merged.capabilities = [...destCaps, ...missing]
  ensureDir(dirname(dest))
  writeFileSync(dest, `${JSON.stringify(merged, null, 2)}\n`, 'utf8')
  log(`  merged ${missing.length} seed capabilities into: ${dest}`)
  return 'updated'
}

function mergePoliciesSeed(src: string, dest: string): 'updated' | 'unchanged' {
  if (!existsSync(dest)) {
    copyFile(src, dest)
    return 'updated'
  }

  let srcData: Record<string, unknown>
  let destData: Record<string, unknown>
  try {
    srcData = JSON.parse(readFileSync(src, 'utf8')) as Record<string, unknown>
    destData = JSON.parse(readFileSync(dest, 'utf8')) as Record<string, unknown>
  } catch (err) {
    log(`  ⚠ could not merge policies seed: ${(err as Error).message}`)
    return 'unchanged'
  }

  const srcPolicies = Array.isArray(srcData.policies) ? srcData.policies : []
  const destPolicies = Array.isArray(destData.policies) ? destData.policies : []
  const existingIds = new Set(
    destPolicies
      .map((policy) => (policy && typeof policy === 'object' ? (policy as Record<string, unknown>).id : undefined))
      .filter((id): id is string => typeof id === 'string' && id.length > 0)
  )
  const missing = srcPolicies.filter((policy) => {
    if (!policy || typeof policy !== 'object') return false
    const id = (policy as Record<string, unknown>).id
    return typeof id === 'string' && id.length > 0 && !existingIds.has(id)
  })

  if (missing.length === 0) return 'unchanged'
  if (DRY) {
    log(`  [dry] would merge ${missing.length} seed policies into: ${dest}`)
    return 'updated'
  }

  const merged: Record<string, unknown> = { ...destData }
  if (!('$schema' in merged) && '$schema' in srcData) merged.$schema = srcData.$schema
  if (!('version' in merged) && 'version' in srcData) merged.version = srcData.version
  merged.policies = [...destPolicies, ...missing]
  ensureDir(dirname(dest))
  writeFileSync(dest, `${JSON.stringify(merged, null, 2)}\n`, 'utf8')
  log(`  merged ${missing.length} seed policies into: ${dest}`)
  return 'updated'
}


function removeRelocatedStaleCopy(src: string, staleDest: string, dest: string): boolean {
  if (staleDest === dest || !existsSync(staleDest)) return false
  if (readFileSync(src).compare(readFileSync(staleDest)) !== 0) return false
  if (DRY) {
    log(`  [dry] would remove relocated stale copy: ${staleDest}`)
    return true
  }
  unlinkSync(staleDest)
  log(`  removed relocated stale copy: ${staleDest}`)
  return true
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

function isSourceWorkingTreeDirty(sourceRoot: string): boolean {
  try {
    const out = execSync('git status --porcelain -- .lazy-harness', {
      cwd: sourceRoot,
      encoding: 'utf8'
    }).trim()
    return out.length > 0
  } catch {
    return false
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
    // Same commit, but check working-tree for uncommitted source changes that
    // would otherwise be silently skipped by the equal-fast-path.
    if (isSourceWorkingTreeDirty(sourceRoot)) {
      return {
        status: 'ahead',
        hostSha,
        sourceSha,
        message: 'Source working-tree has uncommitted .lazy-harness changes (dirty)'
      }
    }
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
  targetPath?: string
  kind?: 'file' | 'directory'
  glob?: string[]
  exclude?: string[]
}

const removedName = (left: string, right: string): string => `${left}${right}`

const KNOWN_REMOVED_MANAGED_FILES = [
  '.lazy-harness/scripts/operational-state.ts',
  '.lazy-harness/scripts/task-router.ts',
  `.lazy-harness/scripts/${removedName('context', '-broker-dogfood.ts')}`,
  `.lazy-harness/scripts/${removedName('context', '-delivery.ts')}`,
  `.lazy-harness/scripts/${removedName('relevant', '-record-query.ts')}`,
  `.lazy-harness/scripts/${removedName('context', '-index.ts')}`,
  '.lazy-harness/schemas/operational-state-packet.schema.json',
  `.lazy-harness/schemas/${removedName('context', '-delivery-packet.schema.json')}`,
  `.lazy-harness/schemas/${removedName('relevant', '-record-index.schema.json')}`,
  `.lazy-harness/schemas/${removedName('context', '-index.schema.json')}`,
  `.lazy-harness/generated/${removedName('context', '-index.json')}`,
  '.lazy-harness/spec/platform/operational-state-packet.md',
  `.lazy-harness/spec/platform/${removedName('context', '-broker-dogfood.md')}`,
  `.lazy-harness/spec/platform/${removedName('context', '-delivery-contract.md')}`,
  `.lazy-harness/spec/platform/${removedName('relevant', '-record-query.md')}`,
  '.lazy-harness/tests/operational-state-packet.md',
  `.lazy-harness/tests/${removedName('context', '-broker-dogfood.md')}`,
  `.lazy-harness/tests/${removedName('relevant', '-record-query-cli-equals-flags.md')}`,
  '.lazy-harness/fixtures/task-router/cases.json',
  `.lazy-harness/scripts/${removedName('jcode', '-wiring.ts')}`,
  `.lazy-harness/scripts/${removedName('skill', '-create.ts')}`,
  '.lazy-harness/spec/platform/graph-explain.md',
  '.lazy-harness/spec/platform/graph-path.md',
  '.lazy-harness/spec/platform/graph-query.md',
  '.lazy-harness/spec/platform/graph-cleanup.md',
  '.lazy-harness/tests/graph-explain.md',
  '.lazy-harness/tests/graph-path.md',
  '.lazy-harness/tests/graph-query.md',
  '.lazy-harness/tests/graph-cleanup.md'
]

const KNOWN_REMOVED_MANAGED_DIRS = [
  `.lazy-harness/fixtures/${removedName('context', '-delivery')}`,
  '.lazy-harness/fixtures/task-router'
]

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
  items: ManifestItem[],
  skipKnowledgeSeeds = false
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
      const dest = join(targetLazy, item.targetPath ?? item.path)
      if (!existsSync(src)) {
        missing++
        continue
      }
      if (isCapabilitiesSeedItem(item)) {
        const result = mergeCapabilitiesSeed(src, dest)
        if (result === 'updated') updated++
        else unchanged++
        continue
      }
      if (isPoliciesSeedItem(item)) {
        const result = mergePoliciesSeed(src, dest)
        if (result === 'updated') updated++
        else unchanged++
        continue
      }
      if (existsSync(dest) && readFileSync(src).compare(readFileSync(dest)) === 0) {
        unchanged++
      } else {
        copyFile(src, dest)
        updated++
      }
      if (item.targetPath) {
        const staleDest = join(targetLazy, item.path)
        if (removeRelocatedStaleCopy(src, staleDest, dest)) updated++
      }
      continue
    }

    const srcDir = join(sourceLazy, item.path)
    if (!existsSync(srcDir)) {
      missing++
      continue
    }
    const managedFiles = new Set<string>()
    const files = walkFiles(srcDir)
    for (const f of files) {
      if (!shouldIncludeManifestPath(f, item.glob, item.exclude)) continue
      managedFiles.add(f)
      const src = join(srcDir, f)
      const dest = join(targetLazy, item.targetPath ?? item.path, f)
      if (isKnowledgeSeedItem(item) && f.endsWith('.jsonl')) {
        if (skipKnowledgeSeeds) continue
        const result = mergeJsonlSeed(src, dest, targetRoot)
        if (result === 'updated') updated++
        else unchanged++
        continue
      }
      if (existsSync(dest) && readFileSync(src).compare(readFileSync(dest)) === 0) {
        unchanged++
      } else {
        copyFile(src, dest)
        updated++
      }
    }
    if (isKnowledgeSeedItem(item)) continue
    const destDir = join(targetLazy, item.targetPath ?? item.path)
    for (const f of walkFiles(destDir)) {
      if (!shouldIncludeManifestPath(f, item.glob, item.exclude)) continue
      if (managedFiles.has(f)) continue
      const stale = join(destDir, f)
      if (DRY) {
        log(`  [dry] would remove stale managed file: ${stale}`)
      } else {
        unlinkSync(stale)
        log(`  removed stale managed file: ${stale}`)
      }
      updated++
    }
  }

  log(`  → ${updated} updated, ${unchanged} unchanged, ${missing} missing`)
  return { updated, unchanged, missing }
}

function removeKnownRemovedManagedFiles(sourceRoot: string, targetRoot: string): number {
  let removed = 0
  for (const rel of KNOWN_REMOVED_MANAGED_FILES) {
    const sourcePath = join(sourceRoot, rel)
    const targetPath = join(targetRoot, rel)
    if (existsSync(sourcePath) || !existsSync(targetPath)) continue
    if (DRY) log(`  [dry] would remove known removed managed file: ${targetPath}`)
    else {
      unlinkSync(targetPath)
      log(`  removed known removed managed file: ${targetPath}`)
    }
    removed++
  }
  for (const rel of KNOWN_REMOVED_MANAGED_DIRS) {
    const sourcePath = join(sourceRoot, rel)
    const targetPath = join(targetRoot, rel)
    if (existsSync(sourcePath) || !existsSync(targetPath)) continue
    if (DRY) log(`  [dry] would remove known removed managed dir: ${targetPath}`)
    else {
      rmSync(targetPath, { recursive: true, force: true })
      log(`  removed known removed managed dir: ${targetPath}`)
    }
    removed++
  }
  if (removed > 0) log(`  → ${removed} known removed managed files pruned`)
  return removed
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

function reconcileAgentActivation(targetRoot: string): 'repaired' | 'dry-run' | 'activation-required' {
  if (!isTrustedRoot(targetRoot)) {
    log(`  ⊘ Jcode root remains untrusted; activate explicitly:`)
    log(`    ${join(targetRoot, '.lazy-harness', 'bin', 'lazy')} agent activate --target ${targetRoot}`)
    return 'activation-required'
  }
  const lazy = join(targetRoot, '.lazy-harness', 'bin', 'lazy')
  const argv = ['agent', 'activate', '--target', targetRoot, '--format=json']
  if (DRY) argv.push('--dry-run')
  const result = spawnSync(lazy, argv, { encoding: 'utf8', env: process.env })
  if (result.status !== 0) {
    const detail = result.stderr.trim() || result.stdout.trim() || `exit ${result.status ?? 1}`
    throw new Error(`trusted-root activation repair failed: ${detail}`)
  }
  log(`  ✓ trusted Pi/OMP/Jcode activation ${DRY ? 'checked' : 'repaired'}`)
  return DRY ? 'dry-run' : 'repaired'
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
  if (args.skipKnowledgeSeeds) log(`  knowledge seeds: SKIPPED (--skip-knowledge-seeds)`)

  // Drift detection
  const drift = detectDrift(sourceRoot, targetRoot)
  log(`\n[Drift] ${drift.status}: ${drift.message}`)
  log(`  host:   ${drift.hostSha.slice(0, 12) || '(none)'}`)
  log(`  source: ${drift.sourceSha.slice(0, 12) || '(none)'}`)

  if (drift.status === 'equal' && !args.force) {
    log('\n[Activation]')
    try {
      reconcileAgentActivation(targetRoot)
    } catch (error) {
      console.error(`Error: ${error instanceof Error ? error.message : String(error)}`)
      process.exit(3)
    }
    log('\n✓ Already in sync.')
    process.exit(0)
  }
  if ((drift.status === 'ahead' || drift.status === 'divergent') && !args.force) {
    console.error(`\nError: drift detected (${drift.status}). Use --force to proceed.`)
    process.exit(2)
  }

  // Sync
  const manifest = loadManifest(sourceRoot)
  const result = syncCategoryA(
    sourceRoot,
    targetRoot,
    manifest.categories.A.items,
    args.skipKnowledgeSeeds
  )
  result.updated += removeKnownRemovedManagedFiles(sourceRoot, targetRoot)

  log('\n[Activation]')
  let activation: 'repaired' | 'dry-run' | 'activation-required'
  try {
    activation = reconcileAgentActivation(targetRoot)
  } catch (error) {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`)
    process.exit(3)
  }

  // Publish the synced marker only after trusted activation repair succeeds.
  log('\n[Marker]')
  updateMarker(sourceRoot, targetRoot)

  // Summary
  log('\n[Summary]')
  log(`  updated:   ${result.updated}`)
  log(`  unchanged: ${result.unchanged}`)
  log(`  missing:   ${result.missing}`)
  log(`  activation: ${activation}`)
  log('')
  if (DRY) {
    log('Dry run complete. Re-run without --dry-run to apply.')
  } else {
    log(`✓ Synced. Next: python3 .lazy-harness/scripts/self-test.py`)
  }
}

main()
