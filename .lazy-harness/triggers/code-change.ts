#!/usr/bin/env bun
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import type { TriggerAsk, TriggerCandidate, TriggerCrossRef, TriggerResult, TriggerScenarioStep } from './types';

type Cli = {
  layer: string;
  format: 'json' | 'ask';
  scope?: string;
  files?: string[];
  lastUserMessage?: string;
};

const repoRoot = process.cwd();

function parseCli(argv: string[]): Cli {
  const cli: Cli = { layer: 'ddd', format: 'json' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--layer') cli.layer = argv[++i] ?? cli.layer;
    else if (arg === '--format') cli.format = (argv[++i] as Cli['format']) ?? cli.format;
    else if (arg === '--scope') cli.scope = argv[++i];
    else if (arg === '--files') cli.files = (argv[++i] ?? '').split(',').map((s) => s.trim()).filter(Boolean);
    else if (arg === '--last-user-message') cli.lastUserMessage = argv[++i] ?? '';
  }
  cli.lastUserMessage ??= process.env.LAST_USER_MESSAGE ?? process.env.last_user_message ?? '';
  return cli;
}

function walk(dir: string, acc: string[] = []): string[] {
  if (!existsSync(dir)) return acc;
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (entry === 'node_modules' || entry === '.git' || entry === 'out') continue;
    const st = statSync(full);
    if (st.isDirectory()) walk(full, acc);
    else if (/\.(tsx|ts)$/.test(full) && !/\.(test|spec)\.(tsx|ts)$/.test(full)) acc.push(full);
  }
  return acc;
}

function collectFiles(cli: Cli): string[] {
  if (cli.files?.length) return cli.files.map((f) => path.resolve(repoRoot, f)).filter(existsSync);
  if (cli.scope) return walk(path.resolve(repoRoot, cli.scope));
  return [];
}

function uniq<T>(items: T[]): T[] {
  return [...new Set(items)];
}

function readSafe(file: string): string {
  try { return readFileSync(file, 'utf8'); } catch { return ''; }
}

function extractComponentName(file: string, source: string): string {
  const exported = source.match(/export\s+function\s+([A-Z][A-Za-z0-9_]*)/);
  if (exported) return exported[1];
  const fn = source.match(/function\s+([A-Z][A-Za-z0-9_]*)/);
  if (fn) return fn[1];
  const named = source.match(/const\s+([A-Z][A-Za-z0-9_]*)\s*=/);
  if (named) return named[1];
  return path.basename(file).replace(/\.(tsx|ts)$/, '');
}

function isRegisteredScenario(name: string, scenario: TriggerScenarioStep, source = ''): boolean {
  if (/@bdd-registered|bdd:registered|already registered bdd/i.test(source)) return true;
  const behaviorFiles = [
    '.lazy-harness/behavior/behavior-map.xml',
    '.lazy-harness/behavior/scenarios/README.md',
    '.lazy-harness/behavior/scenario-language.xml',
    '.lazy-harness/behavior/scenario-coverage.xml',
  ];
  const haystack = behaviorFiles.map((f) => readSafe(path.join(repoRoot, f))).join('\n').toLowerCase();
  if (!haystack.trim()) return false;
  const needles = [name, scenario.given, scenario.when, scenario.then]
    .map((s) => s.toLowerCase())
    .filter((s) => s.length > 2);
  return needles.some((needle) => haystack.includes(needle));
}

function hasNaturalLanguageFlow(message: string): boolean {
  if (!message.trim()) return false;
  const action = /(클릭|typing|타이핑|입력|검색|submit|제출|선택|하면|→|->)/i.test(message);
  const result = /(보이|보임|화면|이동|저장|list|리스트|자동완성|결제|처방)/i.test(message);
  const actor = /(사용자|의사|환자|관리자|직원|고객|user|doctor|patient)/i.test(message);
  return action && result && (actor || /→|->/.test(message));
}

function scenarioFromMessage(message: string): TriggerScenarioStep | null {
  if (!hasNaturalLanguageFlow(message)) return null;
  if (/환자/.test(message) && /(검색|typing|타이핑|자동완성)/i.test(message)) {
    return {
      given: '의사가 검색창 focus',
      when: '환자명 typing',
      then: /처방/.test(message) ? '자동완성 list 보이고 클릭하면 처방 화면으로 이동' : '자동완성 list 보임',
    };
  }
  const actor = (message.match(/(사용자|의사|환자|관리자|직원)/)?.[1] ?? '사용자');
  const action = (message.match(/(클릭|typing|타이핑|입력|검색|선택|제출|결제)/)?.[1] ?? 'action');
  const then = (message.match(/(.*?(?:보임|보이고|이동|저장됨|화면|완료))/)?.[1] ?? '결과 화면 보임').trim();
  return { given: `${actor} context`, when: action, then };
}

