# schemas

Result schema (Principle #9 Unified Result Schema) + container XML schemas + generated index schemas.

Important generated index schemas:

- `implementation-index.schema.json` — derived implementation map cache.
- `context-index.schema.json` — derived record/source cache for record/profile/graph retrieval metadata.
- `context-tier-manifest.schema.json` — optional advisory context tier manifest shape for always/phase/task/optional pointer hints.
- `record-decision-packet.schema.json` — post-turn record-action Record Decision Packet.

## Trigger to fill

Schema change.

## Status

- Empty is valid (Principle #10 Empty-Container Tolerance)
- Will be filled when triggers fire (Principle #6 Trigger-Based Growth)
- Auto-audited on update (Principle #1.2 Drafting and Auditing)
