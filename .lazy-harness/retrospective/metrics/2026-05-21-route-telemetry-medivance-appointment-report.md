# Route Telemetry vs Medivance Appointment Worktree — 1st Report

Date: 2026-05-21
Status: report + improvement plan
Scope: `/home/lazydino/dev/medivance.pr-dev-appointment-reservation-sheet`
Source route data: `.lazy-harness/logs/route-decisions.jsonl` in the worktree
Compared against: recent commits and current dirty diff in the same worktree

## Executive summary

The route telemetry is now collecting enough data to expose a real weakness: current routing mostly reflects the **user message text**, not the **actual changed files / commit risk**.

This means the current router is useful for capturing interaction-level ambiguity, but it can miss risk that is only visible from code changes, git diff, or commit metadata.

Most important finding:

> There may be high/medium-risk false negatives. The worktree contains recent commits and current dirty changes touching TRPC routers, Prisma schemas, permissions/auth, deletion behavior, dashboard/action workflows, and treatment-document flows, but route telemetry shows `highRisk = 0` and only 3 canonical captures out of 60 route samples.

Do **not** immediately weaken/strengthen heuristics blindly. The next improvement should add **evidence logging and diff-aware route analysis**.

## Data snapshot

### Route telemetry summary

From `/home/lazydino/dev/medivance.pr-dev-appointment-reservation-sheet`:

```text
totalRoutes: 60

intent:
  docs: 7
  investigation: 51
  fix: 2

scope:
  trivial: 6
  code-local: 40
  unknown: 12
  behavior: 2

risk:
  low: 45
  medium: 15
  high: 0

confidence:
  high: 6
  medium: 41
  low: 13

gateMode:
  none: 46
  option-gate: 13
  narrow-confirm: 1

recordSearchMode:
  none: 6
  recommended: 40
  required: 14

recordCaptureMode:
  none: 6
  candidate: 51
  canonical: 3

implementationMapTier:
  none: 18
  file-map: 40
  symbol-flow: 2

ratios:
  optionGate: 21.7%
  lowConfidence: 21.7%
  candidateCapture: 85.0%
  canonicalCapture: 5.0%
```

### Recent worktree commits inspected

Recent branch:

```text
pr/dev-appointment-reservation-sheet
```

Recent commits inspected:

```text
83f7d66e Feat: 치료 기록 삭제 버튼 추가
abe4649d Feat: 예약 복사 붙혀넣기 모드 추가
1e27518a Fix: 예약 우클릭 메뉴 아이콘 수정
4bd9e2dc Feat: 예약 우클릭 메뉴 추가
2c6a38a3 Feat: 예약셀 우클릭 상세 드롭다운 추가
a28f0f47 Fix: 기록지 액션 완료 기준 단순화
ebd2ed80 Fix: 예약 상세 치료기록 담당자 표시 수정
7665c719 Feat: 치료시트 담당자 색상 표시
249ed124 Feat: 예약 상세 상태액션 draft 선저장
051e382f Fix: 시트 기록지 필요 옵션 동작 수정
03b479f2 Fix: 예약·치료시트 치료기록 액션 동기화 복구
2961c7a4 Fix: 치료 회차를 선택일 기준으로 동적 재계산
```

Last 12 commits diffstat:

```text
28 files changed, 1652 insertions(+), 209 deletions(-)
notable paths:
  prisma/schema/schedule.prisma
  src/main/trpc/routers/appointment.ts (+926 net-heavy)
  src/renderer/src/screens/Appointment/**
  tests/integration/**
```

Current dirty diff at report time:

```text
20 files changed, 744 insertions(+), 63 deletions(-)
notable paths:
  docs/permissions-list.md
  prisma/schema/patient.prisma
  prisma/schema/user.prisma
  src/main/services/createAction.ts
  src/main/trpc/routers/action.ts
  src/main/trpc/routers/appointment.ts
  src/main/trpc/routers/treatmentDocument.ts
  src/renderer/src/contexts/auth/AuthProvider.tsx
  src/renderer/src/contexts/auth/types.ts
  src/renderer/src/screens/Setting/tabs/PermissionsTab/constants.ts
  src/renderer/src/screens/TreatmentDocument/TreatmentDocumentModal.tsx
  tests/integration/**
```

## Commit reclassification findings

Recent commit subjects + changed files were re-run through `lazy route` with `--changed-files`.

### Strong false-negative candidates

#### 1. `83f7d66e Feat: 치료 기록 삭제 버튼 추가`

Route result:

```text
intent: refactor
scope: code-local
risk: medium
gate: none
recordSearch: recommended
recordCapture: candidate
implMap: file-map
layers: [tdd]
```

Why this looks wrong:

- Subject includes `삭제` (delete) and a user-visible delete button.
- Files touch TRPC router + Appointment modal UI + test.
- Deletion behavior is at least behavior/contract/risk-sensitive.
- It should likely be `behavior` or `contract`, with `recordSearch: required`, `recordCapture: canonical`, `implMap: symbol-flow`, and probably `gate: narrow-confirm` or explicit destructive confirmation depending on data deletion semantics.

This is the clearest high/medium-risk false-negative candidate.

#### 2. Current dirty work touches permissions/auth/schema/TRPC but telemetry historically shows `highRisk = 0`

Dirty paths include:

```text
prisma/schema/patient.prisma
prisma/schema/user.prisma
src/renderer/src/contexts/auth/AuthProvider.tsx
src/renderer/src/contexts/auth/types.ts
src/renderer/src/screens/Setting/tabs/PermissionsTab/constants.ts
src/main/trpc/routers/action.ts
src/main/trpc/routers/treatmentDocument.ts
```

These path patterns should raise at least contract/ownership/security/permission evidence. Existing route telemetry cannot tell whether the corresponding user prompts were classified correctly because logs do not store evidence tags or changed-file snapshots.

Likely needed route behavior for such diffs:

```text
scope: contract or ownership
risk: medium/high depending on operation
recordSearch: required
recordCapture: canonical if confirmed behavior/permission contract changes
implMap: symbol-flow or full-graph
gate: narrow-confirm or option-gate for permission/source-of-truth ambiguity
```

### Medium-risk but gate-none cases

Telemetry found one actual route sample:

```text
line 25: len=381, intent=fix, scope=code-local, risk=medium, gate=none,
recordCapture=canonical, implMap=file-map, layers=[tdd]
```

Commit reclassification showed many fixes to TRPC/router/appointment workflows still become `code-local + gate none`. Gate-none may be OK for simple bug fixes, but the router should record evidence explaining why it did not escalate.

## Option-gate / low-confidence candidates

13 of 60 routes are `option-gate` and `lowConfidence`, mostly:

```text
scope: unknown
risk: medium
confidence: low
gate: option-gate
recordSearch: required
recordCapture: candidate
implMap: none
```

Notable issue:

- Many have `messageLength = 501`, suggesting payload truncation or a fixed hook extraction cap.
- Without raw messages or evidence tags, it is impossible to determine whether these were true ambiguity or false-positive gates.

## Logging gaps discovered

Current telemetry is not enough to diagnose false negatives reliably.

Missing fields:

```json
{
  "routeVersion": "1.1",
  "source": "response.completed | manual-route | commit-reclassify",
  "matchedSignals": [],
  "riskEvidence": [],
  "scopeEvidence": [],
  "gateReasonCode": "short-reference | high-risk | behavior | contract | ownership | unknown | none",
  "pathEvidence": [],
  "changedFileCount": 0,
  "changedFileKinds": [],
  "truncatedLikely": false,
  "commitSubjectHash": null
}
```

Especially important:

