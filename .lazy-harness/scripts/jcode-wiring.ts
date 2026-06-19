import { existsSync, mkdirSync, readFileSync, writeFileSync, chmodSync, lstatSync, renameSync, unlinkSync } from 'node:fs'
import { basename, dirname, join, relative } from 'node:path'

interface JcodeWiringOptions {
  targetRoot: string
  dryRun?: boolean
  quiet?: boolean
}

const SKILLS = [
  {
    name: 'lazy-init',
    description: 'Bootstrap lazy-harness on a host project.',
    usage: '.lazy-harness/bin/lazy init --target <dir> [--dry-run|--force]'
  },
  {
    name: 'lazy-sync',
    description: 'Sync framework Category A from the recorded source checkout while preserving host memory.',
    usage: '.lazy-harness/bin/lazy sync [--dry-run|--force]'
  },
  {
    name: 'lazy-update',
    description: 'Fetch the latest lazy-harness source and sync this host.',
    usage: '.lazy-harness/bin/lazy update [--dry-run|--force|--ref <ref>]'
  },
  {
    name: 'lazy-doctor',
    description: 'Run lazy-harness health/audit checks.',
    usage: '.lazy-harness/bin/lazy doctor --profile=smoke'
  },
  {
    name: 'lazy-test',
    description: 'Run lazy-harness reproducible self-test for the host.',
    usage: '.lazy-harness/bin/lazy test'
  },
  {
    name: 'lazy-skill-create',
    description: 'Create a project-local custom Jcode skill wrapper.',
    usage: '.lazy-harness/bin/lazy skill create <name> [--description <text>] [--script <file>]'
  },
  {
    name: 'lazy-impl-map-migrate',
    description: 'Guided LLM-assisted implementation-map migration using read-only CLI audit evidence; never bulk rewrites records automatically.',
    usage: '.lazy-harness/bin/lazy impl-map --format=json && .lazy-harness/bin/lazy graph-hygiene --format=json',
    details: `## When to use

Use this skill when records need \`## Implementation map\` sections and verified \`knowledge/graph.jsonl\` facts. This skill is not a fully automatic migration command. It wraps read-only CLI audit evidence and makes the LLM perform reviewed, batch-scoped edits only after user confirmation.

## Required record sources

- .lazy-harness/spec/platform/implementation-map-migration.md
- .lazy-harness/spec/platform/implementation-map-standard.md
- .lazy-harness/ssot/implementation-map-storage.md
- .lazy-harness/decisions/0030-implementation-map-three-layer-storage.md
- .lazy-harness/spec/platform/graph-hygiene.md

## Flow

1. Run read-only audit: .lazy-harness/bin/lazy impl-map --format=json and .lazy-harness/bin/lazy graph-hygiene --format=json
2. Summarize candidates by layer/feature and present a 3-5 option gate.
3. Stop for user choice before editing records.
4. For the selected batch only, read record bodies, inspect source/tests, update concise Implementation map sections, and append graph facts only for verified relationships.
5. Use Status: needs-review when symbols or ownership cannot be verified quickly.
6. Do not rewrite graph.jsonl wholesale. Do not rewrite \`knowledge/graph.jsonl\` wholesale; append or supersede confirmed facts. Do not edit generated implementation-index as source of truth.
7. Run validation: lazy impl-map, lazy graph-hygiene, and lazy test --scope framework.
8. Record validation evidence and commit only the reviewed batch.
9. After each selected batch is completed and validated, rerun lazy impl-map and lazy graph-hygiene, then present the next 3-5 option gate automatically.
10. The post-batch loop is navigation only. Do not edit the next batch until the user chooses it.
11. Default remains manual option-gate mode.
12. Bounded autopilot mode is allowed only when the user explicitly opts in.
13. In bounded autopilot mode, automatically select the next Recommended batch only after successful validation and only until the max batch limit.
14. If no limit is specified, use a default max batch limit of 3 batches for the current run.
15. Stop on validation failure, needs-review, ignored/tracked file uncertainty, missing source/test evidence, ambiguous ownership/layer/symbol mapping, dirty unrelated worktree changes, graph wholesale cleanup pressure, no clear Recommended batch, or max batch limit reached.
16. When bounded autopilot stops, summarize completed batches, remaining needs-map, graph hygiene status, validation commands, and the exact stop reason, then present a fresh option gate.

OMP compatibility work is intentionally after this guided migration skill exists.`
  },
  {
    name: 'lazy-project-profile',
    description: 'Create or update the host Project Profile through an interview-first architecture flow.',
    usage: 'bun .lazy-harness/scripts/project-profile.ts --mode inspect --format=md',
    details: `## When to use

Use this skill when a host project lacks or needs to update its Project Profile: project goal, folder structure, architecture theory, system design patterns, design system, backend boundaries, test strategy, validation commands, and agent operating policy.

This is an interview-first framework skill. Do not silently invent architecture defaults. Inspect existing code and records first. If non-harness docs such as README.md or docs/** need assimilation, offer to run the separate Document Resource Ingestion flow before Project Profile decisions. Present structured options where decisions are missing or evidence conflicts, then write durable outputs under .lazy-harness/project/** plus relevant DDD/SDD/BDD/TDD/ADR/SSOT records.

## Required record sources

- .lazy-harness/spec/platform/project-profile.md
- .lazy-harness/plans/project-init-interview-spec.md
- .lazy-harness/decisions/0024-ai-first-framework-redesign.md

## Flow

1. Run inspect first: bun .lazy-harness/scripts/project-profile.ts --mode inspect --format=md
2. If skeletons are missing, preview them: bun .lazy-harness/scripts/project-profile.ts --mode plan --format=md
3. Apply only needs-interview skeletons after confirmation: bun .lazy-harness/scripts/project-profile.ts --mode apply --confirm --format=md
4. Generate the open interview queue: bun .lazy-harness/scripts/project-profile.ts --mode interview --dry-run --format=md
5. After user confirmation, persist only the open-question transcript: bun .lazy-harness/scripts/project-profile.ts --mode interview --confirm --format=md
6. Collect explicit confirmed answers in an answers JSON file, preview fill: bun .lazy-harness/scripts/project-profile.ts --mode fill --answers answers.json --dry-run --format=md
7. Only after confirmation, apply matching answers: bun .lazy-harness/scripts/project-profile.ts --mode fill --answers answers.json --confirm --format=md
8. Inspect existing host records and code structure.
9. Check whether Document Resource Ingestion outputs exist and should be used; if outside docs need assimilation, use the separate ingestion flow.
10. Ask 3-5 option gates for decisions that cannot be inferred.
11. Never invent architecture defaults; generated skeletons must remain status=needs-interview until confirmed.
12. Run lazy-harness validation.

Current interview CLI writes only .lazy-harness/project/profile-interview.xml. Fill applies only explicit answer targets and reports unmatched answers without writing them.`
  },
  {
    name: 'lazy-doc-ingest',
    description: 'Inspect non-harness project documents and prepare reviewable document-resource evidence.',
    usage: 'bun .lazy-harness/scripts/document-resource-ingestion.ts --mode inspect --format=md',
    details: `## When to use

Use this skill before Project Profile work when README.md, docs/**, architecture notes, onboarding docs, product briefs, release notes, or legacy planning docs may contain useful project knowledge.

This is a separate capability from /lazy-project-profile. It scans root-bound non-harness documents, scores freshness, authority, duplicate overlap, and contamination risk, and produces a reviewable report. It can also produce plan/apply previews for .lazy-harness/project/document-intake.xml and .lazy-harness/knowledge/candidates.jsonl. It must not auto-promote external document claims into DDD/SDD/BDD/TDD/ADR/SSOT records.

## Required record source

- .lazy-harness/spec/platform/document-resource-ingestion.md

## Flow

1. Run inspect first: bun .lazy-harness/scripts/document-resource-ingestion.ts --mode inspect --format=md
2. Review authoritative/candidate/historical/duplicate/conflicting/rejected suggestions.
3. If the user wants a write preview, run: bun .lazy-harness/scripts/document-resource-ingestion.ts --mode plan --format=md
4. For apply previews only, run: bun .lazy-harness/scripts/document-resource-ingestion.ts --mode apply --dry-run --format=md
5. Present an option gate before writing any ledger or candidate entries:
   - A. create candidate ledger only
   - B. run deeper plan
   - C. skip docs and proceed to Project Profile
   - D. custom
6. Only after user confirmation, run: bun .lazy-harness/scripts/document-resource-ingestion.ts --mode apply --confirm --format=md
7. Never auto-promote external facts without user confirmation.`
  }
]

