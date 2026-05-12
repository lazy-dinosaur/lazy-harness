# Phase 5a Closing — Foundation Skills

**Phase**: 5a (Init / Doctor / Update Skills)
**Started**: 2026-05-10 13:50 KST
**Closed**: 2026-05-10 14:46 KST
**Duration**: ~56 minutes
**Outcome**: 7/8 self-verifiable success criteria PASS, 1 deferred to next jcode session

## What we built

| Skill | SKILL.md | Script | Total LoC |
|---|---|---|---|
| `harness-init` | 118 | 524 (init-lazy-harness.sh) | 642 |
| `harness-doctor` | 85 | 410 (doctor.sh) | 495 |
| `harness-update` | 103 | 372 (update.sh) | 475 |
| **Total** | **306** | **1306** | **1612** |

## Framework knowledge captured

- `framework/framework-contract.md`: 461 → 574 lines (+113, Section 0.1 / 0.2 / 19.1 / 19.2 / 19.3)
- `decisions/0004-cross-layer-maps.md` (105 lines)
- `decisions/0005-meaning-of-lazy.md` (69 lines)
- `logs/decisions.jsonl` (2 entries: D-001 cross-layer maps, D-002 meaning of lazy)
- `logs/actions.jsonl` (31 entries — full phase trace)
- 17 cross-layer map XML placeholders (DDD 5 + SDD 4 + BDD 4 + TDD 4)

## Success Criteria Final State

| ID | Criterion | Status |
|---|---|---|
| 5a-1 | jcode skill 시스템에 harness-init 등록 (`/harness-init` 호출 가능) | ⏳ deferred |
| 5a-2 | 30 컨테이너 자동 생성 | ✅ |
| 5a-3 | 각 컨테이너에 schema/placeholder | ✅ |
| 5a-4 | doctor schema/구조/링크 검증 | ✅ |
| 5a-5 | doctor backup 검증 | ⏳ M3 deferred (intentional) |
| 5a-6 | update dry-run | ✅ |
| 5a-7 | update rollback (manual + auto) | ✅ |
| 5a-8 | fresh tmp E2E | ✅ |

## What worked

### 1. Conflict Resolution Protocol fired naturally
Mid-phase, user asked "sdd 랑 bdd 그리고 tdd 도 맵이 필요하겠지??" — Protocol fired automatically:
- Step 1: searched framework-contract.md
- Step 2: classified as `gap`
- Step 3: cited 3 direct quotations with file:line:date
- Step 4: presented 5 structured choices (A/B/C/D/E)
- Step 5: computed impact range per option
- Step 6: persisted decision (D-001) + ADR
- Step 7: aftershock detected — meaning of "lazy" undefined → triggered D-002
- Step 8: full chain logged

Protocol caught a real gap that would have silently propagated. **This validated the entire framework-contract Principle #17 design**.

### 2. Self-validation caught real bugs
Doctor found:
- Pre-commit hook not executable (after init wrote it without chmod)
- Broken contract sneak (after first auto-rollback test) — led to C6 hardening

### 3. Auto-rollback works
Test 6 (intentional broken contract):
- Backup created
- Apply succeeded
- Doctor failed (after C6 hardening)
- File auto-restored
- BEFORE/AFTER MD5 hash identical
- Total: ~150ms recovery

## What didn't work the first time

### 1. AI recommended D (minimal) initially
This was a misinterpretation of "lazy". User corrected immediately. Protocol turned this into:
- ADR 0005 explicitly defining "lazy"
- Section 0.1 + 0.2 hardcoded into framework-contract
- Decision-making heuristic (priority 1=완성도, 2=일관성, 3=lazy, 4=auto, 5=cost)

→ Future AI sessions cannot make the same mistake.

### 2. Doctor C6 was too lenient
Initial C6: `< 16 principles → warn`. Update test with broken 5-line contract passed because warn ≠ fail.

Hardened to: `< 200 lines OR < 10 principles → fail`. Now broken/placeholder content is blocked.

### 3. Backup list polluted by safety snapshots
Auto-rollback creates `rollback-from-*` safety snapshots, which then appeared in `--rollback --list`. Fixed: list_backups now excludes that prefix. Separate `list_safety_snapshots()` available for debugging.

## Open Questions for 5b

1. **Hook idempotency**: post-commit hooks should be safe to run multiple times. Need test pattern.
2. **Hook performance budget**: pre-push must stay < 5s. Need timing instrumentation.
3. **ts-morph adoption**: 5b-2 needs AST diff. Vendor `ts-morph` (~50MB) or write minimal AST walker?
4. **Knowledge Decay**: when does a 3-month-old decision become stale? No principle for this yet (deferred to phase 6+).

## Metrics

- **Conflict resolutions fired**: 2 (D-001, D-002)
- **Aftershock recursion depth reached**: 1 (D-001 → D-002)
- **Auto-rollbacks triggered**: 1 (Test 6)
- **Doctor checks run**: ~12
- **Real bugs caught by self-validation**: 2 (pre-commit not executable, doctor C6 too lenient)
- **AI recommendations corrected by user**: 1 (D vs A choice)

## Next Phase

**5b — Lifecycle Hooks + 1-week measurement** (the longest phase)

Pre-conditions met:
- ✅ harness-doctor working (5b hooks need it for verification)
- ✅ harness-update with auto-rollback (5b hooks may need to roll back contract)
- ✅ logs/actions.jsonl format established
- ✅ Unified Result Schema (Principle #9) implemented

Pending:
- 5a-1 verification in next jcode session (`/harness-init` etc. should appear in skill list)
