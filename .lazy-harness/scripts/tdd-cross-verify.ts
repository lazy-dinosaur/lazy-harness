import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { candidateTestPaths, matchingTests } from './test-match';

interface CliOptions {
  files: string[];
  queue?: string;
  format: 'json' | 'text';
}

interface TddQuestion {
  id: string;
  criterionId: '5d-3';
  source: 'tdd-cross-verify';
  status: 'open';
  depth: 0;
  fingerprint: string;
  layer: 'tdd';
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

interface FileCheck {
  file: string;
  kind: 'source' | 'test' | 'ignored';
  ok: boolean;
  matchingTests: string[];
  question?: TddQuestion;
  reason?: string;
}

interface VerifyResult {
  ok: boolean;
  mode: 'tdd-cross-verify';
  checked: number;
  passed: number;
  failed: number;
  forceGate: boolean;
  queue?: string;
  files: FileCheck[];
  questions: TddQuestion[];
  warnings: string[];
}

const DEFAULT_QUEUE = '.lazy-harness/questions/open.xml';
const SOURCE_EXT_RE = /\.(ts|tsx|js|jsx)$/;
const TEST_FILE_RE = /\.(test|spec)\.(ts|tsx|js|jsx)$/;

function parseCliArgs(argv: string[]): CliOptions {
  const opts: CliOptions = { files: [], format: 'json' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if ((arg === '--files' || arg === '--changed-files') && next) {
      opts.files.push(...next.split(',').map((entry) => entry.trim()).filter(Boolean));
      i += 1;
    } else if (arg === '--file' && next) {
      opts.files.push(next);
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

function normalizePath(file: string): string {
  return file.replace(/\\/g, '/').replace(/^\.\//, '');
}

function isTestFile(file: string): boolean {
  return TEST_FILE_RE.test(path.basename(file));
}

function isSourceFile(file: string): boolean {
  return SOURCE_EXT_RE.test(file) && !isTestFile(file) && !file.endsWith('.d.ts');
}

function uniqueFiles(files: string[]): string[] {
  return [...new Set(files.map(normalizePath))];
}


function escapeXml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
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

function renderQuestion(question: TddQuestion): string {
  const options = question.options.map((option) => [
    `      <option id="${escapeXml(option.id)}">`,
    `        <label>${escapeXml(option.label)}</label>`,
    option.description ? `        <description>${escapeXml(option.description)}</description>` : '',
    `        <effects>${escapeXml(JSON.stringify(option.effects))}</effects>`,
    '      </option>',
  ].filter(Boolean).join('\n')).join('\n');
  return [
    `  <question id="${escapeXml(question.id)}" criterionId="${question.criterionId}" source="${question.source}" status="${question.status}" depth="0" fingerprint="${escapeXml(question.fingerprint)}" layer="tdd" createdAt="${escapeXml(question.createdAt)}">`,
    `    <text>${escapeXml(question.question)}</text>`,
    `    <recommended>${question.recommended}</recommended>`,
    '    <options>',
    options,
    '    </options>',
    `    <crossRef>${escapeXml(JSON.stringify(question.crossRef))}</crossRef>`,
    '  </question>',
  ].join('\n');
}

function appendQuestions(queue: string, questions: TddQuestion[]): void {
  if (questions.length === 0) return;
  mkdirSync(path.dirname(queue), { recursive: true });
  const addition = questions.map(renderQuestion).join('\n');
  if (!existsSync(queue)) {
    writeFileSync(queue, [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<openQuestions version="1.0" owner="lazy-harness" criterionId="mixed">',
      '  <!-- Generated by .lazy-harness/scripts/tdd-cross-verify.ts. Empty is valid. -->',
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

function questionForMissingTest(file: string, now: string): TddQuestion {
  const suggestedPath = candidateTestPaths(file)[0];
  const fingerprint = hashFingerprint({ source: 'tdd-cross-verify', check: 'test-exists', file });
  return {
    id: `Q-${fingerprint}`,
    criterionId: '5d-3',
    source: 'tdd-cross-verify',
    status: 'open',
    depth: 0,
    fingerprint,
    layer: 'tdd',
    question: `[5d-3 TDD Cross-Verify] '${file}' 변경에 대응하는 test/spec 파일이 없습니다. 어떻게 처리할까요?`,
    recommended: 'A',
    options: [
      {
        id: 'A',
        label: `프로젝트 테스트 전략에 맞춰 ${suggestedPath} 작성 후 실행`,
        description: 'Recommended. test runner는 Project Init Interview/test-strategy 또는 repo-native package script에서 결정합니다.',
        effects: [{ kind: 'tdd-require-test', target: file, suggestedPath, runner: 'project-test-strategy' }],
      },
      {
        id: 'B',
        label: '다른 테스트 명령/기존 테스트 경로를 직접 지정',
        description: '프로젝트 테스트 전략이 다른 runner이거나 기존 통합 테스트로 커버되는 경우 선택합니다.',
        effects: [{ kind: 'decision-log', summary: 'custom-test-strategy-required', reason: file }],
      },
      {
        id: 'C',
        label: '이번 변경에서는 테스트 실행을 명시적으로 skip/defer',
        description: '스킵 사유를 decision log에 남겨 silent skip을 방지합니다.',
        effects: [{ kind: 'defer', reason: `missing-test:${file}` }],
      },
      {
        id: 'D',
        label: '직접 입력',
        effects: [],
      },
    ],
    crossRef: { check: 'test-exists', file, suggestedPath, candidates: candidateTestPaths(file) },
    createdAt: now,
  };
}

export function verifyTddCrossReferences(files: string[], queue?: string): VerifyResult {
  const now = new Date().toISOString();
  const checks: FileCheck[] = [];
  const questions: TddQuestion[] = [];
  const seenQueue = queue ? existingFingerprints(queue) : new Set<string>();
  for (const file of uniqueFiles(files)) {
    if (!SOURCE_EXT_RE.test(file)) {
      checks.push({ file, kind: 'ignored', ok: true, matchingTests: [], reason: 'unsupported-extension' });
      continue;
    }
    if (isTestFile(file)) {
      checks.push({ file, kind: 'test', ok: true, matchingTests: [file] });
      continue;
    }
    if (!isSourceFile(file)) {
      checks.push({ file, kind: 'ignored', ok: true, matchingTests: [], reason: 'not-source' });
      continue;
    }
    const tests = matchingTests(file);
    if (tests.length > 0) {
      checks.push({ file, kind: 'source', ok: true, matchingTests: tests });
      continue;
    }
    const question = questionForMissingTest(file, now);
    checks.push({ file, kind: 'source', ok: false, matchingTests: [], question, reason: 'missing-test' });
    if (!seenQueue.has(question.fingerprint)) {
      questions.push(question);
      seenQueue.add(question.fingerprint);
    }
  }
  if (queue) appendQuestions(queue, questions);
  const sourceChecks = checks.filter((check) => check.kind === 'source');
  const failed = sourceChecks.filter((check) => !check.ok).length;
  // tests/tdd-cross-verify-forcegate-loop.md (regression):
  // forceGate fires only when there is at least one NEW unanswered question for
  // this response. Questions whose fingerprints are already tracked in the queue
  // must not re-trigger the gate, otherwise the same question loops every
  // response.completed until `recent_tool_calls` happens to drop the source
  // path. Dedup intent: ask once per fingerprint, never repeat.
  return {
    ok: failed === 0,
    mode: 'tdd-cross-verify',
    checked: sourceChecks.length,
    passed: sourceChecks.length - failed,
    failed,
    forceGate: questions.length > 0,
    ...(queue ? { queue } : {}),
    files: checks,
    questions,
    warnings: sourceChecks.length === 0 ? ['No source files to verify'] : [],
  };
}

function formatText(result: VerifyResult): string {
  const lines = [`[5d-3 tdd-cross-verify] ok=${result.ok} checked=${result.checked} failed=${result.failed} forceGate=${result.forceGate}`];
  for (const check of result.files) {
    if (check.kind === 'source') lines.push(`- ${check.ok ? 'PASS' : 'FAIL'} ${check.file}${check.reason ? ` ${check.reason}` : ''}`);
  }
  for (const question of result.questions) lines.push(`ask ${question.id}: ${question.question}`);
  for (const warning of result.warnings) lines.push(`warning: ${warning}`);
  return lines.join('\n');
}

function main(): void {
  const opts = parseCliArgs(process.argv.slice(2));
  const result = verifyTddCrossReferences(opts.files, opts.queue);
  if (opts.format === 'json') console.log(JSON.stringify(result, null, 2));
  else console.log(formatText(result));
  if (result.forceGate) process.exitCode = 2;
}

if (import.meta.main) main();
