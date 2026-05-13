import { createHash } from 'node:crypto';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';

type Layer = 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr' | 'ssot';
type Confidence = 'high' | 'medium' | 'low' | 'ambiguous';
type CandidateType =
  | 'domain-term'
  | 'business-invariant'
  | 'contract-source'
  | 'user-behavior'
  | 'regression-fact'
  | 'decision-tradeoff'
  | 'source-of-truth'
  | 'ambiguous-knowledge';

type OutputFormat = 'json' | 'text' | 'ask';

interface CliOptions {
  text: string[];
  fixture?: string;
  format: OutputFormat;
  plan: boolean;
}

interface IntakeOption {
  id: 'A' | 'B' | 'C' | 'D' | 'custom';
  label: string;
  recommended?: boolean;
  targetLayer?: Layer;
}

interface IntakeCandidate {
  id: string;
  text: string;
  candidateType: CandidateType;
  recommendedLayer?: Layer;
  alternativeLayers: Layer[];
  confidence: Confidence;
  targetFile?: string;
  action: 'record-candidate' | 'ask' | 'ignore';
  reason: string;
  options: IntakeOption[];
  evidence: string[];
}

interface IntakeResult {
  ok: boolean;
  mode: 'plan';
  source: 'text' | 'fixture';
  checkedTexts: number;
  candidates: IntakeCandidate[];
  warnings: string[];
}

const FIXTURE_DIR = '.lazy-harness/triggers/fixtures/knowledge-intake';

function parseArgs(argv: string[]): CliOptions {
  const opts: CliOptions = { text: [], format: 'json', plan: false };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === '--text' && next) {
      opts.text.push(next);
      i += 1;
    } else if (arg === '--fixture' && next) {
      opts.fixture = next;
      i += 1;
    } else if (arg === '--format' && (next === 'json' || next === 'text' || next === 'ask')) {
      opts.format = next;
      i += 1;
    } else if (arg === '--plan') {
      opts.plan = true;
    } else if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    }
  }
  return opts;
}

function printHelp(): void {
  console.log(`Usage: bun .lazy-harness/scripts/knowledge-intake.ts --text <text> --plan [--format json|text|ask]
       bun .lazy-harness/scripts/knowledge-intake.ts --fixture all --plan

Stage 1 only: detects knowledge candidates. It never writes records.`);
}

function hashId(text: string, type: CandidateType, layer?: Layer): string {
  return `KI-${createHash('sha256').update(`${type}\0${layer ?? ''}\0${text}`).digest('hex').slice(0, 16)}`;
}

function uniq<T>(items: T[]): T[] {
  return [...new Set(items)];
}

function hasAny(text: string, patterns: RegExp[]): boolean {
  return patterns.some((pattern) => pattern.test(text));
}

function makeOptions(primary: Layer | undefined, alternatives: Layer[], candidateType: CandidateType): IntakeOption[] {
  const layers = uniq([...(primary ? [primary] : []), ...alternatives]).slice(0, 3);
  const labels: Record<Layer, string> = {
    ddd: 'DDD record로 등록',
    sdd: 'SDD/spec record로 등록',
    bdd: 'BDD scenario/behavior로 등록',
    tdd: 'TDD/regression record로 등록',
    adr: 'ADR/decision 후보로 등록',
    ssot: 'SSOT registry/source 후보로 등록',
  };
  const options: IntakeOption[] = layers.map((layer, index) => ({
    id: (['A', 'B', 'C'] as const)[index],
    label: labels[layer],
    recommended: layer === primary,
    targetLayer: layer,
  }));
  options.push({ id: 'D', label: `skip/defer: ${candidateType} 후보가 이번 작업에 필요하지 않음` });
  options.push({ id: 'custom', label: '직접 입력' });
  return options;
}

function targetFor(layer?: Layer): string | undefined {
  switch (layer) {
    case 'ddd': return '.lazy-harness/domain/ubiquitous-language.xml';
    case 'sdd': return '.lazy-harness/spec/spec-language.xml';
    case 'bdd': return '.lazy-harness/behavior/scenarios/';
    case 'tdd': return '.lazy-harness/regression/registry.jsonl';
    case 'adr': return '.lazy-harness/logs/decisions.jsonl';
    case 'ssot': return '.lazy-harness/ssot/registry.xml';
    default: return undefined;
  }
}

