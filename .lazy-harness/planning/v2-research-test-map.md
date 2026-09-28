# V2 연구 영역과 시험 지도

최신 직접 비교는 [pilot02 최종 결과](../evidence/v2-recording-method-pilot02-result.md)와 [통합 HTML 보고서](../evidence/v2-recording-method-pilot02-result.html)를 참조한다. 실제4행 실행·독립 검수가 끝났고 유한 기능은 수용됐지만 지정 CLI 절차는 미검증이다. 아래 과거 ‘미실행/설계 단계’ 문구는 각 당시 상태이며 최신 결과로 소급 변경하지 않는다.

## Rule digest
- Status: advisory
- Layer: Planning
- Scope: host-project
- Aliases:
  - V2 연구 시험 지도
  - 업무 객체 단위 시험
- Applies when: V2 연구를 작은 실험으로 분리하고 다음 시험 범위를 선택할 때.
- Must: 사용자 방향과 구현 후보를 구별한다. 코드 단위 테스트, 실제 모델 평가, 통합·동시성 시험의 증거를 혼동하지 않는다. 이 보고서로 제품 스키마·실험 예산·실행을 승인하지 않는다.

## 연구 전체 보존 — 사용자 확정 요구와 미완료 점검

- **User-confirmed:** 사용자가 ‘우리 연구 기록들은 다 저장되야해 그래야 하네스 만드는데 도움이 되지 미래에 이해하지?’라고 확인했다. 연구 기록은 미래의 하네스 설계·판단을 위한 자산이며, 성공한 실험만이 아니라 전체 연구를 보존하는 것이 목적이다.
- 보존 항목: 연구 목적·질문·가설, 실행 조건·입력·모델·평가 기준, 결과와 근거, 실패·중단·판정 정정, 해석 한계와 미확인 사항, 후속 과제. 완료한 연구와 후보·미실행 연구를 구별하며 과거 실패를 소급 통과시키지 않는다.
- **User-confirmed — 세부 조건 보존:** 사용자가 ‘연구 실험 저장할 때 자세한 조건들도 저장해놔’라고 명시했다. 요약 결과뿐 아니라 실제 프롬프트·입력 원문, 표현 틀과 필수 항목, 항목마다 그 조건을 둔 이유, 공통 조건과 방식별 차이, 이력 보존/전체 재작성 여부, 모델·추론 설정·도구 접근·입출력 상한, 호출 순서·반복 수·재시도 규칙, 측정 구간·정답 및 부분점수 기준을 연결해 보존한다. 조건이 달라지면 이전 조건·변경 이유를 남기며, 길이 등 통제하지 못한 요인과 실무상 필요성을 검증하지 않은 조건도 구별한다. 이번 지시는 저장 내용의 구체화이며 추가 실험이나 과거 전수 보완 실행 승인이 아니다.
- **사용자 재확인(이번 비교 전):** ‘연구와 실험 전부다 저장 되어야해’, ‘목적과 의의등 여러가지 전부 다 기록되어야해’. 결과뿐 아니라 최초 목적·문제의식·의의·가설·설계 선택 이유·승인·입력/모델/조건·실제 응답·실패·초기 채점·정정 이유·비용·한계·미해결 사항을 함께 남긴다. 목적은 결과를 보고 소급 변경하지 않고 변화 이력을 구분한다. 이 항목은 승인된 연구 보존 범위의 재확인이며 전역 정책/백업 기술을 새로 채택하지 않는다.
- **현재 한계:** 개별 기록과 원본은 분산 저장되어 있다. 모든 연구의 누락 없는 목록화, 목적→결과→원본 연결, 임시 경로 의존 제거 및 원격 백업 완료는 아직 확인하지 않았다. 로컬 파일 존재를 전체 보존 완료로 주장하지 않는다.
- **本次 bounded 재확인:** 기존 지도·보존 manifest와 최근 직접 읽은 실험 원문/결과를 근거로 한다. 전수 스캔은 재실행하지 않았다. 보존 manifest는 외부 원본7개만 대상으로 한다고 명시하며, 전체 대화·웹 원문을 인증하지 않는다. 최신 [F/S 읽기](../evidence/v2-reading-display-pilot03.md), [읽기·갱신 후속](../evidence/v2-followup-01.md), [네 방식 실패](../evidence/v2-four-methods-01.md), [네 방식 최종/Parent 정정](../evidence/v2-four-methods-01-result-v3.md), [Parent 판정](../evidence/v2-four-methods-01-parent-assessment-v3.json)을 이 지도에 연결한다. 새 [동일 스키마 비교 목적·의의·승인](v2-vision-feasibility-research.md)은 결과 전에 기록했다. 원격 백업·임시경로 전체 수렴·문헌 원문 전수 보존은 계속 미확인으로 남긴다.
- **Backlog / pending:** (1) 기존 연구 목록을 정리하고 각 목적·결과·원본 위치 및 완료/중단/미실행 상태를 대조한다. (2) 기록 누락·오래된 요약·깨진 연결·`.local` 또는 `/tmp` 및 세션 디렉터리에만 의존하는 증거를 식별한다. (3) 보존 대상·민감정보·용량·버전 관리 범위를 포함한 정리안을 제안하고 확인받은 범위만 보완한다.
- 새 기록 방식 비교의 실행보다 먼저 해결할 보존 요구로 다룬다. 이번 누적은 요구사항과 점검 backlog의 보존이며 전체 감사·이동·삭제·커밋·푸시·원격 업로드의 완료나 포괄 승인이 아니다.
- 관련 최신 연구: `.lazy-harness/planning/v2-change-tracking-reliability-plan.md`, `.lazy-harness/evidence/v2-change-tracking-study03-result.json`. 초기 연구 지도 아래의 역사적 모델·계획 상태를 최신 실행 전체로 오인하지 않는다.

### Discovery capture — 연구 보존 요구

| Layer | 판단 | 내용 |
|---|---|---|
| DDD | none | 새 제품 도메인 정의 없음 |
| SDD | candidate | 연구 목적·결과·원본 연결과 완전성 확인 항목; 형식/스키마 미정 |
| BDD | none | 제품 사용자 흐름 변경 없음 |
| TDD | candidate | 누락·깨진 연결·임시 경로 의존 탐지 기준; 검사 구현 미실행 |
| ADR | none | 저장 기술·백업 방식 선택 없음 |
| SSOT | none | 저장소 소유권·전역 운영 정책·환경 설정 변경 없음 |
| Planning | updated | 전체 연구 보존 목적과 확인 요구, 점검/정리 backlog를 이 primary record에 누적 |

Rule placement: 이번 내용은 V2 연구 보존 요구와 계획이므로 이 Planning에 둔다. 새 전역 운영 규칙이나 개인 메모로 복제하지 않는다. 정책/저장 계약의 독립 변경이 필요하면 기존 canonical 규칙을 먼저 resolve하고 별도 확인한다.

### 보존 점검01 — 읽기 전용 조사 결과

- 범위: V2/lazy-harness-v2 이름의 Planning/TDD/evidence 문서42개와 V2 실험·로컬 산출물·도식 관련 파일 **1,031개 / 37,021,959바이트(약37MB)**. `.git`/Python cache 제외. 연구 관련 이름과 명시 경로에 한정한1차 조사이며 전체 저장소/전체 대화/웹 원문의 전수 보존 인증이 아니다.
- Git 확인: 문서42개 중 기존4개 tracked, 신규38개 untracked. 조사 파일 전체는 tracked4 / untracked889 / ignored138. **파일은 로컬에 있지만 Git 이력에 모두 들어간 상태가 아니다.** 원격 백업은 확인하지 않았다.
- Markdown exact path 참조는 present256회 / missing5회 / brace·glob·축약 표현11회. missing3개는 과거 roadmap의 예정 Deliverables여서 유실로 단정하지 않는다. 나머지2개는 과거 npm 설치 경로로, 현재 문서에서 별도의 local-packages 경로를 기록하고 있다. 자동 링크 교체는 하지 않았다.
- 외부 연구 파일11개의 현재 bytes와 조사 파일의 SHA-256을 비교했다. 비어 있지 않은3개는 프로젝트 내 정확한 사본이 있다. **비어 있지 않은7개는 조사 범위에서 정확한 사본을 못 찾았다**: 과거4개 검토/실행 보고서, native 준비 receipt1개, Sol 표준검증 캡처2개. JSON 내부/base64 내장 보존까지 대조하지 않았으므로 ‘유일본’·‘데이터 유실’로 확정하지 않는다.
- `/tmp/v2-task-contract-standard.json`은0바이트다. 기존 TDD가180초 제한과 빈 캡처를 이미 기록했다. 다른 빈 파일들과 해시가 같아도 보존 사본으로 인정하지 않는다. 최초 기계적 비교값과 이 해석을 함께 보존했다.
- 실제 읽은 연구 기록에는 목적·조건·결과·실패·한계가 남아 있다. 다만 예전 문서의 ‘아직 미수정/미실행’ 문구와 최신 결과가 여러 문서에 흩어져 있어, 역사적 시점 표시와 최신 결과 연결을 보강할 필요가 있다. 문헌 URL/캐시의 원문 사본 범위와 모든 JSON 내부 원본 연결은 추가 점검 대상이다.

