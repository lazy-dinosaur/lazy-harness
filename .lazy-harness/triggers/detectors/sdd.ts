import { execFileSync } from 'node:child_process';
import {
  CallExpression,
  Node,
  Project,
  SourceFile,
  SyntaxKind,
  VariableDeclaration,
} from 'ts-morph';
import { compactSignature, normalizePath, splitIdentifierWords, unique } from '../common';
import {
  ACRONYM_LENGTH,
  DDD_INFERENCE_STOP_WORDS,
  DOMAIN_SEED_NOUNS,
  KNOWN_ACRONYM_EXPANSIONS,
  SHORT_ACRONYM_NOISE_WORDS,
  ZOD_HELPER_WORDS,
  canonicalAcronymDisplay,
  filterDddTermWords,
  filePathToDomainHint,
  hasKnownTerm,
  inferAmbiguousAcronyms,
  inferAmbiguousAcronymsFromObjectFields,
  inferMatchedDddTerms,
  isAcronymCandidate,
  isZodExpressionText,
} from './ddd';
import type { StructuredAsk, TriggerCandidate, TriggerConfidence } from '../types';

export interface ContractCandidate {
  kind: 'zod-schema' | 'trpc-procedure';
  name: string;
  filePath: string;
  line: number;
  exported: boolean;
  signature: string;
  operation?: 'query' | 'mutation' | 'subscription';
  inputSchema?: string;
  zodCall?: string;
  inferredDddTerms: string[];
  ambiguousAcronyms: string[];
}

export function extractContracts(sourceFile: SourceFile): ContractCandidate[] {
  const filePath = normalizePath(sourceFile.getFilePath());
  return [...extractZodSchemas(sourceFile, filePath), ...extractTrpcProcedures(sourceFile, filePath)];
}

function extractZodSchemas(sourceFile: SourceFile, filePath: string): ContractCandidate[] {
  const schemas: ContractCandidate[] = [];

  for (const declaration of sourceFile.getDescendantsOfKind(SyntaxKind.VariableDeclaration)) {
    const initializer = declaration.getInitializer();
    if (!initializer) continue;

    const zodCall = findZodCall(initializer);
    if (!zodCall) continue;

    const name = declaration.getName();
    const exported = isExportedVariableDeclaration(declaration);
    if (!exported && !/Schema$/i.test(name)) continue;

    schemas.push({
      kind: 'zod-schema',
      name,
      filePath,
      line: declaration.getStartLineNumber(),
      exported,
      signature: compactSignature(initializer.getText()),
      zodCall: getCallHead(zodCall),
      inferredDddTerms: inferDddTerms(name),
      ambiguousAcronyms: unique([
        ...inferAmbiguousAcronyms(name),
        ...inferAmbiguousAcronymsFromObjectFields(initializer.getText()),
      ]).sort(),
    });
  }

  return schemas;
}

function extractTrpcProcedures(sourceFile: SourceFile, filePath: string): ContractCandidate[] {
  const procedures: ContractCandidate[] = [];
  const seen = new Set<string>();

  for (const call of sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression)) {
    const operation = getTrpcOperation(call);
    if (!operation) continue;
    if (!call.getExpression().getText().includes('.input(')) continue;

    const name = getProcedureName(call) ?? `${operation}Procedure@${call.getStartLineNumber()}`;
    const inputSchema = getTrpcInputSchema(call);
    const ambiguousAcronyms = unique([
      ...inferAmbiguousAcronyms(name),
      ...(inputSchema ? inferAmbiguousAcronymsFromObjectFields(inputSchema) : []),
      ...inferAmbiguousAcronyms(filePathToDomainHint(filePath)),
    ]).sort();
    const candidate: ContractCandidate = {
      kind: 'trpc-procedure',
      name,
      filePath,
      line: call.getStartLineNumber(),
      exported: isInExportedDeclaration(call),
      signature: compactSignature(call.getText()),
      operation,
      inputSchema,
      inferredDddTerms: unique([...inferDddTerms(name), ...(inputSchema ? inferDddTerms(inputSchema) : [])]),
      ambiguousAcronyms,
    };
    const key = contractKey(candidate);
    if (!seen.has(key)) {
      seen.add(key);
      procedures.push(candidate);
    }
  }

  return procedures;
}

