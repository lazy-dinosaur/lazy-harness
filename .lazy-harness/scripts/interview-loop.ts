import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

interface CliOptions {
  mode: 'collect';
  input?: string;
  queue: string;
  format: 'json' | 'text';
}

interface TriggerAskOption {
  id: string;
  label: string;
  description?: string;
}

interface TriggerAsk {
  question: string;
  recommended: string;
  options: TriggerAskOption[];
  crossRef?: unknown;
  notes?: string[];
}

interface TriggerCandidate {
  layer?: 'ddd' | 'sdd' | 'bdd' | 'ssot' | 'tdd';
  criterionId?: string;
  kind?: string;
  name?: string;
  filePath?: string;
  line?: number;
  confidence?: string;
  ask?: TriggerAsk;
  metadata?: Record<string, unknown>;
}

interface CrossLayerGap {
  fromLayer: string;
  targetLayer: string;
  term: string;
  candidateName: string;
  filePath?: string;
  severity: string;
  reason: string;
}

interface TriggerRunResult {
  candidates?: TriggerCandidate[];
  crossLayer?: {
    criterionId?: string;
    gaps?: CrossLayerGap[];
    summary?: Record<string, number>;
  };
}

interface InterviewOption {
  id: string;
  label: string;
  description?: string;
  effects: Array<Record<string, unknown>>;
}

interface InterviewQuestion {
  id: string;
  criterionId: '5d-1';
  source: 'trigger-candidate' | 'cross-layer-gap';
  status: 'open';
  depth: number;
  fingerprint: string;
  candidateName?: string;
  layer?: string;
  question: string;
  recommended: string;
  options: InterviewOption[];
  crossRef?: unknown;
  createdAt: string;
}

interface ExistingQuestion {
  fingerprint: string;
  raw: string;
}

interface CollectResult {
  ok: boolean;
  mode: 'collect';
  queue: string;
  created: number;
  existing: number;
  totalOpen: number;
  questions: InterviewQuestion[];
  warnings: string[];
}

const DEFAULT_QUEUE = '.lazy-harness/questions/open.xml';

function parseCliArgs(argv: string[]): CliOptions {
  const opts: CliOptions = { mode: 'collect', queue: DEFAULT_QUEUE, format: 'json' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === '--mode' && next) {
      if (next !== 'collect') throw new Error(`Unsupported mode for 5d-1: ${next}`);
      opts.mode = next;
      i += 1;
    } else if ((arg === '--input' || arg === '--file') && next) {
      opts.input = next;
      i += 1;
    } else if (arg === '--queue' && next) {
      opts.queue = next;
      i += 1;
    } else if (arg === '--format' && (next === 'json' || next === 'text')) {
      opts.format = next;
      i += 1;
    }
  }
  return opts;
}

function readInput(input?: string): TriggerRunResult {
  const text = input ? readFileSync(input, 'utf8') : readFileSync(0, 'utf8');
  return JSON.parse(text) as TriggerRunResult;
}

function stableJson(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, entryValue]) => entryValue !== undefined)
      .sort(([a], [b]) => a.localeCompare(b));
    return `{${entries.map(([key, entryValue]) => `${JSON.stringify(key)}:${stableJson(entryValue)}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function hashFingerprint(parts: Record<string, unknown>): string {
  return createHash('sha256').update(stableJson(parts)).digest('hex').slice(0, 16);
}

function questionId(fingerprint: string): string {
  return `Q-${fingerprint}`;
}

function normalizeOptions(options: TriggerAskOption[] | undefined): InterviewOption[] {
  return (options ?? []).map((option) => ({
    id: option.id,
    label: option.label,
    ...(option.description ? { description: option.description } : {}),
    effects: [],
  }));
}

