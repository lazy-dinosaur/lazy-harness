# TDD — 최소 명확화 파일럿 source-audit 교정

Date: 2026-09-20
Status: active
Layer: TDD

## Rule digest

- Status: active
- Layer: TDD
- Scope: host-project
- Aliases:
  - minimal clarification source audit
  - 동일 payload attribution regression
- Applies when: `fragment-minimal-clarification-01`의 역사 결과를 재해석하거나 교정 assessment를 재생성할 때.
- Must: 실제 participant-visible `prompt + payload` 동일성을 먼저 판정하고, 동일 입력 차이를 intervention win/loss로 세지 않으며, required/allowed/forbidden/UNKNOWN을 분리하고, operation ambiguity와 사후 adjudication을 공개하고, 기존 raw/gold/assessment/report hash를 보존한다.

## Regression cases

1. **Identical payload:** Q01/E01/E05/E06/E07은 arm label과 bookkeeping을 제외한 실제 입력 hash가 같고 treatment 평가 불가다.
2. **Taxonomy separation:** required 밖의 source-supported extra는 allowed, 근거가 부족하면 UNKNOWN이며 자동 forbidden이 아니다. E03의 session restore는 직원 restore 변경과 무관해 forbidden으로 분리한다.
3. **Ambiguous operation:** E04 required ID recall은 채점하지만 `update|supersede|conflict-flag`가 유일하게 정해지지 않아 operation으로 승자를 고르지 않는다.
4. **Repair label versus text:** reviewer `repaired` 10건의 generation candidate→final text diff는 0건이고 original→final changed text는 12건이다.
5. **Historical immutability:** 기존 packet/run/generation/review/gold/grading/assessment/HTML 75개 파일은 sibling SHA-256 manifest와 일치해야 한다.
6. **Explicit denominator:** 전체12, intervention 평가 가능7, 동일 입력 평가 불가5, 평가 가능 중 방향성 F 개선1/회귀0/동률6을 별도 필드로 유지한다.

## Layer completeness matrix

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 지식/도메인 용어 정의를 바꾸지 않고 실험 판정만 교정한다. |
| SDD | 없음 | 제품/API/component contract 변경이 없다. |
| BDD | 없음 | 사용자-visible 제품 흐름 변경이 없다. |
| SSOT | 없음 | config/schema/env/ownership 변경이 없다. |

## Implementation map

- Source: `experiments/v2-agentic-wiki-fragment-01/fragment-minimal-clarification-01/source_audit.py`
  - `canonical_visible`: 실제 runner transport에 맞춰 `prompt + payload`만 canonicalize한다.
  - `impact_arm`: source taxonomy별 required recall과 allowed/forbidden/UNKNOWN extras를 분리한다.
  - `repair_audit`: generation candidate/final label/text 차이를 구별한다.
  - `hashes`: 기존 역사 산출물의 SHA-256 readback을 만든다.
- Test: `experiments/v2-agentic-wiki-fragment-01/fragment-minimal-clarification-01/test_source_audit.py`
- Outputs: `assessment-source-audit-v2.json`, `historical-sha256-source-audit-v2.json`, `.lazy-harness/evidence/v2-fragment-minimal-clarification-01-corrected.html`.
- Primary planning record: `.lazy-harness/planning/v2-vision-feasibility-research.md`의 “최소 명확화 SOURCE-BASED 평가 교정”.

## Evidence boundary

이 테스트는 오프라인 사후 평가의 내부 일관성과 역사 파일 불변을 보호한다. 새 corpus, 반복 실행, 독립 인간 검토, treatment 인과효과, adoption threshold를 검증하지 않는다. D06 targeted-prompt contamination은 유지·공개한다.

## Bounded confirmation regression — 2026-09-20

새 within-corpus 24-task/3-repeat confirmation은 `experiments/v2-agentic-wiki-fragment-01/fragment-minimal-clarification-confirmation-01/test_confirmation.py`로 보호한다. 참가자-visible hash와 repeat packet 고정, required/allowed/forbidden/UNKNOWN 분리, indeterminate operation 비채점, candidate→review 실제 text diff, 양팔 1,021 full-input no-truncation, 기존 75 historical artifact hash, cap/hold 불변을 검사한다. 사후 exact source audit가 `D04-F036-A05`의 substantive supersession을 serious source regression으로 잡았고, 이 실패를 지우는 재실행은 하지 않았다.

