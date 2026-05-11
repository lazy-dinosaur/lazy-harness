// 의도적 multi-step UI flow
import { useState } from 'react';

export function PatientSearchAutocomplete() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Array<{ id: string; name: string }>>([]);
  const [selected, setSelected] = useState<{ id: string; name: string } | null>(null);

  const handleSearch = () => {
    // search logic
    setResults([]);
  };

  const handleSelect = (item: { id: string; name: string }) => {
    setSelected(item);
    // navigate to prescription screen
  };

  return (
    <form onSubmit={handleSearch}>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <ul>
        {results.map((r) => <li key={r.id} onClick={() => handleSelect(r)}>{r.name}</li>)}
      </ul>
      {selected ? <div>처방 화면으로 이동 준비</div> : null}
    </form>
  );
}
