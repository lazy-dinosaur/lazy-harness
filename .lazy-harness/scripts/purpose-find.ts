#!/usr/bin/env bun
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join, relative, resolve } from 'node:path'

type Format = 'json' | 'md'
type Purpose = 'fact' | 'rulebook' | 'test' | 'capability' | 'source' | 'architecture' | 'full'

type Candidate = {
  path?: string
  id?: string
  title?: string
  kind?: string
  level?: string
  matchCount: number
  matched: string[]
  source?: string
}

type FindResult = {
  schemaVersion: '1.0'
  mode: 'purpose-scoped-find'
  purpose: Purpose
  query: string
  root: string
  evidence: {
    schemaVersion: '1.0'
    event: 'purpose-scoped-retrieval.evidence'
    purpose: Purpose
    searchEvidence: boolean
    readEvidence: false
    qualifiesSearchDebt: boolean
    caveat: string
  }
  searchSpaces: string[]
  commands: string[]
  candidates: {
    records: Candidate[]
    rules: Candidate[]
    capabilities: Candidate[]
    sourceFiles: Candidate[]
    testFiles: Candidate[]
    graphRows: Candidate[]
  }
  escalation: string[]
  notes: string[]
}

const PURPOSES = new Set(['fact', 'record', 'information', 'rulebook', 'rules', 'operating-rule', 'operating-rules', 'test', 'tests', 'validation', 'capability', 'capabilities', 'source', 'implementation', 'architecture', 'design', 'full'])
const RECORD_DIRS = ['.lazy-harness/domain', '.lazy-harness/spec', '.lazy-harness/behavior', '.lazy-harness/tests', '.lazy-harness/decisions', '.lazy-harness/ssot', '.lazy-harness/planning', '.lazy-harness/plans', '.lazy-harness/project']
const FACT_RECORD_DIRS = ['.lazy-harness/domain', '.lazy-harness/spec', '.lazy-harness/behavior', '.lazy-harness/tests', '.lazy-harness/decisions', '.lazy-harness/ssot', '.lazy-harness/project']
const SOURCE_DIRS = ['src', 'tests', 'packages', '.lazy-harness/scripts', '.lazy-harness/hooks', '.lazy-harness/bin']
const TEXT_EXTENSIONS = new Set(['.md', '.xml', '.json', '.jsonl', '.ts', '.tsx', '.js', '.jsx', '.py', '.sh', '.yaml', '.yml', '.toml', '.txt'])

