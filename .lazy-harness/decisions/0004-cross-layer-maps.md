# ADR 0004 — Cross-Layer Map Containers (A: Full Mirror Pattern)

**Date**: 2026-05-10
**Status**: Accepted
**Deciders**: Lazydino
**Trigger**: 사용자 질문 "sdd 랑 bdd 그리고 tdd 도 맵이 필요하겠지??" — DDD 컨테이너 (Section 6.1) 에는 4 종 map 명시되어 있지만 SDD / BDD / TDD 에는 대응 map 없음 → gap.

## Context

framework-contract Section 6.1 는 DDD 컨테이너로 다음 4 종을 명시:

```
domain/
  domain-map.xml             entire domain landscape
  ubiquitous-language.xml    canonical terms
  bounded-contexts.xml       boundaries
  context-map.xml            context relations
  aggregates.xml             aggregate / entity / value object
```

반면 SDD (Section 6 Categories) 는 frontend/backend/data/integration/infra/platform 카테고리만 나열. landscape map / language / boundaries / relations 없음.

BDD (Section 13) 는 개별 scenario 표준만. scenario landscape 없음.

TDD 는 컨테이너만 명시. test ↔ spec ↔ regression 매핑 map 없음.

→ 4 layer 중 DDD 만 시야가 풍부, 나머지 3 개는 시야 결여 → 일관성 위반.

## Options Considered

| Option | 설명 | files | impact |
|---|---|---|---|
| A | Full mirror — DDD 패턴 그대로 SDD/BDD/TDD 각자 4 종 map 추가 | 12 | full consistency |
| B | 단일 master-map.xml (cross-layer) | 1 | requires TS generator |
| C | 하이브리드 A + B | 13 | M2 위험 |
| D | minimal — landscape 1 종씩 (3 개) | 3 | 일관성 부족 |

AI 초기 추천: D (이유: "lazy 답게 시작")

사용자 정정: ADR 0005 — "lazy" 는 개발자 effort minimization 이지 framework minimalism 이 아님. 따라서 평가 우선순위 (Principle 0.2 priority 1, 2, 3 = 완성도 + 일관성 + 사용자 lazy) 에 따라 **A 가 정답**.

## Decision

**A 채택**. 12 개 placeholder XML 컨테이너 생성.

```
spec/
  spec-map.xml             전체 SDD landscape (frontend + backend + data + ...)
  spec-language.xml        SDD 표준 용어 (alias 포함)
  spec-boundaries.xml      카테고리 간 책임 경계
  spec-relations.xml       카테고리 간 의존 관계

behavior/
  behavior-map.xml         전체 BDD scenario landscape
  scenario-language.xml    BDD 도메인 용어
  scenario-coverage.xml    화면 / 유스케이스 ↔ scenario 커버리지 매트릭스
  scenario-relations.xml   scenario 간 의존 (precondition / shared given)

tests/
  test-map.xml             전체 TDD landscape
  test-language.xml        test type 분류 (e2e / integration / unit / regression)
  test-coverage.xml        spec ↔ test 매핑
  test-protection-matrix.xml  test ↔ regression ↔ scenario 4 축 매핑
```

각 placeholder 는 빈 XML skeleton 으로 init 시 생성 (Empty-Container Tolerance #10 적용).

trigger 발동 시 content 가 채워짐:
- spec-map.xml ← 새 SDD entry 추가될 때마다 갱신
- behavior-map.xml ← 새 scenario 추가될 때마다 갱신
- test-coverage.xml ← post-impact hook 이 AST 분석으로 자동 갱신 (M3)
- scenario-coverage.xml ← BDD draft 시 자동 cross-reference (M2)

## Consequences

### Positive

- 4 layer 가 동등한 시야 보유 (DDD-style "한 눈에 보는" 시점이 SDD/BDD/TDD 에도)
- Conflict Resolution Protocol Step 1 (Search) 이 더 빨라짐 — 4 layer 의 map 부터 검색
- Drift detection 이 더 강력 (각 layer 가 자체 boundary / relation 갖고 있어 boundary 위반 즉시 감지)
- 사용자 lazy 강화: "어디 봐야 하지?" 질문이 사라짐 (각 layer map 이 entry point)

### Negative

- 초기 init 시 12 개 placeholder XML 생성 → 빈 컨테이너 noise 늘어남
- Empty-Container Tolerance (#10) 가 더 중요해짐 — doctor 가 "비어있음 = OK" 명시적으로 알아야 함

### Cascade

| Document | 영향 |
|---|---|
| `framework/framework-contract.md` Section 6.1 → 6.5 (확장) | 4 layer 모두 명시 (≈ 80 줄 추가) |
| `framework/framework-contract.md` Section 6 (SDD Categories) | landscape map 언급 추가 |
| `framework/framework-contract.md` Section 13 (BDD Standard) | scenario-coverage 언급 추가 |
| `scripts/init-lazy-harness.sh` | 12 placeholder XML skeleton 생성 추가 |
| `scripts/doctor.sh` | 12 placeholder 존재 확인 + 비어있음 OK 처리 |
| `decisions/0005-meaning-of-lazy.md` | 이 ADR 의 motivating reasoning |

## References

- 직전 Conflict Resolution Protocol 발동: 사용자 질문 "sdd 랑 bdd 그리고 tdd 도 맵이 필요하겠지?"
- Principle 0.2: priority 1 (완성도) > 2 (일관성) > 3 (lazy) > 4 (auto) > 5 (cost)
- Principle #6: Trigger-Based Growth (placeholder 는 trigger 가 채움)
- Principle #10: Empty-Container Tolerance (빈 컨테이너 = valid state)
- ADR 0005: Meaning of "lazy" (이 결정의 이론적 근거)

## Implementation map

- Status: `needs-review`
- Primary files:
  - `.lazy-harness/domain/domain-map.xml`, `.lazy-harness/spec/spec-map.xml`, `.lazy-harness/behavior/behavior-map.xml`, `.lazy-harness/tests/test-map.xml` — current map container examples.
  - `.lazy-harness/scripts/doctor.py` — XML parse validation.
- Key symbols:
  - `check_xml_parse` (`doctor.py`) — validates XML containers parse.
- Flow:
  1. Layer map containers exist for multiple layers.
  2. Doctor/self-test XML parse validates that containers remain parseable.
  3. Original 12 placeholder mirror/generator automation is historical and only partially represented now.
- Tests / protection:
  - `python3 .lazy-harness/scripts/self-test.py` and `doctor.py` parse all `.xml` files.
- Cross-layer links:
  - ADR: `.lazy-harness/decisions/0005-meaning-of-lazy.md`
- Machine index:
  - graph ids: `kg_adr0004_layer_maps_exist`, `kg_adr0004_xml_parse_protection`
  - generated index key: `pending`