function questionFromCandidate(candidate: TriggerCandidate, now: string): InterviewQuestion | null {
  if (!candidate.ask?.question) return null;
  const fingerprint = hashFingerprint({
    source: 'trigger-candidate',
    layer: candidate.layer,
    candidateName: candidate.name,
    question: candidate.ask.question,
    crossRef: candidate.ask.crossRef ?? candidate.metadata?.crossRef,
  });
  return {
    id: questionId(fingerprint),
    criterionId: '5d-1',
    source: 'trigger-candidate',
    status: 'open',
    depth: 0,
    fingerprint,
    ...(candidate.name ? { candidateName: candidate.name } : {}),
    ...(candidate.layer ? { layer: candidate.layer } : {}),
    question: candidate.ask.question,
    recommended: candidate.ask.recommended,
    options: normalizeOptions(candidate.ask.options),
    crossRef: candidate.ask.crossRef ?? candidate.metadata?.crossRef,
    createdAt: now,
  };
}

function questionFromCrossLayer(gaps: CrossLayerGap[], summary: Record<string, number> | undefined, now: string): InterviewQuestion | null {
  if (gaps.length === 0) return null;
  const fingerprint = hashFingerprint({
    source: 'cross-layer-gap',
    gaps: gaps.map((gap) => ({
      fromLayer: gap.fromLayer,
      targetLayer: gap.targetLayer,
      term: gap.term,
      candidateName: gap.candidateName,
      severity: gap.severity,
    })),
    summary,
  });
  const gapLabels = gaps.map((gap) => `${gap.fromLayer}->${gap.targetLayer}:${gap.term}`).join(', ');
  return {
    id: questionId(fingerprint),
    criterionId: '5d-1',
    source: 'cross-layer-gap',
    status: 'open',
    depth: 0,
    fingerprint,
    question: `[5d-1 Interview Loop] cross-layer gap ${gaps.length}건 검출: ${gapLabels}. 어떤 방식으로 정리할까요?`,
    recommended: 'A',
    options: [
      {
        id: 'A',
        label: '관련 DDD/SDD/BDD/SSOT 항목을 같은 결정으로 정리',
        description: 'Recommended when gaps describe one feature decision cascade.',
        effects: gaps.map((gap) => ({ kind: 'decision-log', summary: gap.reason, reason: 'cross-layer-gap' })),
      },
      {
        id: 'B',
        label: '가장 상위 DDD term 부터 먼저 확정',
        description: 'Domain-first resolution. Follow-up aftershock may create SDD/BDD questions.',
        effects: [],
      },
      {
        id: 'C',
        label: '이번 작업 범위 밖으로 defer',
        description: 'Record explicit deferral so the same gap is not silently forgotten.',
        effects: [{ kind: 'defer', reason: 'out-of-scope-for-current-change' }],
      },
      {
        id: 'D',
        label: '직접 입력',
        effects: [],
      },
    ],
    crossRef: { gaps, summary: summary ?? {} },
    createdAt: now,
  };
}

function collectQuestions(result: TriggerRunResult, now = new Date().toISOString()): InterviewQuestion[] {
  const questions = (result.candidates ?? [])
    .map((candidate) => questionFromCandidate(candidate, now))
    .filter((question): question is InterviewQuestion => question !== null);
  const crossLayerQuestion = questionFromCrossLayer(result.crossLayer?.gaps ?? [], result.crossLayer?.summary, now);
  if (crossLayerQuestion) questions.push(crossLayerQuestion);
  return questions;
}

function escapeXml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function parseAttributes(raw: string): Record<string, string> {
  const attrs: Record<string, string> = {};
  for (const match of raw.matchAll(/([A-Za-z0-9_-]+)="([^"]*)"/g)) {
    attrs[match[1]] = match[2];
  }
  return attrs;
}

function readExistingQuestions(queue: string): ExistingQuestion[] {
  if (!existsSync(queue)) return [];
  const text = readFileSync(queue, 'utf8');
  const existing: ExistingQuestion[] = [];
  for (const match of text.matchAll(/<question\b([^>]*)>[\s\S]*?<\/question>/g)) {
    const attrs = parseAttributes(match[1] ?? '');
    const fingerprint = attrs.fingerprint;
    if (!fingerprint) continue;
    existing.push({ fingerprint, raw: match[0] });
  }
  return existing;
}

