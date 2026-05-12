import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

interface CliOptions {
  decisions: string;
  queue: string;
  format: 'json' | 'text';
}

interface DecisionRecord {
  id: string;
  source?: string;
  questionId?: string;
  selectedOption?: string;
  summary?: string;
  effects?: Array<Record<string, unknown>>;
  aftershockDepth?: number;
  createdAt?: string;
}

interface AftershockQuestion {
  id: string;
  criterionId: '5d-4';
  source: 'aftershock';
  status: 'open';
  depth: number;
  fingerprint: string;
  layer: 'ddd' | 'sdd' | 'bdd' | 'ssot' | 'tdd';
  question: string;
  recommended: 'A';
  options: Array<{
    id: 'A' | 'B' | 'C' | 'D';
    label: string;
    description?: string;
    effects: Array<Record<string, unknown>>;
  }>;
  crossRef: Record<string, unknown>;
  createdAt: string;
}

interface AftershockResult {
  ok: boolean;
  mode: 'aftershock-reanalysis';
  decisions: string;
  queue: string;
  scannedDecisions: number;
  created: number;
  existing: number;
  questions: AftershockQuestion[];
  warnings: string[];
}

const DEFAULT_DECISIONS = '.lazy-harness/logs/decisions.jsonl';
const DEFAULT_QUEUE = '.lazy-harness/questions/open.xml';
const MAX_AFTERSHOCK_DEPTH = 2;

function parseCliArgs(argv: string[]): CliOptions {
  const opts: CliOptions = { decisions: DEFAULT_DECISIONS, queue: DEFAULT_QUEUE, format: 'json' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === '--decisions' && next) {
      opts.decisions = next;
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

function escapeXml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function readDecisions(file: string): DecisionRecord[] {
  if (!existsSync(file)) return [];
  return readFileSync(file, 'utf8')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line) as DecisionRecord);
}

function existingFingerprints(queue: string): Set<string> {
  if (!existsSync(queue)) return new Set();
  const text = readFileSync(queue, 'utf8');
  const fingerprints = new Set<string>();
  for (const match of text.matchAll(/<question\b([^>]*)>/g)) {
    const fingerprint = match[1].match(/fingerprint="([^"]+)"/)?.[1];
    if (fingerprint) fingerprints.add(fingerprint);
  }
  return fingerprints;
}

function effectKind(effect: Record<string, unknown>): string {
  return String(effect.kind ?? 'unknown');
}

function effectName(effect: Record<string, unknown>): string {
  return String(effect.term ?? effect.name ?? effect.target ?? effect.summary ?? 'unnamed');
}

function aftershockLayer(kind: string): AftershockQuestion['layer'] {
  if (kind.startsWith('ddd-')) return 'sdd';
  if (kind.startsWith('sdd-')) return 'bdd';
  if (kind.startsWith('bdd-')) return 'tdd';
  if (kind.startsWith('ssot-')) return 'tdd';
  if (kind.startsWith('tdd-')) return 'bdd';
  return 'ddd';
}

function followUpEffect(layer: AftershockQuestion['layer'], name: string, decisionId: string): Record<string, unknown> {
  if (layer === 'sdd') return { kind: 'sdd-register-contract', name: `${name}Contract`, reason: `aftershock:${decisionId}` };
  if (layer === 'bdd') return { kind: 'bdd-register-scenario', name: `${name}Scenario`, given: name, when: 'decision-applied', then: 'cross-layer-consistency' };
  if (layer === 'tdd') return { kind: 'tdd-require-test', target: name, suggestedPath: `${name}.test.ts` };
  if (layer === 'ssot') return { kind: 'ssot-register-utility', name: `${name}Utility`, domain: name, kindHint: 'aftershock' };
  return { kind: 'decision-log', summary: `aftershock-follow-up:${name}`, reason: decisionId };
}

function aftershockQuestion(decision: DecisionRecord, effect: Record<string, unknown>, now: string): AftershockQuestion | null {
  const kind = effectKind(effect);
  if (kind === 'defer' || kind === 'decision-log' || kind === 'unknown') return null;
  const depth = Number(decision.aftershockDepth ?? 0) + 1;
  if (depth > MAX_AFTERSHOCK_DEPTH) return null;
  const name = effectName(effect);
  const layer = aftershockLayer(kind);
  const fingerprint = hashFingerprint({ source: 'aftershock', decisionId: decision.id, kind, name, layer });
  return {
    id: `Q-${fingerprint}`,
    criterionId: '5d-4',
    source: 'aftershock',
    status: 'open',
    depth,
    fingerprint,
    layer,
    question: `[5d-4 Aftershock] 결정 '${decision.id}'의 effect '${kind}:${name}'가 ${layer.toUpperCase()} 후속 정합성 확인을 요구합니다. 어떻게 처리할까요?`,
    recommended: 'A',
    options: [
      {
        id: 'A',
        label: `${layer.toUpperCase()} 후속 항목을 이번 결정 cascade 에 포함`,
        description: 'Recommended. 한 결정이 만든 cross-layer cascade 를 같은 루프에서 닫습니다.',
        effects: [followUpEffect(layer, name, decision.id)],
      },
      {
        id: 'B',
        label: '이미 충족됨으로 기록',
        description: '기존 artifact 에서 충족됨을 확인한 경우 선택합니다.',
        effects: [{ kind: 'decision-log', summary: `aftershock-already-covered:${kind}:${name}`, reason: decision.id }],
      },
      {
        id: 'C',
        label: '후속 작업으로 defer',
        description: '이번 scope 밖이면 명시적으로 deferred 처리합니다.',
        effects: [{ kind: 'defer', reason: `aftershock:${decision.id}:${kind}:${name}` }],
      },
      {
        id: 'D',
        label: '직접 입력',
        effects: [],
      },
    ],
    crossRef: { decisionId: decision.id, questionId: decision.questionId, selectedOption: decision.selectedOption, effect, targetLayer: layer },
    createdAt: now,
  };
}

