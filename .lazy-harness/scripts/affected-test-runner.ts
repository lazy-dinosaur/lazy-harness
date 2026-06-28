import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { candidateTestPaths, matchingTests } from './test-match';

interface CliOptions {
  files: string[];
  queue?: string;
  strategy?: string;
  format: 'json' | 'text';
  run: boolean;
}

interface AffectedQuestion {
  id: string;
  criterionId: '5d-3';
  source: 'affected-test-runner';
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

interface FilePlan {
  file: string;
  kind: 'source' | 'test' | 'ignored';
  matchingTests: string[];
  question?: AffectedQuestion;
  reason?: string;
}

interface TestRunResult {
  command: string[];
  exitCode: number;
  stdout: string;
  stderr: string;
}

interface AffectedTestResult {
  ok: boolean;
  mode: 'affected-test-runner';
  checked: number;
  runnableTests: string[];
  forceGate: boolean;
  queue?: string;
  framework: {
    detected: boolean;
    runner: 'test-strategy' | 'package-script' | 'unknown';
    commandTemplate?: string;
    scriptName?: string;
    strategyPath?: string;
    reason?: string;
  };
  files: FilePlan[];
  questions: AffectedQuestion[];
  run?: TestRunResult;
  warnings: string[];
}

const DEFAULT_QUEUE = '.lazy-harness/questions/open.xml';
const SOURCE_EXT_RE = /\.(ts|tsx|js|jsx)$/;
const TEST_FILE_RE = /\.(test|spec)\.(ts|tsx|js|jsx)$/;

function parseCliArgs(argv: string[]): CliOptions {
  const opts: CliOptions = { files: [], format: 'json', run: true };
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
    } else if (arg === '--strategy' && next) {
      opts.strategy = next;
      i += 1;
    } else if (arg === '--format' && (next === 'json' || next === 'text')) {
      opts.format = next;
      i += 1;
    } else if (arg === '--no-run') {
      opts.run = false;
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

function uniqueFiles(files: string[]): string[] {
  return [...new Set(files.map(normalizePath))];
}

function isTestFile(file: string): boolean {
  return TEST_FILE_RE.test(path.basename(file));
}

function isSourceFile(file: string): boolean {
  return SOURCE_EXT_RE.test(file) && !isTestFile(file) && !file.endsWith('.d.ts');
}


function unescapeXml(value: string): string {
  return value
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&');
}

function readAttribute(text: string, name: string): string | undefined {
  const match = text.match(new RegExp(`${name}="([^"]+)"`));
  return match ? unescapeXml(match[1]) : undefined;
}

function detectStrategy(strategyPath?: string): AffectedTestResult['framework'] | undefined {
  const candidates = [strategyPath, '.lazy-harness/tests/test-strategy.xml'].filter(Boolean) as string[];
  for (const candidate of candidates) {
    if (!existsSync(candidate)) continue;
    const text = readFileSync(candidate, 'utf8');
    const routing = text.match(/<affectedTestRouting\b[^>]*>/)?.[0]
      ?? text.match(/<affectedTests\b[^>]*command="[^"]+"[^>]*>/)?.[0]
      ?? text.match(/<testCommand\b[^>]*>/)?.[0];
    const commandTemplate = routing ? readAttribute(routing, 'command') : undefined;
    if (commandTemplate) {
      return {
        detected: true,
        runner: 'test-strategy',
        commandTemplate,
        strategyPath: candidate,
      };
    }
    return {
      detected: false,
      runner: 'unknown',
      strategyPath: candidate,
      reason: 'test strategy exists but has no affected test command',
    };
  }
  return undefined;
}

function detectPackageScript(): AffectedTestResult['framework'] {
  if (!existsSync('package.json')) return { detected: false, runner: 'unknown', reason: 'package.json not found' };
  try {
    const packageJson = JSON.parse(readFileSync('package.json', 'utf8')) as { scripts?: Record<string, string> };
    const scripts = packageJson.scripts ?? {};
    for (const scriptName of ['test:run', 'test:unit', 'test']) {
      const script = scripts[scriptName];
      if (!script) continue;
      return {
        detected: true,
        runner: 'package-script',
        scriptName,
        commandTemplate: `bun run ${scriptName} {tests}`,
      };
    }
    return { detected: false, runner: 'unknown', reason: 'package.json has no test:run/test:unit/test script' };
  } catch (error) {
    return { detected: false, runner: 'unknown', reason: `package.json parse failed: ${String(error)}` };
  }
}

function detectTestCommand(strategyPath?: string): AffectedTestResult['framework'] {
  return detectStrategy(strategyPath) ?? detectPackageScript();
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

function renderQuestion(question: AffectedQuestion): string {
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

function appendQuestions(queue: string, questions: AffectedQuestion[]): void {
  if (questions.length === 0) return;
  mkdirSync(path.dirname(queue), { recursive: true });
  const addition = questions.map(renderQuestion).join('\n');
  if (!existsSync(queue)) {
    writeFileSync(queue, [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<openQuestions version="1.0" owner="lazy-harness" criterionId="mixed">',
      '  <!-- Generated by .lazy-harness/scripts/affected-test-runner.ts. Empty is valid. -->',
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

function testStrategyQuestion(file: string, reason: 'missing-test' | 'missing-framework', now: string): AffectedQuestion {
  const suggestedPath = candidateTestPaths(file)[0];
  const fingerprint = hashFingerprint({ source: 'affected-test-runner', reason, file });
  const reasonLabel = reason === 'missing-test' ? '대응 test/spec 파일이 없습니다' : '테스트 실행 명령이 명확하지 않습니다';
  return {
    id: `Q-${fingerprint}`,
    criterionId: '5d-3',
    source: 'affected-test-runner',
    status: 'open',
    depth: 0,
    fingerprint,
    layer: 'tdd',
    question: `[5d-3 Affected Test] '${file}' 검증 중 ${reasonLabel}. 어떤 방식으로 진행할까요?`,
    recommended: 'A',
    options: [
      {
        id: 'A',
        label: `프로젝트 테스트 전략에 맞춰 ${suggestedPath} 작성 후 실행`,
        description: 'Recommended. runner는 Project Init Interview/test-strategy 또는 package script에서 결정합니다.',
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
        effects: [{ kind: 'defer', reason: `affected-test:${reason}:${file}` }],
      },
      {
        id: 'D',
        label: '직접 입력',
        effects: [],
      },
    ],
    crossRef: { check: 'affected-test-runner', reason, file, suggestedPath, candidates: candidateTestPaths(file) },
    createdAt: now,
  };
}

function splitShellWords(command: string): string[] {
  const words: string[] = [];
  let current = '';
  let quote: 'single' | 'double' | null = null;
  for (let i = 0; i < command.length; i += 1) {
    const char = command[i];
    if (char === "'" && quote !== 'double') {
      quote = quote === 'single' ? null : 'single';
      continue;
    }
    if (char === '"' && quote !== 'single') {
      quote = quote === 'double' ? null : 'double';
      continue;
    }
    if (/\s/.test(char) && !quote) {
      if (current) words.push(current);
      current = '';
      continue;
    }
    current += char;
  }
  if (current) words.push(current);
  return words;
}

function buildTestCommand(framework: AffectedTestResult['framework'], tests: string[]): string[] {
  const template = framework.commandTemplate;
  if (!template) return [];
  const parts = splitShellWords(template);
  const command: string[] = [];
  let injected = false;
  for (const part of parts) {
    if (part === '{tests}') {
      command.push(...tests);
      injected = true;
    } else if (part.includes('{tests}')) {
      command.push(part.replace('{tests}', tests.join(' ')));
      injected = true;
    } else {
      command.push(part);
    }
  }
  if (!injected) command.push(...tests);
  return command;
}

function runConfiguredTests(framework: AffectedTestResult['framework'], tests: string[]): TestRunResult {
  const command = buildTestCommand(framework, tests);
  if (command.length === 0) {
    return { command: [], exitCode: 1, stdout: '', stderr: 'No affected test command configured' };
  }
  const completed = spawnSync(command[0], command.slice(1), { encoding: 'utf8' });
  return {
    command,
    exitCode: completed.status ?? 1,
    stdout: completed.stdout ?? '',
    stderr: completed.stderr ?? '',
  };
}

export function runAffectedTests(files: string[], options: { queue?: string; run?: boolean; strategy?: string } = {}): AffectedTestResult {
  const now = new Date().toISOString();
  const queue = options.queue;
  const framework = detectTestCommand(options.strategy);
  const filePlans: FilePlan[] = [];
  const questions: AffectedQuestion[] = [];
  const existing = queue ? existingFingerprints(queue) : new Set<string>();
  for (const file of uniqueFiles(files)) {
    if (!SOURCE_EXT_RE.test(file)) {
      filePlans.push({ file, kind: 'ignored', matchingTests: [], reason: 'unsupported-extension' });
      continue;
    }
    if (isTestFile(file)) {
      filePlans.push({ file, kind: 'test', matchingTests: [file] });
      continue;
    }
    if (!isSourceFile(file)) {
      filePlans.push({ file, kind: 'ignored', matchingTests: [], reason: 'not-source' });
      continue;
    }
    const tests = matchingTests(file);
    if (!framework.detected) {
      const question = testStrategyQuestion(file, 'missing-framework', now);
      filePlans.push({ file, kind: 'source', matchingTests: tests, question, reason: 'missing-framework' });
      if (!existing.has(question.fingerprint)) questions.push(question);
      continue;
    }
    if (tests.length === 0) {
      const question = testStrategyQuestion(file, 'missing-test', now);
      filePlans.push({ file, kind: 'source', matchingTests: [], question, reason: 'missing-test' });
      if (!existing.has(question.fingerprint)) questions.push(question);
      continue;
    }
    filePlans.push({ file, kind: 'source', matchingTests: tests });
  }
  if (queue) appendQuestions(queue, questions);
  const runnableTests = uniqueFiles(filePlans.flatMap((plan) => plan.matchingTests));
  const run = framework.detected && runnableTests.length > 0 && options.run !== false ? runConfiguredTests(framework, runnableTests) : undefined;
  // tests/tdd-cross-verify-forcegate-loop.md (regression):
  // forceGate must only trigger when there is at least one NEW unanswered
  // question (i.e. fingerprint not yet in queue). Otherwise the same question
  // ask-loops every response.completed until `recent_tool_calls` no longer
  // mentions the source path. Plan.question being non-undefined alone is not
  // enough — that question may already be open in the queue.
  const newQuestionFiles = new Set(questions.map((question) => question.id));
  const needsInterview = filePlans.some((plan) => plan.kind === 'source' && plan.question !== undefined && newQuestionFiles.has(plan.question.id));
  const forceGate = needsInterview || (run ? run.exitCode !== 0 : false);
  const checked = filePlans.filter((plan) => plan.kind === 'source').length;
  return {
    ok: !forceGate,
    mode: 'affected-test-runner',
    checked,
    runnableTests,
    forceGate,
    ...(queue ? { queue } : {}),
    framework,
    files: filePlans,
    questions,
    ...(run ? { run } : {}),
    warnings: checked === 0 ? ['No source files to verify'] : [],
  };
}

function formatText(result: AffectedTestResult): string {
  const lines = [`[affected-test-runner] ok=${result.ok} checked=${result.checked} tests=${result.runnableTests.length} forceGate=${result.forceGate}`];
  if (result.run) lines.push(`run: ${result.run.command.join(' ')} exit=${result.run.exitCode}`);
  for (const question of result.questions) lines.push(`ask ${question.id}: ${question.question}`);
  for (const warning of result.warnings) lines.push(`warning: ${warning}`);
  return lines.join('\n');
}

function main(): void {
  const opts = parseCliArgs(process.argv.slice(2));
  const result = runAffectedTests(opts.files, { queue: opts.queue, run: opts.run, strategy: opts.strategy });
  if (opts.format === 'json') console.log(JSON.stringify(result, null, 2));
  else console.log(formatText(result));
  if (result.forceGate) process.exitCode = 2;
}

if (import.meta.main) main();