| 연구 묶음 | 연구 목적 | 기록된 결과·한계 | 정본 |
|---|---|---|---|
| 구상·문헌 조사 | 영역 책임·소화·근거 연결의 실현 가능성 | 선행 패턴과 한계 조사; 결합 성능/우월성 미검증 | `v2-vision-feasibility-research.md` |
| 샌드박스 | 독립 run·기록 보존·reset·합성 비교 기반 | 기계적 보호 및18개 단위검사; 실제 모델 의미 정확성/공유 동시성 아님 | `../tests/v2-sandbox-bootstrap.md` |
| 태스크 계약 | 상태 갱신과 기록을 한 번에 남길 수 있는가 | 3상황/18지점/12검사; 가짜 pass receipt를 받아들이는 한계 보존 | `../tests/v2-task-contract-pilot.md` |
| Sol 실제 작업01 | 실제 수정 중 이유·실행근거가 남는가 | 5검사/280확인; 단일 작은 작업, 일반 준수율 아님 | `../tests/v2-sol-recording-pilot.md` |
| Sol 변경02·03 | 요구 변경 후 이전 완료 근거를 재사용하지 않는가 | 02 사전 정보 노출 보존; 분리03은7검사/271확인, OS sandbox 아님 | `../tests/v2-sol-requirement-change.md` |
| Luna 소화01 | 기록만으로 현재 요구·이유·근거를 복원하는가 | 핵심7질문/14주장 검수, 표현 보완1개 및 장기 갱신 미검증 | `../tests/v2-luna-record-reader.md` |
| 첫 원문/소화본 비교 | 후속 판단의 품질을 유지하는가 | A1/3·B0/3, 채택 보류; 형식·근거·의미·평가자료 결함 분리 | `../tests/v2-reading-comparison.md` |
| 요청 목록 표시 수정 | 실제 요청과 반환 자료를 분리 보존하는가 | 실제 요청3/반환0 복구,33집중검사; 원답 의미 성공으로 승격 안 함 | `../tests/v2-request-list-projection.md` |
| 변경 추적 비교 | 미수정→승인→수정·검증을 기억이 따라가는가 | 중단01·02 보존; 재시험03 A9/9·B9/9·소화9/9, 한 사례의 제한된 결과 | `v2-change-tracking-reliability-plan.md` |
| 다음 기록 방식 비교 | V1식 절차와 목적·태스크·완료조건 선행 절차의 효과 | 방향 선택됨; 직접 비교 미실행, 현재 보존 점검을 우선함 | `v2-change-tracking-reliability-plan.md` |

- 조사 원본: `.local/v2-preservation-audit-01/`의 inventory/references/external-copy-check/summary 및 git 상태·diff. Canonical 사본: `.lazy-harness/evidence/v2-research-preservation-audit-01.json`. 최초 목록 출력의 장식용 printf 옵션 오류는 기록했고 뒤따른 파일/Git 조사는 완료됐다. 소스·원본 이동/삭제, stage/commit/push/upload는 하지 않았다.
- 다음 보완 제안(pending): 외부 원본의 내장 사본 여부 확인 → 미보존 연구 근거를 출처/hash와 함께 프로젝트에 복사 보존 → 연구별 최신 연결과 역사적 상태를 정리 → 별도 승인한 버전 관리/백업 범위만 적용. 기존 내용/실패 원본은 덮어쓰지 않는다.
- Discovery capture: Planning=updated(본 목적/결과 목록과 조사), SDD=candidate(보존·추적 경계), TDD=candidate(빈 파일과 사본 검증/재구성 검사), DDD/BDD/ADR/SSOT=none. 이번은 저장 기술·운영 정책 채택이 아니다. Task23은 전체 보존 보완이 남아 in_progress.
- **사용자 선택(user-confirmed):** ‘로컬 보존 정리까지 (Recommended)’를 선택했다. 내장 사본 확인, 부족한 원본의 프로젝트 내 복사 보존, 최신 결과 연결 정리를 승인했다. 기존 파일·실패 기록 보존, 삭제·커밋·푸시·업로드 없음. 이 선택 자체는 보존 완료가 아니다.
- **로컬 보완01 실행:** 내장 사본 확인에서 JSON589개를 읽었고13개는 파싱 불가로 별도 목록을 보존했다(삭제·보정하지 않음). 조사대상7개 중 Sol 상태 출력1개는 기존 JSON 문자열에도 있었음을 확인했다. 나머지는 이 exact UTF-8/base64 대조 범위에서 내장 사본을 찾지 못했다.
- 해당7개를 독립적으로 접근 가능한 원본 사본으로 `.lazy-harness/evidence/v2-research-preserved-originals-01/`에 보존했다(총26,505바이트). [Manifest](../evidence/v2-research-preserved-originals-01/manifest.json)에 원본 경로·저장 경로·bytes·SHA-256·내장 사본 위치를 연결했다. 원본과 사본의 byte 동일성 및 원본 해시 불변을 확인했다. 빈 timeout 캡처는 성공 결과로 만들지 않았다.
- 과거 실제 Sol 실행 경로와 native 준비 receipt, 읽기 비교 초기 설계 검수, 변경 추적 독립 설계 검수는 위 manifest의01/05/04/03번 사본으로 찾을 수 있다. 과거 npm 설치 경로는 역사적 근거이며 현재 설치 위치로 자동 대체하지 않았다.
- 주요 Sol/읽기 비교 문서에 보존 manifest 및 최신 결과 연결을 추가했다. 기존 ‘미실행/미수정’ 문구는 당시 이력으로 남기고 후속 결과와 구별한다. 새 실험이나 판정 변경은 없다.
- 남은 범위: 파싱 불가13개와 JSONL 등 다른 표현의 보존 연결, 문헌/웹 캐시 원문·미열거 세션의 전체 범위, Git/원격 백업과 복구 검증. 따라서 이번에 발견한7개 원본의 로컬 보완 완료와 ‘모든 연구의 영구 보존 완료’를 구별한다. Discovery capture: 동일 Planning 갱신; 기존 SDD/TDD 후보 유지, 그 외 독립 delta 없음.

### 보존 점검02 — 추가 확인과 현재 문헌 사본

