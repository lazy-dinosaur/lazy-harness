import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  Node,
  Project,
  SourceFile,
  SyntaxKind,
  VariableDeclaration,
} from 'ts-morph';
import { compactSignature, isTypescriptFile, normalizePath, splitIdentifierWords } from './common';
import {
  DOMAIN_SEED_NOUNS,
  classifyNounWord,
  extractDeclarations,
  filePathToDomainHint,
  getPreviousDeclarationNames,
  hasKnownTerm,
  toDddCandidate,
  type DeclarationCandidate,
} from './detectors/ddd';
import {
  contractKey,
  extractContracts,
  getPreviousContractKeys,
  isExportedVariableDeclaration,
  toSddCandidate,
  type ContractCandidate,
} from './detectors/sdd';
import { detectBdd } from './detectors/bdd';
import { buildCrossLayerMap } from './cross-layer';
import { readKnownTerms } from './registries';
import { validateStructuredAsks } from './structured-ask';
import type {
  StructuredAsk,
  TriggerCandidate,
  TriggerConfidence,
  TriggerCrossLayerMap,
  TriggerCrossRef,
  TriggerRunResult,
  TriggerScenarioStep,
} from './types';

type CodeChangeLayer = 'ddd' | 'sdd' | 'bdd' | 'ssot' | 'all';

interface CliOptions {
  scopes: string[];
  files: string[];
  format: 'json' | 'ask';
  layer: CodeChangeLayer;
  tsconfig: string;
  ubiquitousLanguageFile: string;
  specLanguageFile: string;
  ssotRegistryFile: string;
  forbiddenTermsFile: string;
  changedOnly: boolean;
  newOnly: boolean;
  lastUserMessage?: string;
}

interface SsotUtilityCandidate {
  kind: 'helper' | 'mapper' | 'validator' | 'normalizer' | 'formatter' | 'parser';
  name: string;
  filePath: string;
  line: number;
  exported: boolean;
  signature: string;
  domainHint?: string;
}

