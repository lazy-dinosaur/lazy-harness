import { useState } from 'react';
import { z } from 'zod';

export interface ReferralIntakeRecord {
  referralId: string;
  patientId: string;
  requestedDepartment: string;
  triageStatus: 'draft' | 'ready' | 'sent';
}

export const referralIntakeSchema = z.object({
  referralId: z.string(),
  patientId: z.string(),
  requestedDepartment: z.string(),
  triageStatus: z.enum(['draft', 'ready', 'sent']),
});

export function ReferralIntakePatientSearch() {
  const [query, setQuery] = useState('');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [results, setResults] = useState<Array<{ id: string; label: string }>>([]);

  const handleQueryChange = (value: string) => {
    setQuery(value);
    setResults(value ? [{ id: 'patient-1', label: value }] : []);
  };

  const handlePatientClick = (id: string) => {
    setSelectedPatientId(id);
  };

  return (
    <form onSubmit={(event) => event.preventDefault()}>
      <input value={query} onChange={(event) => handleQueryChange(event.target.value)} placeholder="환자 의뢰 검색 자동완성" />
      <ul>
        {results.map((patient) => (
          <li key={patient.id}>
            <button type="button" onClick={() => handlePatientClick(patient.id)}>
              {patient.label}
            </button>
          </li>
        ))}
      </ul>
      <output>{selectedPatientId ? '의뢰 상세로 이동' : '환자 의뢰 자동완성 list 보임'}</output>
    </form>
  );
}

export function calculateReferralChecksum(input: string): number {
  return [...input].reduce((sum, char) => sum + char.charCodeAt(0), 0);
}

export const normalizeReferralStatus = (status: string): string => {
  return status.trim().toLowerCase();
};
