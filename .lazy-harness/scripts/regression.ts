#!/usr/bin/env bun
/**
 * regression.ts — canonical writer + linter for the Fix-commit regression registry.
 *
 * The registry (`.lazy-harness/regression/registry.jsonl`) is host-owned runtime
 * data: one JSON object per line recording a Fix commit's protected regression.
 * `check-fix-regression.sh` reads it (JSON-parse, whitespace/encoding agnostic) to
 * decide whether a Fix commit still needs a promoted regression entry.
 *
 * Subcommands:
 *   add  --sha <40-hex> --description <text> --test <path> [--test <path>...] --repro <text>
 *        Validated, canonical append. Rejects placeholder garbage (`<...>`, `pending`),
 *        enforces a 40-hex sha, dedups by sha. This is the only sanctioned write path —
 *        agents must not hand-append raw JSON.
 *   lint [--format=json|md] [--fail-on-issues]
 *        Reports entries that fail validation (invalid JSON, bad sha, placeholder
 *        fields, missing/empty required fields). Supports migration + the commit gate.
 *
 * Read-only except `add`, which only appends a validated line.
 */
import { existsSync, readFileSync, appendFileSync, mkdirSync } from 'node:fs'
import path from 'node:path'

const REGISTRY_REL = '.lazy-harness/regression/registry.jsonl'
const SHA_RE = /^[0-9a-f]{40}$/
const PLACEHOLDER_RE = /<[^<>]+>/
const PENDING_RE = /^pending(:|$)/i

type Format = 'json' | 'md'

interface RegistryEntry {
  sha: string
  description: string
  protectedBy: string[]
  reproSteps: string
}

interface LintIssue {
  line: number
  sha: string
  code: string
  detail: string
}

function usage(code = 2): never {
  process.stderr.write(
    [
      'usage:',
      '  lazy regression add --sha <40-hex> --description <text> --test <path> [--test <path>...] --repro <text>',
      '  lazy regression lint [--format=json|md] [--fail-on-issues]',
    ].join('\n') + '\n',
  )
  process.exit(code)
}

function readEntries(file: string): { line: number; raw: string; parsed: RegistryEntry | null }[] {
  if (!existsSync(file)) return []
  const out: { line: number; raw: string; parsed: RegistryEntry | null }[] = []
  const lines = readFileSync(file, 'utf8').split('\n')
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i].trim()
    if (!raw) continue
    let parsed: RegistryEntry | null = null
    try {
      const obj = JSON.parse(raw) as Record<string, unknown>
      parsed = {
        sha: typeof obj.sha === 'string' ? obj.sha : '',
        description: typeof obj.description === 'string' ? obj.description : '',
        protectedBy: Array.isArray(obj.protectedBy) ? obj.protectedBy.filter((x): x is string => typeof x === 'string') : [],
        reproSteps: typeof obj.reproSteps === 'string' ? obj.reproSteps : '',
      }
    } catch {
      parsed = null
    }
    out.push({ line: i + 1, raw, parsed })
  }
  return out
}

function validateField(name: string, value: string): string | null {
  if (!value.trim()) return `${name} is empty`
  if (PLACEHOLDER_RE.test(value)) return `${name} contains a literal placeholder (\`<...>\`)`
  return null
}