- 사용자 ‘좋아 진행해줘’에 따라 남은 로컬 보존 점검을 이어갔다. 새 기록 방식 실험을 실행하거나 원격 업로드하지 않았다.
- 파싱 불가로 남았던 JSON13개는 **모두0바이트**이며 같은 이름의 비어 있지 않은 `.md` 대체 파일도 없었다. 이 경로를 결과 원문으로 사용하지 않는다. 빈 파일만으로 연구 결과 유실을 단정하거나 내용을 만들어 채우지 않는다.
- 조사대상 JSONL/JSONL.bin **82파일은 모든 비어 있지 않은 행이 파싱됨**. 이 중54파일은 synthetic test-artifacts이며 실제 모델 실행으로 세지 않는다. 형식 유효성은 의미 정확성·전수 보존의 증명이 아니다.
- JSON에 명시적으로 base64+sha256으로 보존된 **1,053개 항목(서로 다른 bytes 해시358개)**을 디코딩하여 선언된 해시/크기와 대조했고 불일치0개였다. 이는 프로젝트 내 캡처의 무결성 확인이며 외부의 모든 과거 세션이나 원본 파일을 확인했다는 뜻은 아니다.
- 문헌 인용 **32개 URL**의 현재 HTTP 응답을 각각1회 받아 `.lazy-harness/evidence/v2-web-reference-capture-01/`에 보존했다(11,919,421바이트). URL·최종URL·수집시각·HTTP상태·content type·해시를 [manifest](../evidence/v2-web-reference-capture-01/manifest.json)에 기록했다.32개 모두 HTTP2xx지만 내용 전체성은 별개다. PDF 헤더3개를 확인했고 HTML title의 단순 접근 차단 신호는 없었다.
- **현재 문헌 사본 ≠ 당시 연구 입력 원본.** 모든 새 문헌 사본은 historicalInput=false다. arXiv abs는 초록 페이지, GitHub URL은 방문 페이지이며 전체 논문·저장소를 보존했다고 주장하지 않는다. 최초 열람 bytes와의 동일성은 미확인이고 과거 판단의 근거를 소급 교체하지 않는다.
- 기존 보완 원본7개+현재 문헌 응답32개, 총39개를 별도 임시 디렉터리에 쓰고 다시 읽어 해시39/39 일치를 확인했다. 이는 해당 파일의 로컬 복사·재읽기 검사이며 전체 연구 저장소의 재난 복구/원격 백업 검증이 아니다. 원본 삭제·수정·커밋·푸시·업로드 없음.
- 추가 근거: [02 점검 및 문헌 인용 목록](../evidence/v2-research-preservation-audit-02.json), [내장 원본 해시 대조](../evidence/v2-research-embedded-bytes-audit-02.json), [로컬 복사·재읽기 검사](../evidence/v2-preservation-local-restore-check-02.json). 수집 스크립트는 `.local/v2-preservation-audit-02/capture-web.py`; 보존 데이터 수집용이며 제품 기능/소화기 구현이 아니다.
- 남은 미확인 범위는 **최초 웹 열람 원문·미열거 외부 세션의 완전한 재구성, 논문/저장소 전체 사본, Git·원격 백업/복구**다. 현재 조사범위의 기록·캡처 점검 및 로컬 보완과 이를 구별한다. Discovery capture: Planning=updated, SDD/TDD=기존 보존/검사 후보 유지, DDD/BDD/ADR/SSOT=none; 새로운 저장 정책 채택 없음.

## 연구 목적·의의 통합 — pilot02 이후 사용자 요청

> User-confirmed: ‘이거랑 지금까지 연구한 것들의 목적과 의의들도 다 적어주면 좋아’. 최신 HTML을 단일 실험의 비용 표에서 V2 연구 흐름을 설명하는 읽기용 보고서로 확장한다. 이 절은 기존 연구의 종합이며 새 실험/스키마/기술 채택이 아니다.

**원래 목적:** 문서가 누적될수록 찾고 이해하기 어려워진다는 사용자 경험에서 출발해, 작업의 목적·이유·실행 결과를 보존하고 현재 지식으로 정리하여 다음 AI의 작업에 활용한다. 문서 수 감소나 온톨로지 도입 자체가 목표가 아니다. 필요한 의미·근거·최신성을 유지하면서 전체 읽기/작업 비용과 누락을 줄일 수 있는지를 검증한다. 아래 의의는 관측을 V2 설계 질문에 연결한 해석이며 성능 보장/채택 결정이 아니다.

| 연구 묶음 | 목적 | 확인 결과 | 의의 / 남은 한계 | 근거 |
|---|---|---|---|---|
| V2 방향·책임 분해 | 도구/폴더 중심에서 지속적인 프로젝트 이해로 중심 이동 | 읽기·작업 기록·소화 책임과9개 연구 영역 정리 | 분산 배치·저장 기술보다 필요한 책임부터 시험; 최종 구현 구조 미채택 | `lazy-harness-v2-direction-purpose.md`, `v2-vision-feasibility-research.md` |
| Wiki·Compiler·Knap | 문서 정리와 의미 소화의 경계 확인 | 위키 유지/어휘 링크/템플릿 출력과 의미 충돌 해결은 다름 | 코드의 기계적 처리와 모델의 의미 판단을 분리; 저자 성능 독립 재현 없음 | `v2-vision-feasibility-research.md` §11/14/15 |
| RDF/OWL/SHACL·Palantir·Digital Twin | 대상·관계·주장·조건·근거·변경을 어떻게 표현하는가 | 의미 모델/구조 검사/실행 action/상태 동기화의 책임 구별 | 형식 통과를 진실로 오인하지 않는 설계 기준; RDF/DB/플랫폼 채택 아님, Digital Twin 원문 fetch403 | `v2-vision-feasibility-research.md` §3/15 |
| A-MEM/Mem0/Zep/Sleep-time/LongMemEval/RAG | 기억 갱신·시간성·보류·읽기 비용 평가 참고 | 기존 기억 갱신과 검색·생성, 선행 소화 비용의 평가 축 조사 | 현재/과거/미확인을 구별하는 실험 설계에 사용; 논문 결과를 V2 성능으로 이전하지 않음 | `v2-vision-feasibility-research.md` §8/11 |
| Orleans/Kafka/CQRS/Restate·권한 | 영역 처리 순서·병렬성·복구·읽기/쓰기 경계 연구 | 직렬 처리도 의미 충돌을 없애지 않고 journal도 자연어 재현을 보장하지 않음 | 기반 기술과 지식 정확성을 따로 검증; 분산 시스템/공유 DB 미구현 | `v2-vision-feasibility-research.md` §4–7 |
| 독립 샌드박스 | 합성 입력으로 반복·reset·채점·보존 기반 확인 | 18단위검사, 입력/결과 보존과 독립 run | 연구소 기반을 검증한 것이지 모델 소화/공유 동시성 증거 아님 | `../tests/v2-sandbox-bootstrap.md` |
| 태스크 계약 | 상태 갱신만으로 근거 있는 진행 기록이 남는가 | 3상황/18지점/12검사; 가짜 pass 영수증도 받아들이는 한계 확인 | 계획 버전/작업 버전/실제 receipt를 구별해야 함; 모델 준수/DB 원자성 미검증 | `../tests/v2-task-contract-pilot.md` |
| Sol 실제 기록01 | 실제 작업자가 이유와 실행 근거를 남길 수 있는가 | 테스트5개/부모 확인280항목,7이벤트·의미 메모3문장 | 최소 기록으로 작업을 복원할 가능성; 단일 상세 지시 과제, 비용 절감 미검증 | `../tests/v2-sol-recording-pilot.md` |
| Sol 요구 변경02/03 | 과거 완료를 새 조건에 그대로 쓰지 않는가 | 02 미래 요구 노출 보존; 입력 분리03 테스트7개/271확인 | 입력 오염과 모델 능력을 분리하고 변경 후 근거를 다시 판단; OS 격리 아님 | `../tests/v2-sol-requirement-change.md` |
| Luna 소화01 | 작업자 대화·코드 없이 기록만으로 현재 상태 복원 | 16sources/핵심7질문 취지 일치/14주장 출처 검수, 표현 보완1개 | 기록→작은 지식 후보의 가능성; 지속 갱신·전체 비용 절감 미검증 | `../tests/v2-luna-record-reader.md` |
| 첫 원문/소화본 읽기 비교 | 소화본이 실제 후속 답변 품질을 유지하는가 | A1/3·B0/3 전체 통과, 채택 보류 | 단발 소화 성공과 후속 활용 성공은 다름; 형식·의미·증거·런타임 실패 분리 | `../tests/v2-reading-comparison.md` |
| 요청 목록 투영 수정 | 요청했지만 못 받은 자료가 평가에서 사라지는가 | requested3/returned0 복구,33집중검사 | 평가 도구도 검증 대상; 자료 미반환을 미요청으로 해석하지 않음 | `../tests/v2-request-list-projection.md` |
| 변경 추적 재시험03 | 미수정→승인→수정·검증을 지식이 따라가는가 | A9/9·B9/9·소화9/9; B 읽기만 저렴하나 소화 포함 더 비쌈 | 읽기 비용과 전체 비용 분리; 한 사례3반복×3시점, 우월성 미입증 | `v2-change-tracking-reliability-plan.md` |
| 연구 보존01/02 | 미래 설계자가 목적·실패·원본까지 재검토할 수 있는가 | 원본7개/현재 웹응답32개 보완,선택39개 재읽기 hash 일치 | 로컬 존재/현재 수집/당시 원문/Git/백업을 분리; 전수 복구 미확인 | 이 문서 보존 절 |
| 격리·SDK·실제 chat 승인 | 공정한 입력·실행 근거·모델/비용/승인을 실제로 연결 | bwrap 도구/receipt/인증 metadata/실제4회 chat 승인; 최초 TTY 실패 보존 | 실험 기반 오작동을 기록 품질 문제와 분리; hard 과금상한·적대적 grader 보장 아님 | `v2-recording-method-comparison-plan.md`, `../evidence/v2-chat-approval-bridge-review-01.md` |
| 기록 생성 A/B pilot02 | 기록을 만드는 절차가 새 AI의 실제 수정에 주는 효과 | 유한 기능4개 수용, A USD1.097326/B USD1.605958; CLI 절차 미검증 | B의 T1 실행은 확인, 추가 기능 이점은 이번에 미관찰; 인과적 우열 불명 | `../evidence/v2-recording-method-pilot02-result.md` |
| 개념도·검수 HTML | 사람이 목적·후보·증거·정정을 보고 판단할 수 있는가 | Archify 개념도, 연구/시험/결과 HTML 작성·정정 | 사람의 검수 창구; 그림이 배포 구조나 성능 증거는 아님 | `v2-review.html`, `visuals/harness-v2/README.md` |

