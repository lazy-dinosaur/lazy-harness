import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { InterfaceDeclaration, Project, SourceFile, TypeAliasDeclaration } from 'ts-morph';
import { normalizePath, splitIdentifierWords } from '../common';
import type { StructuredAsk, TriggerCandidate, TriggerConfidence } from '../types';

export interface DeclarationCandidate {
  kind: 'interface' | 'type';
  name: string;
  filePath: string;
  line: number;
  exported: boolean;
  memberCount: number;
  unionLiteralCount: number;
  hasTypeParameters: boolean;
  isZodInferAlias: boolean;
}

export const ACRONYM_LENGTH = 3;

export const DOMAIN_SEED_NOUNS = [
  'Patient',
  'Appointment',
  'Reservation',
  'Hospital',
  'Doctor',
  'Treatment',
  'Prescription',
  'Schedule',
  'Scheduling',
  'License',
  'Notification',
  'Review',
  'Chat',
  'Call',
  'Attendance',
  'Order',
  'Payment',
  'Customer',
  'Clinic',
  'Leave',
  'Vacation',
  'Supply',
  'Annual',
  'Restore',
  'Replacement',
  'Staff',
  'User',
  'Vendor',
  'Department',
  'Location',
  'Finance',
  'Cost',
  'Shift',
  'Role',
  'Permission',
  'Referral',
  'Campaign',
  'Cart',
  'Meeting',
  'Notice',
  'Inspection',
];

export const KNOWN_ACRONYM_EXPANSIONS: Record<string, string> = {
  EMR: 'Electronic Medical Record',
};

const DOMAINISH_SUFFIXES = [
  'Status',
  'State',
  'Profile',
  'Policy',
  'Rule',
  'Context',
  'Request',
  'Result',
  'Snapshot',
  'Source',
  'Handler',
  'Record',
  'Event',
  'Command',
  'Summary',
  'Item',
  'Entry',
  'Data',
  'Tx',
  'Shape',
];

export const ZOD_HELPER_WORDS = new Set([
  'z',
  'zod',
  'any',
  'array',
  'bigint',
  'boolean',
  'brand',
  'catch',
  'coerce',
  'date',
  'default',
  'discriminated',
  'effect',
  'effects',
  'enum',
  'function',
  'instanceof',
  'intersection',
  'lazy',
  'literal',
  'map',
  'native',
  'never',
  'null',
  'nullable',
  'number',
  'object',
  'optional',
  'pipeline',
  'preprocess',
  'promise',
  'readonly',
  'record',
  'schema',
  'set',
  'string',
  'symbol',
  'transform',
  'tuple',
  'undefined',
  'union',
  'unknown',
  'void',
]);

const EXCLUDED_PATTERNS = [
  /Props$/,
  /Component$/,
  /Test$/,
  /Mock$/,
  /Fixture$/,
  /^Mock/,
  /^Test/,
  /^Json(Value)?$/,
  /^ApiResponse$/,
  /Callback$/,
  /^Options$/,
  /^HangulFuzzyOptions$/,
  /^Figma[A-Z]/,
];

export const DDD_INFERENCE_STOP_WORDS = new Set([
  'a',
  'all',
  'and',
  'an',
  'at',
  'by',
  'count',
  'counts',
  'create',
  'delete',
  'find',
  'for',
  'from',
  'get',
  'id',
  'ids',
  'in',
  'list',
  'many',
  'multiple',
  'of',
  'one',
  'or',
  'range',
  'remove',
  'search',
  'submit',
  'the',
  'to',
  'update',
  'upsert',
  'with',
]);

export const SHORT_ACRONYM_NOISE_WORDS = new Set(['at', 'by', 'in', 'of', 'on', 'or', 'to']);
export function extractDeclarations(sourceFile: SourceFile): DeclarationCandidate[] {
  const filePath = normalizePath(sourceFile.getFilePath());
  const interfaces = sourceFile.getInterfaces().map((node) => declarationFromInterface(node, filePath));
  const typeAliases = sourceFile.getTypeAliases().map((node) => declarationFromTypeAlias(node, filePath));
  return [...interfaces, ...typeAliases];
}