### Layer completeness matrix — confirmation

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 도메인 용어/규칙을 바꾸지 않고 동결 corpus 연구만 수행했다. |
| SDD | 없음 | 제품 API/component 계약 변경이 없다. |
| BDD | 없음 | 제품 사용자 흐름 변경이 없다. |
| SSOT | 없음 | config/schema/env/ownership 변경이 없다. |

## Purpose-aligned direct-understanding regression — 2026-09-20

`experiments/v2-agentic-wiki-fragment-01/fragment-minimal-clarification-purpose-01/test_preflight.py`는 새 bounded diagnostic의 source path/hash/line/quote fail-closed, missing-source negative fixture, `Reservation.notes` shared claim을 separate fields로 바꾸는 broader rewrite negative fixture, byte-equal text의 misleading repaired label, direct packet no-truncation/source 비노출, semantic all-of/any-of rubric, all-assigned 분모와 serious source regression0을 보호한다. 실제 결과는 ambiguity6 중 변경5/fallback1, control4, 참가자40회이며 기존 raw·gold·두 historical failure run은 유지한다. 광범위 scanner는 bounded artifact 밖을 건드리지 않기 위해 생략하고 focused regression과 standard validation만 수행한다.

### Layer completeness matrix — purpose diagnostic

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 corpus의 domain claim을 바꾸지 않고 referent answerability만 시험했다. |
| SDD | 없음 | 제품 API/component 계약 변경이 없다. |
| BDD | 없음 | 제품 사용자 흐름 변경이 없다. |
| SSOT | 없음 | config/schema/env/ownership 변경이 없다. |

## Independent role-capability regression — 2026-09-20

`experiments/v2-agentic-wiki-fragment-01/fragment-role-capability-01/test_preflight.py`는 역할별 40 fixture의 동결 hash/count, 실제 nonempty source path/hash/line/quote, missing-source fail case, shared claim을 separate field로 뒤집는 금지 rewrite, no-truncation/exact source payload, byte-equal unchanged control, required/allowed/forbidden/UNKNOWN 및 lifecycle operation 구분을 보호한다. `test_mock_lifecycle.py`는 disposable copy에서 deactivate 전 snapshot/history와 restore 후 text/active/revision, 원 fixture hash 불변을 검증하며 실제 DB/production에는 적용하지 않는다. 실제80 Luna medium 결과와 lifecycle fixture 4건의 operation-gold 결함은 원자료와 함께 보존하고 재실행으로 지우지 않았다.

### Layer completeness matrix — role capability

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 corpus의 domain 사실을 변경하지 않고 역할 능력만 측정했다. |
| SDD | 없음 | 제품 API/component/fragment-store draft contract를 변경하지 않았다. |
| BDD | 없음 | 제품 사용자 흐름 변경이 없다. |
| SSOT | 없음 | config/schema/env/ownership 변경이 없다. |

## Role-guideline developmental retest regression — 2026-09-20

`experiments/v2-agentic-wiki-fragment-01/fragment-role-capability-02/test_preflight.py`의 12 tests와 `test_mock_lifecycle.py` 1 test는 sibling revision의 frozen guideline/source/fixture/rubric/mutation hashes와 역할별8 case, source path/hash/line/quote/original, missing-source negative, source schema/fact 불변, multi-claim list와 coupled conditions, already-current/tentative lifecycle gold, reference ambiguity, clean-control 의도, role isolation, conflict taxonomy, historical fixture/rubric/raw/result hash, shared ledger baseline/cap/reserve/holds를 보호한다. participant 전에 13/13 통과했고 actual runner는 frozen hash 재검사와 full catalog sequential reservation preflight 뒤 80회만 실행했다. disposable lifecycle test만 deactivate/restore를 수행하며 production/DB는 건드리지 않는다.

사후 readback에서 `review-05`의 `해당 sheet`가 clean control이 아니고 일부 conflict assertion의 authority/replacement provenance가 불충분했음을 발견했다. 동결 fixture/rubric/output은 수정하지 않았고 `semantic-audit.json`에 source-adjudicated secondary를 분리했다. 따라서 이 회귀는 “audit가 완전했다”가 아니라 결함을 숨기지 않고 frozen mechanical 값과 함께 보존하는 계약까지 보호한다.