**현재 종합:** 실제 기록→소화 후보→후속 읽기/수정의 부분 연결은 확인했지만, 비용·정확도의 지속적인 개선과 공유 지식 병합/복구·자동 영역 분할·대규모 확장은 입증하지 않았다. 읽기 비교의 A/B와 기록 생성 비교의 A/B는 서로 다른 조건이다. 각 실험 비용의 포함 범위가 달라 이 숫자를 단순 합산해 전체 연구비로 제시하지 않는다.

Coverage: 이 대화의 V2 연구 묶음을 위 canonical 근거에서 종합했다. 저장소의 모든 과거 프로젝트/미열거 세션/논문 전문을 전수 조사했다는 주장은 아니다. 최신 결과를 우선하고 과거 미실행 상태·오판·실패는 역사로 유지한다.

Discovery capture: Planning=이 절과 기존 HTML에 종합 갱신; DDD/SDD/BDD/TDD/ADR/SSOT=기존 결과·후보 재사용, 독립 계약/기술 채택 없음. Implementation map: 이 문서의 목적·의의 표 + 기존 구상/각 TDD/결과 evidence → `../evidence/v2-recording-method-pilot02-result.html`의 연구 개요/17묶음/최신 실험 상세. 신규 제품 함수·graph edge는 없다.
전용 Reader run `8e07a95a-db08-420b-8490-f4f58113270a`는 runtime-owned identity/budget 누락으로 canonical read0/incomplete였다. 실패 packet과 작업 전 HTML/연구 지도/Git 상태는 `.local/v2-research-report-expansion-01/`에 보존하고 Parent direct map→concrete node→canonical read로 근거를 확보했다. 모델 실험 재실행·전역 설정 수정·다른 CLI-agent 우회는 하지 않았다.
통합 보고서 bounded checkpoint: HTML 구조/17묶음별 목적·결과·의의·한계·근거, 로컬 링크34개(25고유 대상)/내부 앵커5개, 정본 수치12개 일치. 기존 pilot02 상세 본문은 확장 전과 byte-equivalent다. 최초 검사에서 이 V2 checkout에 없는 개념 지도 링크1개를 발견해 제거했고 실패 receipt도 보존했다. `<style>`을 잘못 겨냥한 title edit는 즉시 undo한 뒤 올바른 줄을 수정했다. `.local/v2-research-report-expansion-01/bounded-check{,-initial-failure}.json` 참조. 재귀 artifact 검사·전체 validator·모델 재실행은 하지 않았으며 브라우저 렌더 검증과도 구별한다.

### 사용자 설명 방식 정정 — 쉬운 말 재작성
사용자는 모든 연구도 마지막 작업 카드 예시처럼 사람이 알아듣게 설명하고 HTML에 전부 정리하라고 요청했다. 기존17묶음의 결과는 바꾸지 않고, ‘왜 궁금했나 → 무엇을 기대했나 → 실제로 무엇을 시켰나/조사했나 → 어떻게 됐나 → 그래서 알게 된 것’으로 같은 HTML을 재작성했다. 설명용 예시는 실제 시험과 구분했고 기술명·정확 수치·원본은 접어서 볼 수 있게 했다. 특히 원문/정리본 **읽기 비교**와 문서/지속 카드 **작업 절차 비교**를 분리했다. 실패·정정·미확인 범위와 기존 pilot02 상세는 유지한다.
이 변경은 이 연구 전달물의 사용자 확인 요구이며 새 operating rule/연구 결과/기술 채택이 아니다. Discovery capture: Planning=설명 요구·표현 수정; DDD/SDD/BDD/TDD/ADR/SSOT=no independent delta. Implementation map: 이 절 → `../evidence/v2-recording-method-pilot02-result.html`의17개 `study-*` 구간과 기존 근거 링크. 새 모델 시험·전역 설정 변경·감사 사본 추가 복제·삭제 없음.


## 1. 결론

연구는 **업무를 정의하고 수행하는 계층 → 기록을 보존하는 계층 → 지식을 유지·읽는 계층 → 실행과 격리를 관리하는 계층**으로 나눌 수 있다. 이는 서비스 배포도나 실제 지식 파티션 목록이 아닌 연구 책임 분해다.

첫 연구 단위의 추천은 **업무 객체 하나, 작은 태스크, 연결된 실행 근거, 완료 조건**이다. 정상 진행·계획 변경·실패를 같은 계약으로 표현하고, Sol이 중복 보고서 없이 그 계약을 준수할 수 있는지 먼저 평가한다. 이후 Luna 소화·읽기를 연결한다. 추천 순서이며 실행 승인이나 스키마 채택은 아니다.

핵심 질문은 세 가지다.
1. 작업 계획과 실행 상태를 갱신하는 것 자체로 충분한 작업 기록이 남는가?
2. 그 기록을 소화해 현재 지식을 정확하게 유지하고 다음 작업에 활용할 수 있는가?
3. 이 연결이 기존 방식보다 누락·중단·전체 비용을 줄이는가?

## 2. 결정 수준과 현재 구현

### 사용자 확인 방향
- 파티션 ID와 지식 ID를 중심으로 사실을 구조화한다. 주체·설명·타입의 구체 의미는 설계 중이다.
- 기존 지식을 추가만 하지 않고 수정·통합·철회하는 소화를 지향한다.
- 작업의 파생 기준 상태, 격리, 갱신·병합 관계에 따라 지식도 관리해야 한다.
- 실제 작업자: GPT5.6 Sol medium. 내부 기록 읽기·작성·소화: GPT5.6 Luna medium. 조율: GPT6 Astra low/medium 중 미정. 표기는 사용자 명칭이며 provider/model ID 가용성 확인 전이다.
- 하네스 준수를 실제로 확보해야 한다. 작은 단위부터 단독·연결·전체 흐름을 검증한다.

### 최근 제안과 미정
- 업무 객체를 계획·실행·기록의 공통 기준으로 하여 중복 서술을 줄이는 것은 사용자 제안/연구 가설이다.
- 행동 ‘원장’ 명칭은 재검토 중이다. 불변성·정정·보존 계약은 아직 확정하지 않았다.
- 별도 임시 지식 저장소는 필수가 아니다. 현재 지식과 관련 미소화 이력을 읽는 흐름이 후보이다.
- PostgreSQL은 허용 후보이며 DB 생성·물리 테이블·트랜잭션 계약은 미정이다.
- 업무 완료 훅, 기록 툴, 자동 라우팅, 데몬, 검색 방식은 설계 후보이다.

### 이미 있는 실험 기반
`experiments/v2-sandbox/`는 명시적 set/propose 합성 입력, append/integrate/scoped 비교, 독립 run, 결과 보존, reset 세대, 타입-aware 채점과 임계값을 지원한다. 이전 18개 단위 테스트 및 framework 88개 회귀 통과는 이 기반과 당시 변경의 증거다.

**이 기반은 실제 모델 소화·업무 준수·공유 DB 동시성·분기 지식 병합을 구현하거나 입증하지 않았다.** 아래 시험 목록을 기존 테스트 이름이나 구현된 기능으로 읽으면 안 된다.