export function getPreviousDeclarationNames(project: Project, filePath: string, warnings: string[]): Set<string> {
  const names = new Set<string>();
  let previousText = '';

  try {
    previousText = execFileSync('git', ['show', `HEAD:${filePath}`], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch {
    return names;
  }

  try {
    const previousSource = project.createSourceFile(`/.lazy-harness/.tmp/previous-${filePath.replace(/[^A-Za-z0-9_.-]/g, '-')}`, previousText, {
      overwrite: true,
    });
    for (const declaration of extractDeclarations(previousSource)) {
      names.add(`${declaration.kind}:${declaration.name}`);
    }
  } catch (error) {
    warnings.push(`Failed to parse HEAD version of ${filePath}: ${error instanceof Error ? error.message : String(error)}`);
  }

  return names;
}

function declarationFromInterface(node: InterfaceDeclaration, filePath: string): DeclarationCandidate {
  return {
    kind: 'interface',
    name: node.getName(),
    filePath,
    line: node.getStartLineNumber(),
    exported: node.isExported(),
    memberCount: node.getMembers().length,
    unionLiteralCount: 0,
    hasTypeParameters: node.getTypeParameters().length > 0,
    isZodInferAlias: false,
  };
}

function declarationFromTypeAlias(node: TypeAliasDeclaration, filePath: string): DeclarationCandidate {
  const typeNodeText = node.getTypeNode()?.getText() ?? '';
  return {
    kind: 'type',
    name: node.getName(),
    filePath,
    line: node.getStartLineNumber(),
    exported: node.isExported(),
    memberCount: countTypeMembers(typeNodeText),
    unionLiteralCount: countUnionLiterals(typeNodeText),
    hasTypeParameters: node.getTypeParameters().length > 0,
    isZodInferAlias: /\bz\.infer\s*</.test(typeNodeText),
  };
}
export function isAcronymCandidate(term: string): boolean {
  const normalized = term.replace(/[^A-Za-z0-9]/g, '');
  const lower = normalized.toLowerCase();
  if (!normalized || DDD_INFERENCE_STOP_WORDS.has(lower) || SHORT_ACRONYM_NOISE_WORDS.has(lower) || ZOD_HELPER_WORDS.has(lower)) return false;
  if (normalized.length !== ACRONYM_LENGTH) return false;
  return /^[A-Z]{3}$/.test(normalized) || /^[A-Z][a-z]{2}$/.test(normalized);
}

export function inferAmbiguousAcronyms(value: string): string[] {
  const acronyms = new Set<string>();
  for (const word of splitIdentifierWords(value)) {
    if (!isAmbiguousAcronymWord(word)) continue;
    acronyms.add(word.toUpperCase());
  }
  return [...acronyms].sort();
}

export function inferAmbiguousAcronymsFromObjectFields(value: string): string[] {
  const acronyms = new Set<string>();
  for (const match of value.matchAll(/\b([A-Za-z][A-Za-z0-9_]*)\s*:/g)) {
    for (const acronym of inferAmbiguousAcronyms(match[1] ?? '')) {
      acronyms.add(acronym);
    }
  }
  return [...acronyms].sort();
}

function isAmbiguousAcronymWord(word: string): boolean {
  if (!/^[a-z][a-z0-9]{2}$/.test(word)) return false;
  if (DDD_INFERENCE_STOP_WORDS.has(word) || ZOD_HELPER_WORDS.has(word)) return false;
  return true;
}

export function canonicalAcronymDisplay(term: string): string {
  const normalized = term.replace(/[^A-Za-z0-9]/g, '');
  if (/^[A-Z][a-z]{2}$/.test(normalized)) return normalized;
  return normalized.toUpperCase();
}

export function hasKnownTerm(terms: Set<string>, term: string): boolean {
  const normalized = term.trim();
  if (!normalized) return false;
  return terms.has(normalized.toLowerCase()) || terms.has(normalized.toUpperCase().toLowerCase());
}

function getAcronymCompoundPrefix(name: string): string | null {
  const allCapsMatch = name.match(/^([A-Z]{3})(?=[A-Z][a-z])/);
  if (allCapsMatch?.[1] && isAcronymCandidate(allCapsMatch[1])) return allCapsMatch[1];

  const pascalAcronymMatch = name.match(/^([A-Z][a-z]{2})(?=[A-Z])/);
  if (pascalAcronymMatch?.[1] && KNOWN_ACRONYM_EXPANSIONS[pascalAcronymMatch[1].toUpperCase()] && isAcronymCandidate(pascalAcronymMatch[1])) {
    return pascalAcronymMatch[1];
  }

  return null;
}

export function filePathToDomainHint(filePath: string): string {
  return path.basename(filePath, path.extname(filePath));
}

export function isZodExpressionText(value: string): boolean {
  return /\bz\s*\./.test(value) || /\bZ(?:od)?(?:Object|String|Number|Array|Enum|Boolean|Date|Union|Literal)\b/i.test(value);
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


function isMeaningfulDddTerm(term: string): boolean {
  if (!term || isZodExpressionText(term)) return false;

  const words = filterDddTermWords(splitIdentifierWords(term));
  if (words.length === 0) return false;
  if (isZodHelperComposite(words)) return false;

  if (words.length === 1) return classifyNounWord(words[0]) !== 'noise';

  return words.some((word) => classifyNounWord(word) !== 'noise');
}

function classifyNounWord(word: string): 'noise' | 'acronym-candidate' | 'meaningful' {
  if (SHORT_ACRONYM_NOISE_WORDS.has(word)) return 'noise';
  if (DOMAIN_SEED_NOUNS.some((noun) => noun.toLowerCase() === word)) return 'meaningful';
  if (word.length === ACRONYM_LENGTH) return 'acronym-candidate';
  return 'meaningful';
}

function filterDddTermWords(words: string[]): string[] {
  return words.filter((word) => !DDD_INFERENCE_STOP_WORDS.has(word) && !SHORT_ACRONYM_NOISE_WORDS.has(word) && !ZOD_HELPER_WORDS.has(word));
}

function isZodHelperComposite(words: string[]): boolean {
  const joined = words.join('');
  if (ZOD_HELPER_WORDS.has(joined)) return true;
  return joined.startsWith('z') && ZOD_HELPER_WORDS.has(joined.slice(1));
}


export function inferMatchedDddTerms(signature: string, knownDddTerms: Set<string>): string[] {
  const known = new Set([...knownDddTerms, ...DOMAIN_SEED_NOUNS.map((term) => term.toLowerCase())]);
  const matched = new Set<string>();
  for (const match of signature.matchAll(/\b([A-Za-z][A-Za-z0-9_]*)\s*:/g)) {
    const fieldName = match[1] ?? '';
    const term = splitIdentifierWords(fieldName.replace(/Id$/i, ''))
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join('');
    if (term && isMeaningfulDddTerm(term) && known.has(term.toLowerCase())) matched.add(term);
  }
  return [...matched].sort();
}

export function toDddCandidate(declaration: DeclarationCandidate, knownTerms: Set<string>, forbiddenTerms: Set<string>): TriggerCandidate | null {
  if (!isPascalCase(declaration.name)) return null;
  if (hasKnownTerm(knownTerms, declaration.name)) return null;
  if (hasKnownTerm(forbiddenTerms, declaration.name)) return null;
  if (EXCLUDED_PATTERNS.some((pattern) => pattern.test(declaration.name))) return null;
  if (declaration.name.length <= 2) return null;

  if (declaration.hasTypeParameters) return null;
  if (declaration.isZodInferAlias) return null;

  const domainSeed = DOMAIN_SEED_NOUNS.find((noun) => declaration.name.includes(noun));
  const suffix = DOMAINISH_SUFFIXES.find((item) => declaration.name.endsWith(item));
  const acronymCompound = getAcronymCompoundPrefix(declaration.name);
  const inDomainPath = /src\/main\/(services|trpc\/routers|db|utils|types)\//.test(declaration.filePath)
    || declaration.filePath.includes('.lazy-harness/triggers/fixtures/');

  let confidence: TriggerConfidence | null = null;
  const reasons: string[] = [];

  const acronymCandidate = isAcronymCandidate(declaration.name);
  if (acronymCandidate && inDomainPath) {
    confidence = 'ambiguous';
    reasons.push('3-letter acronym candidate', 'domain path', 'ADR 0019 force gate');
  } else if (acronymCompound && inDomainPath && (declaration.memberCount >= 2 || declaration.unionLiteralCount >= 2)) {
    confidence = 'high';
    reasons.push(`acronym-prefixed compound '${acronymCompound}'`, 'domain path', '2+ members or union literals');
  } else if (domainSeed && inDomainPath && (declaration.memberCount >= 2 || declaration.unionLiteralCount >= 2)) {
    confidence = 'high';
    reasons.push(`domain seed noun '${domainSeed}'`, 'domain path', '2+ members or union literals');
  } else if (acronymCompound && inDomainPath) {
    confidence = 'medium';
    reasons.push(`acronym-prefixed compound '${acronymCompound}'`, 'domain path');
  } else if ((domainSeed || suffix) && inDomainPath) {
    confidence = 'medium';
    if (domainSeed) reasons.push(`domain seed noun '${domainSeed}'`);
    if (suffix) reasons.push(`domain-ish suffix '${suffix}'`);
    reasons.push('domain path');
  } else if (domainSeed) {
    confidence = 'low';
    reasons.push(`domain seed noun '${domainSeed}'`);
  } else if (/src\/main\/(utils|types)\//.test(declaration.filePath) && (declaration.memberCount >= 1 || declaration.unionLiteralCount >= 2)) {
    confidence = 'low';
    reasons.push('domain utility path', 'PascalCase declaration with members');
  }

  if (!confidence) return null;

  const ask = buildDddAsk(declaration, confidence, acronymCandidate);
  return {
    layer: 'ddd',
    criterionId: acronymCandidate ? '5c-2' : '5c-1',
    kind: declaration.kind,
    name: declaration.name,
    filePath: declaration.filePath,
    line: declaration.line,
    confidence,
    reason: reasons.join(' + '),
    ask,
    isAcronymCandidate: acronymCandidate,
    metadata: {
      exported: declaration.exported,
      memberCount: declaration.memberCount,
      unionLiteralCount: declaration.unionLiteralCount,
      hasTypeParameters: declaration.hasTypeParameters,
      isZodInferAlias: declaration.isZodInferAlias,
    },
  };
}

function buildDddAsk(declaration: DeclarationCandidate, confidence: TriggerConfidence, acronymCandidate = false): StructuredAsk {
  if (confidence === 'ambiguous' && acronymCandidate) {
    const acronym = declaration.name.toUpperCase();
    const expansion = KNOWN_ACRONYM_EXPANSIONS[acronym];
    return {
      question: `[5c-2 SDD trigger] acronym candidate '${declaration.name}' 검출. confidence: ambiguous. 다음 중 어느 것?`,
      recommended: 'A',
      options: [
        {
          id: 'A',
          label: `${acronym}${expansion ? ` (${expansion})` : ''} 약어로 ubiquitous-language 등록`,
          description: 'Recommended. canonical/acronym/fullName 으로 영구 기록하고 다음 detector 호출에서 재질문하지 않음',
        },
        {
          id: 'B',
          label: '다른 acronym 풀네임으로 등록',
          description: '사람이 다른 fullName/canonical term 을 직접 입력',
        },
        {
          id: 'C',
          label: '약어 아님 — forbidden-terms.xml 에 noise 로 등록',
          description: '향후 같은 token 은 silent skip',
        },
        {
          id: 'D',
          label: '다른 layer 로 routing',
          description: 'DDD term / SSOT helper 등 적절한 layer 로 보냄',
        },
        {
          id: 'E',
          label: 'skip / 직접 입력',
          description: '이번 호출만 넘기거나 사람이 처리 방식을 직접 지정',
        },
      ],
      notes: [
        'ADR 0019: ambiguous confidence → force + structured ask, silent skip 금지',
        `${declaration.name}: 3-letter acronym 후보`,
      ],
    };
  }

  return {
    question: `[5c-1 DDD trigger] 새 ${declaration.kind} '${declaration.name}' 검출. DDD ubiquitous-language 후보로 등록할까요?`,
    recommended: 'A',
    options: [
      {
        id: 'A',
        label: 'ubiquitous-language.xml 에 등록',
        description: `${declaration.name} 을 canonical domain term 후보로 기록`,
      },
      {
        id: 'B',
        label: '기존 term 의 alias 로 등록',
        description: '이미 같은 개념이 있으면 alias 로 연결',
      },
      {
        id: 'C',
        label: 'domain 용어 아님, 제외',
        description: '기술 타입 또는 구현 세부사항으로 분류',
      },
      {
        id: 'D',
        label: '직접 입력',
        description: '사람이 canonical term/정의/처리 방식을 직접 지정',
      },
    ],
  };
}

function countTypeMembers(typeNodeText: string): number {
  const objectMatch = typeNodeText.match(/^\s*\{([\s\S]*)\}\s*$/);
  if (!objectMatch) return 0;
  return objectMatch[1]
    .split(/[;\n]/)
    .map((item) => item.trim())
    .filter((item) => item && !item.startsWith('//')).length;
}

function countUnionLiterals(typeNodeText: string): number {
  return (typeNodeText.match(/['"][^'"]+['"]/g) ?? []).length;
}

function isPascalCase(value: string): boolean {
  return /^[A-Z][A-Za-z0-9]*$/.test(value);
}