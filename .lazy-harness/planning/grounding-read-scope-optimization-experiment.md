# Grounding 읽기 범위 최소화 실험 — exact-node drill 집중 모드

Status: active
Layer: Planning
Date: 2026-09-14
Authority: 사용자 옵션 게이트 확정 (읽기 범위 최소화 + 이 호스트 먼저 실험)

## Rule digest

- Status: active
- Layer: Planning
- Scope: framework-global (실험은 원본 dev checkout 국한)
- Aliases: focused drill, exact-node drill, grounding token 절감
- Applies when:
  - `lazy map <record-path>` 정확 경로 drill이 fuzzy 관련 노드 8개를 함께 반환해 토큰을 낭비할 때
- Must:
  - 정확 record path 조회는 해당 record 1개 + 그 record의 탐색 메타데이터(aliases/source/tests/referencedBy/digest 관련 record)만 반환
  - fuzzy 이웃 5개를 `Related records (compact)` 한 줄 항목(경로+제목+상태+대표 별칭 2개)으로 제공해 잘못 선택 감지 신호를 유지 — 이웃의 전체 메타데이터는 제외
  - 이웃 한 줄은 사용자가 필요한 이웃만 골라 drill 하도록 판단 가능한 의미(제목/상태/별칭)를 담아야 한다
  - keyword/feature-id/alias 조회는 기존 fuzzy 다중 결과를 그대로 유지
  - 읽기 빚 증거 탐지는 `lazy map` 외에 `record-map.ts` 직접 호출(bun/python3)도 인정한다
  - 게이트 차단 힌트는 신규 스코프(complete overview)와 재접지(기존 governing record drill, 저비용)를 구분해 안내한다
  - 검색·안전 의미는 불변: free-form 거부, complete overview 전체 목록, cues-only 경고 그대로
- Must not:
  - overview `--complete` 완전 목록을 줄이거나 gate hint를 약화하지 않는다 (ADR0049 완전 탐색 유지)
  - drill 결과에서 실제 탐색에 필요한 메타데이터를 제거하지 않는다
- Record completion: 공식 배포 승인 시 ADR 또는 목적별 SDD/TDD(`tests/purpose-scoped-retrieval.md`)로 승격 검토

## 배경

Task367 세션 비용 분석에서 grounding 표면 비용 확인: overview-complete 35,099 bytes(≈9k tokens) + drill 노드당 11,069~17,101 bytes. 특히 drill은 정확 경로 조회에도 fuzzy 매치 8개 record + graph rows + 전체 drill-down 후보를 반환했다. 사용자가 "읽기 범위 최소화 + 이 호스트 먼저 실험" 확정.

## 변경 (이 dev checkout, 미공개)

1. `.lazy-harness/scripts/record-map.ts` `buildRecordMap`: `looksLikeRecordPath(query)`이고 record path와 정확 일치하면 focused 분기 — records 1개(역참조 포함), features 0, exact 매치 graph rows만, drilldown은 해당 record에서만 구성. notes에 focused임과 fuzzy 재조회 방법 명시.
2. `.lazy-harness/scripts/self-test.py` `check_purpose_scoped_retrieval_cli`: focused 계약 regression 추가 (counts 1/0, Focused note, keyword fuzzy ≥2 유지).

## 측정

| 표면 | 변경 전 | 변경 후 |
|---|---:|---:|
| `lazy map .lazy-harness/ssot/reader-integrated-deployment-binding.md` | 11,069 B | 1,985 B (이웃 5개+별칭 포함) |
| `lazy map .lazy-harness/spec/platform/prompt-budget.md` | (fuzzy 동급 11k+) | 3,556 B |
| keyword/feature drill (`sync-install-update`) | 21,266 B | 21,266 B (불변) |
| overview `--complete` | 35,099 B | 불변 (의도적) |

정확 경로 drill 기준 약 70–82% 절감(이웃 신호 포함 상태). grounding 1회(overview 1 + drill 1–2) 기준 대략 15–35% 절감, 반복 drill이 많은 work unit일수록 큼.

## 검증