function renderQuestion(question: AftershockQuestion): string {
  const options = question.options.map((option) => [
    `      <option id="${escapeXml(option.id)}">`,
    `        <label>${escapeXml(option.label)}</label>`,
    option.description ? `        <description>${escapeXml(option.description)}</description>` : '',
    `        <effects>${escapeXml(JSON.stringify(option.effects))}</effects>`,
    '      </option>',
  ].filter(Boolean).join('\n')).join('\n');
  return [
    `  <question id="${escapeXml(question.id)}" criterionId="${question.criterionId}" source="${question.source}" status="${question.status}" depth="${question.depth}" fingerprint="${escapeXml(question.fingerprint)}" layer="${question.layer}" createdAt="${escapeXml(question.createdAt)}">`,
    `    <text>${escapeXml(question.question)}</text>`,
    `    <recommended>${question.recommended}</recommended>`,
    '    <options>',
    options,
    '    </options>',
    `    <crossRef>${escapeXml(JSON.stringify(question.crossRef))}</crossRef>`,
    '  </question>',
  ].join('\n');
}

function appendQuestions(queue: string, questions: AftershockQuestion[]): void {
  if (questions.length === 0) return;
  mkdirSync(path.dirname(queue), { recursive: true });
  const addition = questions.map(renderQuestion).join('\n');
  if (!existsSync(queue)) {
    writeFileSync(queue, [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<openQuestions version="1.0" owner="lazy-harness" criterionId="mixed">',
      '  <!-- Generated by .lazy-harness/scripts/aftershock-reanalysis.ts. Empty is valid. -->',
      addition,
      '</openQuestions>',
      '',
    ].join('\n'), 'utf8');
    return;
  }
  const text = readFileSync(queue, 'utf8');
  const next = text.includes('</openQuestions>')
    ? text.replace('</openQuestions>', `${addition}\n</openQuestions>`)
    : `${text.trim()}\n${addition}\n`;
  writeFileSync(queue, next, 'utf8');
}

export function analyzeAftershock(decisionsFile = DEFAULT_DECISIONS, queue = DEFAULT_QUEUE): AftershockResult {
  const now = new Date().toISOString();
  const decisions = readDecisions(decisionsFile);
  const existing = existingFingerprints(queue);
  const warnings: string[] = [];
  const candidates = decisions.flatMap((decision) => (decision.effects ?? [])
    .map((effect) => aftershockQuestion(decision, effect, now))
    .filter((question): question is AftershockQuestion => question !== null));
  const seenNew = new Set<string>();
  const questions = candidates.filter((question) => {
    if (existing.has(question.fingerprint) || seenNew.has(question.fingerprint)) return false;
    seenNew.add(question.fingerprint);
    return true;
  });
  appendQuestions(queue, questions);
  if (decisions.length === 0) warnings.push('No decisions to re-analyze');
  if (candidates.length === 0 && decisions.length > 0) warnings.push('No aftershock-producing effects found');
  return {
    ok: true,
    mode: 'aftershock-reanalysis',
    decisions: decisionsFile,
    queue,
    scannedDecisions: decisions.length,
    created: questions.length,
    existing: candidates.length - questions.length,
    questions,
    warnings,
  };
}

function formatText(result: AftershockResult): string {
  return [
    `[5d-4 aftershock] scanned=${result.scannedDecisions} created=${result.created} existing=${result.existing}`,
    ...result.questions.map((question) => `- ${question.id} ${question.layer} depth=${question.depth}`),
    ...result.warnings.map((warning) => `warning: ${warning}`),
  ].join('\n');
}

function main(): void {
  const opts = parseCliArgs(process.argv.slice(2));
  const result = analyzeAftershock(opts.decisions, opts.queue);
  if (opts.format === 'json') console.log(JSON.stringify(result, null, 2));
  else console.log(formatText(result));
}

if (import.meta.main) main();
