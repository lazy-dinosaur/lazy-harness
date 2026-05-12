import { useState } from 'react';

export function CrossLayerPatientAutocomplete() {
  const [query, setQuery] = useState('');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [results, setResults] = useState<Array<{ id: string; name: string }>>([]);

  const handleQueryChange = (value: string) => {
    setQuery(value);
    setResults(value ? [{ id: 'patient-1', name: value }] : []);
  };

  const handlePatientClick = (id: string) => {
    setSelectedPatientId(id);
  };

  return (
    <form onSubmit={(event) => event.preventDefault()}>
      <input value={query} onChange={(event) => handleQueryChange(event.target.value)} placeholder="환자 검색 자동완성" />
      <ul>
        {results.map((patient) => (
          <li key={patient.id}>
            <button type="button" onClick={() => handlePatientClick(patient.id)}>
              {patient.name}
            </button>
          </li>
        ))}
      </ul>
      <output>{selectedPatientId ? '처방 화면으로 이동' : '자동완성 list 보임'}</output>
    </form>
  );
}