function usage(exitCode = 0): never {
  const out = exitCode === 0 ? console.log : console.error
  out(`Usage: lazy find --purpose <purpose> <query> [--format=json|md] [--limit=N]

Purposes:
  fact|record        Project facts/contracts/implementation truth. Uses records/graph/source cues.
  rulebook|rules     Project operating rules. Uses .lazy-harness/rules and capabilities first.
  test|validation    Tests/validation. Uses TDD/test/source-test/capability surfaces first.
  capability         Registered affordances. Uses capabilities.json first.
  source             Implementation/source location. Uses source/test files first.
  architecture       Broad design/change retrieval with layer completeness cues.
  full               Explicit broad retrieval across all supported spaces.

The CLI is cue-only. The LLM/user chooses --purpose explicitly; this tool must not infer purpose from raw prompts.
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

function parseArgs(argv: string[]): { root: string; purpose: Purpose; query: string; format: Format; limit: number } {
  let purpose = ''
  let format: Format = 'md'
  let limit = 8
  let target = process.env.LAZY_HOST_ROOT || process.cwd()
  const positional: string[] = []
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a === '-h' || a === '--help') usage(0)
    if (a === '--purpose') purpose = value(argv, i++, a)
    else if (a.startsWith('--purpose=')) purpose = a.slice('--purpose='.length)
    else if (a === '--format') format = value(argv, i++, a) as Format
    else if (a.startsWith('--format=')) format = a.slice('--format='.length) as Format
    else if (a === '--limit') limit = Number(value(argv, i++, a))
    else if (a.startsWith('--limit=')) limit = Number(a.slice('--limit='.length))
    else if (a === '--target') target = value(argv, i++, a)
    else if (a.startsWith('--target=')) target = a.slice('--target='.length)
    else if (a.startsWith('--')) {
      console.error(`Unknown option: ${a}`)
      usage(2)
    } else positional.push(a)
  }
  if (!purpose) {
    console.error('lazy find requires --purpose')
    usage(2)
  }
  const normalized = normalizePurpose(purpose)
  if (!normalized) {
    console.error(`Unsupported purpose: ${purpose}`)
    usage(2)
  }
  if (format !== 'json' && format !== 'md') {
    console.error(`Unsupported format: ${format}`)
    usage(2)
  }
  if (!Number.isFinite(limit) || limit < 1) limit = 8
  const query = positional.join(' ').trim()
  if (!query) {
    console.error('lazy find requires a query')
    usage(2)
  }
  return { root: resolve(target), purpose: normalized, query, format, limit }
}

function normalizePurpose(purpose: string): Purpose | null {
  const p = purpose.trim().toLowerCase()
  if (!PURPOSES.has(p)) return null
  if (p === 'record' || p === 'information') return 'fact'
  if (p === 'rules' || p === 'operating-rule' || p === 'operating-rules') return 'rulebook'
  if (p === 'tests' || p === 'validation') return 'test'
  if (p === 'capabilities') return 'capability'
  if (p === 'implementation') return 'source'
  if (p === 'design') return 'architecture'
  return p as Purpose
}

function rel(root: string, path: string): string {
  return relative(root, path).split('\\').join('/')
}

function ext(path: string): string {
  const m = path.match(/(\.[^.\/]+)$/)
  return m ? m[1] : ''
}

function walk(root: string, dir: string, opts: { max?: number; onlyText?: boolean } = {}): string[] {
  const start = join(root, dir)
  const out: string[] = []
  const max = opts.max || 3000
  const visit = (path: string) => {
    if (out.length >= max || !existsSync(path)) return
    for (const item of readdirSync(path, { withFileTypes: true })) {
      if (out.length >= max) return
      if (item.name === '.git' || item.name === 'node_modules' || item.name === '.playwright-mcp') continue
      const p = join(path, item.name)
      if (item.isDirectory()) visit(p)
      else if (item.isFile()) {
        if (!opts.onlyText || TEXT_EXTENSIONS.has(ext(item.name))) out.push(p)
      }
    }
  }
  visit(start)
  return out
}

function tokens(query: string): string[] {
  return query.toLowerCase().split(/\s+/).map((s) => s.trim()).filter(Boolean)
}

function scoreText(query: string, text: string): { score: number; matched: string[] } {
  const lower = text.toLowerCase()
  const matched = tokens(query).filter((t) => lower.includes(t))
  return { score: matched.length, matched }
}

function titleOf(text: string, fallback: string): string {
  const m = text.match(/^#\s+(.+)$/m)
  return m ? m[1].trim() : fallback
}

function safeRead(path: string): string {
  try {
    return readFileSync(path, 'utf8')
  } catch {
    return ''
  }
}

function fileCandidates(root: string, dirs: string[], query: string, limit: number, kind: string, testOnly = false): Candidate[] {
  const out: Candidate[] = []
  for (const dir of dirs) {
    for (const file of walk(root, dir, { onlyText: true })) {
      const rp = rel(root, file)
      if (testOnly) {
        const base = rp.toLowerCase()
        if (!base.includes('/tests/') && !base.includes('.test.') && !base.includes('.spec.') && !base.startsWith('.lazy-harness/tests/')) continue
      }
      const text = safeRead(file)
      const scored = scoreText(query, `${rp}\n${text.slice(0, 16000)}`)
      if (scored.score > 0) out.push({ path: rp, title: titleOf(text, rp), kind, matchCount: scored.score, matched: scored.matched })
    }
  }
  return out.sort((a, b) => b.matchCount - a.matchCount || String(a.path).localeCompare(String(b.path))).slice(0, limit)
}

function capabilityCandidates(root: string, query: string, limit: number): Candidate[] {
  const path = join(root, '.lazy-harness/ssot/capabilities.json')
  if (!existsSync(path)) return []
  const data = JSON.parse(safeRead(path) || '{"capabilities":[]}')
  const caps = Array.isArray(data.capabilities) ? data.capabilities : []
  return caps.map((cap: Record<string, unknown>) => {
    const text = JSON.stringify(cap)
    const scored = scoreText(query, text)
    return { id: String(cap.id || ''), path: '.lazy-harness/ssot/capabilities.json', title: String(cap.description || cap.id || ''), kind: String(cap.kind || 'capability'), level: String(cap.level || ''), matchCount: scored.score, matched: scored.matched, source: String(cap.sourceRecord || '') }
  }).filter((c: Candidate) => c.matchCount > 0).sort((a: Candidate, b: Candidate) => b.matchCount - a.matchCount || String(a.id).localeCompare(String(b.id))).slice(0, limit)
}

function graphCandidates(root: string, query: string, limit: number): Candidate[] {
  const path = join(root, '.lazy-harness/knowledge/graph.jsonl')
  if (!existsSync(path)) return []
  const out: Candidate[] = []
  for (const line of safeRead(path).split('\n')) {
    if (!line.trim()) continue
    const scored = scoreText(query, line)
    if (scored.score === 0) continue
    try {
      const row = JSON.parse(line)
      out.push({ id: String(row.id || ''), path: String(row.path || '.lazy-harness/knowledge/graph.jsonl'), title: String(row.target || row.id || ''), kind: String(row.kind || row.relation || 'graph'), matchCount: scored.score, matched: scored.matched, source: String(row.source || '') })
    } catch {
      out.push({ path: '.lazy-harness/knowledge/graph.jsonl', title: line.slice(0, 80), kind: 'graph', matchCount: scored.score, matched: scored.matched })
    }
  }
  return out.sort((a, b) => b.matchCount - a.matchCount || String(a.id || a.path).localeCompare(String(b.id || b.path))).slice(0, limit)
}

function commandsFor(purpose: Purpose, query: string): string[] {
  const q = shellQuote(query)
  switch (purpose) {
    case 'rulebook':
      return [
        `.lazy-harness/bin/lazy rules resolve --intent ${q} --format=md`,
        `.lazy-harness/bin/lazy rules resolve --action ${q} --format=md`,
        `.lazy-harness/bin/lazy capability resolve --intent ${q} --format=md`,
        `.lazy-harness/bin/lazy capability resolve --action ${q} --format=md`,
      ]
    case 'test':
      return [
        `grep -rli ${q} .lazy-harness/tests tests src packages`,
        `.lazy-harness/bin/lazy capability resolve --intent validating_changes --format=md`,
        `.lazy-harness/bin/lazy affected --files <changed-files>`,
      ]
    case 'capability':
      return [`.lazy-harness/bin/lazy capability resolve --intent ${q} --format=md`, `.lazy-harness/bin/lazy capability resolve --action ${q} --format=md`]
    case 'source':
      return [`grep -rli ${q} src tests packages .lazy-harness/scripts`, `.lazy-harness/bin/lazy map ${q} --format=md --limit=8`]
    case 'architecture':
      return [`.lazy-harness/bin/lazy map --overview --format=md --limit=20`, `.lazy-harness/bin/lazy map ${q} --format=md --limit=8`, `grep -rli ${q} .lazy-harness tests src packages`]
    case 'full':
      return [`.lazy-harness/bin/lazy map --overview --format=md --limit=20`, `.lazy-harness/bin/lazy map ${q} --format=md --limit=8`, `.lazy-harness/bin/lazy rules resolve --intent ${q} --format=md`, `.lazy-harness/bin/lazy capability resolve --intent ${q} --format=md`, `grep -rli ${q} .lazy-harness tests src packages`]
    case 'fact':
    default:
      return [`.lazy-harness/bin/lazy map ${q} --format=md --limit=8`, `grep -rli ${q} .lazy-harness tests src packages`]
  }
}

function shellQuote(s: string): string {
  return `'${s.replace(/'/g, `'\\''`)}'`
}


