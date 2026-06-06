# ADR 0008 — AST Contract Diff Strategy (5b-2 Deferred Decision)

**Date**: 2026-05-10
**Status**: **REVERSED by ADR 0013 (2026-05-10 same day)** — ts-morph 즉시 채택, 5c-2 로 통합
**Deciders**: Lazydino
**Trigger**: Phase 5b criterion 5b-2 — `post-impact hook 이 ts-morph AST diff 로 contract-history.xml 갱신`

> **Reverse 이유**: ADR 0013 에서 사용자 통찰로 5c 재정의 — Figma adapter 가 아니라 Code-Trigger Adapter. AST 가 5c 의 prerequisite 이라 1주 측정 안 기다리고 즉시 채택. 옛 5b-2a → 새 5c-2 로 elevate.

## Context

Phase 5b 의 7 criteria 중 5b-2 만 외부 의존성 (ts-morph) 필요. 나머지 (5b-1/3/4/5/7) 는 sh 만으로 구현 완료.

**ts-morph 가 필요한 이유**:
- TypeScript AST 비교 = 정확한 contract diff 추출 (signature 변경, 타입 변경, public/private 변경)
- regex / sed 로는 false positive / negative 너무 많음
- contract-history.xml 의 신뢰도 핵심

**ts-morph 도입 비용**:
- node_modules 무게 (~30MB ts-morph + typescript)
- 매 commit 시 TypeScript 재파싱 = 느려짐 (medivance src 5000 파일 추정 시 5~15 초)
- bun 환경이지만 ts-morph 호환은 됨 (검증 됨)
- learning curve: AST query API 익숙해질 시간

## Decision

**5b 에서는 ts-morph 도입하지 않는다. design 만 정착.**

**구체 plan**:

1. **이번 5b 에서**: `.lazy-harness/scripts/contract-diff.ts` placeholder 작성 (interface + TODO)
2. **5b-2 실제 구현**: M3 (5c) 또는 트리거가 명확해질 때
   - Trigger: 실제 contract drift 사고가 발생 + 사람이 수동 추적해서 시간 낭비
   - 또는 medivance 1주 사용 후 retrospective 에서 "contract drift 빈도 ≥ 주 3회" 확인
3. **임시 대체 (5b interim)**:
   - post-commit hook 이 src/ 변경 파일 list 만 logs/contract-touch.jsonl 에 기록
   - 사람이 필요할 때 수동으로 review
   - regex-based 추정 (e.g., `export.*function` count diff) 도 안 함 — false signal 방지

## Why defer

> "lazy" 의 발현 (ADR 0005): 개발자 노력 최소화 — 지금 필요하지 않은 도구를 미리 만들지 말 것.

3 가지 deferred reason:

1. **확실한 trigger 가 없음** — medivance 에서 contract drift 가 실제 문제인지 1주 측정 필요 (5b-6)
2. **수동 cost vs 자동화 cost 비교 안 됨** — 일단 사람이 git diff 로 보는 게 빠를 가능성
3. **ts-morph 도입 시 다른 변화 동반** — package.json 변경, husky chain 의 commit-msg 와 충돌 가능성, 빌드 시간 영향. 작은 결정 아님.

## What we DO commit to in 5b

- `contract-touch.jsonl` 만 기록 (path + line count diff, no AST)
- `.lazy-harness/scripts/contract-diff.ts` skeleton 작성 (interface 정의만)
- `manifests/skills.xml` 에 5b-2 status="deferred-to-5b-2a" 명시
- 5b retrospective 에서 "contract drift 가 실제 문제였는가?" 측정

## Skeleton interface (TS)

```typescript
// .lazy-harness/scripts/contract-diff.ts (5b 시점에는 placeholder)

export interface ContractDiff {
  path: string
  type: 'signature-change' | 'type-change' | 'visibility-change' | 'removal' | 'addition'
  before: string  // AST node text
  after: string
  riskTier: 'public-api' | 'internal' | 'test'
  confidence: 'high' | 'medium' | 'low'
}

// 5b-2a 에서 ts-morph 로 구현될 함수 (지금은 throw)
export async function diffContracts(
  fromSha: string,
  toSha: string,
  paths: string[]
): Promise<ContractDiff[]> {
  throw new Error('Not implemented — see ADR 0008. Deferred to 5b-2a (after medivance 1-week measurement).')
}
```

## Consequences

### Positive

- 5b 가 외부 의존 없이 완성 가능 (sh + jq only)
- 1주 실측 후 ts-morph 가 정말 필요한지 데이터로 결정
- contract drift 가 실제 자주 일어나지 않으면 영영 도입 안 해도 됨 (lazy)

### Negative

- contract-history.xml 이 5b 동안 비어있음 (수동 작성만 가능)
- 5b-2 가 5b success criteria 에서 partial completion → status="deferred-to-5b-2a"

### Cascade

- `planning/phase-5-plan.xml` 의 5b-2 status update
- `.lazy-harness/scripts/contract-diff.ts` skeleton 생성
- 5b retrospective 에 "5b-2 deferred — measure first" 명시
- Phase 5b 끝날 때 측정 결과 기준으로 5b-2a 시작 또는 영구 defer 결정

## References

- ADR 0005 — Meaning of Lazy (개발자 노력 최소화)
- Phase 5b plan: `.lazy-harness/planning/phase-5-plan.xml` 5b-2/5b-6
- Principle #11 (Trigger-Based Growth) — trigger 없으면 만들지 않음

## Implementation map

- Status: `verified`
- Primary files:
  - `.lazy-harness/scripts/contract-diff.ts` — placeholder/skeleton retained for deferred AST contract diff.
  - `.lazy-harness/decisions/0013-framework-external-dependency-invariant.md` — later ADR reverses/elevates parts of this decision.
- Key symbols:
  - `ContractDiff`, `diffContracts`, `summarizeTouchedContracts` (`contract-diff.ts`) — current skeleton and lightweight interim summary.
- Flow:
  1. ADR 0008 is explicitly marked reversed by ADR 0013.
  2. `contract-diff.ts` still matches the deferred skeleton shape and throws for `diffContracts`.
  3. Current active trigger work moved elsewhere; this map is verified as historical/deferred state only.
- Tests / protection:
  - No dedicated executable self-test for `contract-diff.ts`; source read confirms skeleton status.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0013-framework-external-dependency-invariant.md`
- Machine index:
  - graph ids: `kg_adr0008_contract_diff_skeleton`, `kg_adr0008_reversed_by_0013`
  - generated index key: `pending`