const GENERATED_MARKER = 'Generated by lazy-harness. Local edits below this line make the file user-owned.'
const PROJECT_RULES_POINTER_ONLY_MARKER = 'pointer-only by default'
const REJECTED_LAYER2_BLOCK_START = '# BEGIN lazy-harness mandatory Layer 2 force-gates'
const REJECTED_LAYER2_BLOCK_END = '# END lazy-harness mandatory Layer 2 force-gates'
const MESSAGE_RECEIVED_HOOK_START = '# BEGIN lazy-harness message.received static-harness hook'
const MESSAGE_RECEIVED_HOOK_END = '# END lazy-harness message.received static-harness hook'
const LEGACY_DIRECT_MESSAGE_RECEIVED_HOOK_START = '# BEGIN lazy-harness message.received direct-search hook'
const LEGACY_DIRECT_MESSAGE_RECEIVED_HOOK_END = '# END lazy-harness message.received direct-search hook'
const LEGACY_MESSAGE_RECEIVED_HOOK_START = '# BEGIN lazy-harness message.received context hook'
const LEGACY_MESSAGE_RECEIVED_HOOK_END = '# END lazy-harness message.received context hook'
const READ_DEBT_HOOK_START = '# BEGIN lazy-harness read-debt action permit hook'
const READ_DEBT_HOOK_END = '# END lazy-harness read-debt action permit hook'