## 3. 연구 책임 지도

```text
[요구·PRD / 업무 객체]
       ↓ 태스크·완료 조건
[Sol의 실행] → [도구 증거 + 결정/예외 기록]
       ↑                 ↓
[준수·완료 확인] ← [업무 상태와 연결된 이력]
                         ↓
                 [영역 배정 + Luna 소화]
                         ↕
                 [영역별 현재 지식]
                         ↓
       [Luna 읽기 ← 관련 미소화 이력]
                         ↓
                  [다음 작업에 사용]

공통 축: 기준 상태·격리·병합 / 저장·복구 / 런타임·비용·권한
```

영역 배정과 소화는 같은 모델 호출에서 수행할 수 있다. 읽기와 소화는 다른 책임이지만 항상 별도 프로세스일 필요는 없다. 업무·태스크 계층과 지식 책임 파티션도 동일한 트리가 아니다.

## 4. 시험 종류: 무엇을 증명할 수 있나?

| 시험 수준 | 방법 | 증명 범위 / 한계 |
|---|---|---|
| 코드 단위 테스트 | 모델 없이 고정 입력과 기대 상태 비교 | 필드·참조·전이·채점 규칙. 실제 모델 이해를 증명하지 못함 |
| 실제 모델 평가 | 고정 과제, 숨겨진 기대 결과, 모델 호출 기록 | 해당 조건의 의미 이해·준수·비용. 반복과 분포 평가 필요 |
| 계약·통합 시험 | 모델 stub 또는 실제 모델과 저장/툴을 연결 | 경계 간 데이터 전달과 반영. stub 성공과 실제 모델 성공을 별도 보고 |
| 장애·동시성 시험 | 제어된 순서, 장애 지점, 재전달 주입 | 일관성·중복·복구. 단순 병렬 프로세스 실행과 다름 |
| 종단 간 비교 | 계획부터 다음 작업 활용까지 수행 | 전체 효용. 원인 분리를 위해 앞 단계 증거가 필요 |

명확한 사실·상태는 코드로 채점하고, 설명 의미는 사전 채점표와 사람 검수로 평가한다. LLM 채점은 보조로 쓸 수 있으나 유일한 정답 판정자로 삼지 않는 것이 후보이다.

## 5. 영역별 단위 시험과 연구 질문

### A. 업무 객체·PRD·태스크 모델
**책임:** 무엇을 왜 어디까지 할지, 어떤 기준 상태에서 시작했는지, 어디까지 진행됐는지 표현한다.

- 코드 단위: 업무/태스크 참조, 허용 상태 전이, 계획 버전 연결, 완료 조건 누락 처리, 취소·보류·재개 계약.
- 예시: 검증 근거가 없는 태스크의 완료 요청 → 거부 또는 검토 대기라는 사전 합의 결과. 실패했다고 업무 계획 자체를 자동 변경하지 않음.
- 예외 시험: 태스크 완료 후 완료 조건 변경 → 이전 증거가 새 조건을 충족하는지 재평가. 완료 이력은 지우지 않음.
- 모델 연구: 동일 요구를 Sol이 쪼갤 때 작업 범위 누락, 불필요하게 잘게 쪼개기, 의존성 누락, 검증 불가능한 완료 조건 비율.
- 미정: 최소 필드, PRD 필수 정도, task 크기, 병렬 태스크 의존성, 완료 판단 주체.

### B. 실행 기록·행동 이력 확보
**책임:** 실행 결과는 도구에서, 이유·새 결정·미해결은 작업자에게서 얻어 업무에 연결한다.

- 코드 단위: 이벤트 ID/작업 ID 연결, 중복 제출, 순서, 잘못된 참조, 시도와 성공 구분, 출력 제한·민감 정보 처리 계약.
- 계약 시험: 한 번의 태스크 갱신 요청이 현재 상태와 이력에 일관되게 반영되는가. 오류 시 부분 반영이 남는가.
- 모델 연구: 업무 객체 갱신 방식과 별도 작업 보고서 방식에서 목적·이유·결과·예외의 보존률과 중복 서술 토큰 비교.
- 반례: 파일 diff는 있으나 설계 이유는 없음; 테스트 실행 시작만 있고 종료 결과가 없음; 기록 전에 프로세스 종료.
- 미정: Sol 최소 입력과 Luna 최초 작성의 경계, 수집 범위, 기록 보존·정정 방식.

### C. 준수·완료 게이트
**책임:** 규칙을 제시하는 데 그치지 않고 실제 기록·검증 절차를 따르게 한다.

- 코드 단위: 기록 미제출·저장 실패·근거 불일치 시 완료/인계 요청 처리. 정상 제출은 통과. 반복 확인의 중복 상태 방지.
- 실제 모델 연구: 안내만 제공 / 구조화 툴 / 완료 확인 장치 등의 조건별 미준수율, 재촉 횟수, 총 비용 비교. 정확한 비교 조건은 미정.
- 반례: 무의미한 ‘완료함’ 기록으로 형식 통과; 과거 테스트 결과를 새 변경 증거로 재사용; 승인 없는 완료 조건 완화.
- 핵심: 저장 성공·필드 존재는 코드로 확인할 수 있으나 의미 누락 없음은 보장하지 못한다.
- 미정: 어느 경계를 막는지, 긴급 중단·실패 인계 예외, 누가 해제하는지. 새로운 훅 도입은 미승인.

### D. 영역 배정·관련 정보 찾기
**책임:** 어떤 지식을 읽고 어디에 반영할지 구별한다.

- 코드 단위: 존재하지 않는 파티션 참조, 읽기/쓰기 허용 범위, 미분류 보존, 배정 결과의 형식 검사.
- 모델 연구: 같은 ‘세션’이 인증/결제 문맥에 등장, 여러 영역에 관련된 정책, 어느 영역에도 확실히 속하지 않는 기록.
- 평가: 관련 영역 recall, 잘못된 쓰기 영역 비율, 불필요 복제, 보류와 추가 조회 비용.
- 반례: 관련 영역 두 개를 모두 수정 권한이 있는 것으로 오인; 새 용어마다 파티션 생성.
- 미정: 분할·합병 기준, 다중 책임, 영역 생성 권한. 독립 라우터는 필수 아님. 자체 검색 알고리즘 구현은 이 연구의 전제가 아님.

### E. 소화·지식 스키마·의사결정 연결
**책임:** 기록과 기존 근거를 대조해 추가·수정·통합·철회·보류를 판단한다.

- 코드 단위: 변경안 필드·타입·대상 버전·근거 참조·중복 반영 검사. 원자적으로 반영할 범위는 합의 후 시험.
- 모델 연구: 신규 사실, 값 변경, 예외, 동의어, 상충 주장, 제안→시도→실패→복원.
- 예시: 30분으로 바꾸려다 60분으로 복원 → 동일 대상·범위에서 현재 지식은 60분, 이전 시도는 근거 이력에 남음.
- 평가: 중요한 주장 보존, 잘못된 채택, 근거 연결 정확도, 예외 손실, 과도한 보류, 소화 비용.
- 미정: 주체·타입·관계의 의미, 객체 ID, 조건·시간 표현, 결정 모델과 지식 모델의 경계. 모든 항목을 단일 정확 문자열로 채점하면 안 됨.

### F. 읽기·미소화 정보 활용
**책임:** 현재 지식에 아직 반영되지 않은 관련 이력까지 고려해 필요한 정보를 제공한다.

- 코드 단위: 작업 범위·지식 버전·처리 경계 필터, 이미 반영된 이벤트 중복 포함, 권한 밖 기록 제외.
- 모델 연구: 같은 질문을 소화 전/후에 질의. 완료 주장과 실제 검증 결과 충돌, 폐기된 값, 조건부 예외, 근거 없음에 대한 보류.
- 비교 후보: 지식만 / 관련 이력만 / 지식+관련 미소화 이력. 조건별 접근 가능 정보 차이를 명시.
- 평가: 정답·근거·최신성·누출·읽기 토큰·지연. 읽기 오류가 검색 누락인지 해석 오류인지 분리.
- 미정: 관련 로그 선별법, 답변 근거 형식, 다른 작업 이력 공개 범위, 신선도 요구.

### G. 기준 상태·격리·갱신·병합
**책임:** 작업이 어떤 상태에서 시작했고 무엇을 자체 변경했는지 보존한다.

