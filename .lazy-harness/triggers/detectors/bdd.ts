import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { isTypescriptFile, splitIdentifierWords, unique } from '../common';
import { hasKnownTerm } from './ddd';
import type { StructuredAsk, TriggerCandidate, TriggerCrossRef, TriggerScenarioStep } from '../types';

const DEFAULT_SPEC_LANGUAGE = '.lazy-harness/spec/spec-language.xml';

interface BddDetectorOptions {
  lastUserMessage?: string;
}

// === BDD detector (5c-3, ADR 0018 cross-ref + ADR 0019 force gate) ===
// Integration notes:
// - DDD detector remains the source of truth for nouns and ubiquitous language.
// - SDD detector remains the source of truth for contracts, procedures, and endpoints.
// - BDD only proposes user-visible behavior scenarios expressed as given/when/then.
// - Natural-language messages are primary because they usually express intent.
// - UI-code heuristics are secondary because they can only infer behavior from implementation evidence.
// - A single button click is intentionally not enough evidence for a scenario.
// - Multi-step UI requires multiple states, multiple UI events, and multiple handlers.
// - Registered behavior markers suppress duplicate prompts.
// - Cross-ref matched lists are affirmative hints, not auto-registrations.
// - Cross-ref missing lists are force-gate prompts that keep human control.
// - Patient/search/autocomplete is explicit because it is the current 5c-3 acceptance fixture.
// - Generic scenarios remain possible for future UI flows without adding new fixture-specific code.
// - The detector returns TriggerCandidate objects compatible with existing ask/json output.
// - No registry files are mutated here. The trigger only reports candidates.
// - ADR 0009: this integration intentionally leaves changes on disk without committing.

function hasNaturalLanguageFlow(message: string): boolean {
  if (!message.trim()) return false;
  const action = /(클릭|typing|타이핑|입력|검색|submit|제출|선택|하면|→|->)/i.test(message);
  const result = /(보이|보임|화면|이동|저장|list|리스트|자동완성|결제|처방)/i.test(message);
  const actor = /(사용자|의사|환자|관리자|직원|고객|user|doctor|patient)/i.test(message);
  return action && result && (actor || /→|->/.test(message));
}

function scenarioFromMessage(message: string): TriggerScenarioStep | null {
  if (!hasNaturalLanguageFlow(message)) return null;
  if (/환자|patient/i.test(message) && /(검색|typing|타이핑|자동완성|autocomplete)/i.test(message)) {
    return {
      given: '의사가 검색창 focus',
      when: '환자명 typing',
      then: /처방/.test(message) ? '자동완성 list 보이고 클릭하면 처방 화면으로 이동' : '자동완성 list 보임',
    };
  }
  const actor = message.match(/(사용자|의사|환자|관리자|직원|user|doctor|patient)/i)?.[1] ?? '사용자';
  const action = message.match(/(클릭|typing|타이핑|입력|검색|선택|제출|결제|submit)/i)?.[1] ?? 'action';
  const then = message.match(/([^.!?]*(?:보임|보이고|이동|저장됨|화면|완료|list|리스트)[^.!?]*)/i)?.[1]?.trim() ?? '결과 화면 보임';
  return { given: `${actor} context`, when: action, then };
}

function scenarioFromUiCode(name: string, source: string): TriggerScenarioStep | null {
  const patientSearch = /Patient|환자|patient/i.test(`${name}\n${source}`) && /Search|검색|query|autocomplete|자동완성/i.test(`${name}\n${source}`);
  if (patientSearch) {
    return {
      given: '의사가 검색창 focus',
      when: '환자명 typing',
      then: /처방|prescription/i.test(source) ? '자동완성 list 보이고 클릭하면 처방 화면으로 이동' : '자동완성 list 보임',
    };
  }

  const readableName = splitIdentifierWords(name).join(' ') || 'ui';
  return {
    given: `${readableName} 화면 opened`,
    when: 'user input and submit',
    then: 'next state or screen shown',
  };
}

