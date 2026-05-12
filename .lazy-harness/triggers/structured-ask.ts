import type {
  StructuredAskValidationIssue,
  StructuredAskValidationReport,
  TriggerCandidate,
  TriggerCrossLayerMap,
} from './types';

export function validateStructuredAsks(
  candidates: TriggerCandidate[],
  crossLayer?: TriggerCrossLayerMap,
): StructuredAskValidationReport {
  const issues: StructuredAskValidationIssue[] = [];
  for (const candidate of candidates) {
    issues.push(...validateStructuredAsk(candidate));
  }
  if (crossLayer && crossLayer.gaps.length > 0) {
    issues.push(...validateCrossLayerStructuredAsk(crossLayer));
  }
  return {
    criterionId: '5c-7',
    ok: issues.length === 0,
    checkedCandidates: candidates.length + (crossLayer && crossLayer.gaps.length > 0 ? 1 : 0),
    issues,
  };
}

export function validateStructuredAsk(candidate: TriggerCandidate): StructuredAskValidationIssue[] {
  const issues: StructuredAskValidationIssue[] = [];
  const prefix = {
    candidateName: candidate.name,
    candidateLayer: candidate.layer,
  } as const;

  if (!candidate.ask.question.trim()) {
    issues.push({ ...prefix, field: 'ask.question', message: 'question is required' });
  }
  const optionCount = candidate.ask.options.length;
  if (optionCount < 3 || optionCount > 5) {
    issues.push({ ...prefix, field: 'ask.options', message: `expected 3~5 options, got ${optionCount}` });
  }
  const optionIds = candidate.ask.options.map((option) => option.id);
  const duplicateIds = optionIds.filter((id, index) => optionIds.indexOf(id) !== index);
  if (duplicateIds.length > 0) {
    issues.push({ ...prefix, field: 'ask.options[].id', message: `duplicate option IDs: ${unique(duplicateIds).join(', ')}` });
  }
  if (!optionIds.includes(candidate.ask.recommended)) {
    issues.push({ ...prefix, field: 'ask.recommended', message: `recommended option '${candidate.ask.recommended}' is missing` });
  }
  for (const option of candidate.ask.options) {
    if (!/^[A-E]$/.test(option.id)) {
      issues.push({ ...prefix, field: 'ask.options[].id', message: `option ID '${option.id}' must be A-E` });
    }
    if (!option.label.trim()) {
      issues.push({ ...prefix, field: `ask.options.${option.id}.label`, message: 'option label is required' });
    }
  }
  const directInputOrSkip = candidate.ask.options.some((option) => /직접 입력|skip|제외|noise|대상 아님/.test(option.label));
  if (!directInputOrSkip) {
    issues.push({ ...prefix, field: 'ask.options', message: 'must include direct input, skip, exclude, or noise option' });
  }
  if (candidate.confidence === 'high' && candidate.ask.recommended !== 'A') {
    issues.push({ ...prefix, field: 'ask.recommended', message: 'high confidence candidates should recommend option A' });
  }
  if (candidate.confidence === 'ambiguous') {
    const forceGateText = `${candidate.ask.question} ${candidate.ask.notes?.join(' ') ?? ''} ${candidate.ask.options.map((option) => `${option.label} ${option.description ?? ''}`).join(' ')}`;
    if (!/ambiguous|애매|사람|force/i.test(forceGateText)) {
      issues.push({ ...prefix, field: 'ask', message: 'ambiguous candidates must surface force-gate wording' });
    }
  }
  return issues;
}

function validateCrossLayerStructuredAsk(crossLayer: TriggerCrossLayerMap): StructuredAskValidationIssue[] {
  const issues: StructuredAskValidationIssue[] = [];
  const prefix = {
    candidateName: 'cross-layer consistency map',
    candidateLayer: 'cross-layer' as const,
  };
  const optionIds = ['A', 'B', 'C', 'D'];
  if (crossLayer.criterionId !== '5c-5') {
    issues.push({ ...prefix, field: 'crossLayer.criterionId', message: `expected 5c-5, got ${crossLayer.criterionId}` });
  }
  if (optionIds.length < 3 || optionIds.length > 5 || !optionIds.includes('A')) {
    issues.push({ ...prefix, field: 'crossLayer.ask.options', message: 'cross-layer ask must expose 3~5 options with A recommended' });
  }
  if (crossLayer.gaps.length === 0) {
    issues.push({ ...prefix, field: 'crossLayer.gaps', message: 'cross-layer ask must be backed by at least one gap' });
  }
  return issues;
}

function unique<T>(items: T[]): T[] {
  return [...new Set(items)];
}