- 코드 단위: 기준 상태 참조, 작업별 변경 가시성, 잘못된 기준 버전 거부, 지식 상태와 코드 revision 연결.
- 통합 예시: S0에서 A/B 파생 → A 병합으로 S1 → B는 여전히 S0 기반. B의 갱신/병합에서 양쪽 변경을 비교.
- 모델 연구: 코드 merge는 성공했지만 같은 정책에 대한 지식이 상충하는 사례. 로컬 사실을 공통 상태로 오인하는지.
- 장애 시험: 코드 반영과 지식 반영 중간 실패, 미커밋 상태, 지식 소화 지연, 기준 snapshot 누락.
- 미정: 논리 snapshot/delta 방식, merge·rebase 처리, 다중 영역 원자성. Git 독립 ID를 유지하되 Git 메타데이터를 근거로 연결할 수 있음.

### H. DB·처리 상태·복구
**책임:** 로그/업무/지식/처리 정보를 안전하게 보존·조회한다.

- 코드 단위: 저장/조회, 참조 제약, 실패 분류. DB가 필요한 검증은 순수 단위가 아니라 DB 통합 시험으로 표시.
- 통합: 트랜잭션 rollback, 중복 키, 오래된 버전의 갱신, 로그 저장 후 알림 누락.
- 장애·동시성: 지식 반영 직후 처리 위치 저장 전 종료; 같은 이벤트 재전달; 같은 영역 두 writer; 다른 영역 독립 처리.
- 검증 결과는 ‘최종 값만 같다’가 아니라 중복 관계·결정·부수 효과가 없는지까지 확인.
- 미정: PostgreSQL/SQLite, isolation level, cursor/receipt, retention, backup. SQLite 성공을 PostgreSQL 동시성 증거로 대체하지 않음.

### I. 런타임·데몬·모델 조율
**책임:** 저장 성공, 처리 요청, 읽기 응답, 모델 호출·예산·취소를 연결한다.

- 코드 단위: fake 모델/시계로 배치·timeout·재시도·취소·예산 상한·일감 없음 처리.
- 통합: 기록 저장 확인 뒤 작업자 진행 가능, 데몬 재시작 후 미처리 발견, 읽기 요청의 응답·오류 전달.
- 실제 모델 연구: 매번 명시적 위임 / 기록 이벤트 기반 배치 처리의 전체 호출·토큰·지연·누락 비교.
- 미정: 호출 인터페이스, 모델 ID, 실행 위치, 배치 크기, polling/event, backpressure. 데몬 상주와 모델 상시 추론은 다름.

## 6. 첫 시험 묶음 제안

한 번에 전체 구조를 만들지 않는다. 다음은 dependency 순서의 후보이다.

| 단계 | 최소 산출물 | 합격 판단의 종류 | 다음 단계 전 확인 |
|---|---|---|---|
| P0 계약 예시 | 업무 1개·태스크·최소 로그·지식 조각·상태 전이 예시 | 사람의 의미 검수 | 필드·완료·예외 기준 합의 |
| P1 기계적 계약 | 고정 fixture와 fake 실행 결과 | 결정적 테스트 | 잘못된 제출을 거부하고 정상 경로 통과 |
| P2 Sol 기록 준수 | 작은 실제 코드 작업과 갱신 이력 | 모델 평가 + 실제 코드 테스트 | 계획·결정·예외 보존, 중복 서술과 중단 비용 |
| P3 Luna 소화/읽기 | P2 기록과 별도 고정 fixture | 사실별 채점 + 근거 검수 | 요구·실제 상태·보류 구별 |
| P4 격리/병합 | 두 작업의 기준 상태와 변경분 | 통합·의미 충돌 평가 | 교차 작업 누출·오승격 없음 |
| P5 데몬·공유 DB | 복구 가능한 처리 연결 | 장애·동시성 시험 | 중복·부분 반영·과부하 처리 |

P2 오류를 P3 모델 능력 탓으로 돌리지 않도록, P3에는 사람이 미리 검수한 고정 기록도 별도로 투입한다. 반대로 사람이 보완한 기록으로 얻은 결과를 ‘작업자가 원래 잘 기록했다’고 보고하지 않는다.

첫 실행 증거: [태스크 계약 파일럿 결과](../tests/v2-task-contract-pilot.md) — P0–P1에 해당하는 세 상황 고정 입력 실험. 실제 모델 평가(P2/P3)가 아님.