function candidate(text: string, candidateType: CandidateType, layer: Layer | undefined, alternatives: Layer[], confidence: Confidence, reason: string, evidence: string[]): IntakeCandidate {
  const action = confidence === 'high' && layer && alternatives.length === 0 ? 'record-candidate' : 'ask';
  return {
    id: hashId(text, candidateType, layer),
    text,
    candidateType,
    recommendedLayer: layer,
    alternativeLayers: uniq(alternatives.filter((entry) => entry !== layer)),
    confidence,
    targetFile: targetFor(layer),
    action,
    reason,
    options: makeOptions(layer, alternatives, candidateType),
    evidence,
  };
}

function detectOne(rawText: string): IntakeCandidate[] {
  const text = rawText.trim();
  if (!text) return [];
  const lower = text.toLowerCase();
  const out: IntakeCandidate[] = [];

  const mentionsBug = hasAny(lower, [/\bbug\b/, /regression/, /재발/, /버그/, /실패/, /failed?/, /null/, /edge case/]);
  const mentionsTest = hasAny(lower, [/\btest\b/, /spec/, /tdd/, /테스트/, /검증/]);
  const mentionsUserFlow = hasAny(lower, [/user|사용자|flow|journey|screen|button|click|see|보여|클릭|화면|시나리오|coordinator|patient|queue|먼저/]);
  const mentionsContract = hasAny(lower, [/api|schema|contract|payload|endpoint|component|props|zod|request|response|status|source|external|comes from|에서 온다|스키마|계약/]);
  const mentionsConfig = hasAny(lower, [/config|env|환경변수|registry|source of truth|ssot|single source|원천|설정|token|secret/]);
  const mentionsDecision = hasAny(lower, [/choose|decide|decision|trade.?off|because|instead of|not .* but|말고|대신|선택|결정|아키텍처|architecture|policy/]);
  const mentionsDomain = hasAny(lower, [/means|is not|is a|domain|entity|aggregate|invariant|business rule|always|never|must|should|란|의미|도메인|엔티티|규칙|항상|절대|반드시|해야/]);

  if (mentionsBug || (mentionsTest && hasAny(lower, [/protect|coverage|재발|회귀|regression/]))) {
    out.push(candidate(
      text,
      'regression-fact',
      'tdd',
      mentionsDomain ? ['ddd'] : [],
      mentionsBug ? 'high' : 'medium',
      'Bug/regression/test-protection language should become TDD evidence.',
      ['bug/test/regression keyword'],
    ));
  }

  if (mentionsConfig) {
    out.push(candidate(
      text,
      'source-of-truth',
      'ssot',
      mentionsContract ? ['sdd'] : [],
      mentionsContract ? 'ambiguous' : 'medium',
      'Config/env/source-of-truth language should be registered in SSOT.',
      ['config/env/SSOT keyword'],
    ));
  }

  if (mentionsContract) {
    out.push(candidate(
      text,
      'contract-source',
      'sdd',
      mentionsConfig ? ['ssot'] : [],
      mentionsConfig ? 'ambiguous' : 'medium',
      'API/schema/contract/data-source language should become SDD evidence.',
      ['contract/schema/API/source keyword'],
    ));
  }

  if (mentionsUserFlow) {
    out.push(candidate(
      text,
      'user-behavior',
      'bdd',
      mentionsDomain ? ['ddd'] : [],
      mentionsDomain ? 'ambiguous' : 'medium',
      'User-visible behavior or flow should become BDD scenario evidence.',
      ['user/flow/UI behavior keyword'],
    ));
  }

  if (mentionsDomain) {
    const invariant = hasAny(lower, [/always|never|must|should|항상|절대|반드시|해야|cannot|must not/]);
    out.push(candidate(
      text,
      invariant ? 'business-invariant' : 'domain-term',
      'ddd',
      mentionsUserFlow ? ['bdd'] : mentionsDecision ? ['adr'] : [],
      mentionsUserFlow || mentionsDecision ? 'ambiguous' : 'medium',
      invariant ? 'Invariant-like language should become DDD or ADR evidence.' : 'Definition/domain language should become DDD evidence.',
      [invariant ? 'invariant keyword' : 'definition/domain keyword'],
    ));
  }

  if (mentionsDecision) {
    out.push(candidate(
      text,
      'decision-tradeoff',
      'adr',
      mentionsDomain ? ['ddd'] : mentionsContract ? ['sdd'] : [],
      mentionsDomain || mentionsContract ? 'ambiguous' : 'medium',
      'Decision/tradeoff language should be recorded as decision evidence before becoming ADR if durable.',
      ['decision/tradeoff keyword'],
    ));
  }

  if (out.length === 0 && text.length >= 24) {
    out.push(candidate(
      text,
      'ambiguous-knowledge',
      undefined,
      ['ddd', 'sdd', 'bdd'],
      'low',
      'The text may contain reusable project knowledge, but no layer-specific trigger was confident.',
      ['non-empty text with no confident layer trigger'],
    ));
  }

  return dedupeCandidates(out);
}

