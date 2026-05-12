export function formatPatientName(patient: { firstName: string; lastName: string }): string {
  return `${patient.lastName}${patient.firstName}`;
}