function cmdAdd(root: string, argv: string[]): never {
  let sha = ''
  let description = ''
  let repro = ''
  const tests: string[] = []
  let verifyPaths = true
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '--sha') sha = argv[++i] ?? ''
    else if (a === '--description' || a === '--desc') description = argv[++i] ?? ''
    else if (a === '--test' || a === '--protected-by') tests.push(argv[++i] ?? '')
    else if (a === '--repro' || a === '--repro-steps') repro = argv[++i] ?? ''
    else if (a === '--no-verify-paths') verifyPaths = false
    else if (a === '--root') i++
    else usage()
  }

  const errors: string[] = []
  if (!SHA_RE.test(sha)) errors.push(`--sha must be a 40-char lowercase hex git sha (got ${JSON.stringify(sha)})`)
  const descErr = validateField('--description', description)
  if (descErr) errors.push(descErr)
  const reproErr = validateField('--repro', repro)
  if (reproErr) errors.push(reproErr)
  if (tests.length === 0) errors.push('at least one --test (protectedBy) path is required')
  for (const t of tests) {
    if (!t.trim()) errors.push('--test path is empty')
    else if (PLACEHOLDER_RE.test(t)) errors.push(`--test contains a literal placeholder: ${JSON.stringify(t)}`)
    else if (PENDING_RE.test(t)) errors.push(`--test is a pending stub, not a real path: ${JSON.stringify(t)}`)
  }
  if (errors.length) {
    process.stderr.write('lazy regression add rejected:\n' + errors.map((e) => `  - ${e}`).join('\n') + '\n')
    process.exit(2)
  }

  const file = path.join(root, REGISTRY_REL)
  for (const { parsed } of readEntries(file)) {
    if (parsed && parsed.sha === sha) {
      process.stdout.write(`regression entry for ${sha.slice(0, 8)} already registered; nothing to do.\n`)
      process.exit(0)
    }
  }

  if (verifyPaths) {
    const missing = tests.filter((t) => !existsSync(path.join(root, t)) && !existsSync(t))
    if (missing.length) {
      process.stderr.write('warning: protectedBy paths not found (recorded anyway): ' + missing.join(', ') + '\n')
    }
  }

  const entry: RegistryEntry = { sha, description: description.trim(), protectedBy: tests, reproSteps: repro.trim() }
  const dir = path.dirname(file)
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  appendFileSync(file, JSON.stringify(entry) + '\n', 'utf8')
  process.stdout.write(`registered regression entry for ${sha.slice(0, 8)} → ${REGISTRY_REL}\n`)
  process.exit(0)
}

function lintEntries(root: string): { issues: LintIssue[]; inspected: number } {
  const file = path.join(root, REGISTRY_REL)
  const issues: LintIssue[] = []
  const entries = readEntries(file)
  for (const { line, raw, parsed } of entries) {
    const head = raw.slice(0, 12)
    if (!parsed) {
      issues.push({ line, sha: head, code: 'invalid-json', detail: 'line is not valid JSON' })
      continue
    }
    const sha = parsed.sha
    if (!SHA_RE.test(sha)) issues.push({ line, sha: sha || head, code: 'bad-sha', detail: `sha ${JSON.stringify(sha)} is not a 40-hex git sha` })
    const descErr = validateField('description', parsed.description)
    if (descErr) issues.push({ line, sha, code: 'bad-description', detail: descErr })
    const reproErr = validateField('reproSteps', parsed.reproSteps)
    if (reproErr) issues.push({ line, sha, code: 'bad-repro', detail: reproErr })
    if (parsed.protectedBy.length === 0) {
      issues.push({ line, sha, code: 'missing-protected-by', detail: 'protectedBy is empty' })
    } else {
      for (const t of parsed.protectedBy) {
        if (PLACEHOLDER_RE.test(t)) issues.push({ line, sha, code: 'placeholder-protected-by', detail: `protectedBy has a literal placeholder: ${JSON.stringify(t)}` })
        else if (PENDING_RE.test(t)) issues.push({ line, sha, code: 'pending-protected-by', detail: `protectedBy is a pending stub: ${JSON.stringify(t)}` })
      }
    }
  }
  return { issues, inspected: entries.length }
}

function cmdLint(root: string, argv: string[]): never {
  let format: Format = 'json'
  let failOnIssues = false
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a.startsWith('--format=')) format = a.slice('--format='.length) === 'md' ? 'md' : 'json'
    else if (a === '--fail-on-issues') failOnIssues = true
    else if (a === '--root') i++
    else usage()
  }
  const { issues, inspected } = lintEntries(root)
  if (format === 'md') {
    const lines = ['# Regression registry lint', '', `- inspected entries: ${inspected}`, `- issues: ${issues.length}`]
    if (issues.length) {
      lines.push('', '## Issues')
      for (const it of issues) lines.push(`- [${it.code}] line ${it.line} (${it.sha}) — ${it.detail}`)
    } else {
      lines.push('', 'All registry entries pass validation.')
    }
    process.stdout.write(lines.join('\n') + '\n')
  } else {
    process.stdout.write(JSON.stringify({ schemaVersion: 'regression-lint/v1', mode: 'regression-lint', inspected, issueCount: issues.length, issues }, null, 2) + '\n')
  }
  process.exit(failOnIssues && issues.length > 0 ? 2 : 0)
}

function main(): void {
  const argv = process.argv.slice(2)
  const sub = argv[0]
  const rest = argv.slice(1)
  let root = process.cwd()
  const rootIdx = rest.indexOf('--root')
  if (rootIdx >= 0 && rest[rootIdx + 1]) root = path.resolve(rest[rootIdx + 1])
  if (sub === 'add') cmdAdd(root, rest)
  if (sub === 'lint') cmdLint(root, rest)
  usage()
}

main()