const LEGACY_GENERATED_CUES: Record<string, string[]> = {
  '.jcode/AGENTS.md': [
    "This directory is Lazydino's private project-local harness for Jcode.",
    'experimental-lazy-harness',
    'Lazy-Harness Framework (CRITICAL',
    '/harness-doctor',
    'C1~C16',
    'framework-contract.md',
    'harness-init',
    'harness-update'
  ],
  '.jcode/config.toml': [
    '# Project-local Jcode harness config.',
    'ignore_project_agents = true',
    'event = "session.stop"',
    'test-session-stop.sh',
    'test-response-completed.sh',
    'private_instructions = ["rules/*.md", "monorepo/*/AGENTS.md", "missing/*.md","AGENTS.md"]'
  ],
  '.jcode/harness/10-routing-policy.md': [
    'Use the configured Jcode agent profiles intentionally.',
    'Model/persona guidance',
    'Concrete implementation, backend edits, command execution, and validation loops'
  ],
  '.jcode/hooks/check-bash.sh': [
    'Refusing rm -rf /',
    'Refusing sudo rm -rf /',
    'Refusing filesystem creation on block device',
    'Refusing raw disk write',
    'Refusing dangerous shell command',
    'Hook event 검증',
    'tool.execute.before'
  ],
  '.jcode/hooks/log-tool.sh': [
    'lazy-dogfood',
    'event-trace.log',
    'tool-events.jsonl'
  ]
}

const LEGACY_SKILL_CUES = [
  'framework-contract.md',
  '/harness-init',
  '/harness-doctor',
  '/harness-update',
  'Do not edit generated framework files directly in the host; use lazy update/sync.'
]

function log(options: JcodeWiringOptions, message: string): void {
  if (!options.quiet) console.log(message)
}

function ensureDir(options: JcodeWiringOptions, dir: string): void {
  if (options.dryRun) {
    log(options, `  [dry] mkdir ${dir}`)
    return
  }
  mkdirSync(dir, { recursive: true })
}

function managedContent(content: string): string {
  const marker = `# ${GENERATED_MARKER}\n`
  if (content.startsWith('#!')) {
    const firstNewline = content.indexOf('\n')
    if (firstNewline >= 0) return `${content.slice(0, firstNewline + 1)}${marker}${content.slice(firstNewline + 1)}`
  }
  if (content.startsWith('---\n')) {
    const frontmatterEnd = content.indexOf('\n---\n', 4)
    if (frontmatterEnd >= 0) {
      const insertAt = frontmatterEnd + '\n---\n'.length
      return `${content.slice(0, insertAt)}${marker}${content.slice(insertAt)}`
    }
  }
  return `${marker}${content}`
}

function relFromTarget(options: JcodeWiringOptions, path: string): string {
  return relative(options.targetRoot, path).split('\\').join('/')
}

