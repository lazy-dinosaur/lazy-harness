import { existsSync, mkdirSync, readFileSync, writeFileSync, chmodSync, symlinkSync, lstatSync } from 'node:fs'
import { dirname, join } from 'node:path'

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
6. Inspect existing host records and code structure.
7. Check whether Document Resource Ingestion outputs exist and should be used; if outside docs need assimilation, use the separate ingestion flow.
8. Ask 3-5 option gates for decisions that cannot be inferred.
9. Never invent architecture defaults; generated skeletons must remain status=needs-interview until confirmed.
10. Run lazy-harness validation.

Current interview CLI writes only .lazy-harness/project/profile-interview.xml. A later fill step may apply confirmed answers into profile records.`
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

function writeManaged(options: JcodeWiringOptions, path: string, content: string, mode = 0o644): void {
  const nextContent = managedContent(content)
  if (existsSync(path)) {
    const existing = readFileSync(path, 'utf8')
    if (!existing.includes(GENERATED_MARKER)) {
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

function ensureLazyHarnessInstruction(options: JcodeWiringOptions): void {
  const path = join(options.targetRoot, '.jcode', 'harness', '05-lazy-harness.md')
  if (existsSync(path)) {
    log(options, `  ✓ keep existing ${path}`)
    return
  }
  if (options.dryRun) {
    log(options, `  [dry] symlink ${path} -> ../../.lazy-harness/AGENTS.md`)
    return
  }
  mkdirSync(dirname(path), { recursive: true })
  try {
    symlinkSync('../../.lazy-harness/AGENTS.md', path)
    log(options, `  ✓ symlinked ${path}`)
  } catch {
    const source = join(options.targetRoot, '.lazy-harness', 'AGENTS.md')
    const content = existsSync(source)
      ? readFileSync(source, 'utf8')
      : '# Lazy-Harness instructions\n\nMissing .lazy-harness/AGENTS.md. Re-run lazy update.\n'
    writeFileSync(path, content)
    log(options, `  ✓ copied lazy-harness instructions to ${path}`)
  }
}

function projectAgents(): string {
  return `# Private Jcode Harness\n\nThis directory is project-local/private Jcode wiring generated by lazy-harness.\n\n## Intent\n\n- Load .lazy-harness/AGENTS.md every session through .jcode/harness/05-lazy-harness.md.\n- Keep .jcode/ local/private by default. It is added to .git/info/exclude by lazy-init.\n- Preserve team/project AGENTS.md unless .jcode/config.toml explicitly changes ignore_project_agents.\n\n## Working style\n\n- Read lazy-harness records before host-specific implementation.\n- Run focused validation after code changes.\n- Avoid destructive actions unless explicitly requested.\n`
}

function routingPolicy(): string {
  return `# Jcode Agent Routing Policy\n\nUse subagents only when they reduce risk or speed up real progress.\n\n- Planning/architecture: planner, metis, reviewer.\n- Concrete implementation: coder, hephaestus, executor.\n- Unknown codebase area: searcher, librarian, atlas, explore.\n- Difficult debugging: sisyphus, oracle.\n- Visual/UI inspection: visual, multimodal-looker.\n`
}

function projectRules(): string {
  return `# Project-local Jcode Notes\n\nThis file is intentionally local/private Jcode wiring. It is pointer-only by default.\n\nDo not store host/team rule bodies here. When project rules, workflow policies, ownership boundaries, or custom behavior are discovered, record the durable content in .lazy-harness records first:\n\n- .lazy-harness/ssot/rule-sources.md for rule placement\n- .lazy-harness/ssot/project-identity.md or a dedicated SSOT for ownership/source-of-truth\n- .lazy-harness/{domain,spec,behavior,tests,decisions,ssot,planning}/** for layer facts and plans\n\nUse this file only for local/private Jcode execution preferences or short pointers to canonical .lazy-harness records. If adding a true local-only note, include Rule placement with Scope: jcode-local.\n\n## Lazy-harness wiring\n\n- .jcode/harness/05-lazy-harness.md points at .lazy-harness/AGENTS.md.\n- .jcode/config.toml enables Jcode private hooks and lazy-harness lifecycle hooks.\n- .jcode/ is local/private and should stay untracked.\n`
}

function archivePath(root: string, basename: string): string {
  const archiveDir = join(root, '.jcode', 'archive')
  let candidate = join(archiveDir, basename)
  if (!existsSync(candidate)) return candidate
  const suffix = new Date().toISOString().replace(/[:.]/g, '-')
  candidate = join(archiveDir, basename.replace(/\.md$/, `.${suffix}.md`))
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
  return `# Project-local Jcode harness config generated by lazy-harness.\n# Local-only: .jcode/ is excluded via .git/info/exclude.\n\n[prompt]\nignore_project_agents = false\nignore_global_agents = false\nload_jcode_agents = true\nload_harness_dir = true\n# Optional M45+ private instruction globs, relative to .jcode/.\nprivate_instructions = [\"rules/*.md\", \"monorepo/*/AGENTS.md\"]\n\n[hooks]\nenabled = true\n\n[[hooks.commands]]\nevent = \"tool.execute.before\"\ntool = \"bash\"\ncommand = \".jcode/hooks/check-bash.sh\"\nblocking = true\ntimeout_ms = 3000\n\n# Edit/write/multiedit development-time record checks are intentionally not\n# registered as blocking Jcode hooks. Lazy-harness keeps development fast and\n# enforces framework consistency at git pre-commit/pre-push instead. Agents\n# should still follow .lazy-harness/AGENTS.md proactively; commit-time gates\n# catch missed record/validation work.\n\n[[hooks.commands]]\nevent = \"response.completed\"\ntool = \"*\"\ncommand = \".lazy-harness/hooks/lifecycle/on-response-completed.sh\"\nblocking = false\ntimeout_ms = 5000\n\n[[hooks.commands]]\nevent = \"tool.execute.after\"\ntool = \"*\"\ncommand = \".jcode/hooks/log-tool.sh\"\nblocking = false\ntimeout_ms = 3000\n`
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
  writeManaged(options, join(root, '.jcode', 'config.toml'), configToml())
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
      if (!stat.isSymbolicLink()) log(options, `  ℹ ${instructionPath} is a regular file fallback`)
    } catch {
      // ignore
    }
  }
}
