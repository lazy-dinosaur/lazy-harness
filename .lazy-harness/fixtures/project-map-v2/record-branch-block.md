# Fixture — Project Map branch block

This fixture shows how a canonical layer record stores Project Map V2 metadata.

## Project Map branch

- Anchor: `chat-window-patient-sharing`
- Branch: `facts`
- Node: `patient-sharing-identity-rule`
- Primary: `facts`
- Facets: `DDD`, `SSOT`
- Edges:
  - `chat-window-patient-sharing --has-fact--> patient-sharing-identity-rule`
  - `patient-sharing-identity-rule --related-to--> chat-patient-sharing-api-contract`
- Related records:
  - `.lazy-harness/behavior/chat-window-patient-sharing.md`
  - `.lazy-harness/spec/chat-patient-sharing-api.md`
  - `.lazy-harness/tests/chat-patient-sharing.md`
  - `.lazy-harness/ssot/patient-sharing-ownership.md`

## Fixture note

The example names are illustrative. Host-specific facts must be confirmed before becoming canonical records.