function looksLikeLegacyGeneratedDefault(options: JcodeWiringOptions, path: string, existing: string): boolean {
  const rel = relFromTarget(options, path)
  const cues = LEGACY_GENERATED_CUES[rel] ?? []
  if (cues.some((cue) => existing.includes(cue))) return true
  if (rel.startsWith('.jcode/skills/lazy-') && rel.endsWith('/SKILL.md')) {
    return LEGACY_SKILL_CUES.some((cue) => existing.includes(cue))
  }
  return false
}

function archiveExisting(options: JcodeWiringOptions, path: string, reason: string): string {
  const backup = archivePath(options.targetRoot, `${basename(path)}.${reason}`)
  if (options.dryRun) return backup
  mkdirSync(dirname(backup), { recursive: true })
  renameSync(path, backup)
  return backup
}

function writeManaged(options: JcodeWiringOptions, path: string, content: string, mode = 0o644): void {
  const nextContent = managedContent(content)
  if (existsSync(path)) {
    const existing = readFileSync(path, 'utf8')
    if (!existing.includes(GENERATED_MARKER)) {
      if (looksLikeLegacyGeneratedDefault(options, path, existing)) {
        const backup = archiveExisting(options, path, 'pre-generated-marker')
        if (options.dryRun) {
          log(options, `  [dry] archive stale generated ${path} -> ${backup}; write current template`)
          return
        }
        writeFileSync(path, nextContent, { mode })
        if (mode & 0o111) chmodSync(path, mode)
        log(options, `  ✓ repaired stale generated ${path}; archived previous content at ${backup}`)
        return
      }
      log(options, `  ✓ keep user-owned ${path}`)
      return
    }
    if (existing === nextContent) {
      log(options, `  ✓ unchanged ${path}`)
      return
    }
    if (options.dryRun) {
      log(options, `  [dry] update generated ${path}`)
      return
    }
    writeFileSync(path, nextContent, { mode })
    if (mode & 0o111) chmodSync(path, mode)
    log(options, `  ✓ updated generated ${path}`)
    return
  }
  if (options.dryRun) {
    log(options, `  [dry] write ${path}`)
    return
  }
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, nextContent, { mode })
  if (mode & 0o111) chmodSync(path, mode)
  log(options, `  ✓ wrote ${path}`)
}

function cleanupRejectedLayer2Block(options: JcodeWiringOptions, path: string): void {
  if (!existsSync(path)) return
  const existing = readFileSync(path, 'utf8')
  if (!existing.includes(REJECTED_LAYER2_BLOCK_START)) return
  const next = existing.replace(
    new RegExp(`${REJECTED_LAYER2_BLOCK_START}[\\s\\S]*?${REJECTED_LAYER2_BLOCK_END}\\n?`, 'm'),
    ''
  ).trimEnd() + '\n'
  if (next === existing) return
  if (options.dryRun) {
    log(options, `  [dry] remove rejected mandatory Layer 2 block from ${path}`)
    return
  }
  writeFileSync(path, next)
  log(options, `  ✓ removed rejected mandatory Layer 2 block from ${path}`)
}

function messageReceivedHookBlock(): string {
  return `${MESSAGE_RECEIVED_HOOK_START}
# Bounded pre-turn static harness inventory/search prompt and search-debt journal.
# This is not a semantic search backend, not a user-text classifier, not a tool
# allowlist, and not a broad edit gate; timeout/failure is fail-open.
[[hooks.commands]]
event = "message.received"
command = ".lazy-harness/hooks/lifecycle/on-message-received.sh"
blocking = true
timeout_ms = 800
${MESSAGE_RECEIVED_HOOK_END}
`
}

