import { createHash } from 'node:crypto';
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

interface CliOptions {
  mode: 'collect' | 'answer';
  input?: string;
  queue: string;
  decisions: string;
  format: 'json' | 'text';
  questionId?: string;
  answer?: string;
  apply: boolean;
}

interface TriggerAskOption {
  id: string;
  label: string;
  description?: string;
  effects?: Array<Record<string, unknown>>;
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
  status: 'open' | 'answered' | 'superseded' | 'deferred';
  depth: number;
  fingerprint: string;
  candidateName?: string;
  layer?: string;
  question: string;
  recommended: string;
  options: InterviewOption[];
  crossRef?: unknown;
  createdAt: string;
  answeredAt?: string;
  decisionId?: string;
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

interface DecisionRecord {
  id: string;
  source: 'interview-loop';
  questionId: string;
  selectedOption: string;
  summary: string;
  effects: Array<Record<string, unknown>>;
  aftershockDepth: number;
  createdAt: string;
}

interface AnswerResult {
  ok: boolean;
  mode: 'answer';
  queue: string;
  decisions: string;
  applied: boolean;
  questionId: string;
  selectedOption: string;
  effects: Array<Record<string, unknown>>;
  decision?: DecisionRecord;
  warnings: string[];
}

const DEFAULT_QUEUE = '.lazy-harness/questions/open.xml';
const DEFAULT_DECISIONS = '.lazy-harness/logs/decisions.jsonl';

function parseCliArgs(argv: string[]): CliOptions {
  const opts: CliOptions = { mode: 'collect', queue: DEFAULT_QUEUE, decisions: DEFAULT_DECISIONS, format: 'json', apply: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === '--mode' && next) {
      if (next !== 'collect' && next !== 'answer') throw new Error(`Unsupported mode: ${next}`);
      opts.mode = next;
      i += 1;
    } else if ((arg === '--input' || arg === '--file') && next) {
      opts.input = next;
      i += 1;
    } else if (arg === '--queue' && next) {
      opts.queue = next;
      i += 1;
    } else if (arg === '--decisions' && next) {
      opts.decisions = next;
      i += 1;
    } else if (arg === '--question-id' && next) {
      opts.questionId = next;
      i += 1;
    } else if ((arg === '--answer' || arg === '--option') && next) {
      opts.answer = next;
      i += 1;
    } else if (arg === '--apply') {
      opts.apply = true;
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
    effects: option.effects ?? [],
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

function decodeXml(value: string): string {
  return value
    .replace(/&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&gt;/g, '>')
    .replace(/&lt;/g, '<')
    .replace(/&amp;/g, '&');
}

function parseAttributes(raw: string): Record<string, string> {
  const attrs: Record<string, string> = {};
  for (const match of raw.matchAll(/([A-Za-z0-9_-]+)="([^"]*)"/g)) {
    attrs[match[1]] = decodeXml(match[2]);
  }
  return attrs;
}

function tagText(raw: string, tag: string): string {
  const match = raw.match(new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`));
  return match?.[1] ? decodeXml(match[1].trim()) : '';
}

function parseJsonText(raw: string, fallback: unknown): unknown {
  const text = decodeXml(raw.trim());
  if (!text) return fallback;
  try {
    return JSON.parse(text);
  } catch {
    return fallback;
  }
}

function parseOptions(raw: string): InterviewOption[] {
  const optionsRaw = raw.match(/<options>[\s\S]*?<\/options>/)?.[0] ?? '';
  const options: InterviewOption[] = [];
  for (const match of optionsRaw.matchAll(/<option\b([^>]*)>[\s\S]*?<\/option>/g)) {
    const optionRaw = match[0];
    const attrs = parseAttributes(match[1] ?? '');
    options.push({
      id: attrs.id,
      label: tagText(optionRaw, 'label'),
      ...(tagText(optionRaw, 'description') ? { description: tagText(optionRaw, 'description') } : {}),
      effects: parseJsonText(tagText(optionRaw, 'effects'), []) as Array<Record<string, unknown>>,
    });
  }
  return options;
}

function parseQuestion(raw: string): InterviewQuestion | null {
  const openTag = raw.match(/<question\b([^>]*)>/);
  if (!openTag) return null;
  const attrs = parseAttributes(openTag[1] ?? '');
  if (!attrs.id || !attrs.fingerprint) return null;
  return {
    id: attrs.id,
    criterionId: '5d-1',
    source: attrs.source === 'cross-layer-gap' ? 'cross-layer-gap' : 'trigger-candidate',
    status: (attrs.status as InterviewQuestion['status']) || 'open',
    depth: Number(attrs.depth ?? '0'),
    fingerprint: attrs.fingerprint,
    ...(attrs.candidateName ? { candidateName: attrs.candidateName } : {}),
    ...(attrs.layer ? { layer: attrs.layer } : {}),
    question: tagText(raw, 'text'),
    recommended: tagText(raw, 'recommended'),
    options: parseOptions(raw),
    crossRef: parseJsonText(tagText(raw, 'crossRef'), {}),
    createdAt: attrs.createdAt,
    ...(attrs.answeredAt ? { answeredAt: attrs.answeredAt } : {}),
    ...(attrs.decisionId ? { decisionId: attrs.decisionId } : {}),
  };
}

function readQuestions(queue: string): InterviewQuestion[] {
  if (!existsSync(queue)) return [];
  const text = readFileSync(queue, 'utf8');
  return [...text.matchAll(/<question\b[^>]*>[\s\S]*?<\/question>/g)]
    .map((match) => parseQuestion(match[0]))
    .filter((question): question is InterviewQuestion => question !== null);
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
    question.answeredAt ? `answeredAt="${escapeXml(question.answeredAt)}"` : '',
    question.decisionId ? `decisionId="${escapeXml(question.decisionId)}"` : '',
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

function writeQueue(queue: string, questions: InterviewQuestion[]): void {
  mkdirSync(path.dirname(queue), { recursive: true });
  const rendered = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<openQuestions version="1.0" owner="lazy-harness" criterionId="5d-1">',
    '  <!-- Generated by .lazy-harness/scripts/interview-loop.ts. Empty is valid. -->',
    ...questions.map(renderQuestion),
    '</openQuestions>',
    '',
  ].join('\n');
  writeFileSync(queue, rendered, 'utf8');
}

export function collectInterviewQuestions(result: TriggerRunResult, queue = DEFAULT_QUEUE): CollectResult {
  const existing = readQuestions(queue);
  const existingFingerprints = new Set(existing.map((question) => question.fingerprint));
  const warnings: string[] = [];
  const candidates = collectQuestions(result);
  const seenNew = new Set<string>();
  const created = candidates.filter((question) => {
    if (existingFingerprints.has(question.fingerprint) || seenNew.has(question.fingerprint)) return false;
    seenNew.add(question.fingerprint);
    return true;
  });
  writeQueue(queue, [...existing, ...created]);
  if (candidates.length === 0) warnings.push('No structured asks or cross-layer gaps found');
  return {
    ok: true,
    mode: 'collect',
    queue,
    created: created.length,
    existing: existing.length,
    totalOpen: existing.filter((question) => question.status === 'open').length + created.length,
    questions: created,
    warnings,
  };
}

function decisionId(now: string, questionIdValue: string, optionId: string): string {
  const day = now.slice(0, 10);
  const suffix = hashFingerprint({ now, questionId: questionIdValue, optionId }).slice(0, 8);
  return `D-${day}-${suffix}`;
}

function appendDecision(pathname: string, decision: DecisionRecord): void {
  mkdirSync(path.dirname(pathname), { recursive: true });
  appendFileSync(pathname, `${JSON.stringify(decision, null, 0)}\n`, 'utf8');
}

export function answerInterviewQuestion(input: {
  queue?: string;
  decisions?: string;
  questionId: string;
  answer: string;
  apply?: boolean;
}): AnswerResult {
  const queue = input.queue ?? DEFAULT_QUEUE;
  const decisions = input.decisions ?? DEFAULT_DECISIONS;
  const questions = readQuestions(queue);
  const question = questions.find((candidate) => candidate.id === input.questionId);
  if (!question) throw new Error(`Question not found: ${input.questionId}`);
  if (question.status !== 'open') throw new Error(`Question is not open: ${input.questionId} (${question.status})`);
  const selected = question.options.find((option) => option.id === input.answer);
  if (!selected) throw new Error(`Invalid answer '${input.answer}' for ${input.questionId}`);

  const now = new Date().toISOString();
  const decision: DecisionRecord = {
    id: decisionId(now, question.id, selected.id),
    source: 'interview-loop',
    questionId: question.id,
    selectedOption: selected.id,
    summary: selected.label,
    effects: selected.effects,
    aftershockDepth: question.depth,
    createdAt: now,
  };

  if (input.apply) {
    question.status = 'answered';
    question.answeredAt = now;
    question.decisionId = decision.id;
    writeQueue(queue, questions);
    appendDecision(decisions, decision);
  }

  return {
    ok: true,
    mode: 'answer',
    queue,
    decisions,
    applied: input.apply === true,
    questionId: question.id,
    selectedOption: selected.id,
    effects: selected.effects,
    ...(input.apply ? { decision } : {}),
    warnings: input.apply ? [] : ['Preview only. Re-run with --apply to persist status and decision log.'],
  };
}

function formatText(result: CollectResult | AnswerResult): string {
  if (result.mode === 'collect') {
    return [
      `[5d-1 interview-loop] created=${result.created} existing=${result.existing} totalOpen=${result.totalOpen}`,
      ...result.questions.map((question) => `- ${question.id} ${question.source} ${question.layer ?? ''} ${question.candidateName ?? ''}`.trim()),
      ...result.warnings.map((warning) => `warning: ${warning}`),
    ].join('\n');
  }
  return [
    `[5d-2 interview-loop] question=${result.questionId} answer=${result.selectedOption} applied=${result.applied}`,
    `effects=${result.effects.length}`,
    ...result.warnings.map((warning) => `warning: ${warning}`),
  ].join('\n');
}

function main(): void {
  const opts = parseCliArgs(process.argv.slice(2));
  const result = opts.mode === 'collect'
    ? collectInterviewQuestions(readInput(opts.input), opts.queue)
    : answerInterviewQuestion({
      queue: opts.queue,
      decisions: opts.decisions,
      questionId: opts.questionId ?? '',
      answer: opts.answer ?? '',
      apply: opts.apply,
    });
  if (opts.format === 'json') {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(formatText(result));
  }
}

if (import.meta.main) {
  main();
}
