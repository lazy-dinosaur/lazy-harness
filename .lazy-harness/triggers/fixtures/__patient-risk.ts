export interface PatientRiskProfile {
  patientId: string;
  riskLevel: 'low' | 'medium' | 'high';
  reasons: string[];
}