export function getPreviousContractKeys(project: Project, filePath: string, warnings: string[]): Set<string> {
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
    const previousSource = project.createSourceFile(`/.lazy-harness/.tmp/previous-contracts-${filePath.replace(/[^A-Za-z0-9_.-]/g, '-')}`, previousText, {
      overwrite: true,
    });
    for (const contract of extractContracts(previousSource)) {
      names.add(contractKey(contract));
    }
  } catch (error) {
    warnings.push(`Failed to parse HEAD contract version of ${filePath}: ${error instanceof Error ? error.message : String(error)}`);
  }

  return names;
}

export function contractKey(contract: ContractCandidate): string {
  return `${contract.kind}:${contract.name}:${contract.operation ?? ''}`;
}
export function toSddCandidate(
  contract: ContractCandidate,
  knownSddTerms: Set<string>,
  knownDddTerms: Set<string>,
  forbiddenTerms: Set<string>,
): TriggerCandidate | null {
  const registryKeys = [contract.name, ...contract.inferredDddTerms].map((item) => item.toLowerCase());
  if (registryKeys.some((key) => knownSddTerms.has(key))) return null;

  const dddReferenceTerms = getDddReferenceTerms(contract, knownDddTerms).filter((term) => !hasKnownTerm(forbiddenTerms, term));
  const ambiguousDddTerms = unique([
    ...contract.ambiguousAcronyms.filter((term) => !hasKnownTerm(knownDddTerms, term) && !hasKnownTerm(forbiddenTerms, term)),
    ...dddReferenceTerms
      .filter((term) => !hasKnownTerm(knownDddTerms, term) && !hasKnownTerm(forbiddenTerms, term) && isAcronymCandidate(term))
      .map((term) => canonicalAcronymDisplay(term)),
  ]).sort();
  const missingDddTerms = dddReferenceTerms.filter((term) => !hasKnownTerm(knownDddTerms, term) && !isAcronymCandidate(term));
  const matchedDddTerms = unique([
    ...dddReferenceTerms.filter((term) => hasKnownTerm(knownDddTerms, term)),
    ...inferMatchedDddTerms(contract.signature, knownDddTerms),
  ]).sort();
  const crossRef = {
    ddd: {
      missing: missingDddTerms,
      matched: matchedDddTerms,
      ambiguous: ambiguousDddTerms,
    },
  };
  const confidence = getSddConfidence(contract, ambiguousDddTerms);
  const reasonParts = [contract.kind === 'zod-schema' ? 'Zod contract signature' : `tRPC ${contract.operation} input contract`];
  if (contract.exported) reasonParts.push('exported');
  if (missingDddTerms.length > 0) reasonParts.push(`DDD reference gap: ${missingDddTerms.join(', ')}`);
  if (ambiguousDddTerms.length > 0) reasonParts.push(`ambiguous acronym candidate: ${ambiguousDddTerms.join(', ')}`);

  return {
    layer: 'sdd',
    criterionId: '5c-2',
    kind: contract.kind,
    name: contract.name,
    filePath: contract.filePath,
    line: contract.line,
    confidence,
    reason: reasonParts.join(' + '),
    ask: buildSddAsk(contract, crossRef),
    isAcronymCandidate: isAcronymCandidate(contract.name),
    metadata: {
      exported: contract.exported,
      signature: contract.signature,
      operation: contract.operation,
      inputSchema: contract.inputSchema,
      zodCall: contract.zodCall,
      inferredDddTerms: unique([...dddReferenceTerms, ...ambiguousDddTerms]).sort(),
      ambiguousAcronyms: ambiguousDddTerms,
      ddd: crossRef.ddd,
      crossRef,
    },
  };
}

function getDddReferenceTerms(contract: ContractCandidate, knownDddTerms: Set<string>): string[] {
  return uniqueTermsByLower([
    ...contract.inferredDddTerms,
    ...(knownDddTerms.has(contract.name.toLowerCase()) ? [contract.name] : []),
  ].filter(isMeaningfulDddTerm)).sort();
}