### P2 실행 준비 차단 — 기존 경로 점검
- 사용자 승인: 실제 Sol 연구로 이어가기 요청 후, 누락 오류에 대해 ‘기존 실행 경로 점검’을 선택. 설치 변경·외부 CLI 우회 승인은 아님.
- 확인: subagent list(capabilities=true)와 models 조회 성공. registry에 `openai-codex/gpt-5.6-sol` 존재. 모델 등록은 실제 호출 성공 증거가 아니다.
- 오류: skill read는 `E_NOT_FOUND`; subagent guide(tool-reference)는 `/home/lazydino/.pi/agent/npm/node_modules/pi-subagents/docs/tool-reference.md` ENOENT. `ls -ld` 및 디렉터리 목록도 `/home/lazydino/.pi/agent/npm/node_modules/pi-subagents` 부재 확인.
- 해석 한계: 등록 도구가 참조하는 디스크 경로를 찾을 수 없는 상태. 삭제·이동·세션 캐시 등 원인은 미확인. 패키지가 시스템 전체에서 미설치라고 단정하지 않는다.
- 실행 상태: child 미실행, run ID 없음. 부모 cwd `/home/lazydino/dev/lazy-harness`; 대상 `/home/lazydino/dev/lazy-harness.v2`, branch `design/harness-v2`, HEAD `58fbcbf`. 기존 dirty/untracked 작업은 보존했고 실행 경로 점검은 변경을 만들지 않았다.
- 후속 backlog: 같은 실행 프로토콜의 실제 설치 위치/세션 로딩 상태를 확인하고 복구안을 사용자에게 제시한다. 승인 없이 설치 변경·다른 CLI·다른 모델로 대체하지 않는다.
- Discovery capture: Planning updated — 이 차단 기록. DDD/SDD/BDD/ADR/SSOT none — 계약·정책·설치 설정 변경 없음. TDD none — 제품 결함 재현/회귀 시험이 아니라 실행 인프라의 읽기 전용 점검이며 원인 미확인.
- 후속 읽기 전용 확인: 사용자의 커스텀 설치 단서에 따라 `/home/lazydino/.pi/agent/settings.json`을 확인했다. packages에 `local-packages/pi-subagents-readfix-1/node_modules/pi-subagents`가 등록돼 있다. `/home/lazydino/.pi/agent/local-packages/pi-subagents-readfix-1/node_modules/pi-subagents` 및 그 아래 `skills/pi-subagents/SKILL.md`, `docs/tool-reference.md` 파일 존재를 확인했다. 앞선 npm 경로 부재를 패키지 전체 부재/재설치 필요로 일반화하면 안 된다. custom 변경 내용과 현재 실행 도구가 왜 옛 경로를 참조하는지는 아직 미확인. 설치/설정 수정·자식 실행 없음.
- 같은 프로토콜 실행 확인 결과: workflow `1511a1f5-98ab-4abd-9524-7003747644ab` failed. 정확한 오류: `Workflow parser dependency 'acorn' is unavailable from pi-subagents. Reinstall pi-subagents dependencies before launching workflowScript.` fan-out 0/1, child session 미생성, resume 불가. Sol 호출/파일 읽기는 시작되지 않았다. receipt: `/tmp/pi-subagents-uid-1000/async-subagent-runs/1511a1f5-98ab-4abd-9524-7003747644ab/workflow-receipt.json`. 대상 cwd/branch/HEAD 재확인: `/home/lazydino/dev/lazy-harness.v2`, `design/harness-v2`, `58fbcbf`; 기존 dirty/untracked 상태 보존. 오류의 재설치 문구는 복구 승인/원인 확정이 아니다. 로컬 커스텀 설치의 acorn 존재 및 현재 세션의 모듈 해석 경로를 아직 비교하지 않았다. 설치·설정 변경/다른 실행 모드 우회 없음.
- acorn 오류 후 읽기 전용 비교: Node createRequire로 실제 custom package.json 기준 `acorn`은 `/home/lazydino/.pi/agent/local-packages/pi-subagents-readfix-1/node_modules/acorn/dist/acorn.js`에 정상 resolve됨. 과거 npm package.json 경로 기준은 MODULE_NOT_FOUND. custom 소스 `src/workflows/scripted-workflow.ts`는 createRequire(import.meta.url)을 사용하고 parser resolution 실패를 일반 재설치 안내로 감싼다. 따라서 커스텀 설치 전체의 의존성 누락보다는 세션/실행 도구의 과거 경로 참조가 유력하다. 실제 실패 프로세스의 import.meta.url 직접 계측은 하지 않아 최종 원인 확정과 구별한다. 재설치·설정 변경 없음.
- 사용자 reload 후 동일 프로토콜 재시도 성공: workflow `3e136c46-7b9b-47f1-81fb-8992f363d058`, child `a7ebccda-2278-47d9-8bd0-a1cf277894f0`. status에서 complete/process terminal observed, gpt-5.6-sol thinking medium 확인. 반환한 normal/failure/changed_requirement는 지정 fixture와 일치. outputReference: `/home/lazydino/.pi/agent/sessions/--home-lazydino-dev-lazy-harness--/subagent-artifacts/outputs/3e136c46-7b9b-47f1-81fb-8992f363d058/sol-route-check-reload.md`. 이 읽기 전용 canary에서 acorn 장애는 재발하지 않았다. 실제 작업 기록 실험(P2)·전체 도구 동작·설치 무결성 검증이 아니며 reload가 내부적으로 무엇을 바꿨는지까지 계측한 것은 아니다. Discovery capture: Planning updated; DDD/SDD/BDD/TDD/ADR/SSOT none — 실행 경로 확인 증거만 추가.
- 실제 P2 첫 단일 표본 준비: [Sol 실제 작업·기록 시험](../tests/v2-sol-recording-pilot.md). task.json을 사전 제공하고 Sol이 timeout 설정 함수와 테스트를 실제 수정하며 record.py로 기록하도록 한다. recorder 사전 검사 7/7, 시작 fixture는 실패 조건 유지, baseline 별도 보존. 구현/실험 증거의 primary는 해당 TDD이며 본문 중복 없음.
- P2 단일 표본 결과: Sol medium 실제 코드 수정 완료(496c5007), 7개 진행 이벤트·의미 메모 3문장·실제 최종 테스트 5개 통과. parent 독립 코드/무결성 확인 280항목 통과, child 약96.7초·보고 비용 $0.335653. 별도 작업 보고서 없이 실패 원인/수정 이유/최종 상태를 확인했다. 이는 단일 상세 지시 과제의 수행 가능성 증거이며 비용 절감·일반 준수율·Luna 소화는 미검증. 상세 결과/한계는 위 TDD에만 수렴.
- 사용자 후속 승인: 요구 변경/실패 대응 → Luna의 기록 이해·소화 → 반복·비교 → 격리·병합·복구 순서로 진행한다. 첫 단계 정본은 [Sol 요구 변경 시험 02](../tests/v2-sol-requirement-change.md). 이후 todo #18–20에 의존 순서 보존. 앞선 정책 정렬 실패 #16은 별도 유지하며 자동 수정하지 않는다.
- 변경 시험02는 child가 연구 문서에서 변경 조건을 미리 읽어 비예고 변경 평가로 판정하지 않았다. 사용자 선택으로 작업자 입력을 별도 root에 분리한 재시험03 수행: 실제 테스트7개·parent 확인271항목 통과, 이전 계획 완료 거부/이력 보존/새 검증 완료 확인. 전체 tool trace에서 외부 연구 문서 읽기는 없었다. 태스크 설명+이력 묶음의 읽기를 다음 Luna 단계로 평가한다. 상세 결과·한계·원본 증거는 변경 시험 정본에 수렴.
- Luna 읽기 첫 시험 완료: 기록 묶음만 읽고 핵심 질문7개 취지 일치, 주장14개 출처 대조, 표현 보완1개. 현재 요구와 과거 통과·parent 개입 구별. [Luna 시험 정본](../tests/v2-luna-record-reader.md)에 근거와 한계 보존. 단발 소화 가능성이지 지속 갱신·비용 절감 증명은 아님.
- 사용자 정정: 기존 하네스 정책정렬 실패는 새 하네스 연구 완료의 blocker가 아니며 유지보수 #16으로만 분리한다. 새 실험의 코드/기록/모델 평가 기준을 적용한다. 검증 스크립트 비활성화·기존 오류 해결을 의미하지 않는다. #15/#17 연구 완료 상태를 이에 맞춰 정리했다.

## 7. 공정한 비교와 증거 보존

- 비교 시 요구·초기 코드·지식·태스크 난이도·모델 설정·예산을 맞춘다. 조작하는 축은 처음에는 하나로 제한한다.
- plan-informed 조건만 더 많은 정답 정보를 받지 않도록 PRD의 정보량을 통제한다. 계획 자체의 품질 평가는 별도 과제다.
- 테스트 정답·미래 정정·평가자 의견은 작업/소화 모델에 숨긴다. 전용 새 문맥에서 읽기 시험을 수행한다.
- 모델 비결정성을 고려해 반복 결과와 최악 사례를 보고한다. 최소 반복 수·합격률은 사전에 합의한다. 소수 표본으로 p95나 규모 확장성을 주장하지 않는다.
- 토큰·비용에는 계획, 기록, 소화, 읽기, 조율, 재시도, 사람 보완 후 재실행까지 포함한다. 청구/캐시 단가를 모르면 토큰과 지연만 보고하고 금액을 추정 확정하지 않는다.
- run ID, 입력/코드/프롬프트 버전, 실제 model ID·설정, 툴 receipt, 모델 출력, 채점표, 실패·취소를 보존한다. 민감 정보 수집 제한은 실행 전 정한다.
- 초기 사례가 평가용으로 튜닝되면 별도 holdout 사례를 둔다. 런타임 오류와 모델 판단 실패를 구분해 집계한다.
- 숫자 합격선은 이 보고서에서 임의 확정하지 않는다. 권한 밖 반영·정답 누출 등은 별도 안전 실패 항목으로 합의할 후보이다.

## 8. 연구 자료의 활용 위치

- W3C RDF/OWL/SHACL: E의 의미·관계·구조 검사 구별. 표준 채택이 실험 전제는 아님.
- Palantir Action: A/C의 입력·검증·상태 변경 계약 참고. Palantir 플랫폼 복제나 실행 채택 아님.
- Python Wiki Compiler: B/H의 결정적 처리와 E의 의미 판단 분리, 단계별 테스트 참고. 어휘 연결로 의미 소화를 대체하지 않음.
- A-MEM/Mem0/Zep/Sleep-time Compute/LongMemEval: E/F의 갱신·시간·보류·비용 평가 참고.
- CQRS/Orleans/Restate/Kafka: G/H/I의 읽기·쓰기 분리, 처리 위치·복구 원리 참고. 자연어 소화의 결정적 재현을 보장하지 않음.
- 출처 링크와 원문/검색 발췌/미재현 경계는 [연구 정본](v2-vision-feasibility-research.md)에 보존되어 있다.

## 9. 누락 없이 검토해야 할 경계

1. 업무 계획은 의도이고 실행 증거는 실제 결과다. 두 표현을 하나로 혼동하지 않는다.
2. 완료 체크는 의미의 진실 보증이 아니다. 변경된 완료 조건에 과거 검증을 그대로 재사용하지 않는다.
3. 업무를 닫는 것, 작업 지식을 소화하는 것, 공통 지식으로 병합하는 것은 서로 다른 경계다.
4. 로그를 한 번 제출하게 하는 것과 DB 내부를 한 테이블로 만드는 것은 다른 결정이다.
5. 기준 commit만으로 dirty 상태·정책·지식 소화 지연까지 식별할 수 없다.
6. log/원장 명칭보다 정정·보존·처리 계약이 중요하다.
7. 별도 임시 지식이 없어도 미소화 읽기 범위와 처리 경계는 필요하다.
8. 기록 내용의 지시가 실행 권한으로 승격되면 안 된다. 프롬프트만으로 OS/DB 격리를 보장하지 않는다.