- `check_purpose_scoped_retrieval_cli` PASS (focused 신규 계약 + 이웃 compact/별칭 2개 제한 포함)
- `check_record_index_generator_phase3` PASS
- `check_retrieval_workflow_benchmark_cli` PASS
- `lazy check --files record-map.ts,self-test.py` PASS (2 files, 오류 0)

## 2차 실험 — 재접지 반복 비용 절감 (같은 세션)

원인 2건 확인: (a) 증거 탐지기 `LAZY_MAP_COMMAND_RE`가 `record-map.ts` 직접 호출(bun/python3)을 인식하지 못해, 같은 작업 중 실제 드릴을 했어도 게이트가 재차단됨(이번 세션에서 2회 발생). (b) 차단 힌트가 항상 complete overview(≈9k tokens)를 요구해, 이미 governing record를 아는 재접지에서 과잉 비용.

변경:
1. `check-read-debt-permit.py` `LAZY_MAP_COMMAND_RE`에 `scripts/record-map.ts` 직접 호출 형식 추가. `record-index.ts --write` 등 deterministic cache 배제는 기존 `DETERMINISTIC_PACKET_RE` 선행 체크로 유지.
2. 동일 helper 차단 힌트를 이중화: 신규 스코프는 `--overview --complete`, 이번 세션에서 이미 grounding한 work unit 재접지는 해당 record/feature drill(`lazy map <path>`) 안내. 증거 요구 자체는 완화 없음 — drill도 기존부터 증거로 인정되었고, 안내만 실제 필요 최소 경로로 교정.
3. `check_message_received_hook_context_injection`에 `record-map.ts` 직접 드릴/overview 증거 케이스 2건과 힌트 구문 2종 assertion 추가.

검증: `check_message_received_hook_context_injection` PASS, `check_read_debt_permit_generic_external_action` PASS, `lazy check --files check-read-debt-permit.py,self-test.py` PASS. 효과: 재차단 낭비 왕복 제거 + 재접지 1회 비용 9k→1~2k tokens.

## 정확도 검증 (전체)

1. 정확도 프로브(7개 실제 record 경로 + keyword): 전부 PASS — (a) exact record 경로/제목/상태 정확 반환, (b) 이웃 전부 실존(전체 overview 대조, 위조 0), (c) 자기 자신 미포함, (d) 이웃 전원 제목·상태 신호 보유, 별칭 ≤2, (e) keyword fuzzy 다중 결과 불변(records 8/features 1 동일).
2. 전체 표준 검증 `lazy validate --plan standard --files <3파일> --evidence-cache=off`: static 3파일 PASS + **full-self-test 90 checks / skipped 0 / 192.5s PASS** — map-first retrieval contract, message.received search-debt injection, read-debt guard, retrieval benchmark CLI 등 변경 계약 전부 포함 전 프레임워크 회귀 통과.
3. 배포 전 전체 회귀 1회 조건(정확도 답변 시 약속)은 이 검증으로 충족. 공식 배포 자체는 여전히 별도 승인.
- free-form 거부·`--query` 거부·overview 계약 기존 assertion 통과

## 경계

- 공식 main/릴리스/호스트 배포 미수행 — 효과 확인 후 별도 승인. Medivance/PWA/homepage 호스트에는 반영되지 않음.
- `self-test.py`의 `agent-owned-target-context-transition` expectation 라인은 Task367 이전부터 있던 기존 로컬 변경(unstaged)이며 이 실험과 무관.
- 미해결 후보(별결정): overview-complete 경로 압축(≈10–20%, drill copy-paste 신뢰성 트레이드오프), 승인 절차 일괄화.

## Implementation map

- `.lazy-harness/scripts/record-map.ts` — `buildRecordMap` focused exact-record branch (`sameTraversalKey`/`recordMatch`/`graphMatch` exact 필터 재사용)
- `.lazy-harness/scripts/self-test.py` — `check_purpose_scoped_retrieval_cli` focused/fuzzy regression
- 보호: `.lazy-harness/tests/purpose-scoped-retrieval.md` (신규 계약 승격 시 갱신 대상)