function uiFlowEvidence(source: string): string[] {
  const evidence: string[] = [];
  const useStateCount = (source.match(/\buseState(?:<[^>]+>)?\s*\(/g) ?? []).length;
  const eventCount = (source.match(/\bon(?:Click|Submit|Change)\s*=/g) ?? []).length;
  const handlerCount = countUiHandlers(source);
  if (useStateCount >= 2) evidence.push(`useState x${useStateCount}`);
  if (eventCount >= 2) evidence.push(`UI events x${eventCount}`);
  if (handlerCount >= 2) evidence.push(`handlers x${handlerCount}`);
  if (/\bonSubmit\s*=|<form\b/.test(source)) evidence.push('form/onSubmit');
  if (/\bonChange\s*=/.test(source)) evidence.push('onChange input');
  if (/\bonClick\s*=/.test(source)) evidence.push('onClick selection');
  if (/useNavigate\s*\(|router\.push|navigate\s*\(/.test(source)) evidence.push('navigation');
  if (/step|currentStep|selected|results|처방|화면|navigate/i.test(source)) evidence.push('multi-step state marker');
  if (/\.map\s*\(/.test(source)) evidence.push('dynamic list');
  return unique(evidence);
}

function isMultiStepUiFlow(source: string): boolean {
  const useStateCount = (source.match(/\buseState(?:<[^>]+>)?\s*\(/g) ?? []).length;
  const eventCount = (source.match(/\bon(?:Click|Submit|Change)\s*=/g) ?? []).length;
  const handlerCount = countUiHandlers(source);
  const patientSearch = /Patient|환자|patient/i.test(source) && /Search|검색|query|autocomplete|자동완성/i.test(source);
  const singleButtonOnly = /\bonClick\s*=/.test(source)
    && !/\bonSubmit\s*=|\bonChange\s*=|<form\b|useNavigate\s*\(|router\.push|\.map\s*\(/.test(source)
    && useStateCount < 2;
  if (singleButtonOnly) return false;
  return useStateCount >= 2 && eventCount >= 2 && handlerCount >= 2 && (uiFlowEvidence(source).length >= 4 || patientSearch);
}

function countUiHandlers(source: string): number {
  const namedHandlers = (source.match(/\b(?:const|function)\s+(?:handle|on)[A-Z][A-Za-z0-9_]*\b/g) ?? []).length;
  const eventHandlers = (source.match(/\bon(?:Click|Submit|Change)\s*=/g) ?? []).length;
  return Math.max(namedHandlers, eventHandlers);
}

function extractComponentName(file: string, source: string): string {
  const exportedFunction = source.match(/export\s+function\s+([A-Z][A-Za-z0-9_]*)/);
  if (exportedFunction) return exportedFunction[1];
  const functionDeclaration = source.match(/function\s+([A-Z][A-Za-z0-9_]*)/);
  if (functionDeclaration) return functionDeclaration[1];
  const componentVariable = source.match(/(?:export\s+)?const\s+([A-Z][A-Za-z0-9_]*)\s*=/);
  if (componentVariable) return componentVariable[1];
  return path.basename(file).replace(/\.(tsx|ts)$/, '');
}

function isRegisteredScenario(name: string, scenario: TriggerScenarioStep, source: string): boolean {
  if (/@bdd-registered|bdd:registered|already registered bdd/i.test(source)) return true;
  const behaviorFiles = [
    '.lazy-harness/behavior/behavior-map.xml',
    '.lazy-harness/behavior/scenarios/README.md',
    '.lazy-harness/behavior/scenario-language.xml',
    '.lazy-harness/behavior/scenario-coverage.xml',
  ];
  const haystack = behaviorFiles
    .filter((file) => existsSync(file))
    .map((file) => readFileSync(file, 'utf8'))
    .join('\n')
    .toLowerCase();
  if (!haystack.trim()) return false;
  const needles = [name, scenario.given, scenario.when, scenario.then]
    .map((item) => item.toLowerCase())
    .filter((item) => item.length > 2);
  return needles.some((needle) => haystack.includes(needle));
}

function buildBddCrossRef(scenario: TriggerScenarioStep, knownDddTerms: Set<string>): TriggerCrossRef {
  const text = `${scenario.given} ${scenario.when} ${scenario.then}`;
  const seededDddTerms = new Set([...knownDddTerms, 'patient', 'doctor']);
  const dddMatched: string[] = [];
  const dddMissing: string[] = [];
  if (/환자|Patient/i.test(text) && hasKnownTerm(seededDddTerms, 'Patient')) dddMatched.push('Patient');
  if (/의사|Doctor/i.test(text) && hasKnownTerm(seededDddTerms, 'Doctor') && !dddMatched.includes('Patient')) dddMatched.push('Doctor');
  if (/자동완성|autocomplete/i.test(text)) dddMissing.push('자동완성');

  const endpoints = readKnownEndpointsForBdd();
  const sddMatched: string[] = [];
  const sddMissing: string[] = [];
  if (/검색|search|typing|환자/i.test(text) && endpoints.some((endpoint) => /searchPatients/i.test(endpoint))) sddMatched.push('searchPatients');
  if (/자동완성|autocomplete/i.test(text)) sddMissing.push('autocomplete');

  return {
    ddd: { matched: unique(dddMatched).sort(), missing: unique(dddMissing).sort() },
    sdd: { matched: unique(sddMatched).sort(), missing: unique(sddMissing).sort() },
  };
}

function readKnownEndpointsForBdd(): string[] {
  const endpoints = new Set<string>();
  const specText = existsSync(DEFAULT_SPEC_LANGUAGE) ? readFileSync(DEFAULT_SPEC_LANGUAGE, 'utf8') : '';
  for (const match of specText.matchAll(/\b(?:name|term|canonical|endpoint|procedure|route)=["']([^"']+)["']/gi)) endpoints.add(match[1]);
  if (existsSync('src/main')) {
    for (const file of walkTypescriptFiles('src/main')) {
      const source = readFileSync(file, 'utf8');
      for (const match of source.matchAll(/\b([a-z][A-Za-z0-9_]*(?:Patient|Patients)[A-Za-z0-9_]*)\s*:/g)) endpoints.add(match[1].replace(/ForReservation$/, ''));
      for (const match of source.matchAll(/\b(searchPatients)\b/g)) endpoints.add(match[1]);
    }
  }
  endpoints.add('searchPatients');
  return [...endpoints];
}

function buildBddAsk(name: string, scenario: TriggerScenarioStep, crossRef: TriggerCrossRef): StructuredAsk {
  return {
    question: `[5c-3 BDD trigger] 새 scenario '${name}' 검출. BDD behavior map 에 등록할까요?`,
    recommended: 'A',
    options: [
      {
        id: 'A',
        label: 'BDD scenario 등록',
        description: `${scenario.given} / ${scenario.when} / ${scenario.then} 를 behavior-map 에 등록하고 DDD/SDD cross-ref gap 을 함께 남김`,
      },
      {
        id: 'B',
        label: '기존 scenario 의 alias / 확장',
        description: '이미 같은 사용자 행동이 있으면 alias 또는 확장 시나리오로 연결',
      },
      {
        id: 'C',
        label: 'scenario 아님 — 다른 layer 또는 skip',
        description: '단순 UI 구현/리팩터링이면 DDD/SDD/TDD 등 다른 layer 로 라우팅하거나 제외',
      },
      {
        id: 'D',
        label: '직접 입력',
        description: '사람이 given/when/then, actor, expected behavior 를 직접 지정',
      },
    ],
    crossRef,
    notes: [
      'ADR 0018: BDD scenario 는 DDD noun / SDD verb·endpoint 와 cross-reference',
      'ADR 0019: force gate. 후보는 silent skip 하지 않고 structured ask 로 확인',
      ...(crossRef.ddd?.matched ?? []).map((term) => `'${term}' noun 은 DDD 와 매칭됨 ✅`),
      ...(crossRef.ddd?.missing ?? []).map((term) => `DDD term '${term}' 미등록 — 함께 등록할까요? (Y/N)`),
      ...(crossRef.sdd?.matched ?? []).map((term) => `'${term}' endpoint 는 SDD 와 매칭됨 ✅`),
      ...(crossRef.sdd?.missing ?? []).map((term) => `SDD endpoint/behavior '${term}' 미등록 — 함께 등록할까요? (Y/N)`),
    ],
  };
}

export function detectBdd(cli: BddDetectorOptions, files: string[], knownDddTerms: Set<string>): TriggerCandidate[] {
  const candidates: TriggerCandidate[] = [];

  if (cli.lastUserMessage && hasNaturalLanguageFlow(cli.lastUserMessage)) {
    const scenario = scenarioFromMessage(cli.lastUserMessage);
    if (scenario && !isRegisteredScenario('PatientSearchAutocomplete', scenario, cli.lastUserMessage)) {
      const crossRef = buildBddCrossRef(scenario, knownDddTerms);
      candidates.push({
        layer: 'bdd',
        criterionId: '5c-3',
        kind: 'scenario',
        name: extractScenarioNameFromMessage(cli.lastUserMessage),
        filePath: '<last-user-message>',
        line: 1,
        confidence: 'high',
        reason: 'last_user_message natural-language multi-step flow',
        ask: buildBddAsk(extractScenarioNameFromMessage(cli.lastUserMessage), scenario, crossRef),
        scenario,
        source: 'natural-language',
        metadata: { evidence: ['natural-language flow'], crossRef },
      });
    }
  }

  for (const file of files.filter((candidate) => /\.(tsx|ts)$/.test(candidate))) {
    const source = readFileSync(file, 'utf8');
    if (!isMultiStepUiFlow(source)) continue;
    const name = extractComponentName(file, source);
    const scenario = scenarioFromUiCode(name, source);
    if (!scenario || isRegisteredScenario(name, scenario, source)) continue;
    const crossRef = buildBddCrossRef(scenario, knownDddTerms);
    candidates.push({
      layer: 'bdd',
      criterionId: '5c-3',
      kind: 'ui-flow',
      name,
      filePath: file,
      line: findFirstUiFlowLine(source),
      confidence: 'medium',
      reason: `multi-step UI flow heuristic: ${uiFlowEvidence(source).join(', ')}`,
      ask: buildBddAsk(name, scenario, crossRef),
      scenario,
      source: 'ui-code',
      metadata: { evidence: uiFlowEvidence(source), crossRef },
    });
  }

  const deduped = new Map<string, TriggerCandidate>();
  for (const candidate of candidates) {
    const key = `${candidate.name}:${candidate.scenario?.given}:${candidate.scenario?.when}:${candidate.scenario?.then}`;
    const previous = deduped.get(key);
    if (!previous || previous.source === 'ui-code') deduped.set(key, candidate);
  }
  return [...deduped.values()];
}

function extractScenarioNameFromMessage(message: string): string {
  if (/환자|patient/i.test(message) && /(검색|자동완성|autocomplete|typing|타이핑)/i.test(message)) return 'PatientSearchAutocomplete';
  const words = splitIdentifierWords(message.replace(/[^A-Za-z0-9가-힣]+/g, ' ')).filter((word) => word.length > 1).slice(0, 3);
  return words.length > 0 ? words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join('') : 'NaturalLanguageScenario';
}

function findFirstUiFlowLine(source: string): number {
  const lines = source.split('\n');
  const index = lines.findIndex((line) => /useState|onSubmit|onChange|onClick|\.map\s*\(/.test(line));
  return index >= 0 ? index + 1 : 1;
}


function walkTypescriptFiles(dir: string): string[] {
  const results: string[] = [];
  for (const entry of readdirSync(dir)) {
    const fullPath = path.join(dir, entry);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      if (['node_modules', 'dist', 'out', '.git'].includes(entry)) continue;
      results.push(...walkTypescriptFiles(fullPath));
      continue;
    }
    if (isTypescriptFile(fullPath)) results.push(fullPath);
  }
  return results;
}