### Layer completeness matrix — role-guideline retest

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 corpus의 Medivance domain fact를 바꾸지 않는다. |
| SDD | 있음 | `.lazy-harness/spec/platform/v2-fragment-knowledge-store.md` §1.2에 역할별 작성/검수/재작성/충돌/lifecycle 계약을 추가했다. |
| BDD | 없음 | 제품 사용자-visible flow 변경이 없다. |
| SSOT | 없음 | config/schema/env/ownership 변경이 없다. |

## Experimental role-base request assembly regression — 2026-09-20

`experiments/v2-agentic-wiki-fragment-01/role-contract-foundation-01/test_request_builder.py`는 기존 `0.1.0-draft` hash/readback 보존과 새 `0.2.0-draft` common+role SYSTEM, exact controller/untrusted envelope serialization, version/hash receipt를 보호한다. review standalone은 candidate만 허용하고 SOURCE key를 fail-closed 거부하며 fidelity는 candidate+source를 요구한다. source ID/quote containment, per-assertion authority/time/scope/replacement provenance, controller-only lifecycle permissions, event permission key 거부, absent-source stage 경계, deterministic no-cross-feed review aggregation을 검사한다. 자연어 task/source의 의미를 이해하거나 prompt injection을 방지한다고 주장하지 않으며 broker/provider를 import·호출하지 않는다. 따라서 역할 의미 준수·pass-rate·production 안전 증거가 아니다.

### Layer completeness matrix — role-base foundation

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 source의 도메인 사실·용어를 바꾸지 않는다. |
| SDD | 있음 | fragment 역할 계약의 비생산 draft pointer를 spec §1.2에 연결했다. |
| BDD | 없음 | 제품 사용자-visible flow 변경이 없다. |
| SSOT | 없음 | config/schema/env/ownership 또는 installed-agent 설정 변경이 없다. |

### Implementation map — role-base foundation

- Contract source: preserved `role-contract-foundation-01/contracts/*-v0.1.0-draft.md` + proposed `*-v0.2.0-draft.md`, frozen by versioned `contract-manifest.json`.
- Exact contract delta/rationale: `v0.1.0-to-v0.2.0.diff`, `v0.2.0-rationale.md`.
- Request assembly: `request_builder.py::contract_material/build_request/aggregate_review`.
- Protection: `test_request_builder.py`.
- Traceability and evidence boundary: `traceability.json`, `README.md`.
- Primary planning capture: `.lazy-harness/planning/v2-vision-feasibility-research.md`의 “역할 기본지침 foundation 오프라인 checkpoint”.

## Candidate-set synthesis preflight regression — 2026-09-21

`experiments/v2-agentic-wiki-fragment-01/three-role-candidate-synthesis-preflight-01/test_preflight.py`의 10개 focused offline test는 frozen9-document source의 path/hash/line/quote, 이전 corrected retest+offline repair 295파일 hash, 역할별 정상·실패·애매 사례, Reader 6-candidate 필요 내용 종합, related supplied extra 비감점, 사실 모순·필요 내용 누락, source-document/event/candidate provenance 분리, 완료 증거 부재의 unknown 보존, ordinary domain noun과 unresolved demonstrative 구별, shown-rule operation 허용 대안, proposal≠approval/apply, unresolved 집계 제외, source-absent stage 격리, 실제 packet byte/conservative admission-unit/no truncation과 dispatch hard-fail을 보호한다. authored good/bad examples는 model run이 아니다. provider/participant/grader/retrieval 호출은 0이고 장부는 spent32.21421171/held2.04543422 및 unknown holds895/989를 유지한다.

### Layer completeness matrix — candidate-set synthesis preflight

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 source의 도메인 사실·용어를 바꾸지 않는다. |
| SDD | 있음 | draft spec §1.2/Implementation map에 후보집합 종합과 역할 provenance/단계 경계를 비생산 experimental pointer로 연결했다. |
| BDD | 없음 | 제품 사용자-visible 흐름을 변경하지 않는다. |
| SSOT | 없음 | config/schema/env/ownership/장부를 변경하지 않는다. |

### Implementation map — candidate-set synthesis preflight

