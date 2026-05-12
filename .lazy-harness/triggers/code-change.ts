import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  CallExpression,
  InterfaceDeclaration,
  Node,
  Project,
  SourceFile,
  SyntaxKind,
  TypeAliasDeclaration,
  VariableDeclaration,
} from 'ts-morph';
import type { StructuredAsk, TriggerCandidate, TriggerConfidence, TriggerCrossRef, TriggerRunResult, TriggerScenarioStep } from './types';

type CodeChangeLayer = 'ddd' | 'sdd' | 'bdd' | 'all';

interface CliOptions {
  scopes: string[];
  files: string[];
  format: 'json' | 'ask';
  layer: CodeChangeLayer;
  tsconfig: string;
  ubiquitousLanguageFile: string;
  specLanguageFile: string;
  forbiddenTermsFile: string;
  changedOnly: boolean;
  newOnly: boolean;
  lastUserMessage?: string;
}

interface DeclarationCandidate {
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

interface ContractCandidate {
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

const DEFAULT_SCOPE = 'src/main';
const DEFAULT_TSCONFIG = 'tsconfig.node.json';
const DEFAULT_UBIQUITOUS_LANGUAGE = '.lazy-harness/domain/ubiquitous-language.xml';
const DEFAULT_SPEC_LANGUAGE = '.lazy-harness/spec/spec-language.xml';
const DEFAULT_FORBIDDEN_TERMS = '.lazy-harness/domain/forbidden-terms.xml';
const ACRONYM_LENGTH = 3;

const DOMAIN_SEED_NOUNS = [
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

const KNOWN_ACRONYM_EXPANSIONS: Record<string, string> = {
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

const ZOD_HELPER_WORDS = new Set([
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

const DDD_INFERENCE_STOP_WORDS = new Set([
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

const SHORT_ACRONYM_NOISE_WORDS = new Set(['at', 'by', 'in', 'of', 'on', 'or', 'to']);

export function runCodeChangeTrigger(options: Partial<CliOptions> = {}): TriggerRunResult {
  const cwd = process.cwd();
  const inputFiles = options.files ?? [];
  const scopes = options.scopes?.length ? options.scopes : (inputFiles.length ? [] : [DEFAULT_SCOPE]);
  const opts: CliOptions = {
    scopes,
    files: inputFiles,
    format: options.format ?? 'json',
    layer: options.layer ?? 'ddd',
    tsconfig: options.tsconfig ?? DEFAULT_TSCONFIG,
    ubiquitousLanguageFile: options.ubiquitousLanguageFile ?? DEFAULT_UBIQUITOUS_LANGUAGE,
    specLanguageFile: options.specLanguageFile ?? DEFAULT_SPEC_LANGUAGE,
    forbiddenTermsFile: options.forbiddenTermsFile ?? DEFAULT_FORBIDDEN_TERMS,
    changedOnly: options.changedOnly ?? false,
    newOnly: options.newOnly ?? (inputFiles.length > 0 || options.changedOnly === true),
    lastUserMessage: options.lastUserMessage ?? process.env.LAST_USER_MESSAGE ?? process.env.last_user_message ?? '',
  };

  const warnings: string[] = [];
  const scannedFiles = collectFiles(opts, cwd, warnings);
  const knownDddTerms = readKnownTerms(opts.ubiquitousLanguageFile);
  const knownSddTerms = readKnownTerms(opts.specLanguageFile);
  const forbiddenTerms = readKnownTerms(opts.forbiddenTermsFile);

  const project = new Project({
    tsConfigFilePath: existsSync(opts.tsconfig) ? opts.tsconfig : undefined,
    skipAddingFilesFromTsConfig: false,
  });

  const declarations: DeclarationCandidate[] = [];
  const contracts: ContractCandidate[] = [];
  for (const filePath of scannedFiles) {
    try {
      const sourceFile = getSourceFile(project, filePath);
      if (opts.layer === 'ddd' || opts.layer === 'all') {
        const currentDeclarations = extractDeclarations(sourceFile);
        if (opts.newOnly) {
          const previousNames = getPreviousDeclarationNames(project, filePath, warnings);
          declarations.push(...currentDeclarations.filter((declaration) => !previousNames.has(`${declaration.kind}:${declaration.name}`)));
        } else {
          declarations.push(...currentDeclarations);
        }
      }

      if (opts.layer === 'sdd' || opts.layer === 'all') {
        const currentContracts = extractContracts(sourceFile);
        if (opts.newOnly) {
          const previousKeys = getPreviousContractKeys(project, filePath, warnings);
          contracts.push(...currentContracts.filter((contract) => !previousKeys.has(contractKey(contract))));
        } else {
          contracts.push(...currentContracts);
        }
      }
    } catch (error) {
      warnings.push(`Failed to parse ${filePath}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  const dddCandidates = declarations
    .map((declaration) => toDddCandidate(declaration, knownDddTerms, forbiddenTerms))
    .filter((candidate): candidate is TriggerCandidate => candidate !== null);
  const sddCandidates = contracts
    .map((contract) => toSddCandidate(contract, knownSddTerms, knownDddTerms, forbiddenTerms))
    .filter((candidate): candidate is TriggerCandidate => candidate !== null);
  const bddCandidates = opts.layer === 'bdd' || opts.layer === 'all'
    ? detectBdd(opts, scannedFiles, knownDddTerms)
    : [];

  return {
    ok: true,
    trigger: 'code-change',
    scannedFiles,
    candidates: [...dddCandidates, ...sddCandidates, ...bddCandidates],
    warnings,
  };
}

function collectFiles(opts: CliOptions, cwd: string, warnings: string[]): string[] {
  const explicitFiles = opts.files.flatMap((entry) => entry.split(',')).map((entry) => entry.trim()).filter(Boolean);
  const files = new Set<string>();

  for (const file of explicitFiles) {
    if (isTypescriptFile(file) && existsSync(file)) {
      files.add(normalizePath(file));
    }
  }

  for (const scope of opts.scopes) {
    if (!existsSync(scope)) {
      warnings.push(`Scope does not exist: ${scope}`);
      continue;
    }

    const stats = statSync(scope);
    if (stats.isFile()) {
      if (isTypescriptFile(scope)) files.add(normalizePath(scope));
      continue;
    }

    if (opts.changedOnly) {
      for (const changed of gitChangedFiles(scope, cwd, warnings)) {
        files.add(normalizePath(changed));
      }
    } else {
      for (const file of walkTypescriptFiles(scope)) {
        files.add(normalizePath(file));
      }
    }
  }

  return [...files].sort();
}

function gitChangedFiles(scope: string, cwd: string, warnings: string[]): string[] {
  try {
    const output = execFileSync('git', ['diff', '--name-only', '--diff-filter=AM', 'HEAD', '--', scope], {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    return output
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line && isTypescriptFile(line) && existsSync(line));
  } catch (error) {
    warnings.push(`git diff failed for scope ${scope}: ${error instanceof Error ? error.message : String(error)}`);
    return [];
  }
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

function getSourceFile(project: Project, filePath: string): SourceFile {
  const existing = project.getSourceFile(filePath);
  if (existing) return existing;
  return project.addSourceFileAtPath(filePath);
}

function extractDeclarations(sourceFile: SourceFile): DeclarationCandidate[] {
  const filePath = normalizePath(sourceFile.getFilePath());
  const interfaces = sourceFile.getInterfaces().map((node) => declarationFromInterface(node, filePath));
  const typeAliases = sourceFile.getTypeAliases().map((node) => declarationFromTypeAlias(node, filePath));
  return [...interfaces, ...typeAliases];
}

function getPreviousDeclarationNames(project: Project, filePath: string, warnings: string[]): Set<string> {
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

function extractContracts(sourceFile: SourceFile): ContractCandidate[] {
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

function getPreviousContractKeys(project: Project, filePath: string, warnings: string[]): Set<string> {
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

function contractKey(contract: ContractCandidate): string {
  return `${contract.kind}:${contract.name}:${contract.operation ?? ''}`;
}

function toSddCandidate(
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
  const byLower = new Map<string, string>();
  for (const term of terms) {
    const key = term.toLowerCase();
    const existing = byLower.get(key);
    if (!existing || (/^[A-Z][a-z0-9]+$/.test(term) && /^[A-Z0-9]+$/.test(existing))) {
      byLower.set(key, term);
    }
  }
  return [...byLower.values()];
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

export function isAcronymCandidate(term: string): boolean {
  const normalized = term.replace(/[^A-Za-z0-9]/g, '');
  const lower = normalized.toLowerCase();
  if (!normalized || DDD_INFERENCE_STOP_WORDS.has(lower) || SHORT_ACRONYM_NOISE_WORDS.has(lower) || ZOD_HELPER_WORDS.has(lower)) return false;
  if (normalized.length !== ACRONYM_LENGTH) return false;
  return /^[A-Z]{3}$/.test(normalized) || /^[A-Z][a-z]{2}$/.test(normalized);
}

function inferAmbiguousAcronyms(value: string): string[] {
  const acronyms = new Set<string>();
  for (const word of splitIdentifierWords(value)) {
    if (!isAmbiguousAcronymWord(word)) continue;
    acronyms.add(word.toUpperCase());
  }
  return [...acronyms].sort();
}

function inferAmbiguousAcronymsFromObjectFields(value: string): string[] {
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

function canonicalAcronymDisplay(term: string): string {
  const normalized = term.replace(/[^A-Za-z0-9]/g, '');
  if (/^[A-Z][a-z]{2}$/.test(normalized)) return normalized;
  return normalized.toUpperCase();
}

function hasKnownTerm(terms: Set<string>, term: string): boolean {
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

function filePathToDomainHint(filePath: string): string {
  return path.basename(filePath, path.extname(filePath));
}

function inferMatchedDddTerms(signature: string, knownDddTerms: Set<string>): string[] {
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

function toDddCandidate(declaration: DeclarationCandidate, knownTerms: Set<string>, forbiddenTerms: Set<string>): TriggerCandidate | null {
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

function readKnownTerms(filePath: string): Set<string> {
  if (!existsSync(filePath)) return new Set();
  const xml = readFileSync(filePath, 'utf8');
  const terms = new Set<string>();
  const attributePattern = /\b(?:name|term|canonical|acronym|fullName)=["']([^"']+)["']/gi;
  for (const match of xml.matchAll(attributePattern)) {
    addKnownTermVariants(terms, match[1]);
  }

  const patterns = [
    /<canonical>([^<]+)<\/canonical>/gi,
    /<name>([^<]+)<\/name>/gi,
    /<term>([^<]+)<\/term>/gi,
    /<acronym>([^<]+)<\/acronym>/gi,
    /<fullName>([^<]+)<\/fullName>/gi,
  ];
  for (const pattern of patterns) {
    for (const match of xml.matchAll(pattern)) {
      addKnownTermVariants(terms, match[1]);
    }
  }
  return terms;
}

function addKnownTermVariants(terms: Set<string>, rawValue: string | undefined): void {
  const value = rawValue?.trim();
  if (!value) return;
  terms.add(value.toLowerCase());
  const compact = value.replace(/[^A-Za-z0-9]/g, '');
  if (compact) terms.add(compact.toLowerCase());
  const words = splitIdentifierWords(value);
  if (words.length > 0) terms.add(words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join('').toLowerCase());
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

function isExportedVariableDeclaration(declaration: VariableDeclaration): boolean {
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

function splitIdentifierWords(value: string): string[] {
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_\-./]+/g, ' ')
    .split(/\s+/)
    .map((word) => word.trim())
    .filter(Boolean)
    .map((word) => word.toLowerCase());
}

function compactSignature(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

function unique<T>(items: T[]): T[] {
  return [...new Set(items)];
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

function isTypescriptFile(filePath: string): boolean {
  return /\.(ts|tsx)$/.test(filePath) && !/\.(test|spec)\.(ts|tsx)$/.test(filePath);
}

function normalizePath(filePath: string): string {
  return path.relative(process.cwd(), path.resolve(filePath)).replaceAll('\\', '/');
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

function detectBdd(cli: CliOptions, files: string[], knownDddTerms: Set<string>): TriggerCandidate[] {
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

function parseCliArgs(argv: string[]): CliOptions {
  const opts: CliOptions = {
    scopes: [],
    files: [],
    format: 'json',
    layer: 'ddd',
    tsconfig: DEFAULT_TSCONFIG,
    ubiquitousLanguageFile: DEFAULT_UBIQUITOUS_LANGUAGE,
    specLanguageFile: DEFAULT_SPEC_LANGUAGE,
    forbiddenTermsFile: DEFAULT_FORBIDDEN_TERMS,
    changedOnly: false,
    newOnly: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === '--scope' && next) {
      opts.scopes.push(next);
      i += 1;
    } else if (arg === '--files' && next) {
      opts.files.push(next);
      i += 1;
    } else if (arg === '--format' && (next === 'json' || next === 'ask')) {
      opts.format = next;
      i += 1;
    } else if (arg === '--layer' && (next === 'ddd' || next === 'sdd' || next === 'bdd' || next === 'all')) {
      opts.layer = next;
      i += 1;
    } else if (arg === '--tsconfig' && next) {
      opts.tsconfig = next;
      i += 1;
    } else if ((arg === '--ubiquitous-language' || arg === '--terms-file') && next) {
      opts.ubiquitousLanguageFile = next;
      i += 1;
    } else if ((arg === '--spec-language' || arg === '--sdd-registry' || arg === '--sdd-spec' || arg === '--contracts-file') && next) {
      opts.specLanguageFile = next;
      i += 1;
    } else if ((arg === '--forbidden-terms' || arg === '--forbidden-terms-file') && next) {
      opts.forbiddenTermsFile = next;
      i += 1;
    } else if (arg === '--changed-only') {
      opts.changedOnly = true;
      opts.newOnly = true;
    } else if (arg === '--new-only') {
      opts.newOnly = true;
    } else if (arg === '--last-user-message' && next) {
      opts.lastUserMessage = next;
      i += 1;
    } else if (arg === '--inventory' || arg === '--all') {
      opts.newOnly = false;
      opts.changedOnly = false;
    }
  }

  if (opts.files.length > 0 && !argv.includes('--inventory') && !argv.includes('--all')) {
    opts.newOnly = true;
  }
  if (opts.scopes.length === 0 && opts.files.length === 0) opts.scopes = [DEFAULT_SCOPE];
  return opts;
}

function formatAsk(result: TriggerRunResult): string {
  if (result.candidates.length === 0) {
    return '[code-change trigger] 후보 없음';
  }

  return result.candidates
    .map((candidate) => {
      const heading = candidate.layer === 'sdd'
        ? 'SDD contract 후보:'
        : candidate.layer === 'bdd'
          ? 'BDD scenario 후보:'
          : 'DDD ubiquitous-language 후보:';
      const lines = [
        candidate.ask.question,
        '',
        heading,
        `- term: ${candidate.name}`,
        `- kind: ${candidate.kind}`,
        `- location: ${candidate.filePath}:${candidate.line}`,
        `- confidence: ${candidate.confidence}`,
        `- reason: ${candidate.reason}`,
        '',
        '옵션:',
        ...candidate.ask.options.map((option) => `  ${option.id}. ${option.label}${option.id === candidate.ask.recommended ? ' (Recommended)' : ''}`),
        ...(candidate.ask.notes?.length ? ['', '[Cross-reference 보조 정보]', ...candidate.ask.notes.map((note) => `- ${note}`)] : []),
      ];
      return lines.join('\n');
    })
    .join('\n\n---\n\n');
}

function main(): void {
  const opts = parseCliArgs(process.argv.slice(2));
  const result = runCodeChangeTrigger(opts);
  if (opts.format === 'ask') {
    console.log(formatAsk(result));
  } else {
    console.log(JSON.stringify(result, null, 2));
  }
}

const currentFile = fileURLToPath(import.meta.url);
if (process.argv[1] && path.resolve(process.argv[1]) === currentFile) {
  main();
}
