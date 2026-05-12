export type TriggerLayer = 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'ssot' | 'regression';

export type TriggerConfidence = 'low' | 'medium' | 'high' | 'ambiguous';

export interface StructuredAskOption {
  id: string;
  label: string;
  description?: string;
}

export interface StructuredAsk {
  question: string;
  recommended: string;
  options: StructuredAskOption[];
  crossRef?: Record<string, unknown>;
  notes?: string[];
}

export interface TriggerScenarioStep {
  given: string;
  when: string;
  then: string;
}

export interface TriggerCrossRef {
  ddd?: { matched: string[]; missing: string[]; ambiguous?: string[] };
  sdd?: { matched: string[]; missing: string[]; ambiguous?: string[] };
  bdd?: { matched: string[]; missing: string[]; ambiguous?: string[] };
}

export interface TriggerCandidate {
  layer: TriggerLayer;
  criterionId: string;
  kind: string;
  name: string;
  filePath: string;
  line: number;
  confidence: TriggerConfidence;
  reason: string;
  ask: StructuredAsk;
  isAcronymCandidate?: boolean;
  scenario?: TriggerScenarioStep;
  source?: 'natural-language' | 'ui-code' | 'hybrid' | 'ast';
  metadata?: Record<string, unknown>;
}

export interface TriggerCrossLayerGap {
  fromLayer: TriggerLayer;
  targetLayer: 'ddd' | 'sdd' | 'bdd' | 'ssot';
  term: string;
  candidateName: string;
  filePath: string;
  severity: 'gap' | 'ambiguous';
  reason: string;
}

export interface TriggerCrossLayerMap {
  criterionId: '5c-5';
  gaps: TriggerCrossLayerGap[];
  summary: Record<string, number>;
}

export interface TriggerRunResult {
  ok: boolean;
  trigger: string;
  scannedFiles: string[];
  candidates: TriggerCandidate[];
  crossLayer?: TriggerCrossLayerMap;
  warnings: string[];
}
