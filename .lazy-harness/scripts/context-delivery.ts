#!/usr/bin/env bun
/**
 * context-delivery.ts — dual-mode retrieval to Context Delivery Packet.
 *
 * Phase 4 of Native Context Broker. Produces packet-shaped required-read
 * context from a generated context index when available, or source-scan fallback
 * via context-index.ts when the cache is missing/stale.
 */
import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import * as path from 'node:path'
import { buildContextIndex, type ContextIndex, type RecordEntry } from './context-index.ts'

type InstructionLevel = 'digest-only' | 'self-resolve-before-answer' | 'self-resolve-before-change' | 'delegate-search'
type QuerySource = 'user-phrase' | 'llm-expansion' | 'deterministic-expansion' | 'record-link' | 'profile-link' | 'fallback'
type ReadKind = 'record' | 'project-profile' | 'graph-edge' | 'source-file' | 'symbol' | 'test' | 'plan' | 'schema' | 'generated-index'
type Format = 'json' | 'md'

interface Args {
  root: string
  message: string
  format: Format
  limit: number
  indexPath: string
  handoffPrompt: boolean
  journal: boolean
  journalPath: string
  messageId: string
  sessionId: string
  turnCount: string
}

interface QueryItem {
  query: string
  source: QuerySource
  purpose: string
  targets?: Array<'records' | 'project-profile' | 'graph' | 'source' | 'tests' | 'symbols'>
}

interface CandidateMeaning {
  label: string
  confidence: number
  why: string
  language?: string
}

interface ReadItem {
  path: string
  kind: ReadKind
  reason: string
  confidence: number
  whyMatched: string
  matchedQueries: string[]
  layer?: string
  symbols?: string[]
}

interface ContextDeliveryPacket {
  schemaVersion: '1.0'
  generatedAt: string
  instructionLevel: InstructionLevel
  resolvedPhrase?: string
  candidateMeanings: CandidateMeaning[]
  queries: QueryItem[]
  requiredRead: ReadItem[]
  optionalRead: ReadItem[]
  confidence: number
  fallbackSearches: string[]
  instruction: string
  notes?: string[]
}

interface ScoredRecord {
  record: RecordEntry
  score: number
  matchedQueries: string[]
  why: string[]
  matchedFields: Set<string>
}

function usage(): never {
  console.error(`Usage: context-delivery --message "..." [options]

Options:
  --root DIR              Host root (default: LAZY_HOST_ROOT or cwd)
  --message TEXT          User/coordinator request to resolve
  --format json|md        Output format (default json)
  --limit N               Max read items per bucket (default 8)
  --index PATH            Optional generated context-index path
  --handoff-prompt        Render optional searcher subagent handoff prompt
  --journal               Append sanitized packet evidence journal for response audit
  --journal-path PATH     Override packet evidence journal path
  --message-id ID         Optional message id to hash into journal
  --session-id ID         Optional session id to hash into journal
  --turn-count N          Optional turn count metadata for journal
  --help                  Show this help

Examples:
  bun .lazy-harness/scripts/context-delivery.ts --message "예약시트 고쳐줘" --format md
  .lazy-harness/bin/lazy context-delivery --message="예약시트 고쳐줘" --format=json
  .lazy-harness/bin/lazy context-delivery --message="예약시트 고쳐줘" --handoff-prompt
  .lazy-harness/bin/lazy context-delivery --message="예약시트 고쳐줘" --journal --message-id=m1
  `)
  process.exit(2)
}

function valueFor(argv: string[], index: number, flag: string): { value: string | null; consumed: number } {
  const current = argv[index]
  if (current === flag) {
    const value = argv[index + 1]
    if (!value) usage()
    return { value, consumed: 1 }
  }
  const prefix = `${flag}=`
  if (current.startsWith(prefix)) {
    const value = current.slice(prefix.length)
    if (!value) usage()
    return { value, consumed: 0 }
  }
  return { value: null, consumed: 0 }
}