function uniqueTermsByLower(terms: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const term of terms) {
    const key = term.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(term);
  }
  return result;
}


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

function getSddConfidence(contract: ContractCandidate, ambiguousDddTerms: string[] = []): TriggerConfidence {
  if (ambiguousDddTerms.length > 0) return 'ambiguous';
  if (contract.kind === 'trpc-procedure') return 'high';
  if (contract.exported && /z\.object\(/.test(contract.signature)) return 'high';
  if (contract.exported) return 'medium';
  return 'low';
}

function buildSddAsk(contract: ContractCandidate, crossRef: { ddd: { missing: string[]; matched: string[]; ambiguous?: string[] } }): StructuredAsk {
  const missingDddTerms = crossRef.ddd.missing;
  const ambiguousDddTerms = crossRef.ddd.ambiguous ?? [];
  if (ambiguousDddTerms.length > 0) {
    const primary = ambiguousDddTerms[0] ?? 'Acronym';
    const expansion = KNOWN_ACRONYM_EXPANSIONS[primary.toUpperCase()];
    const expansionText = expansion ? ` (${expansion})` : '';
    return {
      question: `[5c-2 SDD trigger] acronym candidate '${primary}' 검출. confidence: ambiguous. 다음 중 어느 것?`,
      recommended: 'A',
      options: [
        {
          id: 'A',
          label: `${primary.toUpperCase()}${expansionText} 약어로 ubiquitous-language 등록`,
          description: 'Recommended. acronym 을 canonical/alias domain term 으로 영구 기록하고 다음 detector 호출에서 재질문하지 않음',
        },
        {
          id: 'B',
          label: '다른 acronym 풀네임으로 등록',
          description: '사람이 fullName/canonical term 을 직접 입력',
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
      crossRef,
      notes: [
        'ADR 0019: ambiguous confidence → force + structured ask, silent skip 금지',
        ...ambiguousDddTerms.map((term) => `ambiguous acronym candidate: ${term}${KNOWN_ACRONYM_EXPANSIONS[term.toUpperCase()] ? ` (${KNOWN_ACRONYM_EXPANSIONS[term.toUpperCase()]})` : ''}`),
        ...missingDddTerms.map((term) => `DDD term '${term}' 미등록 — 함께 등록할까요? (Y/N)`),
        ...crossRef.ddd.matched.map((term) => `'${term}' noun 은 DDD 와 매칭됨 ✅`),
      ],
    };
  }

  const gapText = missingDddTerms.length > 0 ? ` DDD missing: ${missingDddTerms.join(', ')}.` : '';
  const ambiguousText = ambiguousDddTerms.length > 0 ? ` Ambiguous acronym: ${ambiguousDddTerms.join(', ')}.` : '';
  return {
    question: `[5c-2 SDD trigger] 새 ${contract.kind} '${contract.name}' 검출.${gapText}${ambiguousText} SDD spec 갱신 후보로 등록할까요?`,
    recommended: ambiguousDddTerms.length > 0 ? 'E' : 'A',
    options: [
      {
        id: 'A',
        label: 'SDD spec-language/spec-map 에 contract 등록',
        description: `${contract.name} 을 contract/procedure 후보로 기록하고 DDD cross-ref gap 을 함께 남김`,
      },
      {
        id: 'B',
        label: '기존 SDD contract 의 변경으로 연결',
        description: '이미 같은 spec 이 있으면 alias 또는 변경 이력으로 연결',
      },
      {
        id: 'C',
        label: 'DDD 용어 먼저 보강 후 재검토',
        description: 'missing DDD term 이 있으면 ubiquitous-language.xml routing 후보로 보냄',
      },
      {
        id: 'D',
        label: 'contract 아님, 제외 또는 직접 입력',
        description: '테스트/임시 validator 이거나 사람이 처리 방식을 직접 지정',
      },
      ...(ambiguousDddTerms.length > 0
        ? [{
            id: 'E',
            label: '약어 후보라서 사람 확인 후 DDD/SDD 등록',
            description: `${ambiguousDddTerms.join(', ')} 는 짧은 약어 후보이므로 자동 제외하지 않고 canonical term/alias 여부를 확인`,
          }]
        : []),
    ],
    crossRef,
    notes: [
      ...crossRef.ddd.missing.map((term) => `DDD term '${term}' 미등록 — 함께 등록할까요? (Y/N)`),
      ...ambiguousDddTerms.map((term) => `DDD term '${term}' 는 약어 후보 — 자동 noise 처리 금지, 사람 확인 필요 ⚠️`),
      ...crossRef.ddd.matched.map((term) => `'${term}' noun 은 DDD 와 매칭됨 ✅`),
    ],
  };
}


function findZodCall(node: Node): CallExpression | null {
  const calls = Node.isCallExpression(node) ? [node, ...node.getDescendantsOfKind(SyntaxKind.CallExpression)] : node.getDescendantsOfKind(SyntaxKind.CallExpression);
  return calls.find((call) => isZodCallExpression(call)) ?? null;
}

function isZodCallExpression(call: CallExpression): boolean {
  const expressionText = call.getExpression().getText();
  return /^z\.[A-Za-z_$][\w$]*(?:\([^)]*\))?(?:\.[A-Za-z_$][\w$]*)*$/.test(expressionText);
}

function getCallHead(call: CallExpression): string {
  return call.getExpression().getText().match(/^z\.[A-Za-z_$][\w$]*/)?.[0] ?? call.getExpression().getText();
}

export function isExportedVariableDeclaration(declaration: VariableDeclaration): boolean {
  return declaration.getFirstAncestorByKind(SyntaxKind.VariableStatement)?.getText().trimStart().startsWith('export ') ?? false;
}

function isInExportedDeclaration(node: Node): boolean {
  return node.getAncestors().some((ancestor) => {
    if (Node.isVariableStatement(ancestor) || Node.isFunctionDeclaration(ancestor) || Node.isClassDeclaration(ancestor)) {
      return ancestor.getText().trimStart().startsWith('export ');
    }
    return false;
  });
}

function getTrpcOperation(call: CallExpression): ContractCandidate['operation'] | null {
  const expression = call.getExpression();
  if (!Node.isPropertyAccessExpression(expression)) return null;
  const name = expression.getName();
  if (name === 'query' || name === 'mutation' || name === 'subscription') return name;
  return null;
}

function getProcedureName(call: CallExpression): string | null {
  const property = call.getFirstAncestor((ancestor) => Node.isPropertyAssignment(ancestor));
  if (property && Node.isPropertyAssignment(property)) return property.getName().replace(/^['"]|['"]$/g, '');

  const variable = call.getFirstAncestor((ancestor) => Node.isVariableDeclaration(ancestor));
  if (variable && Node.isVariableDeclaration(variable)) return variable.getName();

  return null;
}

function getTrpcInputSchema(call: CallExpression): string | undefined {
  const expression = call.getExpression();
  const calls = Node.isCallExpression(expression)
    ? [expression, ...expression.getDescendantsOfKind(SyntaxKind.CallExpression)]
    : expression.getDescendantsOfKind(SyntaxKind.CallExpression);

  const inputCall = calls.find((candidate) => {
    const candidateExpression = candidate.getExpression();
    return Node.isPropertyAccessExpression(candidateExpression) && candidateExpression.getName() === 'input';
  });

  return inputCall?.getArguments()[0]?.getText().trim();
}

function inferDddTerms(name: string): string[] {
  if (isZodExpressionText(name)) return [];

  const normalized = name
    .replace(/^['"]|['"]$/g, '')
    .replace(/(?:Schema|Input|Output|Request|Response|Procedure|Router|Contract|Dto|DTO)$/i, '');
  if (normalized.length <= 2) return [];
  if (isAcronymCandidate(normalized)) return [normalized.toUpperCase()];

  const nounWords = filterDddTermWords(splitIdentifierWords(normalized));
  if (nounWords.length === 0) return [];

  const term = nounWords.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join('');
  return isMeaningfulDddTerm(term) ? [term] : [];
}

function isZodExpressionText(value: string): boolean {
  return /\bz\s*\./.test(value) || /\bZ(?:od)?(?:Object|String|Number|Array|Enum|Boolean|Date|Union|Literal)\b/i.test(value);
}