- risk evidence: delete/destructive, db/prisma/schema, auth/permission, release/deploy, TRPC/router, data mutation
- scope evidence: appointment/treatment-document UI, behavior keywords, contract/config/schema paths
- path evidence: changed files should influence route independently of user prompt text
- truncation flag: `messageLength == 501` should be treated as likely truncated

## Key diagnosis

The current router is too **message-centric**.

It should become **context-aware** in this order:

1. user message route,
2. changed files / git diff route,
3. recent commit route,
4. combined risk result.

The combined result should take the max risk/scope, not average it down.

Example desired rule:

```text
if message says trivial but changed files include prisma/schema or auth/permission/TRPC router:
  route must escalate to contract/ownership evidence,
  recordSearch required,
  at least medium risk,
  canonical capture if confirmed behavior/contract changed.
```

## Recommended plan

### Phase A — Improve telemetry before changing major heuristics

Implement evidence fields without storing raw messages:

- `routeVersion`
- `matchedSignals`
- `riskEvidence`
- `scopeEvidence`
- `pathEvidence`
- `gateReasonCode`
- `truncatedLikely`
- `changedFileCount`
- `changedFileKinds`

Acceptance:

- telemetry still stores no raw message,
- self-test validates evidence fields,
- route-summary reports top evidence counts,
- `messageLength == 501` is visible as truncation risk.

### Phase B — Add diff-aware route context

Enhance `response.completed` auto telemetry to include safe changed-file context where available, or add a separate command:

```bash
.lazy-harness/bin/lazy route-worktree --format=json --log
```

This command should inspect:

- `git diff --name-only`,
- optionally staged files,
- optionally recent commit range,
- path categories only, not file contents by default.

Acceptance:

- dirty Prisma/auth/permission/TRPC/router paths escalate route even if message is vague,
- no raw source content stored,
- telemetry has `source=worktree-route` or `context=dirty-files`.

### Phase C — Add commit reclassification report

Add command:

```bash
.lazy-harness/bin/lazy route-audit --commits=12 --format=md
```

It should:

- classify recent commit subjects + changed file paths,
- compare against route telemetry distribution,
- flag possible false negatives:
  - delete/destructive subject but gate none,
  - schema/auth/permission paths but risk low,
  - behavior-heavy UI paths but scope code-local,
  - TRPC/router + tests but only candidate/file-map.

Acceptance:

- the report flags `Feat: 치료 기록 삭제 버튼 추가` as a risk escalation candidate.

### Phase D — Heuristic adjustments after evidence

Only after A-C:

- escalate Korean destructive verbs (`삭제`, `제거`, `초기화`) better,
- classify `버튼`, `우클릭`, `드롭다운`, `모드`, `상세`, `표시` as behavior signals in Korean,
- classify `prisma/schema`, `AuthProvider`, `PermissionsTab`, `trpc/routers` as path-based contract/security signals,
- avoid over-gating short acknowledgements by using conversation/tool context or a low-impact acknowledgement bucket.

## Initial improvement priorities

1. **High-risk false-negative defense**: path/evidence logging + destructive Korean keyword handling.
2. **Changed-file aware route**: current dirty diff must affect route telemetry.
3. **Truncation visibility**: mark `messageLength == 501` as likely truncated.
4. **Feedback labels**: add lightweight route feedback for false-positive/false-negative labels.
5. **Gate tuning**: only after evidence proves which `unknown` gates are false positives.

## Do not do yet

- Do not reduce option-gate ratio just because it is 21.7%.
- Do not increase canonical captures globally just because candidate is 85%.
- Do not store raw user messages in telemetry.
- Do not make route telemetry canonical.
- Do not replace record-first/default-unknown/option-gate invariants.

## Conclusion

The first telemetry sample did its job: it showed that automatic collection works and surfaced a concrete design gap.

The router should not be judged only by message-level telemetry. Real risk lives in diffs. The next framework improvement should make route telemetry evidence-rich and diff-aware before changing safety heuristics.
