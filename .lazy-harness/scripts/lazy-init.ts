#!/usr/bin/env bun
/**
 * lazy-init — bootstrap lazy-harness on a host project.
 *
 * Reads manifests/init-categories.json and lays down:
 *   Category A: framework 본체 (rsync from source)
 *   Category B: institutional memory 빈 골격 (mkdir + README)
 *   Category C: skip (framework own memory)
 *
 * Post-init actions:
 *   - .git/info/exclude 에 /.lazy-harness/ 추가
 *   - Host 의 .git/hooks/pre-commit 에 delegate
 *   - state/synced-from-commit 박음
 *   - prints project-local Pi/OMP activation command
 *
 * Source: 본 worktree (lazy-harness dev repo) 자체. host-pilot.ts 처럼
 * `--from` 으로 명시하거나, 본 script 가 있는 worktree root 를 auto-detect.
 *
 * Usage:
 *   bun .lazy-harness/scripts/lazy-init.ts --target /path/to/host [--from /path/to/framework-source]
 *   bun .lazy-harness/scripts/lazy-init.ts --target ./ --dry-run
 *   bun .lazy-harness/scripts/lazy-init.ts --target ./ --force
 *
 * Flags:
 *   --target <dir>   Required. Host project root where .lazy-harness/ gets written.
 *   --from <dir>     Optional. Framework source worktree. Defaults to script's resolved worktree.
 *   --dry-run        Print planned actions, don't modify filesystem.
 *   --force          Overwrite existing .lazy-harness/ (default: refuse if non-empty).
 *   --skip-hooks     Don't wire git pre-commit hook.
 *   --quiet          Suppress per-file logs.
 *
 * Exit codes:
 *   0  Success
 *   1  Validation error (e.g., --target missing, target not a git repo)
 *   2  Conflict (target has existing .lazy-harness/ without --force)
 *   3  IO error (rsync/mkdir/write failed)
 */

import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  copyFileSync,
  statSync,
  readdirSync,
  appendFileSync,
  renameSync
} from 'node:fs'
import { join, dirname, basename, resolve, relative } from 'node:path'
import { execSync } from 'node:child_process'

// ─────────────────────────────────────────────────────────────
// Args
// ─────────────────────────────────────────────────────────────

interface Args {
  target: string
  from: string
  dryRun: boolean
  force: boolean
  skipHooks: boolean
  quiet: boolean
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    target: '',
    from: '',
    dryRun: false,
    force: false,
    skipHooks: false,
    quiet: false
  }
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--target') args.target = argv[++i]
    else if (a === '--from') args.from = argv[++i]
    else if (a === '--dry-run') args.dryRun = true
    else if (a === '--force') args.force = true
    else if (a === '--skip-hooks') args.skipHooks = true
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
  console.log(`lazy-init — bootstrap lazy-harness on a host project.

Usage:
  bun lazy-init.ts --target <dir> [options]

Required:
  --target <dir>    Host project root (must be a git repo)

Options:
  --from <dir>      Framework source (defaults to script's worktree)
  --dry-run         Show planned actions only
  --force           Overwrite existing .lazy-harness/
  --skip-hooks      Don't wire git pre-commit hook
  --quiet           Suppress per-file logs

  0 success | 1 validation | 2 conflict | 3 io

After success, run:
  .lazy-harness/bin/lazy agent activate --target <dir>`)
}

// ─────────────────────────────────────────────────────────────
// Source auto-detect
// ─────────────────────────────────────────────────────────────

function detectFrameworkSource(): string {
  // This script lives at <source>/.lazy-harness/scripts/lazy-init.ts
  // Walk up: __dirname → scripts/ → .lazy-harness/ → <source>
  const scriptPath = resolve(import.meta.dir)
  const lazyHarnessDir = dirname(scriptPath)
  const sourceRoot = dirname(lazyHarnessDir)
  // Sanity check
  if (!existsSync(join(sourceRoot, '.lazy-harness', 'AGENTS.md'))) {
    throw new Error(
      `Could not auto-detect framework source. Script at ${scriptPath} — expected <source>/.lazy-harness/scripts/. Pass --from explicitly.`
    )
  }
  return sourceRoot
}