function parseArgs(argv: string[]): Args {
  const root = process.env.LAZY_HOST_ROOT || process.cwd()
  const args: Args = {
    root,
    message: '',
    format: 'json',
    limit: 8,
    indexPath: '',
    handoffPrompt: false,
    journal: false,
    journalPath: '',
    messageId: process.env.LAZY_MESSAGE_ID || process.env.JCODE_MESSAGE_ID || '',
    sessionId: process.env.LAZY_SESSION_ID || process.env.JCODE_SESSION_ID || '',
    turnCount: process.env.LAZY_TURN_COUNT || '',
  }
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i]
    let parsed = valueFor(argv, i, '--root')
    if (parsed.value !== null) { args.root = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--message')
    if (parsed.value !== null) { args.message = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--format')
    if (parsed.value !== null) {
      if (parsed.value !== 'json' && parsed.value !== 'md' && parsed.value !== 'markdown') usage()
      args.format = parsed.value === 'markdown' ? 'md' : parsed.value
      i += parsed.consumed
      continue
    }
    parsed = valueFor(argv, i, '--limit')
    if (parsed.value !== null) { args.limit = Math.max(1, Number(parsed.value) || 8); i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--index')
    if (parsed.value !== null) { args.indexPath = parsed.value; i += parsed.consumed; continue }
    if (arg === '--handoff-prompt') { args.handoffPrompt = true; continue }
    if (arg === '--journal') { args.journal = true; continue }
    parsed = valueFor(argv, i, '--journal-path')
    if (parsed.value !== null) { args.journalPath = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--message-id')
    if (parsed.value !== null) { args.messageId = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--session-id')
    if (parsed.value !== null) { args.sessionId = parsed.value; i += parsed.consumed; continue }
    parsed = valueFor(argv, i, '--turn-count')
    if (parsed.value !== null) { args.turnCount = parsed.value; i += parsed.consumed; continue }
    if (arg === '--help' || arg === '-h') usage()
    else usage()
  }
  if (!args.message.trim()) usage()
  args.root = path.resolve(args.root)
  args.indexPath = args.indexPath ? path.resolve(args.indexPath) : path.join(args.root, '.lazy-harness', 'generated', 'context-index.json')
  args.journalPath = args.journalPath ? path.resolve(args.journalPath) : path.join(args.root, '.lazy-harness', 'state', 'context-delivery-packets.jsonl')
  return args
}

function clamp(value: number): number {
  return Math.max(0, Math.min(1, Number(value.toFixed(2))))
}

function unique(values: Array<string | undefined | null>): string[] {
  return Array.from(new Set(values.map((v) => (v || '').trim()).filter(Boolean)))
}

function stableHash(value: string): string | null {
  const text = String(value || '').trim()
  if (!text) return null
  return createHash('sha256').update(text, 'utf8').digest('hex').slice(0, 16)
}

function lower(value: string): string {
  return value.toLocaleLowerCase()
}

function tokenize(text: string): string[] {
  const ascii = text.match(/[A-Za-z][A-Za-z0-9_.$/-]*/g) || []
  const hangul = text.match(/[가-힣]{2,}/g) || []
  return unique([...ascii, ...hangul]).filter((token) => token.length >= 2)
}

function hasHangul(text: string): boolean {
  return /[가-힣]/.test(text)
}

function isChangeIntent(text: string): boolean {
  return /(고쳐|수정|변경|만들|구현|추가|삭제|디버그|fix|change|update|modify|build|implement|add|delete|debug|refactor)/i.test(text)
}

function isAmbiguousSurface(text: string): boolean {
  return hasHangul(text) || /(sheet|table|page|screen|surface|component|flow|ui|예약|관리|목록|상세)/i.test(text)
}

function isFrameworkContextIntent(text: string): boolean {
  return /(lazy-harness|context delivery|context broker|native context|record query|rule digest|project profile|guidance ladder|framework|broker|retrieval|packet|generated index)/i.test(text)
}

function expandQueries(message: string): QueryItem[] {
  const tokens = tokenize(message)
  const out: QueryItem[] = [
    { query: message.trim(), source: 'user-phrase', purpose: 'Original user request', targets: ['records', 'project-profile', 'source', 'tests'] },
  ]
  if (/예약|reservation|booking|appointment|schedule/i.test(message)) {
    out.push(
      { query: '예약시트 예약 시트 예약표 예약관리 예약관리페이지', source: 'deterministic-expansion', purpose: 'Korean reservation surface aliases', targets: ['records', 'project-profile'] },
      { query: 'reservation sheet booking sheet appointment schedule reservation table schedule grid booking table', source: 'deterministic-expansion', purpose: 'English reservation surface aliases', targets: ['records', 'project-profile', 'source'] },
      { query: 'ReservationSheet ReservationTable ReservationManagementPage AppointmentPage', source: 'deterministic-expansion', purpose: 'Code-style reservation component aliases', targets: ['source', 'symbols', 'tests'] },
    )
  }
  const tokenQuery = tokens.filter((token) => !/^(고쳐|수정|변경|fix|change|update|please)$/i.test(token)).join(' ')
  if (tokenQuery && tokenQuery !== message.trim()) {
    out.push({ query: tokenQuery, source: 'deterministic-expansion', purpose: 'Tokenized request terms', targets: ['records', 'source', 'tests'] })
  }
  return dedupeQueries(out)
}

function dedupeQueries(queries: QueryItem[]): QueryItem[] {
  const seen = new Set<string>()
  const out: QueryItem[] = []
  for (const query of queries) {
    const key = `${query.source}:${query.query}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push(query)
  }
  return out
}

function queryTerms(queries: QueryItem[]): string[] {
  const terms: string[] = []
  for (const query of queries) {
    terms.push(query.query)
    terms.push(...tokenize(query.query))
  }
  return unique(terms).sort((a, b) => b.length - a.length || a.localeCompare(b))
}

function includesTerm(haystack: string, term: string): boolean {
  if (!term.trim()) return false
  return lower(haystack).includes(lower(term))
}

function loadIndex(args: Args): { index: ContextIndex; source: 'generated-index' | 'source-scan' } {
  if (existsSync(args.indexPath)) {
    try {
      const parsed = JSON.parse(readFileSync(args.indexPath, 'utf8')) as ContextIndex
      if (parsed.schemaVersion === '1.0' && Array.isArray(parsed.records)) return { index: parsed, source: 'generated-index' }
    } catch {
      // Fall through to source scan.
    }
  }
  return { index: buildContextIndex(args.root), source: 'source-scan' }
}

function scoreRecord(record: RecordEntry, terms: string[], message: string): ScoredRecord | null {
  let score = 0
  const matchedQueries = new Set<string>()
  const why = new Set<string>()
  const fields = new Set<string>()
  const aliasSurface = [...record.aliases, ...record.surfaceTerms]
  const profileText = record.projectProfileFeatureIds.join(' ')
  const applies = record.digest.appliesWhen.join(' ')
  const digestText = [record.title, record.recordPath, record.digest.bullets.join(' '), record.digest.must.join(' '), record.digest.relatedRecords.join(' ')].join(' ')
  const hints = record.implementationHints
  const hintText = [...hints.routeHints, ...hints.componentHints, ...hints.fileHints, ...hints.symbolHints, ...hints.testHints].join(' ')
  const graphText = [...record.graphIds, ...record.graphHints.flatMap((hint) => [hint.id, hint.relation, hint.source, hint.target, hint.path])].join(' ')

  for (const term of terms) {
    let matchedThisTerm = false
    if (aliasSurface.some((value) => includesTerm(value, term) || includesTerm(term, value))) {
      score += 40
      fields.add('alias')
      why.add('matched alias/surface term')
      matchedThisTerm = true
    }
    if (profileText && includesTerm(profileText, term)) {
      score += 35
      fields.add('project-profile')
      why.add('matched Project Profile feature navigation')
      matchedThisTerm = true
    }
    if (includesTerm(applies, term)) {
      score += 30
      fields.add('appliesWhen')
      why.add('matched Rule digest Applies when')
      matchedThisTerm = true
    }
    if (includesTerm(graphText, term)) {
      score += 25
      fields.add('graph')
      why.add('matched graph/implementation edge')
      matchedThisTerm = true
    }
    if (includesTerm(hintText, term)) {
      score += 25
      fields.add('implementationHint')
      why.add('matched route/component/file/test hint')
      matchedThisTerm = true
    }
    if (includesTerm(digestText, term)) {
      score += 12
      fields.add('digest')
      why.add('matched record title/path/digest text')
      matchedThisTerm = true
    }
    if (matchedThisTerm) matchedQueries.add(term)
  }
  if (matchedQueries.size > 1) score += Math.min(30, (matchedQueries.size - 1) * 10)
  if (record.status === 'deprecated' || record.status === 'reverted') score -= 30
  if (record.scope === 'framework-global' && isAmbiguousSurface(message) && !isFrameworkContextIntent(message)) {
    score = Math.min(score, 35)
    why.add('framework-global example match kept below required-read threshold for product-surface request')
  }
  if (score <= 0) return null
  return { record, score, matchedQueries: Array.from(matchedQueries).slice(0, 10), why: Array.from(why), matchedFields: fields }
}

function readConfidence(score: number): number {
  return clamp(Math.min(0.98, score / 110))
}

function addReadItem(bucket: Map<string, ReadItem>, item: ReadItem): void {
  const existing = bucket.get(`${item.kind}:${item.path}`)
  if (!existing || item.confidence > existing.confidence) bucket.set(`${item.kind}:${item.path}`, item)
}

function recordReadItem(scored: ScoredRecord): ReadItem {
  const record = scored.record
  return {
    path: record.recordPath,
    kind: 'record',
    reason: `Read ${record.layer} record before acting on this surface.`,
    confidence: readConfidence(scored.score),
    whyMatched: scored.why.join('; ') || 'Matched context index evidence.',
    matchedQueries: scored.matchedQueries,
    layer: record.layer,
    symbols: unique([...record.implementationHints.componentHints, ...record.implementationHints.symbolHints]).slice(0, 8),
  }
}

function profileReadItem(scored: ScoredRecord): ReadItem | null {
  if (!scored.record.projectProfileFeatureIds.length) return null
  return {
    path: '.lazy-harness/project/feature-navigation.xml',
    kind: 'project-profile',
    reason: 'Confirm feature aliases/routes/components from Project Profile feature navigation.',
    confidence: clamp(readConfidence(scored.score) - 0.04),
    whyMatched: `Feature ids: ${scored.record.projectProfileFeatureIds.join(', ')}`,
    matchedQueries: scored.matchedQueries,
  }
}

function graphReadItems(scored: ScoredRecord): ReadItem[] {
  return scored.record.graphHints.slice(0, 3).map((hint) => ({
    path: `.lazy-harness/knowledge/graph.jsonl#${hint.id}`,
    kind: 'graph-edge' as const,
    reason: 'Inspect graph edge that links record context to implementation evidence.',
    confidence: clamp(readConfidence(scored.score) - 0.1),
    whyMatched: hint.relation ? `Graph relation ${hint.relation}` : 'Matched graph edge evidence.',
    matchedQueries: scored.matchedQueries,
  }))
}

function fileReadItems(scored: ScoredRecord, changeIntent: boolean): ReadItem[] {
  const record = scored.record
  const out: ReadItem[] = []
  const confidence = clamp(readConfidence(scored.score) - 0.12)
  for (const file of record.implementationHints.fileHints.slice(0, 4)) {
    out.push({
      path: file,
      kind: 'source-file',
      reason: changeIntent ? 'Inspect implementation file before editing.' : 'Inspect implementation file if explanation needs code details.',
      confidence,
      whyMatched: 'Matched file hint from record/profile/implementation map.',
      matchedQueries: scored.matchedQueries,
      symbols: unique([...record.implementationHints.componentHints, ...record.implementationHints.symbolHints]).slice(0, 8),
    })
  }
  for (const test of record.implementationHints.testHints.slice(0, 4)) {
    out.push({
      path: test,
      kind: 'test',
      reason: changeIntent ? 'Inspect or update protection test for this change.' : 'Inspect protection test if validation detail is needed.',
      confidence: clamp(confidence - 0.03),
      whyMatched: 'Matched test hint from record/profile/implementation map.',
      matchedQueries: scored.matchedQueries,
    })
  }
  return out
}

function candidateMeanings(scored: ScoredRecord[], reservationLike: boolean): CandidateMeaning[] {
  const out: CandidateMeaning[] = []
  if (reservationLike) {
    out.push({
      label: 'reservation sheet / reservation management table',
      confidence: scored[0] ? readConfidence(scored[0].score) : 0.6,
      why: 'Deterministic multilingual expansion mapped the Korean reservation surface to reservation UI/table aliases.',
      language: 'ko/en/symbol',
    })
  }
  for (const item of scored.slice(0, 3)) {
    const aliases = item.record.aliases.slice(0, 3).join(' / ')
    out.push({
      label: aliases ? `${item.record.title} / ${aliases}` : item.record.title,
      confidence: readConfidence(item.score),
      why: item.why.join('; ') || 'Matched context index evidence.',
    })
  }
  const seen = new Set<string>()
  return out.filter((item) => {
    const key = item.label
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function fallbackSearches(message: string, queries: QueryItem[]): string[] {
  const terms = queryTerms(queries).filter((term) => term.length >= 2).slice(0, 12)
  const pattern = unique(terms.map((term) => term.replace(/["'`|]/g, ''))).join('|') || message.replace(/["'`|]/g, '')
  return [
    `rg -n "${pattern}" .lazy-harness src tests`,
    'bun .lazy-harness/scripts/context-index.ts --root . --format json',
  ]
}

function buildPacket(args: Args): ContextDeliveryPacket {
  const { index, source } = loadIndex(args)
  const queries = expandQueries(args.message)
  const terms = queryTerms(queries)
  const scored = index.records
    .map((record) => scoreRecord(record, terms, args.message))
    .filter((item): item is ScoredRecord => Boolean(item))
    .sort((a, b) => b.score - a.score || a.record.recordPath.localeCompare(b.record.recordPath))

  const changeIntent = isChangeIntent(args.message)
  const ambiguous = isAmbiguousSurface(args.message)
  const required = new Map<string, ReadItem>()
  const optional = new Map<string, ReadItem>()

  for (const item of scored) {
    const targetBucket = item.score >= 70 ? required : item.score >= 40 ? optional : null
    if (!targetBucket) continue
    addReadItem(targetBucket, recordReadItem(item))
    const profile = profileReadItem(item)
    if (profile) addReadItem(targetBucket, profile)
    for (const graph of graphReadItems(item)) addReadItem(optional, graph)
    const shouldFuseFileTrack = item.matchedFields.has('implementationHint') || item.matchedFields.has('graph') || item.matchedFields.has('project-profile') || item.record.scope === 'host-project'
    if (shouldFuseFileTrack) {
      for (const file of fileReadItems(item, changeIntent)) {
        if (item.score >= 70 && changeIntent) addReadItem(required, file)
        else addReadItem(optional, file)
      }
    }
  }

  const requiredRead = Array.from(required.values())
    .sort((a, b) => b.confidence - a.confidence || a.path.localeCompare(b.path))
    .slice(0, args.limit)
  const optionalRead = Array.from(optional.values())
    .filter((item) => !required.has(`${item.kind}:${item.path}`))
    .sort((a, b) => b.confidence - a.confidence || a.path.localeCompare(b.path))
    .slice(0, args.limit)
  const confidence = requiredRead[0]?.confidence || optionalRead[0]?.confidence || 0
  const instructionLevel: InstructionLevel = requiredRead.length
    ? (changeIntent ? 'self-resolve-before-change' : 'self-resolve-before-answer')
    : (ambiguous ? (changeIntent ? 'self-resolve-before-change' : 'self-resolve-before-answer') : 'digest-only')
  const resolvedPhrase = hasHangul(args.message) ? tokenize(args.message).find((token) => /[가-힣]/.test(token)) : undefined
  return {
    schemaVersion: '1.0',
    generatedAt: new Date().toISOString(),
    instructionLevel,
    ...(resolvedPhrase ? { resolvedPhrase } : {}),
    candidateMeanings: candidateMeanings(scored, /예약|reservation|booking|appointment|schedule/i.test(args.message)).slice(0, 5),
    queries,
    requiredRead,
    optionalRead,
    confidence,
    fallbackSearches: fallbackSearches(args.message, queries),
    instruction: requiredRead.length
      ? 'Read requiredRead before answering or editing. If candidate meanings conflict, ask an option gate.'
      : 'No high-confidence requiredRead was found. Use fallbackSearches or ask an option gate before changing code.',
    notes: [`contextIndexSource=${source}`, `contextIndexFingerprint=${index.fingerprint}`],
  }
}

function renderMarkdown(packet: ContextDeliveryPacket): string {
  const lines = [
    'Context Delivery Packet',
    `Instruction: ${packet.instructionLevel}`,
  ]
  if (packet.resolvedPhrase) lines.push(`Resolved phrase: ${packet.resolvedPhrase}`)
  lines.push(`Confidence: ${packet.confidence.toFixed(2)}`)
  if (packet.candidateMeanings.length) {
    lines.push('', 'Candidate meanings')
    for (const item of packet.candidateMeanings) lines.push(`- ${item.label} (${item.confidence.toFixed(2)}): ${item.why}`)
  }
  if (packet.requiredRead.length) {
    lines.push('', 'Required read before answer/change')
    for (const item of packet.requiredRead) {
      lines.push(`- \`${item.path}\` - ${item.kind} - ${item.confidence.toFixed(2)}`)
      lines.push(`  - Reason: ${item.reason}`)
      lines.push(`  - Matched: ${item.matchedQueries.join(', ')}`)
      if (item.symbols?.length) lines.push(`  - Symbols: ${item.symbols.join(', ')}`)
    }
  }
  if (packet.optionalRead.length) {
    lines.push('', 'Optional read')
    for (const item of packet.optionalRead.slice(0, 5)) lines.push(`- \`${item.path}\` - ${item.kind} - ${item.confidence.toFixed(2)}: ${item.reason}`)
  }
  if (packet.fallbackSearches.length) {
    lines.push('', 'Fallback searches')
    for (const search of packet.fallbackSearches) lines.push(`- \`${search}\``)
  }
  lines.push('', `Instruction: ${packet.instruction}`)
  return `${lines.join('\n')}\n`
}

function safeFence(value: string): string {
  return value.replace(/```/g, "'''").trim()
}

function handoffSeedPacket(packet: ContextDeliveryPacket): ContextDeliveryPacket {
  return {
    ...packet,
    instructionLevel: 'delegate-search',
    instruction: 'Search root-bound records, Project Profile, graph, source files, symbols, and tests; return a ContextDeliveryPacket JSON object matching the schema. Do not mutate files.',
    notes: unique([...(packet.notes || []), 'handoffMode=searcher-subagent', 'mutationAllowed=false']),
  }
}

function renderHandoffPrompt(packet: ContextDeliveryPacket, args: Args): string {
  const seed = handoffSeedPacket(packet)
  const lines = [
    'Context Delivery search handoff',
    '',
    'Task: resolve required-read context for the current request and return a packet-shaped result.',
    '',
    'Current user request:',
    '```text',
    safeFence(args.message),
    '```',
    '',
    'Host root:',
    `\`${args.root}\``,
    '',
    'Root-bound constraints:',
    '- Search only inside the host root.',
    '- Use `.lazy-harness`, Project Profile, graph, source, symbols, and tests as evidence sources.',
    '- Do not mutate files, run migrations, send network requests, or execute destructive commands.',
    '- Do not call `jcode run` from `message.received`; this handoff is for explicit optional delegation only.',
    '- Do not return raw grep chunks or prose-only summaries.',
    '',
    'Candidate queries:',
  ]
  for (const query of packet.queries.slice(0, 8)) {
    const targets = query.targets?.length ? ` [${query.targets.join(', ')}]` : ''
    lines.push(`- ${query.query} (${query.source}: ${query.purpose})${targets}`)
  }
  if (packet.fallbackSearches.length) {
    lines.push('', 'Fallback searches:')
    for (const search of packet.fallbackSearches.slice(0, 5)) lines.push(`- \`${search}\``)
  }
  lines.push(
    '',
    'Return contract:',
    '- Return one JSON object matching `.lazy-harness/schemas/context-delivery-packet.schema.json`.',
    '- Set `instructionLevel` to `delegate-search` when delegation was needed, otherwise keep the stricter self-resolve level.',
    '- Include `candidateMeanings`, `queries`, `requiredRead`, `optionalRead`, `confidence`, `fallbackSearches`, and concise `instruction`.',
    '- Every `requiredRead` item must include path, kind, reason, confidence, whyMatched, and matchedQueries.',
    '- If candidate meanings conflict or confidence is low, say so in `instruction` and preserve fallback searches.',
    '',
    'Seed packet:',
    '```json',
    JSON.stringify(seed, null, 2),
    '```',
    '',
  )
  return lines.join('\n')
}

function sanitizeReadItem(item: ReadItem): Record<string, unknown> {
  return {
    path: item.path,
    kind: item.kind,
    confidence: item.confidence,
    ...(item.layer ? { layer: item.layer } : {}),
    ...(item.symbols?.length ? { symbols: item.symbols.slice(0, 8) } : {}),
    matchedQueryCount: item.matchedQueries.length,
  }
}

function appendPacketJournal(packet: ContextDeliveryPacket, args: Args): void {
  const row = {
    schemaVersion: '1.0',
    event: 'context-delivery.packet',
    timestamp: new Date().toISOString(),
    epochSeconds: Math.floor(Date.now() / 1000),
    messageIdHash: stableHash(args.messageId),
    sessionIdHash: stableHash(args.sessionId),
    turnCount: args.turnCount ? Number(args.turnCount) || args.turnCount : undefined,
    packetHash: stableHash(JSON.stringify(packet)),
    instructionLevel: packet.instructionLevel,
    confidence: packet.confidence,
    requiredReadCount: packet.requiredRead.length,
    optionalReadCount: packet.optionalRead.length,
    candidateMeaningCount: packet.candidateMeanings.length,
    fallbackSearchCount: packet.fallbackSearches.length,
    requiredRead: packet.requiredRead.slice(0, args.limit).map(sanitizeReadItem),
    optionalRead: packet.optionalRead.slice(0, Math.min(args.limit, 5)).map(sanitizeReadItem),
    notes: unique(packet.notes || []).filter((note) => !/contextIndexFingerprint=/.test(note)).slice(0, 8),
  }
  mkdirSync(path.dirname(args.journalPath), { recursive: true })
  let existing: string[] = []
  if (existsSync(args.journalPath)) {
    try {
      existing = readFileSync(args.journalPath, 'utf8').split(/\r?\n/).filter((line) => line.trim()).slice(-199)
    } catch {
      existing = []
    }
  }
  existing.push(JSON.stringify(row, null, 0))
  writeFileSync(args.journalPath, `${existing.join('\n')}\n`, 'utf8')
}

function main(): void {
  const args = parseArgs(process.argv.slice(2))
  const packet = buildPacket(args)
  if (args.journal) appendPacketJournal(packet, args)
  if (args.handoffPrompt) process.stdout.write(renderHandoffPrompt(packet, args))
  else if (args.format === 'md') process.stdout.write(renderMarkdown(packet))
  else process.stdout.write(`${JSON.stringify(packet, null, 2)}\n`)
}

main()