function qualifiesSearchDebt(purpose: Purpose): boolean {
  return !['architecture', 'full'].includes(purpose)
}

function spacesFor(purpose: Purpose): string[] {
  switch (purpose) {
    case 'rulebook': return ['rules', 'capabilities']
    case 'test': return ['tdd-records', 'source-tests', 'validation-capabilities']
    case 'capability': return ['capabilities']
    case 'source': return ['source', 'source-tests', 'graph']
    case 'architecture': return ['overview', 'records', 'rules', 'capabilities', 'source', 'tests', 'graph']
    case 'full': return ['overview', 'records', 'rules', 'capabilities', 'source', 'tests', 'graph']
    case 'fact': return ['records', 'graph', 'implementation-map', 'source']
  }
}

function escalationFor(purpose: Purpose): string[] {
  switch (purpose) {
    case 'rulebook': return ['Escalate to fact records only if the operating rule points to missing contract/source support or the user asks what is true.']
    case 'test': return ['Escalate to SDD/BDD/SSOT records when tests imply contract, behavior, schema, config, or API impact.']
    case 'capability': return ['Read linked rulebook/source records after a capability match before relying on it.']
    case 'source': return ['Escalate to records when implementation facts need contract, decision, or behavior context.']
    case 'architecture': return ['Use layer completeness gate and read actual records/source/tests before mutating.']
    case 'full': return ['Full retrieval is broad; still treat candidates as cue-only until files are read.']
    case 'fact': return ['If records are empty or conflicting, inspect source/tests/config and use an option gate.']
  }
}

