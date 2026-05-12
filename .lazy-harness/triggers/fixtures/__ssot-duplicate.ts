export interface PatientDto {
  id: string;
  displayName: string;
}

export interface PatientRiskProfile {
  patientId: string;
  riskLevel: 'low' | 'medium' | 'high';
}

export function mapPatientToDto(patient: { id: string; firstName: string; lastName: string }): PatientDto {
  return {
    id: patient.id,
    displayName: `${patient.lastName}${patient.firstName}`,
  };
}

export const validatePatientRiskProfile = (profile: PatientRiskProfile): boolean => {
  return Boolean(profile.patientId && profile.riskLevel);
};

export const normalizeAppointmentStatus = (status: string): string => {
  return status.trim().toLowerCase();
};

export function calculateChecksum(input: string): number {
  return [...input].reduce((sum, char) => sum + char.charCodeAt(0), 0);
}