- Protocol/contracts/schema: `protocol.json`, `contracts.json`, `schema.json`.
- Frozen-source fixture builder: `build_preflight.py` → `sources.json`, `fixtures.json`, `example-outputs.json`, `preservation-manifest.json`.
- Scoring/interface: `scorer.py`, `runner_interface.py` → `preflight.json`; runner dispatch는 의도적으로 hard-fail한다.
- Protection: `test_preflight.py`.
- Korean report: `.lazy-harness/evidence/v2-three-role-candidate-synthesis-preflight-01.html`.
- Primary planning capture: `.lazy-harness/planning/v2-vision-feasibility-research.md`의 “CURRENT V2 후보집합 종합 OFFLINE repair closure”.

## Candidate-set semantic scoring separation regression — 2026-09-21

`experiments/v2-agentic-wiki-fragment-01/three-role-candidate-synthesis-preflight-02-semantic-separation/test_semantic_separation.py`의 14개 focused offline test는 preflight-01 원본 12파일 hash 보존과 기계/의미 lane 분리를 보호한다. 같은 keyword의 반대 의미, 자유 paraphrase, false statement 반박, genuine unsupported claim, ordinary noun 대 unresolved pronoun, 복수 supplied evidence ID, quote integrity≠support, invalid adjudicator provenance, allowed operation+wrong rationale, no judgement, fixture-only judgement, incomplete/unresolved review, blind source 비노출을 구조적으로 검사한다. 테스트 fixture는 실제 judge 결과나 performance 표본이 아니며, semantic reliability를 주장하지 않는다.

### Layer completeness matrix — semantic scoring separation

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 source의 도메인 사실·용어를 바꾸지 않는다. |
| SDD | 있음 | 기계 검증과 explicit semantic adjudication/provenance/aggregation 계약을 spec experimental pointer에 추가했다. |
| BDD | 없음 | 제품 사용자-visible flow 변경이 없다. |
| SSOT | 없음 | config/schema/env/ownership/장부를 변경하지 않는다. |

### Implementation map — semantic scoring separation

- Protocol/schema: `three-role-candidate-synthesis-preflight-02-semantic-separation/{protocol.json,schema.json,fixture-examples.json}`.
- Validation/review/aggregation: `review_pipeline.py::{validate_mechanical,build_review_packet,validate_adjudication,evaluate,aggregate}`.
- Protection: `test_semantic_separation.py`.
- Preservation: `preservation-manifest.json`은 preflight-01 12파일 SHA-256을 고정한다.
- Korean report: `.lazy-harness/evidence/v2-three-role-semantic-scoring-separation-02.html`.
- Primary planning capture: `.lazy-harness/planning/v2-vision-feasibility-research.md`의 “CURRENT V2 의미 채점 분리 OFFLINE repair 02 closure”.

## Pilot03 contract repair regression — 2026-09-21

`experiments/v2-agentic-wiki-fragment-01/three-role-candidate-synthesis-pilot-03-contract-repair-04/test_contract_repair.py`는 선언형 operation lifecycle에서 instruction/schema/validator 일치, actual needs_review history/restore contradiction의 post-hoc mechanical 분류와 semantic pending, canonical target/alias, unchanged retain, concrete delta 없는 allowed update 거부, candidate 오류와 participant diagnosis 분리, trusted host request-hash binding과 swapped response 거부, blind source isolation, evidence-reference validity와 entailment 분리, missing judgement pending, keyword meaning heuristic 부재를 보호한다. actual requests1638–1661과 saved participant/review/manual adjudication, preflight02, spent32.22913631/held2.04543422 manifest를 readback한다. replay와 authored example은 새 reviewer/empirical result가 아니다.

### Layer completeness matrix — pilot03 contract repair

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 source의 도메인 사실·용어를 바꾸지 않는다. |
| SDD | 있음 | declarative lifecycle, review object, transport hash binding을 draft spec experimental pointer에 추가했다. |
| BDD | 없음 | 제품 사용자-visible 흐름을 변경하지 않는다. |
| SSOT | 없음 | config/schema/env/ownership/장부를 변경하지 않는다. |

### Implementation map — pilot03 contract repair