// ─────────────────────────────────────────────────────────────
// Manifest
// ─────────────────────────────────────────────────────────────

interface ManifestItem {
  path: string
  targetPath?: string
  kind?: 'file' | 'directory'
  description?: string
  glob?: string[]
  exclude?: string[]
  subdirs?: string[]
  trigger?: string
  seed?: string[]
}

interface InitManifest {
  version: string
  categories: {
    A: { items: ManifestItem[] }
    B: { items: ManifestItem[] }
    C: { items: ManifestItem[] }
  }
  postInit: {
    actions: Array<{
      kind: string
      description: string
      lines?: string[]
      path?: string
      skills?: string[]
    }>
  }
}

function loadManifest(sourceRoot: string): InitManifest {
  const manifestPath = join(sourceRoot, '.lazy-harness', 'manifests', 'init-categories.json')
  if (!existsSync(manifestPath)) {
    throw new Error(`Manifest not found: ${manifestPath}`)
  }
  const raw = readFileSync(manifestPath, 'utf8')
  return JSON.parse(raw) as InitManifest
}

// ─────────────────────────────────────────────────────────────
// Logging
// ─────────────────────────────────────────────────────────────

let DRY = false
let QUIET = false

function log(msg: string): void {
  if (!QUIET) console.log(msg)
}

function logAction(verb: string, target: string): void {
  if (DRY) log(`  [dry] ${verb} ${target}`)
  else if (!QUIET) log(`  ${verb} ${target}`)
}

// ─────────────────────────────────────────────────────────────
// Filesystem helpers
// ─────────────────────────────────────────────────────────────

function ensureDir(dir: string): void {
  if (DRY) {
    logAction('mkdir', dir)
    return
  }
  mkdirSync(dir, { recursive: true })
}

function writeFile(path: string, content: string, mode = 0o644): void {
  if (DRY) {
    logAction('write', path)
    return
  }
  ensureDir(dirname(path))
  writeFileSync(path, content, { mode })
}

function copyFile(src: string, dest: string): void {
  if (DRY) {
    logAction('copy', `${src} → ${dest}`)
    return
  }
  ensureDir(dirname(dest))
  copyFileSync(src, dest)
  // Preserve executable bit
  try {
    const srcMode = statSync(src).mode
    if (srcMode & 0o111) {
      execSync(`chmod +x ${JSON.stringify(dest)}`)
    }
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
    if (e.isDirectory()) {
      out.push(...walkFiles(p, baseDir))
    } else if (e.isFile()) {
      out.push(relative(baseDir, p))
    }
  }
  return out
}