function buildResult(root: string, purpose: Purpose, query: string, limit: number): FindResult {
  const result: FindResult = {
    schemaVersion: '1.0',
    mode: 'purpose-scoped-find',
    purpose,
    query,
    root,
    evidence: {
      schemaVersion: '1.0',
      event: 'purpose-scoped-retrieval.evidence',
      purpose,
      searchEvidence: true,
      readEvidence: false,
      qualifiesSearchDebt: qualifiesSearchDebt(purpose),
      caveat: 'cue-only search evidence; not proof that candidate files were read',
    },
    searchSpaces: spacesFor(purpose),
    commands: commandsFor(purpose, query),
    candidates: { records: [], rules: [], capabilities: [], sourceFiles: [], testFiles: [], graphRows: [] },
    escalation: escalationFor(purpose),
    notes: ['cue-only; read actual files before relying on a match', 'purpose is explicit input; this CLI does not classify raw user prompts'],
  }

  if (purpose === 'rulebook') {
    result.candidates.rules = fileCandidates(root, ['.lazy-harness/rules'], query, limit, 'rulebook')
    result.candidates.capabilities = capabilityCandidates(root, query, limit)
    return result
  }
  if (purpose === 'capability') {
    result.candidates.capabilities = capabilityCandidates(root, query, limit)
    result.candidates.rules = fileCandidates(root, ['.lazy-harness/rules'], query, limit, 'rulebook')
    return result
  }
  if (purpose === 'test') {
    result.candidates.records = fileCandidates(root, ['.lazy-harness/tests'], query, limit, 'tdd-record')
    result.candidates.testFiles = fileCandidates(root, ['tests', 'src', 'packages'], query, limit, 'source-test', true)
    result.candidates.capabilities = capabilityCandidates(root, `${query} validating_changes validation test`, limit)
    return result
  }
  if (purpose === 'source') {
    result.candidates.sourceFiles = fileCandidates(root, SOURCE_DIRS, query, limit, 'source')
    result.candidates.graphRows = graphCandidates(root, query, limit)
    return result
  }
  if (purpose === 'fact') {
    result.candidates.records = fileCandidates(root, FACT_RECORD_DIRS, query, limit, 'record')
    result.candidates.graphRows = graphCandidates(root, query, limit)
    result.candidates.sourceFiles = fileCandidates(root, SOURCE_DIRS, query, Math.max(3, Math.floor(limit / 2)), 'source')
    return result
  }
  // architecture/full broad modes
  result.candidates.records = fileCandidates(root, RECORD_DIRS, query, limit, 'record')
  result.candidates.rules = fileCandidates(root, ['.lazy-harness/rules'], query, limit, 'rulebook')
  result.candidates.capabilities = capabilityCandidates(root, query, limit)
  result.candidates.sourceFiles = fileCandidates(root, SOURCE_DIRS, query, limit, 'source')
  result.candidates.testFiles = fileCandidates(root, ['.lazy-harness/tests', 'tests', 'src', 'packages'], query, limit, 'test', true)
  result.candidates.graphRows = graphCandidates(root, query, limit)
  return result
}

function printJson(data: unknown): void {
  console.log(JSON.stringify(data, null, 2))
}

function printMd(result: FindResult): void {
  console.log('# Purpose-scoped retrieval')
  console.log(`\n- purpose: \`${result.purpose}\``)
  console.log(`- query: \`${result.query}\``)
  console.log(`- searchSpaces: ${result.searchSpaces.map((s) => `\`${s}\``).join(', ')}`)
  console.log(`- searchEvidence: ${result.evidence.searchEvidence ? 'yes' : 'no'}${result.evidence.qualifiesSearchDebt ? ' (qualifies search-debt)' : ' (cue only; broad evidence still required)'}`)
  console.log('\n## Suggested commands')
  for (const command of result.commands) console.log(`- \`${command}\``)
  printCandidateGroup('Records', result.candidates.records)
  printCandidateGroup('Rules', result.candidates.rules)
  printCandidateGroup('Capabilities', result.candidates.capabilities)
  printCandidateGroup('Source files', result.candidates.sourceFiles)
  printCandidateGroup('Test files', result.candidates.testFiles)
  printCandidateGroup('Graph rows', result.candidates.graphRows)
  console.log('\n## Escalation')
  for (const item of result.escalation) console.log(`- ${item}`)
  console.log('\n## Notes')
  for (const note of result.notes) console.log(`- ${note}`)
}

function printCandidateGroup(label: string, candidates: Candidate[]): void {
  console.log(`\n## ${label}`)
  if (candidates.length === 0) {
    console.log('- -')
    return
  }
  for (const c of candidates) {
    const name = c.path || c.id || c.title || '(unknown)'
    const extra = c.id && c.path ? ` (${c.id})` : ''
    console.log(`- ${name}${extra} — matches=${c.matchCount}${c.level ? `, level=${c.level}` : ''}`)
    if (c.title && c.title !== name) console.log(`  - title: ${c.title}`)
    if (c.source) console.log(`  - source: ${c.source}`)
  }
}

const args = parseArgs(process.argv.slice(2))
const result = buildResult(args.root, args.purpose, args.query, args.limit)
if (args.format === 'json') printJson(result)
else printMd(result)
