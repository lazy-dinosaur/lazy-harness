import type { TriggerCandidate, TriggerCrossLayerGap, TriggerCrossLayerMap, TriggerCrossRef } from './types';

export function buildCrossLayerMap(candidates: TriggerCandidate[]): TriggerCrossLayerMap {
  const gaps: TriggerCrossLayerGap[] = [];
  for (const candidate of candidates) {
    const crossRef = getCandidateCrossRef(candidate);
    if (!crossRef) continue;

    for (const targetLayer of ['ddd', 'sdd', 'bdd'] as const) {
      const ref = crossRef[targetLayer];
      if (!ref) continue;
      for (const term of ref.missing ?? []) {
        gaps.push({
          fromLayer: candidate.layer,
          targetLayer,
          term,
          candidateName: candidate.name,
          filePath: candidate.filePath,
          severity: 'gap',
          reason: `${candidate.layer.toUpperCase()} '${candidate.name}' references missing ${targetLayer.toUpperCase()} '${term}'`,
        });
      }
      for (const term of ref.ambiguous ?? []) {
        gaps.push({
          fromLayer: candidate.layer,
          targetLayer,
          term,
          candidateName: candidate.name,
          filePath: candidate.filePath,
          severity: 'ambiguous',
          reason: `${candidate.layer.toUpperCase()} '${candidate.name}' has ambiguous ${targetLayer.toUpperCase()} ownership for '${term}'`,
        });
      }
    }
  }

  const dedupedGaps = dedupeCrossLayerGaps(gaps);
  const summary: Record<string, number> = {};
  for (const gap of dedupedGaps) {
    const key = `${gap.fromLayer}->${gap.targetLayer}:${gap.severity}`;
    summary[key] = (summary[key] ?? 0) + 1;
  }

  return {
    criterionId: '5c-5',
    gaps: dedupedGaps,
    summary,
  };
}

function getCandidateCrossRef(candidate: TriggerCandidate): TriggerCrossRef | null {
  const metadataCrossRef = candidate.metadata?.crossRef;
  if (isTriggerCrossRef(metadataCrossRef)) return metadataCrossRef;
  if (isTriggerCrossRef(candidate.ask.crossRef)) return candidate.ask.crossRef;
  return null;
}

function isTriggerCrossRef(value: unknown): value is TriggerCrossRef {
  if (!value || typeof value !== 'object') return false;
  return ['ddd', 'sdd', 'bdd'].some((key) => key in value);
}

function dedupeCrossLayerGaps(gaps: TriggerCrossLayerGap[]): TriggerCrossLayerGap[] {
  const seen = new Set<string>();
  return gaps.filter((gap) => {
    const key = `${gap.fromLayer}:${gap.targetLayer}:${gap.severity}:${gap.candidateName}:${gap.term}:${gap.filePath}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