## Rule placement
- Rule: V2 연구 책임 분해와 단계별 시험 후보·증거 경계를 정리한 요청 보고서.
- Scope: transient-plan
- Primary record: `.lazy-harness/planning/v2-research-test-map.md`.
- Why not AGENTS.md: 실행 규칙이나 최종 제품 계약을 추가하지 않는 연구 계획이다.
- Why not local notes: 프로젝트 연구이며 개인 런타임 설정이 아니다.
- Confirmation: user-confirmed — 보고서 작성 요청. 각 실험 실행·스키마·합격선 채택은 미승인.

## Discovery capture / Layer assessment
- Planning: 이 보고서에 연구 분해와 실험 후보를 보존하고 구상 정본에서 참조한다. 현재 구상의 정본은 기존 연구 문서 유지.
- SDD: candidate — 업무 상태/기록 툴/반영 계약, 아직 채택하지 않음.
- BDD: candidate — 계획 변경·실패·인계·병합의 시험 시나리오.
- SSOT: no independent delta — DB·모델 실행 ID·운영 정책 채택 없음.
- DDD: candidate — 업무/태스크/현재 지식/행동 이력 의미 경계.
- TDD: candidate — 새 테스트 코드는 작성·실행하지 않음. 기존 샌드박스 회귀 계약을 대체하지 않음.
- ADR: none — 기술 선택 결정 없음.

## Implementation map
- 이 보고서는 연구 계획 산출물이며 신규 런타임 함수·클래스·서비스는 없다. 추정 graph edge를 생성하지 않는다.
- 구상 정본: [V2 research](v2-vision-feasibility-research.md), 특히 §15–16.
- 검수 설명서: [V2 review HTML](v2-review.html). 업무 객체·기준 상태 후속 대화 전 스냅샷이므로 최신 내용을 전부 담고 있지는 않다.
- 기존 실험 계약: [V2 sandbox bootstrap](../tests/v2-sandbox-bootstrap.md).
- 기존 실험 파일: `experiments/v2-sandbox/sandbox.py`, `test_sandbox.py`, `test_scoring.py` — 명시적 합성 replay/채점/격리 기반. 본문의 A–I 제품 모듈 구현으로 매핑하지 않는다.
- 검증 정책: [test-strategy.xml](../tests/test-strategy.xml) — 문서 제작 검증과 미래 연구용 모델 평가를 구별한다.

## Evidence capsule — 새 규칙 전이 단일시험 35 (2026-09-22)
- 사용자 승인 범위에서 이미 공개된 authorized FROZEN corpus 중 이번 보강에는 처음 쓰는 세 원문 `D09-F004-A04`, `D06-F005-A07`, `D04-F017-A02`를 사용했다. 25–34 보강에 사용한 `D04-F037-A02`, `D05-F006-A04`, `D04-F028-A04`는 제외했다. 새 holdout이나 새 제품 결정을 뜻하지 않는다.
- 첫 호출 전에 exact source/provenance/hash, 사례별 비공개 질문3개와 원문 근거 정답, suite34 Recorder guidance와 strong reader instruction의 verbatim 값, strict flat schema, counterbalanced 순서9개를 고정했다. no-change control만 사용했고 source arm에는 exact raw source, record arm에는 이번 Recorder의 actual `record_text`만 제공했다.
- Luna medium 실제 유료 호출은 순차9/9회(receipts 1756–1764), retry/repair/fallback/grader 없음. provider 보고 추가비용 `$0.01071460`; ledger `spent 32.35471151 → 32.36542611`, `held 2.21489061` 유지, unknown-held 1/895/989 및 보호 행 불변. 실행/입력 freeze/종료 UTC와 monotonic 값은 summary에 보존했다.
- worker 잠정 직접 의미 대조: 새 기록3/3은 faithful·standalone·useful, unsupported addition0; 원문 arm 9/9와 기록 arm 9/9가 질문별 원문 근거에 부합했다. upstream record error0, downstream source error0, downstream record error0으로 분리했다. 답끼리 일치하거나 schema 통과만으로 판정하지 않았다. Parent 최종 검토 전 잠정 결과다.
- 범위: 세 사례 각1회이며 이미 노출된 corpus다. 일반 신뢰도, 독립 holdout 성능, 기록 보강의 인과효과, 실제 제품/운영 적용을 증명하지 않는다. 제품 source·DB·정책·설치·전역 설정은 변경하지 않았다.
- Evidence/readback: `experiments/v2-agentic-wiki-fragment-01/tr-new-rules-transfer-35/actual-run-01/`의 `frozen-design-before-first-call.json`, `bound-records-after-recorder.json`, raw request/transport/tool/answer 전부, `manual-assessment.json`, `summary.json`, `report-ko.html`, `artifact-index.json`, `link-check.json`. runner는 `run.py`, transport guard는 `provider_bridge.mjs`, offline contract는 `test_contract.py`다.
- Validation 경계: focused contract test는 통과했다. checkpoint `lazy check`는 기존 연구 artifact의 binary NUL/의도적 malformed JSON scanner debt 때문에 실패했으며 이번 파일의 의미 실패로 승격하지 않는다. 최종 standard 결과는 별도 실행 근거로 보고한다.
- Discovery capture: Planning=this compact capsule only. TDD/SDD/BDD/DDD/ADR/SSOT=no independent product delta; 이 operational test는 새 제품 contract나 정책 채택이 아니다.

## Evidence capsule — 반복 일정 중복 제거 오류 교정 40 (2026-09-22)
- **사용자 승인과 이유:** 사용자는 공개된 기존 요구 `Array.from(new Set([...existing, occurrenceDate]))`를 새 규칙으로 바꾸지 않고, 39 후보가 기존 중복을 보존하는 결함을 실제 반례로 실행해 교정하도록 승인했다. 39의 옛5검사는 `[A]+A`만 확인해 `[A,A]+B`를 놓쳤으므로, 과거 pass를 실패로 바꾸지 말고 ‘통과했지만 불충분’으로 바로잡는 것이 목적이었다.
- **실행 결과:** byte-exact 39 후보는 옛5검사에서 실제 pass했고, 동결 확장 oracle에서는 `[A,A]+B`가 기대 `[A,B]` 대신 `[A,A,B]`가 되어 fail했다. 같은 oracle의 authored positive control과 Luna medium Work 후보는 기존5개+확장5개 총10 assertion을 pass했다. Work diff는 전체 결합 목록을 stable dedupe하도록 바꿨고 분기·fallback·권한 보고는 유지했다.
- **4-role 결과:** 유료 호출은 Work→Recorder→Digester→record-only Answer 순서4회(receipts 1789–1792), 추가비용 `$0.00536`; Recorder는 39의 misleading stable-dedupe 검증 주장을 authoritative experimental correction으로 정정했다. Digester는 변경되지 않은 domain policy가 아니라 prior experimental record/candidate claim을 정확한 교정 대상으로 선택했고, Answer는 Recorder `record_text`만 읽었다.
- **실패 보존과 경계:** 첫 local predispatch attempt는 request `maxTokens`에 catalog ceiling을 넣어 `validateRequest`가 거부했으며 reservation·유료 호출0회였다. 두 번째이자 마지막 기계적 수정은 request에는 stage intended output을, `Ledger.reserve`에는 catalog 128000 ceiling을 전달해 완료했다. 이는 공개 date-list 회귀 반례와 관련 확장 사례이며 독립 holdout·production 검증·일반 신뢰도 증거가 아니다.
- **Evidence/readback:** `experiments/v2-agentic-wiki-fragment-01/tr-error-correction-40/`의 `old39-preservation-manifest-before.json`, `actual-run-01/` 실패, `actual-run-02-mechanical-attempt-02/`의 freeze·controls·raw requests/responses·wire proof·diff·corrected record·Digester·Answer·summary·`report-ko.html`·`post-run-verification.json`. old39 전체192파일과 보호 ledger rows는 불변이다.

| Layer completeness | 판단 |
|---|---|
| DDD | no independent delta — 기존 recurrenceExceptions 의미를 바꾸지 않음 |
| SDD | no independent delta — 공개 API·제품 contract·domain policy 변경 없음 |
| BDD | no independent delta — 제품 사용자 흐름이나 production 동작 변경 없음 |
| SSOT | no independent delta — schema·config·ownership 변경 없음 |

Discovery capture: Planning=이 compact capsule만 갱신. 회귀 증거는 sibling40 실험 artifact에 보존했고 별도 TDD 기록을 중복 생성하지 않았다. ADR/제품 정책 채택 없음.