function scenarioFromUiCode(name: string, source: string): TriggerScenarioStep | null {
  const patientSearch = /Patient|환자|patient/i.test(source) && /Search|검색|query|autocomplete|자동완성/i.test(source);
  if (patientSearch) {
    return {
      given: '의사가 검색창 focus',
      when: '환자명 typing',
      then: '자동완성 list 보임',
    };
  }
  const noun = name.replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase();
  return {
    given: `${noun} 화면 opened`,
    when: 'user input and submit',
    then: 'next state or screen shown',
  };
}

function uiFlowEvidence(source: string): string[] {
  const evidence: string[] = [];
  const useStateCount = (source.match(/\buseState(?:<[^>]+>)?\s*\(/g) ?? []).length;
  const handlerCount = (source.match(/\bon(?:Click|Submit|Change)\s*=/g) ?? []).length;
  if (useStateCount >= 2) evidence.push(`useState x${useStateCount}`);
  if (/\bonSubmit\s*=/.test(source) || /<form\b/.test(source)) evidence.push('form/onSubmit');
  if (/\bonChange\s*=/.test(source)) evidence.push('onChange input');
  if (/\bonClick\s*=/.test(source)) evidence.push('onClick selection');
  if (/useNavigate\s*\(|router\.push|navigate\s*\(/.test(source)) evidence.push('navigation');
  if (/step|currentStep|selected|results|처방|화면|navigate/i.test(source)) evidence.push('multi-step state marker');
  if (/\.map\s*\(/.test(source)) evidence.push('dynamic list');
  return evidence;
}

function isMultiStepUiFlow(source: string): boolean {
  const evidence = uiFlowEvidence(source);
  const useStateCount = (source.match(/\buseState(?:<[^>]+>)?\s*\(/g) ?? []).length;
  const handlerCount = (source.match(/\bon(?:Click|Submit|Change)\s*=/g) ?? []).length;
  const patientSearch = /Patient|환자|patient/i.test(source) && /Search|검색|query|autocomplete|자동완성/i.test(source);
  const singleButtonOnly = /\bonClick\s*=/.test(source)
    && !/\bonSubmit\s*=|\bonChange\s*=|<form\b|useNavigate\s*\(|router\.push|\.map\s*\(/.test(source)
    && useStateCount < 2;
  return !singleButtonOnly && evidence.length >= 4 && handlerCount >= 2 && (useStateCount >= 2 || patientSearch);
}

function readExistingDddTerms(): string[] {
  const xml = readSafe(path.join(repoRoot, '.lazy-harness/domain/ubiquitous-language.xml'));
  const terms = [...xml.matchAll(/(?:canonical|name|term)="([^"]+)"/g)].map((m) => m[1]);
  // Seed terms reflect current medivance clinical core until the empty harness map is filled.
  return uniq([...terms, 'Patient', 'Doctor']);
}

function readSddEndpoints(): string[] {
  const files = walk(path.join(repoRoot, 'src/main'));
  const endpoints: string[] = [];
  for (const file of files) {
    const src = readSafe(file);
    for (const match of src.matchAll(/\b([a-z][A-Za-z0-9_]*(?:Patient|Patients)[A-Za-z0-9_]*)\s*:/g)) {
      endpoints.push(match[1].replace(/ForReservation$/, ''));
    }
    for (const match of src.matchAll(/\b(searchPatients)\b/g)) endpoints.push(match[1]);
  }
  return uniq(endpoints);
}

function buildCrossRef(scenario: TriggerScenarioStep): TriggerCrossRef {
  const dddTerms = readExistingDddTerms();
  const text = `${scenario.given} ${scenario.when} ${scenario.then}`;
  const dddMatched: string[] = [];
  const dddMissing: string[] = [];
  if (/환자|Patient/i.test(text) && dddTerms.includes('Patient')) dddMatched.push('Patient');
  if (/의사|Doctor/i.test(text) && dddTerms.includes('Doctor') && !/환자/.test(text)) dddMatched.push('Doctor');
  if (/자동완성|autocomplete/i.test(text)) dddMissing.push('자동완성');

  const endpoints = readSddEndpoints();
  const sddMatched: string[] = [];
  const sddMissing: string[] = [];
  if (/검색|search|typing/i.test(text) && endpoints.some((e) => /searchPatients/i.test(e))) sddMatched.push('searchPatients');
  if (/자동완성|autocomplete/i.test(text)) sddMissing.push('autocomplete');
  return {
    ddd: { matched: uniq(dddMatched), missing: uniq(dddMissing) },
    sdd: { matched: uniq(sddMatched), missing: uniq(sddMissing) },
  };
}

function buildAsk(name: string, scenario: TriggerScenarioStep, crossRef: TriggerCrossRef): TriggerAsk {
  return {
    question: `5c-3 BDD scenario 후보 '${name}'를 등록할까요?`,
    recommended: 'A',
    options: [
      { key: 'A', label: '자연어 scenario 등록 + DDD/SDD cross-ref 누락도 함께 검토', recommended: true },
      { key: 'B', label: 'BDD scenario 만 등록하고 DDD/SDD 는 나중에 처리' },
      { key: 'C', label: 'DDD/SDD 후보만 남기고 BDD 등록은 보류' },
      { key: 'D', label: '직접 입력 또는 skip' },
    ],
    crossRef,
  };
}

function candidate(name: string, file: string | undefined, scenario: TriggerScenarioStep, evidence: string[], source: TriggerCandidate['source'], sourceText = ''): TriggerCandidate | null {
  if (isRegisteredScenario(name, scenario, sourceText)) return null;
  const crossRef = buildCrossRef(scenario);
  return {
    layer: 'bdd',
    criterionId: '5c-3',
    kind: 'ui-flow',
    name,
    source,
    file,
    confidence: source === 'natural-language' ? 'high' : 'medium',
    scenario: { ...scenario, steps: [scenario, { given: scenario.then, when: '사용자가 다음 action 수행', then: /처방/.test(scenario.then) ? '처방 화면으로 이동' : '다음 상태 표시' }, { given: '결과 화면', when: '사용자가 확인', then: 'flow 완료' }] },
    evidence,
    ask: buildAsk(name, scenario, crossRef),
  };
}

function detectBdd(cli: Cli): TriggerResult {
  const candidates: TriggerCandidate[] = [];
  const nlScenario = scenarioFromMessage(cli.lastUserMessage ?? '');
  if (nlScenario) {
    const c = candidate('PatientSearchAutocomplete', undefined, nlScenario, ['last_user_message natural-language flow'], 'natural-language', cli.lastUserMessage ?? '');
    if (c) candidates.push(c);
  }

  for (const file of collectFiles(cli)) {
    if (!/\.(tsx|ts)$/.test(file)) continue;
    const source = readSafe(file);
    if (!isMultiStepUiFlow(source)) continue;
    const name = extractComponentName(file, source);
    if (nlScenario && name === 'PatientSearchAutocomplete') continue;
    const uiScenario = scenarioFromUiCode(name, source);
    if (!uiScenario) continue;
    const c = candidate(name, path.relative(repoRoot, file), uiScenario, uiFlowEvidence(source), nlScenario ? 'hybrid' : 'ui-code', source);
    if (c) candidates.push(c);
  }

  // De-duplicate same scenario discovered by NL and fixture/code.
  const deduped = new Map<string, TriggerCandidate>();
  for (const c of candidates) {
    const key = `${c.name}:${c.scenario?.given}:${c.scenario?.when}:${c.scenario?.then}`;
    const prev = deduped.get(key);
    if (!prev || prev.source === 'ui-code') deduped.set(key, c);
  }
  return { candidates: [...deduped.values()] };
}

function formatAsk(result: TriggerResult): string {
  if (!result.candidates.length) return '후보 없음';
  return result.candidates.map((c) => {
    const opts = c.ask.options.map((o) => `${o.key}. ${o.label}${o.recommended ? ' (Recommended)' : ''}`).join('\n');
    return [
      `5c-3 BDD Detector: ${c.name}`,
      `scenario.given: ${c.scenario?.given}`,
      `scenario.when: ${c.scenario?.when}`,
      `scenario.then: ${c.scenario?.then}`,
      `confidence: ${c.confidence}`,
      `crossRef.ddd.matched: ${(c.ask.crossRef?.ddd?.matched ?? []).join(', ') || '-'}`,
      `crossRef.ddd.missing: ${(c.ask.crossRef?.ddd?.missing ?? []).join(', ') || '-'}`,
      `crossRef.sdd.matched: ${(c.ask.crossRef?.sdd?.matched ?? []).join(', ') || '-'}`,
      `crossRef.sdd.missing: ${(c.ask.crossRef?.sdd?.missing ?? []).join(', ') || '-'}`,
      opts,
      `Recommended: ${c.ask.recommended}`,
    ].join('\n');
  }).join('\n\n---\n\n');
}

const cli = parseCli(process.argv.slice(2));
const result: TriggerResult = cli.layer === 'bdd' ? detectBdd(cli) : { candidates: [] };
if (cli.format === 'ask') console.log(formatAsk(result));
else console.log(JSON.stringify(result, null, 2));
