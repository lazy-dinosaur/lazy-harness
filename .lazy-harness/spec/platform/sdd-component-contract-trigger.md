# SDD Component Contract Trigger

Status: accepted
Layer: SDD
Date: 2026-05-14

## Purpose

SDD is triggered not only by backend contracts such as Zod schemas and tRPC procedures, but also by UI component/interface contracts.

When a change introduces or modifies exported component props, window controls, IPC-facing UI control contracts, or scroll/window-mode behavior contracts, the agent must treat it as an SDD candidate. TDD regression records may also be required, but TDD does not replace SDD.

## Rule

A component contract candidate exists when code exposes an exported React-style component with a props surface or interaction contract, for example:

- `ChatWindow`
- `WindowControls`
- `onClose`
- `useScrollBehavior`
- `initialScrollSettleMs`
- IPC/window-mode controls

This should produce an SDD trigger before the agent claims the work is complete.

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/triggers/detectors/sdd.ts` — extracts `component-contract` candidates from exported TSX components with props/interaction surfaces.
  - `.lazy-harness/triggers/fixtures/__window-controls-contract.tsx` — regression fixture for the `WindowControls` contract case.
  - `.lazy-harness/scripts/self-test.py` — locks the SDD fixture count and cross-layer SDD→DDD gaps.
- Key symbols:
  - `extractContracts` (`.lazy-harness/triggers/detectors/sdd.ts`) — now includes component contracts after Zod/tRPC contracts.
  - `extractComponentContracts` (`.lazy-harness/triggers/detectors/sdd.ts`) — detects exported React-style component contracts.
  - `WindowControls` (`.lazy-harness/triggers/fixtures/__window-controls-contract.tsx`) — fixture for window-control props and scroll behavior.
- Flow:
  1. `code-change.ts` scans changed TS/TSX files.
  2. SDD detector extracts Zod, tRPC, and component contracts.
  3. `layer-impact-gate.ts` maps SDD candidates to missing `.lazy-harness/spec` updates.
  4. Self-test fails if `WindowControls` is no longer detected as SDD.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py`
  - `python3 .lazy-harness/scripts/doctor.py --profile smoke`
- Ownership boundaries:
  - Owner/upstream: lazy-harness source repo.
  - This detector may identify SDD candidates; it must not auto-write host SDD records without the normal record update flow.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0018-cross-layer-cascade.md`
  - SDD: `.lazy-harness/spec/platform/implementation-map-standard.md`
  - Plan: `.lazy-harness/plans/timsquad-level-product-maturity-gap-closure.md`
- Machine index:
  - graph ids: `pending`
  - generated index key: `pending until implementation-index generator exists`