function dedupeCandidates(candidates: IntakeCandidate[]): IntakeCandidate[] {
  const seen = new Set<string>();
  const result: IntakeCandidate[] = [];
  for (const entry of candidates) {
    const key = `${entry.candidateType}:${entry.recommendedLayer ?? '_'}:${entry.text}`;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(entry);
  }
  return result;
}

function loadFixtureTexts(name: string): string[] {
  if (name === 'all') {
    if (!existsSync(FIXTURE_DIR)) return [];
    return readdirSync(FIXTURE_DIR)
      .filter((file) => file.endsWith('.json'))
      .sort()
      .flatMap((file) => loadFixtureTexts(path.join(FIXTURE_DIR, file)));
  }
  const filePath = name.endsWith('.json') ? name : path.join(FIXTURE_DIR, `${name}.json`);
  const parsed = JSON.parse(readFileSync(filePath, 'utf8')) as { text?: string; texts?: string[] };
  if (Array.isArray(parsed.texts)) return parsed.texts;
  if (typeof parsed.text === 'string') return [parsed.text];
  return [];
}

function run(opts: CliOptions): IntakeResult {
  const texts = [...opts.text];
  let source: 'text' | 'fixture' = 'text';
  if (opts.fixture) {
    texts.push(...loadFixtureTexts(opts.fixture));
    source = 'fixture';
  }
  const candidates = dedupeCandidates(texts.flatMap(detectOne));
  return {
    ok: true,
    mode: 'plan',
    source,
    checkedTexts: texts.length,
    candidates,
    warnings: opts.plan ? [] : ['Stage 1 supports planning only; no writes were performed.'],
  };
}

function printText(result: IntakeResult): void {
  console.log(`knowledge-intake: checked=${result.checkedTexts} candidates=${result.candidates.length}`);
  for (const entry of result.candidates) {
    console.log(`- ${entry.id} ${entry.candidateType} layer=${entry.recommendedLayer ?? 'unknown'} confidence=${entry.confidence}`);
    console.log(`  text: ${entry.text}`);
    console.log(`  action: ${entry.action}${entry.targetFile ? ` target=${entry.targetFile}` : ''}`);
  }
}

function printAsk(result: IntakeResult): void {
  if (result.candidates.length === 0) {
    console.log('knowledge-intake: 후보 없음');
    return;
  }
  console.log('[lazy-harness intake] 미등록 knowledge 후보가 있습니다. 아직 파일은 수정하지 않았습니다.');
  for (const entry of result.candidates.slice(0, 3)) {
    console.log(`\n${entry.id}: ${entry.text}`);
    console.log(`추천: ${entry.recommendedLayer ?? 'unknown'} / ${entry.candidateType} / confidence=${entry.confidence}`);
    for (const option of entry.options) {
      console.log(`  ${option.id}. ${option.label}${option.recommended ? ' (Recommended)' : ''}`);
    }
  }
}

function main(): void {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.text.length === 0 && !opts.fixture) {
    printHelp();
    process.exit(2);
  }
  const result = run(opts);
  if (opts.format === 'text') printText(result);
  else if (opts.format === 'ask') printAsk(result);
  else console.log(JSON.stringify(result, null, 2));
}

main();