const DEFAULT_SCOPE = 'src/main';
const DEFAULT_TSCONFIG = 'tsconfig.node.json';
const DEFAULT_UBIQUITOUS_LANGUAGE = '.lazy-harness/domain/ubiquitous-language.xml';
const DEFAULT_SPEC_LANGUAGE = '.lazy-harness/spec/spec-language.xml';
const DEFAULT_SSOT_REGISTRY = '.lazy-harness/ssot/registry.xml';
const DEFAULT_FORBIDDEN_TERMS = '.lazy-harness/domain/forbidden-terms.xml';

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
    ssotRegistryFile: options.ssotRegistryFile ?? DEFAULT_SSOT_REGISTRY,
    forbiddenTermsFile: options.forbiddenTermsFile ?? DEFAULT_FORBIDDEN_TERMS,
    changedOnly: options.changedOnly ?? false,
    newOnly: options.newOnly ?? (inputFiles.length > 0 || options.changedOnly === true),
    lastUserMessage: options.lastUserMessage ?? process.env.LAST_USER_MESSAGE ?? process.env.last_user_message ?? '',
  };

  const warnings: string[] = [];
  const scannedFiles = collectFiles(opts, cwd, warnings);
  const knownDddTerms = readKnownTerms(opts.ubiquitousLanguageFile);
  const knownSddTerms = readKnownTerms(opts.specLanguageFile);
  const knownSsotTerms = readKnownTerms(opts.ssotRegistryFile);
  const forbiddenTerms = readKnownTerms(opts.forbiddenTermsFile);

  const project = new Project({
    tsConfigFilePath: existsSync(opts.tsconfig) ? opts.tsconfig : undefined,
    skipAddingFilesFromTsConfig: false,
  });

  const declarations: DeclarationCandidate[] = [];
  const contracts: ContractCandidate[] = [];
  const ssotUtilities: SsotUtilityCandidate[] = [];
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

      if (opts.layer === 'ssot' || opts.layer === 'all') {
        const currentUtilities = extractSsotUtilities(sourceFile);
        if (opts.newOnly) {
          const previousKeys = getPreviousSsotKeys(project, filePath, warnings);
          ssotUtilities.push(...currentUtilities.filter((utility) => !previousKeys.has(ssotKey(utility))));
        } else {
          ssotUtilities.push(...currentUtilities);
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
  const ssotCandidates = ssotUtilities
    .map((utility) => toSsotCandidate(utility, knownSsotTerms, knownDddTerms, forbiddenTerms))
    .filter((candidate): candidate is TriggerCandidate => candidate !== null);
  const candidates = [...dddCandidates, ...sddCandidates, ...bddCandidates, ...ssotCandidates];
  const crossLayer = opts.layer === 'all' ? buildCrossLayerMap(candidates) : undefined;
  const structuredAskValidation = validateStructuredAsks(candidates, crossLayer);

  return {
    ok: structuredAskValidation.ok,
    trigger: 'code-change',
    scannedFiles,
    candidates,
    ...(crossLayer ? { crossLayer } : {}),
    structuredAskValidation,
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




function extractSsotUtilities(sourceFile: SourceFile): SsotUtilityCandidate[] {
  const filePath = normalizePath(sourceFile.getFilePath());
  const utilities: SsotUtilityCandidate[] = [];

  for (const fn of sourceFile.getFunctions()) {
    const name = fn.getName();
    if (!name) continue;
    const kind = classifySsotUtility(name);
    if (!kind) continue;
    utilities.push({
      kind,
      name,
      filePath,
      line: fn.getStartLineNumber(),
      exported: fn.isExported(),
      signature: compactSignature(fn.getText()),
      domainHint: inferSsotDomainHint(name, filePath),
    });
  }

  for (const declaration of sourceFile.getVariableDeclarations()) {
    const name = declaration.getName();
    const kind = classifySsotUtility(name);
    if (!kind) continue;
    const initializer = declaration.getInitializer();
    if (!initializer || !(Node.isArrowFunction(initializer) || Node.isFunctionExpression(initializer) || Node.isCallExpression(initializer))) continue;
    utilities.push({
      kind,
      name,
      filePath,
      line: declaration.getStartLineNumber(),
      exported: isExportedVariableDeclaration(declaration),
      signature: compactSignature(declaration.getText()),
      domainHint: inferSsotDomainHint(name, filePath),
    });
  }

  const seen = new Set<string>();
  return utilities.filter((utility) => {
    const key = ssotKey(utility);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function getPreviousSsotKeys(project: Project, filePath: string, warnings: string[]): Set<string> {
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
    const previousSource = project.createSourceFile(`/.lazy-harness/.tmp/previous-ssot-${filePath.replace(/[^A-Za-z0-9_.-]/g, '-')}`, previousText, {
      overwrite: true,
    });
    for (const utility of extractSsotUtilities(previousSource)) {
      names.add(ssotKey(utility));
    }
  } catch (error) {
    warnings.push(`Failed to parse HEAD SSOT version of ${filePath}: ${error instanceof Error ? error.message : String(error)}`);
  }

  return names;
}

function ssotKey(utility: SsotUtilityCandidate): string {
  return `${utility.kind}:${utility.name}`;
}

function classifySsotUtility(name: string): SsotUtilityCandidate['kind'] | null {
  if (/^(map[A-Z]|.*Mapper$|to[A-Z].*Dto$|from[A-Z])/.test(name)) return 'mapper';
  if (/^(validate[A-Z]|isValid[A-Z]|assert[A-Z]|.*Validator$)/.test(name)) return 'validator';
  if (/^(normalize[A-Z]|.*Normalizer$)/.test(name)) return 'normalizer';
  if (/^(format[A-Z]|.*Formatter$)/.test(name)) return 'formatter';
  if (/^(parse[A-Z]|.*Parser$)/.test(name)) return 'parser';
  if (/^(use[A-Z]|get[A-Z]|build[A-Z]|create[A-Z]|calculate[A-Z]|compute[A-Z]|.*Helper$)/.test(name)) return 'helper';
  return null;
}

function inferSsotDomainHint(name: string, filePath: string): string | undefined {
  const utilityWords = ['helper', 'mapper', 'validator', 'normalizer', 'formatter', 'parser', 'format', 'normalize', 'validate', 'assert', 'parse', 'build', 'create', 'calculate', 'compute', 'get', 'map', 'to', 'from', 'use', 'ssot', 'duplicate', 'known'];
  const words = splitIdentifierWords(`${name} ${filePathToDomainHint(filePath)}`)
    .filter((word) => !utilityWords.includes(word.toLowerCase()));
  const seed = words.find((word) => DOMAIN_SEED_NOUNS.some((noun) => noun.toLowerCase() === word.toLowerCase()));
  if (seed) return seed.charAt(0).toUpperCase() + seed.slice(1);
  const meaningful = words.find((word) => word.length > 3 && classifyNounWord(word.toLowerCase()) !== 'noise');
  return meaningful ? meaningful.charAt(0).toUpperCase() + meaningful.slice(1) : undefined;
}

function toSsotCandidate(
  utility: SsotUtilityCandidate,
  knownSsotTerms: Set<string>,
  knownDddTerms: Set<string>,
  forbiddenTerms: Set<string>,
): TriggerCandidate | null {
  if (hasKnownTerm(knownSsotTerms, utility.name)) return null;
  if (hasKnownTerm(forbiddenTerms, utility.name)) return null;

  const domainHint = utility.domainHint;
  const matchedDdd = domainHint && hasKnownTerm(new Set([...knownDddTerms, ...DOMAIN_SEED_NOUNS.map((term) => term.toLowerCase())]), domainHint)
    ? [domainHint]
    : [];
  const missingDdd = domainHint && matchedDdd.length === 0 && !hasKnownTerm(forbiddenTerms, domainHint)
    ? [domainHint]
    : [];
  const ambiguous = domainHint ? [] : [utility.name];
  const confidence = getSsotConfidence(utility, matchedDdd, missingDdd, ambiguous);
  const crossRef: TriggerCrossRef = {
    ddd: { matched: matchedDdd, missing: missingDdd, ambiguous },
  };

  const reasonParts = [`${utility.kind} utility candidate`];
  if (utility.exported) reasonParts.push('exported');
  if (domainHint) reasonParts.push(`domain hint: ${domainHint}`);
  if (missingDdd.length > 0) reasonParts.push(`DDD reference gap: ${missingDdd.join(', ')}`);
  if (ambiguous.length > 0) reasonParts.push('ambiguous domain ownership');

  return {
    layer: 'ssot',
    criterionId: '5c-4',
    kind: utility.kind,
    name: utility.name,
    filePath: utility.filePath,
    line: utility.line,
    confidence,
    reason: reasonParts.join(' + '),
    ask: buildSsotAsk(utility, crossRef),
    metadata: {
      exported: utility.exported,
      signature: utility.signature,
      domainHint,
      crossRef,
    },
  };
}

function buildSsotAsk(utility: SsotUtilityCandidate, crossRef: TriggerCrossRef): StructuredAsk {
  const domainHint = utility.domainHint ?? 'unknown-domain';
  const hasMissingDdd = (crossRef.ddd?.missing.length ?? 0) > 0;
  const hasAmbiguous = (crossRef.ddd?.ambiguous?.length ?? 0) > 0;
  return {
    question: `[5c-4 SSOT trigger] ${utility.kind} '${utility.name}' 검출. SSOT registry 에 등록/중복 여부를 확인할까요?`,
    recommended: hasAmbiguous || hasMissingDdd ? 'B' : 'A',
    options: [
      {
        id: 'A',
        label: `SSOT registry 에 '${utility.name}' 등록 (domain: ${domainHint})`,
        description: 'Recommended when helper/mapper/validator has clear domain ownership.',
      },
      {
        id: 'B',
        label: 'domain context 가 애매함 — force gate 로 사람에게 소유 context 확인',
        description: 'ADR 0019: ambiguous detection 은 silent skip 금지.',
      },
      {
        id: 'C',
        label: '이미 같은 책임의 helper 가 있음 — 기존 SSOT 로 routing',
        description: '중복 구현이면 새 helper 대신 기존 canonical utility 를 사용.',
      },
      {
        id: 'D',
        label: 'SSOT 대상 아님 — forbidden-terms.xml 에 utility noise 로 기록',
      },
      {
        id: 'E',
        label: '직접 입력 / skip',
      },
    ],
    crossRef,
    notes: [
      `kind=${utility.kind}`,
      `domainHint=${domainHint}`,
      `DDD matched=${crossRef.ddd?.matched.join(', ') || '(none)'}`,
      `DDD missing=${crossRef.ddd?.missing.join(', ') || '(none)'}`,
    ],
  };
}

function getSsotConfidence(
  utility: SsotUtilityCandidate,
  matchedDdd: string[],
  missingDdd: string[],
  ambiguous: string[],
): TriggerConfidence {
  if (ambiguous.length > 0) return 'ambiguous';
  if (missingDdd.length > 0) return 'medium';
  if (matchedDdd.length > 0 && utility.exported) return 'high';
  if (matchedDdd.length > 0) return 'medium';
  return 'low';
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
    ssotRegistryFile: DEFAULT_SSOT_REGISTRY,
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
    } else if (arg === '--layer' && (next === 'ddd' || next === 'sdd' || next === 'bdd' || next === 'ssot' || next === 'all')) {
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
    } else if ((arg === '--ssot-registry' || arg === '--ssot-registry-file') && next) {
      opts.ssotRegistryFile = next;
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

  const candidateText = result.candidates
    .map((candidate) => {
      const heading = candidate.layer === 'sdd'
        ? 'SDD contract 후보:'
        : candidate.layer === 'bdd'
          ? 'BDD scenario 후보:'
          : candidate.layer === 'ssot'
            ? 'SSOT utility 후보:'
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

  const crossLayerText = formatCrossLayerAsk(result.crossLayer);
  return crossLayerText ? `${candidateText}\n\n=== Cross-layer consistency map (5c-5) ===\n\n${crossLayerText}` : candidateText;
}

function formatCrossLayerAsk(crossLayer: TriggerCrossLayerMap | undefined): string {
  if (!crossLayer || crossLayer.gaps.length === 0) return '';
  const lines = [
    '[5c-5 Cross-layer trigger] layer 간 gap 이 검출되었습니다. 한 번에 정리할까요?',
    '',
    '요약:',
    ...Object.entries(crossLayer.summary).sort().map(([key, count]) => `- ${key}: ${count}`),
    '',
    'Gap 목록:',
    ...crossLayer.gaps.map((gap) => `- [${gap.severity}] ${gap.fromLayer} → ${gap.targetLayer}: ${gap.term} (${gap.candidateName}, ${gap.filePath})`),
    '',
    '옵션:',
    '  A. 관련 DDD/SDD/BDD/SSOT 후보를 통합 등록 ask 로 묶기 (Recommended)',
    '  B. DDD apex 부터 먼저 확정하고 나머지 layer 를 재계산',
    '  C. 특정 gap 은 intentional 로 기록',
    '  D. 직접 입력 / skip',
  ];
  return lines.join('\n');
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