function hasMessageReceivedHook(existing: string): boolean {
  return /\[\[hooks\.commands\]\][\s\S]*?event\s*=\s*["']message\.received["'][\s\S]*?command\s*=\s*["']\.lazy-harness\/hooks\/lifecycle\/on-message-received\.sh["'][\s\S]*?blocking\s*=\s*true[\s\S]*?timeout_ms\s*=\s*800/m.test(existing)
}

function messageReceivedManagedRegex(): RegExp {
  return new RegExp(`(?:${MESSAGE_RECEIVED_HOOK_START}|${LEGACY_DIRECT_MESSAGE_RECEIVED_HOOK_START}|${LEGACY_MESSAGE_RECEIVED_HOOK_START})[\\s\\S]*?(?:${MESSAGE_RECEIVED_HOOK_END}|${LEGACY_DIRECT_MESSAGE_RECEIVED_HOOK_END}|${LEGACY_MESSAGE_RECEIVED_HOOK_END})\\n?`, 'm')
}

function ensureMessageReceivedHook(options: JcodeWiringOptions, path: string): void {
  if (!existsSync(path)) return
  const existing = readFileSync(path, 'utf8')
  const managedRe = messageReceivedManagedRegex()
  if (existing.includes(MESSAGE_RECEIVED_HOOK_START) || existing.includes(LEGACY_DIRECT_MESSAGE_RECEIVED_HOOK_START) || existing.includes(LEGACY_MESSAGE_RECEIVED_HOOK_START)) {
    const next = existing.replace(managedRe, messageReceivedHookBlock()).trimEnd() + '\n'
    if (next === existing) return
    if (options.dryRun) {
      log(options, `  [dry] refresh message.received static harness hook in ${path}`)
      return
    }
    writeFileSync(path, next)
    log(options, `  ✓ refreshed message.received static harness hook in ${path}`)
    return
  }
  if (hasMessageReceivedHook(existing)) return
  const stripped = existing.replace(managedRe, '').trimEnd()
  const next = `${stripped}\n\n${messageReceivedHookBlock()}`
  if (options.dryRun) {
    log(options, `  [dry] patch message.received static harness hook into ${path}`)
    return
  }
  writeFileSync(path, next)
  log(options, `  ✓ patched message.received static harness hook into ${path}`)
}

function readDebtPermitHookBlock(): string {
  return `${READ_DEBT_HOOK_START}
# Generic pre-action search/read evidence guard. It does not perform semantic
# search and it is not a concrete-tool policy adapter or allowlist. It only checks
# whether message.received produced direct-search/read-debt and whether
# the LLM/searcher already left root-bound harness-following search/read evidence
# before action.
[[hooks.commands]]
event = "tool.execute.before"
tool = "*"
command = ".lazy-harness/hooks/lifecycle/on-tool-execute-before.sh"
blocking = true
timeout_ms = 1200
${READ_DEBT_HOOK_END}
`
}

function hasReadDebtPermitHook(existing: string): boolean {
  return /\[\[hooks\.commands\]\][\s\S]*?event\s*=\s*["']tool\.execute\.before["'][\s\S]*?tool\s*=\s*["']\*["'][\s\S]*?command\s*=\s*["']\.lazy-harness\/hooks\/lifecycle\/on-tool-execute-before\.sh["'][\s\S]*?blocking\s*=\s*true/m.test(existing)
}

function ensureReadDebtPermitHook(options: JcodeWiringOptions, path: string): void {
  if (!existsSync(path)) return
  const existing = readFileSync(path, 'utf8')
  const block = readDebtPermitHookBlock()
  const managedRe = new RegExp(`${READ_DEBT_HOOK_START}[\\s\\S]*?${READ_DEBT_HOOK_END}\\n?`, 'm')
  if (existing.includes(READ_DEBT_HOOK_START)) {
    const next = existing.replace(managedRe, block).trimEnd() + '\n'
    if (next === existing) return
    if (options.dryRun) {
      log(options, `  [dry] refresh generic search/read-debt evidence guard in ${path}`)
      return
    }
    writeFileSync(path, next)
    log(options, `  ✓ refreshed generic search/read-debt evidence guard in ${path}`)
    return
  }
  if (hasReadDebtPermitHook(existing)) return
  const stripped = existing.replace(managedRe, '').trimEnd()
  const next = `${stripped}\n\n${block}`
  if (options.dryRun) {
    log(options, `  [dry] patch generic search/read-debt evidence guard into ${path}`)
    return
  }
  writeFileSync(path, next)
  log(options, `  ✓ patched generic search/read-debt evidence guard into ${path}`)
}


function ensureLazyHarnessInstruction(options: JcodeWiringOptions): void {
  const path = join(options.targetRoot, '.jcode', 'harness', '05-lazy-harness.md')
  const pointer = managedContent(lazyHarnessPointerInstruction())
  if (existsSync(path)) {
    try {
      const stat = lstatSync(path)
      if (stat.isSymbolicLink()) {
        if (options.dryRun) {
          log(options, `  [dry] replace ${path} symlink with pointer-only generated instruction`)
          return
        }
        unlinkSync(path)
        mkdirSync(dirname(path), { recursive: true })
        writeFileSync(path, pointer)
        log(options, `  ✓ replaced ${path} symlink with pointer-only generated instruction`)
        return
      }
      const existing = readFileSync(path, 'utf8')
      if (existing.includes(GENERATED_MARKER)) {
        writeManaged(options, path, lazyHarnessPointerInstruction())
        return
      }
      if (existing.includes('# Lazy-Harness AI 행동 양식') || existing.includes('Missing .lazy-harness/AGENTS.md. Re-run lazy update.')) {
        const backup = archiveExisting(options, path, 'pre-pointer-only')
        if (options.dryRun) {
          log(options, `  [dry] archive stale instruction copy ${path} -> ${backup}; write pointer-only generated instruction`)
          return
        }
        writeFileSync(path, pointer)
        log(options, `  ✓ repaired ${path} as pointer-only generated instruction; archived previous content at ${backup}`)
        return
      }
    } catch {
      // Fall through to user-owned preservation.
    }
    log(options, `  ✓ keep user-owned ${path}`)
    return
  }
  if (options.dryRun) {
    log(options, `  [dry] write pointer-only generated instruction ${path}`)
    return
  }
  mkdirSync(dirname(path), { recursive: true })
  writeFileSync(path, pointer)
  log(options, `  ✓ wrote pointer-only generated instruction ${path}`)
}

function lazyHarnessPointerInstruction(): string {
  return `# Lazy-Harness Pointer

This generated Jcode harness file is intentionally pointer-only.

Canonical rule body: \`.lazy-harness/AGENTS.md\` loaded via root \`AGENTS.md\`.

Do not duplicate the full lazy-harness grammar here. This file exists so project-local Jcode wiring can point at the canonical record without adding a second copy of the same prompt text.

If a session appears not to have loaded the root AGENTS instructions, read \`.lazy-harness/AGENTS.md\` before host-specific work.

Working reminders:

- Start from record-first/default-unknown behavior in \`.lazy-harness/AGENTS.md\`.
- Keep host/team rule bodies in \`.lazy-harness/**\`, not \`.jcode/**\`.
- Run focused validation after code changes.
- Avoid destructive actions unless explicitly requested.
`
}

function projectAgents(): string {
  return `# Private Jcode Harness\n\nThis directory is project-local/private Jcode wiring generated by lazy-harness.\n\n## Intent\n\n- Keep .lazy-harness/AGENTS.md as the canonical full rule body loaded through root AGENTS.md.\n- Keep .jcode/harness/05-lazy-harness.md pointer-only to avoid duplicate prompt grammar.\n- Keep .jcode/ local/private by default. It is added to .git/info/exclude by lazy-init.\n- Preserve team/project AGENTS.md unless .jcode/config.toml explicitly changes ignore_project_agents.\n\n## Working style\n\n- Read lazy-harness records before host-specific implementation.\n- Run focused validation after code changes.\n- Avoid destructive actions unless explicitly requested.\n`
}

function routingPolicy(): string {
  return `# Jcode Agent Routing Policy\n\nUse subagents only when they reduce risk or speed up real progress.\n\n- Planning/architecture: planner, metis, reviewer.\n- Concrete implementation: coder, hephaestus, executor.\n- Unknown codebase area: searcher, librarian, atlas, explore.\n- Difficult debugging: sisyphus, oracle.\n- Visual/UI inspection: visual, multimodal-looker.\n`
}

function projectRules(): string {
  return `# Project-local Jcode Notes\n\nThis file is intentionally local/private Jcode wiring. It is pointer-only by default.\n\nDo not store host/team rule bodies here. When project rules, workflow policies, ownership boundaries, or custom behavior are discovered, record the durable content in .lazy-harness records first:\n\n- .lazy-harness/ssot/rule-sources.md for rule placement\n- .lazy-harness/ssot/project-identity.md or a dedicated SSOT for ownership/source-of-truth\n- .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}/** for layer facts and plans\n\nUse this file only for local/private Jcode execution preferences or short pointers to canonical .lazy-harness records. If adding a true local-only note, include Rule placement with Scope: jcode-local.\n\n## Lazy-harness wiring\n\n- Root AGENTS.md points at .lazy-harness/AGENTS.md as the canonical full rule body.\n- .jcode/harness/05-lazy-harness.md is pointer-only to avoid duplicate prompt grammar.\n- .jcode/config.toml enables Jcode private hooks and lazy-harness lifecycle hooks.\n- .jcode/ is local/private and should stay untracked.\n`
}

function archivePath(root: string, basename: string): string {
  const archiveDir = join(root, '.jcode', 'archive')
  let candidate = join(archiveDir, basename)
  if (!existsSync(candidate)) return candidate
  const suffix = new Date().toISOString().replace(/[:.]/g, '-')
  const withSuffix = basename.match(/\.md$/) ? basename.replace(/\.md$/, `.${suffix}.md`) : `${basename}.${suffix}`
  candidate = join(archiveDir, withSuffix)
  let counter = 1
  while (existsSync(candidate)) {
    const numbered = withSuffix.match(/\.md$/) ? withSuffix.replace(/\.md$/, `.${counter}.md`) : `${withSuffix}.${counter}`
    candidate = join(archiveDir, numbered)
    counter += 1
  }
  return candidate
}

function migrateProjectRulesPointerOnly(options: JcodeWiringOptions, path: string): boolean {
  if (!existsSync(path)) return false
  const existing = readFileSync(path, 'utf8')
  if (existing.includes(GENERATED_MARKER)) return false
  if (existing.includes(PROJECT_RULES_POINTER_ONLY_MARKER)) return false

  const backup = archivePath(options.targetRoot, '20-project-rules.pre-pointer-only-migration.md')
  if (options.dryRun) {
    log(options, `  [dry] migrate user-owned ${path} to pointer-only and archive previous content at ${backup}`)
    return true
  }
  mkdirSync(dirname(backup), { recursive: true })
  writeFileSync(backup, existing)
  writeFileSync(path, managedContent(projectRules()))
  log(options, `  ✓ migrated ${path} to pointer-only; archived previous content at ${backup}`)
  return true
}

function configToml(): string {
  return `# Project-local Jcode harness config generated by lazy-harness.\n# Local-only: .jcode/ is excluded via .git/info/exclude.\n\n[prompt]\nignore_project_agents = false\nignore_global_agents = false\nload_jcode_agents = true\nload_harness_dir = true\n# Optional M45+ private instruction globs, relative to .jcode/.\nprivate_instructions = [\"rules/*.md\", \"monorepo/*/AGENTS.md\"]\n\n[hooks]\nenabled = true\n\n[[hooks.commands]]\nevent = \"tool.execute.before\"\ntool = \"bash\"\ncommand = \".jcode/hooks/check-bash.sh\"\nblocking = true\ntimeout_ms = 3000\n\n# Edit/write/multiedit broad development-time record checks are intentionally\n# not registered as blocking hooks. Lazy-harness keeps development fast and\n# enforces framework consistency at git pre-commit/pre-push commit-time gates.\n# Search/read debt is produced from message.received as a static harness\n# inventory/search prompt and checked by a generic evidence guard; the guard\n# does not perform semantic search and is not a concrete-tool policy adapter,\n# user-text classifier, or allowlist.\n\n[[hooks.commands]]\nevent = \"response.completed\"\ntool = \"*\"\ncommand = \".lazy-harness/hooks/lifecycle/on-response-completed.sh\"\nblocking = false\ntimeout_ms = 5000\n\n[[hooks.commands]]\nevent = \"message.received\"\ncommand = \".lazy-harness/hooks/lifecycle/on-message-received.sh\"\nblocking = true\ntimeout_ms = 800\n\n[[hooks.commands]]\nevent = \"tool.execute.after\"\ntool = \"*\"\ncommand = \".jcode/hooks/log-tool.sh\"\nblocking = false\ntimeout_ms = 3000\n`
}

function checkBashHook(): string {
  return `#!/usr/bin/env bash\nset -euo pipefail\n\npayload=$(cat || true)\n\npython3 - \"$payload\" <<'PY'\nimport json\nimport re\nimport sys\n\npayload = sys.argv[1] if len(sys.argv) > 1 else \"\"\ntry:\n    data = json.loads(payload) if payload.strip() else {}\nexcept Exception:\n    data = {\"raw\": payload}\n\nblob = json.dumps(data, ensure_ascii=False)\nblocked = [\n    (r\"\\brm\\s+-rf\\s+/(?:[\\s\\\\\\\"\\x27}\\]]|$)\", \"Refusing rm -rf /\"),\n    (r\"\\bsudo\\s+rm\\s+-rf\\s+/(?:[\\s\\\\\\\"\\x27}\\]]|$)\", \"Refusing sudo rm -rf /\"),\n    (r\"\\bdd\\s+.*\\bof=/dev/(sd|nvme|vd)\", \"Refusing raw disk overwrite\"),\n    (r\"\\bmkfs(?:\\.[a-z0-9]+)?\\s+/dev/\", \"Refusing filesystem creation on block device\"),\n]\n\nfor pattern, reason in blocked:\n    if re.search(pattern, blob, re.IGNORECASE | re.DOTALL):\n        print(json.dumps({\"action\": \"deny\", \"reason\": reason}))\n        sys.exit(0)\n\nprint(json.dumps({\"action\": \"allow\"}))\nPY\n`
}

function logToolHook(): string {
  return `#!/usr/bin/env bash\nset -euo pipefail\n\nmkdir -p .jcode/hooks\npayload=$(cat || true)\nprintf '%s %s\\n' \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" \"$payload\" >> .jcode/hooks/tool-events.jsonl\nexit 0\n`
}

function skillMarkdown(name: string, description: string, usage: string, details = ''): string {
  const detailsBlock = details ? `
${details}
` : ''
  return `---
name: ${name}
description: ${description}
allowed-tools: bash, read, grep
---

# ${name}

${description}

Run from the host project root:

\`\`\`bash
${usage}
\`\`\`
${detailsBlock}
This skill delegates to the installed .lazy-harness framework. Do not edit generated framework files directly in the host; use lazy update/sync.
`
}

export function installJcodeWiring(options: JcodeWiringOptions): void {
  log(options, '\n[Jcode] Project-local private wiring')
  const root = options.targetRoot
  ensureDir(options, join(root, '.jcode'))
  ensureDir(options, join(root, '.jcode', 'harness'))
  ensureDir(options, join(root, '.jcode', 'hooks'))
  ensureDir(options, join(root, '.jcode', 'skills'))
  ensureDir(options, join(root, '.jcode', 'rules'))
  ensureDir(options, join(root, '.jcode', 'monorepo'))

  writeManaged(options, join(root, '.jcode', 'AGENTS.md'), projectAgents())
  const configPath = join(root, '.jcode', 'config.toml')
  writeManaged(options, configPath, configToml())
  cleanupRejectedLayer2Block(options, configPath)
  ensureMessageReceivedHook(options, configPath)
  ensureReadDebtPermitHook(options, configPath)
  ensureLazyHarnessInstruction(options)
  writeManaged(options, join(root, '.jcode', 'harness', '10-routing-policy.md'), routingPolicy())
  const projectRulesPath = join(root, '.jcode', 'harness', '20-project-rules.md')
  if (!migrateProjectRulesPointerOnly(options, projectRulesPath)) {
    writeManaged(options, projectRulesPath, projectRules())
  }
  writeManaged(options, join(root, '.jcode', 'hooks', 'check-bash.sh'), checkBashHook(), 0o755)
  writeManaged(options, join(root, '.jcode', 'hooks', 'log-tool.sh'), logToolHook(), 0o755)

  for (const skill of SKILLS) {
    writeManaged(
      options,
      join(root, '.jcode', 'skills', skill.name, 'SKILL.md'),
      skillMarkdown(skill.name, skill.description, skill.usage, 'details' in skill ? skill.details : '')
    )
  }

  const instructionPath = join(root, '.jcode', 'harness', '05-lazy-harness.md')
  if (!options.dryRun && existsSync(instructionPath)) {
    try {
      const stat = lstatSync(instructionPath)
      if (!stat.isSymbolicLink()) log(options, `  ℹ ${instructionPath} is pointer-only regular file`)
    } catch {
      // ignore
    }
  }
}