- Rules/validation/review/transport: `operation-lifecycle.json`, `repair.py`.
- Versioned fixtures and examples: `fixtures.json`.
- Preservation/replay/unresolved packets: `preservation-manifest.json`, `posthoc-replay.json`, `unresolved-review-packets.json`.
- Full request samples: `rendered/*.json`.
- Protection: `test_contract_repair.py`.
- Primary planning capture: `.lazy-harness/planning/v2-vision-feasibility-research.md`의 “CURRENT V2 pilot03 contract OFFLINE repair 04 closure”.

## THREE-role offline real-stage handoff adapter regression — 2026-09-22

`experiments/v2-agentic-wiki-fragment-01/tr-int-offline-08/test_adapter.py`의 11개 focused test는 실제 Reader file hash handoff, supplied3/selected1 구분, task-local fixture patch와 root-owned fixed assertions, success3 trace, nonzero/error/timeout의 별도 상태, tampered Reader hold, 실패 후 recorder/digester 부재, traversal/absolute/symlink/stale/cross-task 차단, prep byte/ledger 보존, T1/T2 requirement-following 한계, T3 fixture-only proposal, retain null rewrite `not_applicable`, Parent review render의 private oracle 비노출을 보호한다. scripted fixture 실행은 model/production empirical result나 semantic pass가 아니다.

### Layer completeness matrix — offline handoff adapter

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 source의 도메인 사실·용어를 바꾸지 않는다. |
| SDD | 있음 | actual stage hash handoff, failure hold, recorder/proposal/apply/semantic-pending 경계를 draft spec experimental pointer에 추가했다. |
| BDD | 없음 | 제품 사용자-visible flow나 production behavior를 바꾸지 않는다. |
| SSOT | 없음 | config/schema/env/ownership/ledger를 바꾸지 않는다. |

### Implementation map — offline handoff adapter

- Adapter/stage boundary: `tr-int-offline-08/{adapter.py,fixture_actor.py,root_validate.py}`.
- Preservation/actual traces: `preservation-manifest.json`, `runs/*`, `offline-evidence-index.json`, `evidence-capsule.json`.
- Review-only request rendering: `render_live_requests.py`; dispatch/provider branch 없음.
- Protection: `test_adapter.py`.
- Korean report: `report-ko.html`.
- Primary canonical closure: `.lazy-harness/planning/v2-vision-feasibility-research.md`의 “THREE 역할 실용 작업 handoff adapter OFFLINE closure”.

## T1 actual model-connected isolation regression — 2026-09-22

`experiments/v2-agentic-wiki-fragment-01/tr-int-live-09/test_live_integration.py`의 focused 5개 검사는 이전 sibling hash와 ledger baseline, 한 task/5-call/no-retry/no-apply protocol, gold/private expected-output 없는 render, 단일 `clinic_rules.py` patch allowlist와 path/context/stale 거부, bubblewrap network namespace·host-root 비가시·disposable-only writable·read-only root assertion mount를 보호한다. 실제 run은 Reader/Work 2회 뒤 model patch의 `*** End Patch`를 `PATCH_ROW_DENIED`로 거부했고 root 행동검사·Recorder·Digester·reviewer를 실행하지 않았다. offline good patch pass는 actual model patch success나 semantic result가 아니다.

### Layer completeness matrix — T1 live integration 09

| Layer | Independent semantic delta | 판단 |
|---|---|---|
| DDD | 없음 | 동결 일정 삭제 rule과 용어를 바꾸지 않는다. |
| SDD | 있음 | untrusted model patch의 strong isolation, strict admission, failure-stop 경계를 experimental pointer에 추가한다. |
| BDD | 없음 | production 사용자-visible flow를 변경하지 않는다. |
| SSOT | 없음 | route/catalog/ledger를 readback했지만 config·ownership·cap을 변경하지 않는다. |

### Implementation map — T1 live integration 09

- Request/render/live orchestration: `tr-int-live-09/{render_requests.mjs,run.mjs,protocol.json}`.
- Isolation and root-owned test: `tr-int-live-09/{sandbox_adapter.py,root_test_t1.py}`.
- Protection: `tr-int-live-09/test_live_integration.py`.
- Actual held evidence/report: `tr-int-live-09/{broker,responses,work-output.json,failure.json,evidence-capsule.json,report-ko.html}`.
- Primary closure: `.lazy-harness/planning/v2-vision-feasibility-research.md`의 “T1 실제 model-connected integration 09 — 실패 보존 closure”.
