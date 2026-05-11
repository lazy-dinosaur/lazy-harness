export type TriggerLayer = 'ddd' | 'sdd' | 'bdd' | 'ssot';

export type TriggerConfidence = 'high' | 'medium' | 'low' | 'ambiguous';

export interface TriggerScenarioStep {
  given: string;
  when: string;
  then: string;
}

export interface TriggerScenario extends TriggerScenarioStep {
  steps?: TriggerScenarioStep[];
}

export interface TriggerAskOption {
  key: 'A' | 'B' | 'C' | 'D' | string;
  label: string;
  recommended?: boolean;
}

export interface TriggerCrossRef {
  ddd?: {
    matched: string[];
    missing: string[];
  };
  sdd?: {
    matched: string[];
    missing: string[];
  };
}

export interface TriggerAsk {
  question: string;
  recommended: string;
  options: TriggerAskOption[];
  crossRef?: TriggerCrossRef;
}

export interface TriggerCandidate {
  layer: TriggerLayer;
  criterionId: string;
  kind: string;
  name: string;
  source?: 'natural-language' | 'ui-code' | 'hybrid';
  file?: string;
  confidence: TriggerConfidence;
  scenario?: TriggerScenario;
  evidence: string[];
  ask: TriggerAsk;
}

export interface TriggerResult {
  candidates: TriggerCandidate[];
}
