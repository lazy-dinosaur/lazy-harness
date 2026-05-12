import { execFileSync } from 'node:child_process';
import { Node, Project, SourceFile } from 'ts-morph';
import { compactSignature, normalizePath, splitIdentifierWords } from '../common';
import {
  DOMAIN_SEED_NOUNS,
  classifyNounWord,
  filePathToDomainHint,
  hasKnownTerm,
} from './ddd';
import { isExportedVariableDeclaration } from './sdd';
import type { StructuredAsk, TriggerCandidate, TriggerConfidence, TriggerCrossRef } from '../types';

export interface SsotUtilityCandidate {
  kind: 'helper' | 'mapper' | 'validator' | 'normalizer' | 'formatter' | 'parser';
  name: string;
  filePath: string;
  line: number;
  exported: boolean;
  signature: string;
  domainHint?: string;
}

export function extractSsotUtilities(sourceFile: SourceFile): SsotUtilityCandidate[] {
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

export function getPreviousSsotKeys(project: Project, filePath: string, warnings: string[]): Set<string> {
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

export function ssotKey(utility: SsotUtilityCandidate): string {
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

export function toSsotCandidate(
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




