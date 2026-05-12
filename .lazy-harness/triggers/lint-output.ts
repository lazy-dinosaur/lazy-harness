import { readFileSync } from 'node:fs';

export type LintDriftSource = 'tsc' | 'eslint' | 'unknown';
export type LintDriftCategory = 'environment' | 'code-drift' | 'unknown';
export type LintDriftKind =
  | 'missing-type-definition'
  | 'missing-config'
  | 'missing-module'
  | 'type-mismatch'
  | 'property-missing'
  | 'eslint-rule'
  | 'syntax'
  | 'unknown';

export interface LintDriftCandidate {
  criterionId: '5c-6';
  source: LintDriftSource;
  category: LintDriftCategory;
  kind: LintDriftKind;
  filePath?: string;
  line?: number;
  column?: number;
  code?: string;
  rule?: string;
  message: string;
  raw: string;
  recommended: 'fix-environment' | 'fix-code' | 'inspect';
}

export interface LintDriftResult {
  ok: boolean;
  trigger: 'lint-output';
  candidates: LintDriftCandidate[];
  summary: Record<string, number>;
  warnings: string[];
}

interface CliOptions {
  input?: string;
  format: 'json' | 'text';
}

const TSC_LOCATION = /^(?<file>[^\n()]+)\((?<line>\d+),(?<column>\d+)\):\s+error\s+(?<code>TS\d+):\s+(?<message>.+)$/;
const TSC_GLOBAL = /^error\s+(?<code>TS\d+):\s+(?<message>.+)$/;
const ESLINT_COMPACT = /^(?<file>[^\n:]+):(?<line>\d+):(?<column>\d+):\s+(?<severity>error|warning)\s+(?<message>.*?)\s+(?<rule>[A-Za-z0-9@/_-]+)$/;

export function analyzeLintOutput(output: string): LintDriftResult {
  const warnings: string[] = [];
  const candidates = output
    .split('\n')
    .map((line) => line.trimEnd())
    .filter((line) => line.trim().length > 0)
    .map(parseLintLine)
    .filter((candidate): candidate is LintDriftCandidate => candidate !== null);

  if (output.trim() && candidates.length === 0) {
    warnings.push('No lint/typecheck diagnostics recognized');
  }

  const summary: Record<string, number> = {};
  for (const candidate of candidates) {
    const key = `${candidate.source}:${candidate.category}:${candidate.kind}`;
    summary[key] = (summary[key] ?? 0) + 1;
  }

  return {
    ok: true,
    trigger: 'lint-output',
    candidates,
    summary,
    warnings,
  };
}

function parseLintLine(raw: string): LintDriftCandidate | null {
  const line = raw.trim();
  const tscLocation = line.match(TSC_LOCATION);
  if (tscLocation?.groups) {
    return buildTscCandidate({
      raw,
      filePath: tscLocation.groups.file,
      line: Number(tscLocation.groups.line),
      column: Number(tscLocation.groups.column),
      code: tscLocation.groups.code,
      message: tscLocation.groups.message,
    });
  }

  const tscGlobal = line.match(TSC_GLOBAL);
  if (tscGlobal?.groups) {
    return buildTscCandidate({
      raw,
      code: tscGlobal.groups.code,
      message: tscGlobal.groups.message,
    });
  }

  const eslintCompact = line.match(ESLINT_COMPACT);
  if (eslintCompact?.groups) {
    return {
      criterionId: '5c-6',
      source: 'eslint',
      category: 'code-drift',
      kind: 'eslint-rule',
      filePath: eslintCompact.groups.file,
      line: Number(eslintCompact.groups.line),
      column: Number(eslintCompact.groups.column),
      rule: eslintCompact.groups.rule,
      message: eslintCompact.groups.message.trim(),
      raw,
      recommended: 'fix-code',
    };
  }

  return null;
}

function buildTscCandidate(input: {
  raw: string;
  filePath?: string;
  line?: number;
  column?: number;
  code: string;
  message: string;
}): LintDriftCandidate {
  const { category, kind, recommended } = classifyTscDiagnostic(input.message, input.code);
  return {
    criterionId: '5c-6',
    source: 'tsc',
    category,
    kind,
    filePath: input.filePath,
    line: input.line,
    column: input.column,
    code: input.code,
    message: input.message,
    raw: input.raw,
    recommended,
  };
}

function classifyTscDiagnostic(message: string, code: string): Pick<LintDriftCandidate, 'category' | 'kind' | 'recommended'> {
  if (/Cannot find type definition file for/i.test(message)) {
    return { category: 'environment', kind: 'missing-type-definition', recommended: 'fix-environment' };
  }
  if (/File .* not found/i.test(message) || /Cannot read file/i.test(message)) {
    return { category: 'environment', kind: 'missing-config', recommended: 'fix-environment' };
  }
  if (/Cannot find module .* or its corresponding type declarations/i.test(message)) {
    return { category: 'environment', kind: 'missing-module', recommended: 'fix-environment' };
  }
  if (/Type .* is not assignable to type/i.test(message) || code === 'TS2322') {
    return { category: 'code-drift', kind: 'type-mismatch', recommended: 'fix-code' };
  }
  if (/Property .* does not exist on type/i.test(message) || code === 'TS2339') {
    return { category: 'code-drift', kind: 'property-missing', recommended: 'fix-code' };
  }
  if (/';' expected|Declaration or statement expected|Expression expected/i.test(message)) {
    return { category: 'code-drift', kind: 'syntax', recommended: 'fix-code' };
  }
  return { category: 'unknown', kind: 'unknown', recommended: 'inspect' };
}

function parseCliArgs(argv: string[]): CliOptions {
  const opts: CliOptions = { format: 'json' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if ((arg === '--input' || arg === '--file') && next) {
      opts.input = next;
      i += 1;
    } else if (arg === '--format' && (next === 'json' || next === 'text')) {
      opts.format = next;
      i += 1;
    }
  }
  return opts;
}

function readInput(input?: string): string {
  if (input) return readFileSync(input, 'utf8');
  return readFileSync(0, 'utf8');
}

function formatText(result: LintDriftResult): string {
  if (result.candidates.length === 0) return '[lint-output trigger] 후보 없음';
  return result.candidates
    .map((candidate) => [
      `[5c-6 ${candidate.source}] ${candidate.category}/${candidate.kind}`,
      `- location: ${candidate.filePath ?? '<global>'}${candidate.line ? `:${candidate.line}:${candidate.column ?? 1}` : ''}`,
      `- code/rule: ${candidate.code ?? candidate.rule ?? '(none)'}`,
      `- message: ${candidate.message}`,
      `- recommended: ${candidate.recommended}`,
    ].join('\n'))
    .join('\n\n---\n\n');
}

function main(): void {
  const opts = parseCliArgs(process.argv.slice(2));
  const result = analyzeLintOutput(readInput(opts.input));
  if (opts.format === 'text') {
    console.log(formatText(result));
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

if (import.meta.main) {
  main();
}
