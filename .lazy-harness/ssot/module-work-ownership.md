# SSOT — Module work ownership (who builds what before and after the connection contract)

Status: active
Layer: SSOT
Date: 2026-11-07
Related SSOT: `.lazy-harness/ssot/project-identity.md`, `.lazy-harness/ssot/monitoring-records-ownership.md`
Related contract: the module connection contract SDD being written by the lazy-harness contract session (`spec/platform/module-composition.md`, not yet on main when this record was written)

## Rule digest

- Status: active
- Layer: SSOT
- Scope: host-project
- Confidence: high
- Aliases:
  - 모듈 작업 소유
  - module work ownership
- Surface terms:
  - 모듈 저장소 작업을 다른 세션에 맡기지 마
  - 연결 규약 확정 전 구현 금지
- Applies when:
  - a session working on a module repository (knowledge, monitoring, later modules) considers declaration files, RPC servers, clients, adapters or other connection work
  - a session considers handing module-repository work to another session
- Must:
  - keep each module repository's work with that module's own session
  - let lazy-harness main only define and document the module connection contract
  - wait for the announced final contract commit before building module-side connection pieces (declaration file, JSON-RPC server, client, adapter)
  - adapt each module repository to the final contract in that module's session, with that session's user approval
- Must not:
  - hand module-repository work to the lazy-harness contract session or another module session
  - start module-side connection implementation before the contract is final

## User-confirmed statement

2026-11-07, the user through the lazy-harness contract session (LH-5), as a strong reproach: "너희는 연결 규약이 정해지기도 전에 모듈을 만들기 시작했어. lazy-harness main 저장소는 이제서야 모듈을 어떻게 연결할지 규약을 정하고 있어. 그러니 너희 모듈 작업은 너희가 알아서 해. 이 세션(LH-5)에 일을 맡기지 마." LH-5 then said it only defines and documents the contract in lazy-harness main and announces the commit when final; each module session fixes its own repository to it. The knowledge session's delegation of the knowledge declaration file / JSON-RPC stdio server / TS client draft to LH-5 was withdrawn the same day.

Record placement: user-approved option A — this SSOT alone in its own PR; `project-identity.md` is not edited here (its pending knowledge-session and contract-session sections are uncommitted elsewhere), and the pointer is added when the knowledge correction section lands.

## Implementation map

- Contract (owned by the lazy-harness contract session): `spec/platform/module-composition.md`, in progress — this record does not assume its content.
- Module repositories: `lazy-dinosaur/lazy-harness-knowledge` (knowledge session), `lazy-dinosaur/lazy-harness-monitoring` (monitoring session).
- Knowledge plan: branch `feature/g16-domain-subject` (worktree `lazy-harness.v2-g16`), its knowledge planning record (on that branch, not on main) (withdrawal recorded there).
- Exception path: if a module session believes cross-session help is needed, it asks its own user first; it does not assign the work.

## Rule placement

- Rule: module-repository work stays with each module session; lazy-harness main only defines the contract; no module-side connection build before the final contract.
- Scope: host-project (team-policy ownership boundary, ADR 0032 → SSOT)
- Primary record: this file
- Why not AGENTS.md: project ownership boundary, not a framework behaviour rule
- Why not local notes: every session (LH-1, LH-4, LH-5) must follow it
- Confirmation: user-confirmed