function matchGlob(name: string, glob: string): boolean {
  // Minimal glob: *, **, exact, suffix wildcard
  // Examples: "*.ts", "lifecycle/*.sh", "fixtures/**/*.json", "*.schema.json", "README.md"
  // Convert to regex
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
// Pre-flight
// ─────────────────────────────────────────────────────────────

function preflight(args: Args): void {
  if (!args.target) {
    console.error('Error: --target is required')
    process.exit(1)
  }

  const target = resolve(args.target)
  if (!existsSync(target)) {
    console.error(`Error: target does not exist: ${target}`)
    process.exit(1)
  }

  if (!existsSync(join(target, '.git'))) {
    console.error(`Error: target is not a git repo (no .git/): ${target}`)
    process.exit(1)
  }

  const lazyDir = join(target, '.lazy-harness')
  if (existsSync(lazyDir) && !args.force) {
    // Check if non-empty
    const entries = readdirSync(lazyDir)
    if (entries.length > 0) {
      console.error(
        `Error: ${lazyDir} already exists and is non-empty. Use --force to overwrite, or run lazy-sync.`
      )
      process.exit(2)
    }
  }
}

// ─────────────────────────────────────────────────────────────
// Category A: framework 본체 copy
// ─────────────────────────────────────────────────────────────

function copyCategoryA(
  sourceRoot: string,
  targetRoot: string,
  items: ManifestItem[]
): { copied: number; skipped: number } {
  const sourceLazy = join(sourceRoot, '.lazy-harness')
  const targetLazy = join(targetRoot, '.lazy-harness')

  let copied = 0
  let skipped = 0

  log('\n[Category A] Framework 본체 copy')

  for (const item of items) {
    // Top-level files (AGENTS.md, JCODE-INTEGRATION.md, README.md)
    if (item.path === 'AGENTS.md' || item.path === 'JCODE-INTEGRATION.md' || item.path === 'README.md') {
      const src = join(sourceLazy, item.path)
      const dest = join(targetLazy, item.targetPath ?? item.path)
      if (existsSync(src)) {
        copyFile(src, dest)
        copied++
      } else {
        log(`  ⚠ source missing: ${src}`)
        skipped++
      }
      continue
    }

    if (item.kind === 'file') {
      const src = join(sourceLazy, item.path)
      const dest = join(targetLazy, item.targetPath ?? item.path)
      if (existsSync(src)) {
        copyFile(src, dest)
        copied++
      } else {
        log(`  ⚠ source missing: ${src}`)
        skipped++
      }
      continue
    }

    // Directory with glob
    const srcDir = join(sourceLazy, item.path)
    if (!existsSync(srcDir)) {
      log(`  ⚠ source dir missing: ${srcDir}`)
      skipped++
      continue
    }

    const files = walkFiles(srcDir)
    for (const f of files) {
      if (!shouldInclude(f, item.glob, item.exclude)) continue
      const src = join(srcDir, f)
      const dest = join(targetLazy, item.targetPath ?? item.path, f)
      copyFile(src, dest)
      copied++
    }
  }

  log(`  → ${copied} files copied, ${skipped} skipped`)
  return { copied, skipped }
}

// ─────────────────────────────────────────────────────────────
// Category B: 빈 골격 + README
// ─────────────────────────────────────────────────────────────

function makeReadme(item: ManifestItem): string {
  const lines = [
    `# ${item.path}`,
    '',
    item.description ?? '',
    '',
    '## Trigger to fill',
    '',
    item.trigger ?? '_unspecified_',
    '',
    '## Status',
    '',
    '- Empty is valid (lazy-harness empty-container tolerance).',
    "- Filled when triggers fire — host AI grep's `.lazy-harness/` and adds records.",
    '',
    `_Created by lazy-init from manifests/init-categories.json (Category B)._`
  ]
  return lines.join('\n') + '\n'
}

function makeSeedFile(name: string): string {
  if (name === 'test-strategy.xml') {
    return `<?xml version="1.0" encoding="UTF-8"?>
<testStrategy version="1.0" status="draft" source="lazy-init">
  <!--
    Canonical host test strategy.
    If this is empty/stale, fill it from current host-root evidence only:
    package.json scripts, test config files, tests/**, and project docs.
    Do not inspect parent/sibling repositories.
  -->
  <discovery rootBound="true">
    <allowedSources>
      <source>package.json</source>
      <source>vitest.config.*</source>
      <source>jest.config.*</source>
      <source>playwright.config.*</source>
      <source>tests/**</source>
      <source>src/**/__tests__/**</source>
      <source>docs/**</source>
      <source>AGENTS.md</source>
    </allowedSources>
    <forbiddenSources>
      <source>../**</source>
      <source>sibling repositories</source>
    </forbiddenSources>
  </discovery>
  <commands>
    <lint command="" required="project" />
    <typecheck command="" required="project" />
    <unit command="" required="project" />
    <e2e command="" required="optional" />
  </commands>
  <affectedTestRouting command="" />
  <fallback>
    <packageScripts order="test:run,test:unit,test" />
    <ifMissing>ask-user-and-record</ifMissing>
  </fallback>
  <implementationMap>
    <file path="package.json" role="test command source" />
    <file path=".lazy-harness/tests/test-strategy.xml" role="canonical test strategy" />
  </implementationMap>
</testStrategy>
`
  }
  if (name.endsWith('.jsonl')) {
    return '' // empty JSONL
  }
  return `# ${name}\n\nSeeded by lazy-init. Replace with real content as triggers fire.\n`
}

function createCategoryB(
  targetRoot: string,
  items: ManifestItem[]
): { created: number } {
  const targetLazy = join(targetRoot, '.lazy-harness')

  let created = 0
  log('\n[Category B] Host institutional memory (빈 골격)')

  for (const item of items) {
    const dir = join(targetLazy, item.path)
    ensureDir(dir)

    // Subdirs
    if (item.subdirs) {
      for (const sub of item.subdirs) {
        ensureDir(join(dir, sub))
        writeFile(
          join(dir, sub, 'README.md'),
          makeReadme({ ...item, path: `${item.path}${sub}/`, description: `Subdirectory of ${item.path}: ${sub}` })
        )
      }
    }

    // Top README
    writeFile(join(dir, 'README.md'), makeReadme(item))
    created++

    // Seed files
    if (item.seed) {
      for (const s of item.seed) {
        writeFile(join(dir, s), makeSeedFile(s))
      }
    }
  }

  log(`  → ${created} containers seeded`)
  return { created }
}

// ─────────────────────────────────────────────────────────────
// Post-init actions
// ─────────────────────────────────────────────────────────────

function postInitGitInfoExclude(targetRoot: string, lines: string[]): void {
  // Determine real .git dir (may be a worktree gitdir file)
  let gitDir = join(targetRoot, '.git')
  const gitStat = statSync(gitDir)
  if (gitStat.isFile()) {
    // worktree: .git is a file with "gitdir: <path>"
    const content = readFileSync(gitDir, 'utf8').trim()
    const m = content.match(/^gitdir:\s*(.+)$/)
    if (m) {
      gitDir = m[1]
      if (!gitDir.startsWith('/')) gitDir = resolve(targetRoot, gitDir)
    }
  }

  const excludePath = join(gitDir, 'info', 'exclude')
  ensureDir(dirname(excludePath))

  let existing = ''
  if (existsSync(excludePath)) {
    existing = readFileSync(excludePath, 'utf8')
  }

  const toAdd: string[] = []
  for (const line of lines) {
    if (!existing.includes(line)) toAdd.push(line)
  }

  if (toAdd.length === 0) {
    log(`  ✓ .git/info/exclude already has all entries`)
    return
  }

  if (DRY) {
    logAction('append', `${excludePath}: ${toAdd.join(', ')}`)
    return
  }

  const header = existing.endsWith('\n') || existing === '' ? '' : '\n'
  const block =
    `${header}# Added by lazy-init (${new Date().toISOString()})\n` +
    toAdd.join('\n') +
    '\n'
  appendFileSync(excludePath, block)
  log(`  ✓ appended to ${excludePath}: ${toAdd.join(', ')}`)
}

function postInitPreCommitHook(targetRoot: string): void {
  let gitDir = join(targetRoot, '.git')
  const gitStat = statSync(gitDir)
  if (gitStat.isFile()) {
    const content = readFileSync(gitDir, 'utf8').trim()
    const m = content.match(/^gitdir:\s*(.+)$/)
    if (m) {
      gitDir = m[1]
      if (!gitDir.startsWith('/')) gitDir = resolve(targetRoot, gitDir)
    }
  }

  const hookPath = join(gitDir, 'hooks', 'pre-commit')
  ensureDir(dirname(hookPath))

  const delegateLine = '.lazy-harness/hooks/pre-commit-guard.sh "$@" || exit $?'
  const newHook = `#!/usr/bin/env bash
# pre-commit (lazy-harness commit-time validation delegate)
# Auto-installed by lazy-init. Add project-specific checks before this delegate.

${delegateLine}
`

  if (existsSync(hookPath)) {
    const existing = readFileSync(hookPath, 'utf8')
    if (existing.includes('pre-commit-guard.sh')) {
      log(`  ✓ pre-commit hook already delegates to lazy-harness`)
      return
    }
    // Backup existing
    const bakPath = `${hookPath}.bak.${Date.now()}`
    if (DRY) {
      logAction('backup', `${hookPath} → ${bakPath}`)
      logAction('append-delegate', hookPath)
    } else {
      renameSync(hookPath, bakPath)
      log(`  ✓ backed up existing pre-commit → ${bakPath}`)
      writeFile(hookPath, newHook, 0o755)
      log(`  ✓ installed pre-commit hook (delegate to lazy-harness)`)
    }
    return
  }

  writeFile(hookPath, newHook, 0o755)
  log(`  ✓ installed pre-commit hook`)
}

function postInitVersionMarker(sourceRoot: string, targetRoot: string, markerPath: string): void {
  if (resolve(sourceRoot) === resolve(targetRoot)) {
    log(`  ⊘ skipped: version marker (${markerPath}) for self-target source repo`)
    return
  }

  // Get source commit sha
  let sha = 'unknown'
  try {
    sha = execSync('git rev-parse HEAD', { cwd: sourceRoot, encoding: 'utf8' }).trim()
  } catch {
    /* ignore */
  }

  const content = JSON.stringify(
    {
      syncedFromCommit: sha,
      syncedAt: new Date().toISOString(),
      sourceRoot,
      manifestVersion: '1.0'
    },
    null,
    2
  ) + '\n'

  const path = join(targetRoot, '.lazy-harness', markerPath)
  writeFile(path, content)
  log(`  ✓ version marker: ${markerPath} → ${sha.slice(0, 12)}`)
}

// ─────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  DRY = args.dryRun
  QUIET = args.quiet

  preflight(args)

  const sourceRoot = args.from ? resolve(args.from) : detectFrameworkSource()
  const targetRoot = resolve(args.target)

  log(`lazy-init`)
  log(`  source: ${sourceRoot}`)
  log(`  target: ${targetRoot}`)
  if (DRY) log(`  mode:   DRY-RUN (no changes)`)

  const manifest = loadManifest(sourceRoot)

  // Category A
  const a = copyCategoryA(sourceRoot, targetRoot, manifest.categories.A.items)

  const selfTargetSource = resolve(sourceRoot) === resolve(targetRoot)

  // Category B
  const b = selfTargetSource
    ? (log('\n[Category B] Host institutional memory (빈 골격)'), log('  ⊘ skipped: self-target source repo'), { created: 0 })
    : createCategoryB(targetRoot, manifest.categories.B.items)

  // Post-init actions
  log('\n[Post-init] Side effects')
  for (const action of manifest.postInit.actions) {
    switch (action.kind) {
      case 'git-info-exclude':
        if (action.lines) postInitGitInfoExclude(targetRoot, action.lines)
        break
      case 'pre-commit-hook':
        if (!args.skipHooks) postInitPreCommitHook(targetRoot)
        else log(`  ⊘ skipped: pre-commit-hook (--skip-hooks)`)
        break
      case 'version-marker':
        if (action.path) postInitVersionMarker(sourceRoot, targetRoot, action.path)
        break
      default:
        log(`  ⚠ unknown action kind: ${action.kind}`)
    }
  }

  // Summary
  log('\n[Summary]')
  log(`  Category A: ${a.copied} files copied (framework 본체)`)
  log(`  Category B: ${b.created} containers seeded (institutional memory)`)
  log(`  Post-init:  ${manifest.postInit.actions.length} actions ${DRY ? '(dry)' : 'executed'}`)
  log('')
  if (DRY) {
    log('Dry run complete. Re-run without --dry-run to apply.')
    log(`Activation preview: ${join(targetRoot, '.lazy-harness', 'bin', 'lazy')} agent activate --target ${targetRoot} --dry-run`)
  } else {
    log(`✓ lazy-harness installed at ${join(targetRoot, '.lazy-harness')}`)
    log(`  Next: cd ${targetRoot} && .lazy-harness/bin/lazy agent activate --target ${targetRoot}`)
    log(`  Then: cd ${targetRoot} && python3 .lazy-harness/scripts/self-test.py`)
  }
}

main()