function renderQuestion(question: InterviewQuestion): string {
  const attrs = [
    `id="${escapeXml(question.id)}"`,
    `criterionId="${escapeXml(question.criterionId)}"`,
    `source="${escapeXml(question.source)}"`,
    `status="${escapeXml(question.status)}"`,
    `depth="${question.depth}"`,
    `fingerprint="${escapeXml(question.fingerprint)}"`,
    question.layer ? `layer="${escapeXml(question.layer)}"` : '',
    question.candidateName ? `candidateName="${escapeXml(question.candidateName)}"` : '',
    `createdAt="${escapeXml(question.createdAt)}"`,
  ].filter(Boolean).join(' ');
  const options = question.options.map((option) => [
    `      <option id="${escapeXml(option.id)}">`,
    `        <label>${escapeXml(option.label)}</label>`,
    option.description ? `        <description>${escapeXml(option.description)}</description>` : '',
    `        <effects>${escapeXml(JSON.stringify(option.effects))}</effects>`,
    '      </option>',
  ].filter(Boolean).join('\n')).join('\n');
  return [
    `  <question ${attrs}>`,
    `    <text>${escapeXml(question.question)}</text>`,
    `    <recommended>${escapeXml(question.recommended)}</recommended>`,
    '    <options>',
    options,
    '    </options>',
    `    <crossRef>${escapeXml(JSON.stringify(question.crossRef ?? {}))}</crossRef>`,
    '  </question>',
  ].join('\n');
}

function writeQueue(queue: string, existing: ExistingQuestion[], created: InterviewQuestion[]): void {
  mkdirSync(path.dirname(queue), { recursive: true });
  const rendered = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<openQuestions version="1.0" owner="lazy-harness" criterionId="5d-1">',
    '  <!-- Generated by .lazy-harness/scripts/interview-loop.ts in collect mode. Empty is valid. -->',
    ...existing.map((question) => question.raw.split('\n').map((line) => `  ${line.trimStart()}`).join('\n')),
    ...created.map(renderQuestion),
    '</openQuestions>',
    '',
  ].join('\n');
  writeFileSync(queue, rendered, 'utf8');
}

export function collectInterviewQuestions(result: TriggerRunResult, queue = DEFAULT_QUEUE): CollectResult {
  const existing = readExistingQuestions(queue);
  const existingFingerprints = new Set(existing.map((question) => question.fingerprint));
  const warnings: string[] = [];
  const candidates = collectQuestions(result);
  const seenNew = new Set<string>();
  const created = candidates.filter((question) => {
    if (existingFingerprints.has(question.fingerprint) || seenNew.has(question.fingerprint)) return false;
    seenNew.add(question.fingerprint);
    return true;
  });
  writeQueue(queue, existing, created);
  if (candidates.length === 0) warnings.push('No structured asks or cross-layer gaps found');
  return {
    ok: true,
    mode: 'collect',
    queue,
    created: created.length,
    existing: existing.length,
    totalOpen: existing.length + created.length,
    questions: created,
    warnings,
  };
}

function formatText(result: CollectResult): string {
  return [
    `[5d-1 interview-loop] created=${result.created} existing=${result.existing} totalOpen=${result.totalOpen}`,
    ...result.questions.map((question) => `- ${question.id} ${question.source} ${question.layer ?? ''} ${question.candidateName ?? ''}`.trim()),
    ...result.warnings.map((warning) => `warning: ${warning}`),
  ].join('\n');
}

function main(): void {
  const opts = parseCliArgs(process.argv.slice(2));
  const result = collectInterviewQuestions(readInput(opts.input), opts.queue);
  if (opts.format === 'json') {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(formatText(result));
  }
}

if (import.meta.main) {
  main();
}
