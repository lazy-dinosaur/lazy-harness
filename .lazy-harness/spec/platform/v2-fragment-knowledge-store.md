# SDD — V2 조각(Fragment) 지식 저장소 설계 초안

Status: draft
Date: 2026-09-18
Layer: SDD
Related planning: `.lazy-harness/planning/v2-vision-feasibility-research.md`
Related evidence: `.lazy-harness/evidence/v2-knowledge-representation-research-final-01.html`
Related SDD: `.lazy-harness/spec/platform/host-root-resolution.md`

## Rule digest

- Status: needs-review
- Layer: SDD
- Scope: host-project
- Aliases:
  - 조각 저장소
  - fragment store
  - V2 지식 스키마
  - workspace 조각
  - host 경계
  - 소화 파이프라인
- Applies when:
  - V2 지식 저장 방식(조각/workspace/관계)의 스키마·질의·갱신 계약을 설계하거나 검토할 때
  - V1 기록을 조각으로 옮기는 마이그레이션을 계획할 때
  - 검색 결과가 부족할 때 도메인 라우팅/관계 순회를 도입하자는 제안이 나올 때
  - workspace 종료·소화(digestion)·git 연동 동작을 정할 때
- Must:
  - 조각을 단 하나의 정본으로 두고 문서는 조각에서 만들어 내는 읽기 전용 뷰로 본다
  - 모든 조각/workspace/관계에 `host_id`를 두고 **host 경계는 항상 강제**한다
  - 검색은 기본 전역(해당 host 안에서)이며 도메인·kind 필터는 선택적 좁히기로만 쓴다
  - 미소화 작업 발견은 즉시 workspace 조각으로 적어 세션이 죽어도 잃지 않게 한다
  - 에이전트는 `candidate`까지만 쓰고, `confirmed` 승격은 사용자 확인 또는 명시적 위임이 있을 때만 한다
  - 모든 조각은 ID·출처(provenance)·조건/예외를 보존하고 갱신은 revision 확인 후에만 한다
  - 조각 생성·보완은 §1.1의 저장 품질 규격 v1을 적용하고, 구조 검사와 의미 검수를 분리해 준수 근거를 남긴다
- Must not:
  - 이 초안을 구현 승인·DB 생성 승인으로 읽지 않는다 (Status: draft)
  - 도메인 필터를 검색 전 라우팅 게이트로 만들지 않는다 (host 경계와 혼동 금지)
  - git 존재를 정체성으로 삼지 않는다 (git은 선택적 binding, 비-git 프로젝트도 완전 지원)
  - 삭제로 기록을 지우지 않는다 (비활성화 + history 보존)
  - 다른 workspace의 조각을 기본 검색에 섞지 않는다
- Record completion:
  - 사용자가 스키마/질의/소화 계약을 확정하거나 갱신 실험 결과가 나오면 이 기록을 갱신한다
- Related records:
  - `.lazy-harness/planning/v2-vision-feasibility-research.md`
  - `.lazy-harness/spec/platform/host-root-resolution.md`
  - `.lazy-harness/spec/platform/record-write-update-policy.md`

---

## 1. 목적과 근거

이 문서는 **V2에서 지식을 어떤 모양으로 저장할지**를 정하는 설계 초안이다. 구현이 아니라 계약 초안이다.

| 근거 | 한 줄 결론 |
|---|---|
| [통합 결론](../../evidence/v2-knowledge-representation-research-final-01.html) | 정본은 조각. 문서형·triple·관계는 아래 이유로 탈락/보류 |
| [문서형 vs 조각형](../../evidence/v2-document-fragment-complete-report.html) | 단발 검색 조각 **86.2%** vs 문서 68.4% |
| [P2 실제 V1 비교 r3](../../evidence/v2-agentic-p2-opus-complete-report-r3.html) | 실제 Reader hop **47.6%** vs 조각 lane **81.0%** |
| [D-hybrid](../../evidence/v2-d-hybrid-study-01.html) | 조각만 **93.2%**(55/59) vs 조각+관계 91.5% → **관계는 null 결과**, 재귀 순회 0회 호출 |
| [Triple stage 1 종료](../../evidence/v2-triple-stage1-closeout-01.html) | 순수 triple은 **≈29배 표현 팽창**(13.37 출력토큰/바이트)·갱신 비국소성으로 **기각** |
| [500문서 비교](../../evidence/v2-embedding-comparison-500-complete-report.html) | 전역 검색이 이미 천장. 도메인 필터는 최악 순위만 개선, all@5 불변 → **도메인은 메타데이터** |
| [한/영 4조건](../../evidence/v2-embedding-language-complete-report.html) | 언어 조건별 회수 차이는 있으나 영어 정본화 결론은 없음 |

탐색 패러다임(사용자 확정): V2의 검색은 **평평한 조각 공간에 대한 병렬·반복 재질의**다. **hop은 V2 개념이 아니다**. 관계는 본문에 드러나지 않는 연결(대체·암묵 예외)에만 선택적으로 둔다.

### 1.1 조각 저장 품질 규격 v1 (사용자 확정, 준수 검사 구현 전)

1. **독립 이해:** 대상·행위·적용 조건을 자체 본문에서 알 수 있어야 한다. ‘같은 상태/위 내용/이것’의 참조 대상이 빠지면 보완 대상으로 판정한다.
2. **의미 단위:** 하나의 핵심 주장을 담되, 그 주장의 조건·부정·예외를 떼어내 의미를 바꾸지 않는다. 고정 길이 분할은 기준이 아니다.
3. **의미 보존:** 의무/허용/금지, 시간·주체·범위·예외 및 불확실성을 원문과 대조한다. 관련 문맥은 원문 근거가 있을 때만 명시한다.
4. **추측 금지:** 원문에 없는 이유·조건·확정성을 보충하지 않는다. 모호함이 해소되지 않으면 candidate로 보존하고 검토 사유를 남긴다.
5. **출처:** 본문과 보충 문맥의 원문 위치·버전 또는 동결 해시를 함께 보존한다. 식별자와 원문→조각 대응표를 유지한다.
6. **묶음:** 규칙·근거·예외·검증 사례의 관련성을 보존하되 연결이 없으면 이해할 수 없는 본문을 정당화하지 않는다. 대체·충돌 연결은 근거와 방향을 명시한다.
7. **확정성:** 미확정 발견·제안과 확인된 사실을 구별한다. 모델이 검사를 통과했다고 사용자 확인을 날조하거나 confirmed로 자동 승격하지 않는다.

준수 결과는 기준별 pass/fail/needs-review와 원문 근거로 남긴다. ID·출처·필수 필드 등 구조 검사는 자동화할 수 있지만 의미 보존은 별도 검수 대상이다. 미달 조각은 임시 보존하고 보완 대상으로 표시한다. 이 절은 규격이며 검사 도구가 이미 강제하고 있다는 주장이 아니다.

#### 1.1.1 작업자 제출(원장 fact) 적용 — 최소 구조 게이트 (사용자 확정 2026-09-25)
- **이 규격 v1 이 조각의 단일 규격이다.** 문서 조각화(fragmenter/prompt-v2)와 작업자 judgement 제출(원장 fact)이 모두 따른다. 작업자 작성 가이드(spec/v2-worker-judgement-authoring-guide.md)는 이 절을 따른다.
- **원장 = 자연어 문장 + 규격 칸.** 원장 fact 의 `fact` 문장이 소화 때 **변환 없이 그대로** 정본 조각 text 가 된다(store.build_fragment 가 불일치 거절). 칸은 작성 검사용이며 조각 source 메타데이터로 보존(subject, why). 이유: 소화 단계 변환은 오류 자리(조각화 실측 언어 표류 4/30)와 호출을 늘리고 검수 대상과 정본이 어긋난다. 순수 triple 정본 기각(2026-09-18)과 충돌하지 않음 — 정본은 여전히 자연어.
- **코드 강제(runner.lint_fact, 실패 시 rejected_input)** — cycle-01 실제 회부 원인만 막는 최소안(사용자 선택: 칸을 늘리면 형식만 채우는 칸 채우기가 생김):
  | 칸/조건 | 규격 기준 | 오류 코드 |
  |---|---|---|
  | `subject` 필수, fact 문장에 그대로 등장 | 1 독립 이해 | E_SUBJECT |
  | kind decision·constraint 는 서로 다른 근거 2개 이상(누가 정했나 + 무엇을 정했나: 사용자 발언 + 문서/코드 원문) | 5 출처 | E_EVIDENCE_COUNT |
  | kind decision 은 `why`(사용자가 말한 이유) 필수 | 6 묶음 | E_WHY |
  | evidence_source user_confirmed 는 되묻는 말로 끝나지 않는 사용자 발언 원문 인용 필수(?·그지·맞지·잔아·할까 등으로 끝나면 거절 — 확정을 먼저 받는다) | 7 확정성 | E_USER_REF |
- **개정 3 (사용자 승인 2026-09-27 'a로 가자', update-01 round_forms 근거)**: E_USER_REF 는 evidence_source user_confirmed 일 때 인용된 user_utterance 가 **모두** 되묻지 않는 발언이어야 통과한다(빈 인용도 거절). 이전에는 하나만 비질문이면 통과해, 확정 발언 옆에 질문('~로 쓰면 되지?')을 함께 붙이면 질문이 확정 근거로 섞여 들어갔다. 질문을 맥락으로 인용하려면 다른 근거 유형으로 붙인다. 구현: runner.lint_fact, 보호 테스트 test_standard_lint.py::test_user_confirmed_every_cited_utterance_must_be_non_question (전체 124 passed).
- **개정 2 (사용자 승인 2026-09-25, write-01 근거)**: E_CLAIM_QUOTE 의 '식별자' 는 runner.claim_identifiers 가 정한다 — 백틱 안·camelCase·경로·파일(확장자 포함 통째로)·상수·숫자 포함 ID·대문자 약어+접미·어휘 목록 밖 대문자 단어는 인용에 없으면 거절, 흔한 어휘 약어(API·SSOT·LLM 등 목록)·대문자로 시작하는 일반 하이픈 단어·일반 단어 슬래시는 대상 아님. 거절 피드백에는 고치는 법(원문 줄을 근거로 추가하거나 문장에서 빼기)을 함께 준다.
- **개정 (사용자 승인 2026-09-25, write-01 근거)**: 위 표의 E_SUBJECT 는 거절 전에 runner.normalize_fact 가 자동 보정(subject 를 문장 앞 주어로), keywords 도 자동 보정(E_KEYWORD 는 보정 후에도 남을 때만), **E_EVIDENCE_COUNT 는 거절이 아니라 경고**(근거 충분성은 Jev). 거절 유지: E_CLAIM_QUOTE(인용에 없는 식별자), E_USER_REF(되묻는 발언), E_WHY, 스키마. 이유: 작성 AI 가 내용은 맞게 쓰고 형식만 어긋난 사실의 60% 가 거절되어 실제 사용에서 v1 보다 적게 남았다.
- 의미 기준(2 의미 단위, 3 의미 보존, 4 추측 금지)은 Jev(is_supported·durability·impact·utterance_status)가 판정한다. 작업 중 검수 패킷의 evidence_quote 는 fact 의 **모든 근거**를 [type locator] 원문으로 나열한다(worktime_driver.build_packet).
- 구현: runner.py(MULTI_EVIDENCE_KINDS, QUESTION_TAIL, lint_fact), worktime_driver.build_packet, store.build_fragment(source.subject/why). 보호 테스트: test_standard_lint.py 4개. 러너 전체 98 passed(2026-09-25). 효과 실측: cycle-01 회부 3건 재제출(진행 예정).

### 1.2 역할별 작성·검수·재작성·충돌·수명주기 계약

- **작성:** multi-rule source에는 독립적으로 의미 있는 조각 목록을 허용한다. 문장 수·길이는 독립 claim 수가 아니며, 한 claim의 주체·대상·필수 조건·예외는 함께 둔다. relevant claim coverage와 원문 fidelity/scope loss를 별도 측정하고 장문화나 전체 quote 부착을 요구하지 않는다.
- **검수:** candidate만 읽는 자립성 검사(주체·대상·지시어·조건)와 source 대조 fidelity 검사(누락·범위·모순·unsupported addition)를 순서대로 분리한다. 기준별 evidence를 남기고 focused fragment에 source 전체 coverage를 강요하지 않는다.
- **재작성:** 고정 source·flawed candidate·directive만 입력받고 reviewer 출력에는 의존하지 않는다. 지정 결함을 실제 before/after 문구로 고치되 이미 명확한 내용은 유지하고 새 누락·사실을 만들지 않는다. 정확한 control은 byte-identical과 빈 diff를 허용한다.
- **충돌:** semantic relation, same-claim time/scope/entity alignment, assertion authority/uncertainty, replacement authorization을 별도 축으로 판정한다. tentative/unknown assertion도 논리적으로 모순될 수 있지만 그 자체로 기존 지식 대체를 승인하지 않는다.
- **수명주기:** CURRENT와 EVENT의 실제 차이·권위·expected/allowed/forbidden operation을 먼저 확인한다. already-current는 retain, tentative/unknown은 retain 또는 retain-needs-review 같은 비파괴 처리를 허용한다. 실제 supersession은 predecessor lineage를 보존하고 deactivate는 scope-specific evidence, snapshot/history, restore path를 요구한다. update/supersede처럼 의미상 경계가 겹치면 단일 exact gold를 강제하지 않고 허용 집합을 남긴다.

> **developmental retest 증거(2026-09-20):** 같은 동결 9문서 source를 직접 공급한 Luna medium 5역할×8case×2회에서 작성 의미감사 coverage 40/40 claim-call·fidelity 16/16, 재작성 fidelity 14/16, 검수 source-adjudicated 23/28 defect-call과 unsupported finding 7건, 충돌 54/64 field-call, lifecycle allowed 15/16·forbidden operation 0을 관측했다. 노출된 사례·same-worker Sol 감사이며 독립 확증이 아니다. review-05 control의 `해당 sheet` ambiguity와 conflict authority/replacement provenance가 사전 audit에서 걸러지지 않은 결함도 동결 상태로 보존했으므로 fixture audit 통과를 자동화 완료로 해석하지 않는다. 원자료/한계: [역할 지침 개정 보고서](../../evidence/v2-fragment-role-guidelines-retest-01.html).
>
> **experimental role-base pointer:** `experiments/v2-agentic-wiki-fragment-01/role-contract-foundation-01/`은 기존 `0.1.0-draft`를 byte/hash 보존하고, 별도 `0.2.0-draft` 제안에서 trusted controller envelope와 untrusted data, 실제 candidate-only review standalone/source fidelity 분리, per-assertion provenance, controller-only lifecycle permission을 offline 조립·검사한다. exact diff/rationale/traceability가 함께 있으며 새 의미는 owner review 전 experimental proposal이다. 이 pointer는 제품 계약 채택·역할 성능·semantic injection 방지·다음 inference 승인이 아니다.
>
> **THREE-role offline foundation pointer (2026-09-20):** 사용자 확정 자연 흐름 Reader → 작업 중 Temporary recorder → 나중 Digester를 `experiments/v2-agentic-wiki-fragment-01/three-role-flow-foundation-01/`에서 별도 experimental `0.1.0-draft`로 조립했다. 기존 다섯 역량은 Digester/품질 진단 subskill로 남고 다섯 production agent가 아니다. Reader는 supplied candidate set 선택만 하며 검색 중 소화·silent promotion을 하지 않고, recorder는 current workspace temporary만 기록하며, Digester는 source-backed proposal만 낸다. 사용자 batch approval 뒤 deterministic fixture applier가 scope/revision/history/idempotency/restore를 검사한다. 16 focused offline tests와 receipt는 schema/mechanics 증거일 뿐 semantic search, prompt-injection 방지, 모델 품질, full-KB coverage, DB/production 채택을 증명하지 않는다. 기존 5-role `0.1.0/0.2.0` hash와 ledgers/holds는 불변이며 paid study·integration은 실행하지 않았다.

연결 비교의 실험 경계: 관련성 근거가 있는 규칙/이유/예외/검증 사례 및 대체/충돌만 후보로 둔다. 출처상 같은 묶음이라는 사실과 의미 관계 판정은 구별한다. 연결 회수에도 동일 host/workspace 경계와 토큰 예산을 적용하며 자동 전량 확장은 하지 않는다. 관계별 세부 스키마·회수 한도는 3단계 protocol에서 동결한다.

검증 순서: ① 기존 조각 vs 규격 조각(연결 확장 없음) → ② Luna low/medium의 기록·읽기 분리 비교 → ③ 동일 규격 조각의 연결 회수 유무 비교. ② 결과 전 기본 참가자는 Luna medium이며, low 채택은 사전 정의한 허용 품질차와 중대 오류 기준을 충족할 때만 판단한다.

> **4-arm 소표본 증거(2026-09-20, known diagnostic):** 이전 24 source unit/12 task를 A 원본, B 원문 불변+source-grounded metadata, C 원본+bounded source-section expansion, D standardized+source context로 각 1회 비교했다. A 대비 B 2승/3회귀/7동점, C 4승/1회귀/7동점, D 4승/2회귀/6동점이었다. seed recall@20 합 A/B/C/D=17/17/17/18, expansion-only C/D=4/3이다. E06 필수 ID는 seed rank381/250에서 여전히 미회수였으나 query/gold-blind 인접-section 확장으로 C/D에 노출됐다. 반면 standardized base의 `D06-F005-A06` severe meaning regression은 보강 context와 별개로 그대로 남는다. 목적표집·prior exposure·same-model nonblind grading·1회/cell이므로 판정은 inconclusive이며 관계/문맥 확장을 기본 계약이나 생산 enforcement로 승격하지 않는다. [보고서와 원자료](../../evidence/v2-fragment-four-arm-small-sample-01.html)

## 2. 정체성과 경계 (사용자 확정)

### 2.1 host 경계는 벽, 도메인 필터는 문

| 구분 | 성격 | 동작 |
|---|---|---|
| `host_id` | **항상 강제되는 벽** | 모든 질의에 자동으로 붙는다. 끌 수 없다. 다른 host의 조각은 존재 자체가 보이지 않는다 |
| `domain` | **선택적 좁히기(문)** | 부르면 좁혀지고 안 부르면 전역. 검색 전에 범위를 자르는 게이트가 아니다 |

두 개를 같은 것으로 취급하면 안 된다. host 경계는 사고 방지 장치이고, 도메인 필터는 편의 기능이다.

### 2.2 정체성은 스스로 발급한 ULID

- host 식별자는 **init 시점에 프로젝트 marker 파일에 적어 두는 ULID**다. 경로나 git remote에서 유도하지 않으므로 폴더를 옮기거나 이름을 바꿔도, git이 없어도 정체성이 유지된다.
- marker 탐색은 V1의 host root 해석 규칙을 **재사용**한다(`.lazy-harness/spec/platform/host-root-resolution.md`: `LAZY_HOST_ROOT` 우선, 다음 worktree top-level, 심볼릭 링크 대상 checkout을 root로 착각하지 않기).

### 2.3 workspace는 1급 테이블

작업 단위(브랜치 작업, 실험, 조사 세션)를 workspace로 둔다. 조각은 workspace에 임시로 붙어 있다가 소화되면 host 정본으로 올라간다. 인식 우선순위(위에서 아래로, 먼저 맞으면 끝):

1. **명시적 지정** (사용자/에이전트가 workspace를 직접 지정)
2. **git worktree + branch binding 일치** (bound 된 경우에만)
3. **같은 디렉터리의 active workspace**
4. **host 기본 workspace**

git은 **선택적 binding**이다. 없으면 3·4번으로 동작하며 비-git 프로젝트도 1급으로 지원한다.

## 3. PostgreSQL 스키마 초안 (DDL draft)

아직 만들지 않았다. 아래는 검토용 초안이다.

```sql
CREATE TYPE fragment_kind AS ENUM
  ('fact','decision','rationale','rejected','constraint','procedure','term','question');
CREATE TYPE fragment_confidence AS ENUM ('confirmed','candidate','contested');
CREATE TYPE workspace_status AS ENUM ('active','closed','digested');

-- 작업 공간: 1급 테이블
CREATE TABLE workspace (
  id         TEXT PRIMARY KEY,                  -- ULID
  host_id    TEXT NOT NULL,                     -- 항상 강제되는 경계
  label      TEXT NOT NULL,
  bindings   JSONB NOT NULL DEFAULT '{}',       -- {path, git_branch?, git_worktree?, session_ids[]}
  status     workspace_status NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at  TIMESTAMPTZ
);
CREATE INDEX ON workspace (host_id, status);

-- 조각: 유일한 정본
CREATE TABLE fragment (
  id            TEXT PRIMARY KEY,                 -- ULID
  host_id       TEXT NOT NULL,                    -- 벽. 질의에서 절대 생략되지 않는다
  workspace_id  TEXT REFERENCES workspace(id),    -- NULL = host 정본 계층
  alias         TEXT NOT NULL,                    -- 사람이 읽는 별칭: domain + seq
  domain        TEXT NOT NULL,                    -- 메타데이터일 뿐, 라우팅 게이트 아님
  seq           INTEGER NOT NULL,
  text          TEXT NOT NULL,                    -- 조건·예외를 보존한 자연어 한 덩어리
  keywords      TEXT[] NOT NULL DEFAULT '{}',
  kind          fragment_kind NOT NULL,
  group_id      TEXT,                             -- 같은 capture(결정 묶음) 식별자
  revision      INTEGER NOT NULL DEFAULT 1,
  active        BOOLEAN NOT NULL DEFAULT TRUE,    -- soft delete
  confidence    fragment_confidence NOT NULL DEFAULT 'candidate',
  source        JSONB NOT NULL,                   -- {kind, path|url, lines, commit?, pr?, captured_by, turn}
  valid_from    TIMESTAMPTZ,
  superseded_at TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (host_id, domain, seq)
);
CREATE INDEX ON fragment (host_id, workspace_id) WHERE active;
CREATE INDEX ON fragment (host_id, domain) WHERE active;
CREATE INDEX ON fragment (host_id, kind) WHERE active;
CREATE INDEX ON fragment (group_id);
CREATE INDEX ON fragment USING GIN (keywords);

-- 임베딩: 파생물(언제든 다시 만든다)
CREATE TABLE fragment_embedding (
  fragment_id TEXT NOT NULL REFERENCES fragment(id) ON DELETE CASCADE,
  model       TEXT NOT NULL,                      -- 예: 'e5-small-fp32'
  vector      VECTOR(384) NOT NULL,               -- pgvector
  text_hash   TEXT NOT NULL,                      -- 본문 변경 감지 → stale 판정
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (fragment_id, model)
);

-- 이력: append-only
CREATE TABLE fragment_history (
  history_id  BIGSERIAL PRIMARY KEY,
  fragment_id TEXT NOT NULL,
  revision    INTEGER NOT NULL,
  op          TEXT NOT NULL,                      -- create|update|deactivate|supersede|promote
  snapshot    JSONB NOT NULL,                     -- 변경 직전 조각 전체
  reason      TEXT,
  actor       TEXT,
  at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 관계: 최소 시작 집합만. 본문에 안 드러나는 연결 전용
CREATE TYPE relation_type AS ENUM ('supersedes','conflicts-with');
CREATE TABLE relation (
  host_id    TEXT NOT NULL,                       -- 관계도 host 경계를 넘지 못한다
  src        TEXT NOT NULL REFERENCES fragment(id),
  dst        TEXT NOT NULL REFERENCES fragment(id),
  type       relation_type NOT NULL,
  why        TEXT NOT NULL,                       -- 근거가 되는 원문 구절(필수)
  confidence fragment_confidence NOT NULL DEFAULT 'candidate',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (src, dst, type),
  CHECK (src <> dst)
);
```

설계 메모 — `part-of` 관계는 만들지 않는다(묶음은 `group_id` 한 컬럼으로 충분, D 실험에서 결정론적 파생). 관계 타입은 **2개로 시작**한다(D 실험에서 `refers-to`/`applies-to`가 66%였으나 정확도 기여 없음). `workspace_id IS NULL` = host 정본이며 소화(promote)는 이 컬럼을 NULL로 바꾸는 일이다.

## 4. 질의 인터페이스 계약

```text
search(query, kind[]?, domain[]?, per_kind_quota?, limit=8, offset=0,
       include_inactive=false, workspace='current'|<id>|'canonical_only')
  → [{id, alias, host_id, workspace_id, domain, kind, text, keywords, source, confidence, score}]
expand_group(group_id)   → 같은 묶음의 모든 조각(결정+근거+기각안+제약)
read(ids[])              → note: 원문 그대로 + 출처 + 조건, 요약/병합 없음
```

원칙
1. **host 경계는 자동·필수.** 모든 질의는 현재 host로 묶인다. 인자로 끌 수 없다.
2. **기본 계층 = host 정본 + 현재 workspace.** 다른 workspace의 조각은 **보이지 않는다**(soft delete와 다른 별개 계층 규칙).
3. **기본은 전역 검색.** 도메인/kind 필터는 선택적 좁히기다(500문서 근거: 필터는 최악 순위만 개선, all@5 불변).
4. **후순위 후보 접근은 필수.** `offset`으로 점수 낮은 후보까지 갈 수 있어야 하고 고정 top-k 영구 차단은 금지다.
5. **kind별 할당량(per_kind_quota).** `rationale`이 결과를 덮어 `decision`을 밀어내는 것을 막는다. 예: 10개 = decision 4 + fact 4 + rationale 2.
6. **note는 조각의 묶음**이다. 숨은 LLM 요약·사실 보충 금지(P2 B lane과 동일 계약).
7. 재질의가 기본 전략이다. 링크 따라가기(hop)를 전제하지 않는다.

## 5. 쓰기·갱신 수명주기

| 단계 | 계약 |
|---|---|
| 생성 | 확정 순간(record-as-output) 조각이 태어난다. 나중에 문서에서 뽑는 게 아니라 **그 자리에서 적는다** |
| 작업 중 발견 | 아직 정리되지 않은 발견도 **즉시 workspace 조각으로 저장**한다(`workspace_id` 채움, `confidence='candidate'`). 세션이 죽어도 잃지 않는다 |
| 갱신 | `UPDATE ... WHERE id=? AND revision=?` — 불일치면 거부(낙관적 잠금). 성공 시 `revision+1`, 직전 스냅샷을 history에 append |
| 비활성 | 삭제하지 않는다. `active=false` + history `deactivate`. 검색 기본 제외, `include_inactive`로만 조회 |
| 대체 | 기존 조각을 고치지 않고 **새 조각을 만든 뒤** `relation(new, old, 'supersedes', why)`, 옛 조각은 `superseded_at` 후 비활성 |
| 충돌 | 둘 다 살려두고 `conflicts-with` + `confidence='contested'`. 임의로 한쪽을 지우지 않는다 |
| 승격 | workspace 조각 → host 정본은 6절 소화 파이프라인을 통과해야 한다 |

> **부분 검증(2026-09-18 갱신 흐름 실험, 사용자 승인 실행):** 변경 이벤트 10건(사실값 변경·새 예외·규칙 폐기·조건 범위·용어 재정의·충돌 사실·정책 대체·영향없음 2건)을 fresh-context 참가자가 조각 검색만으로 처리한 실제 결과:
> 필수 조각 회수 **85%**(17/20, gold 있는 8개 이벤트 중 7개 완전 회수), 과잉수정 **제안 36건 중 1건(2.8%)**, 환각 조각 id **0건**,
> operation 정확 일치 **82.4%**(보존 의도 근접 포함 100%), 영향없음 이벤트 기권 **2/2**, 이벤트당 **$0.132 / 42초**.
> **치명적 실패 1건(E06):** 미확정 충돌 사실에서 관련 조각을 다 찾아 읽고도 "미확정은 SSOT 를 덮지 못한다"고 판단해 세 조각을 모두 누락하고 `no_impact` 를 냈다.
> 원실행의 조용한 기권은 탐색 후 판단 단계에서 발생했고 **충돌·미확정 처리 계약 누락과 일치하는 실패**다. 계약 누락만의 인과는 확정하지 않는다.
> 결론: 이 흐름은 **`candidate` 제안 생성에는 사용 가능**하지만 자동 적용은 여전히 금지다. 6절 소화 큐는 **제안 0건(기권)도 사람 심사 대상**으로 다뤄야 하며, 참가자 계약에 "미확정 사실도 충돌로 표시한다"를 명시해야 한다.
> 증거: [갱신 흐름 실험 보고서](../../evidence/v2-update-flow-study-01.html) · 이벤트/gold sha256 `1a4df7e56367a541…`(참가자 실행 전 동결) · 실험 합계 $1.9080.
> 한계: 셀당 1회, 자체 작성 이벤트/gold(독립 blind 아님), 생성 계획을 실제 DB 에 적용하지는 않았다.
>
> **E06 후속(2026-09-19, 단1회):** generic 충돌/미확정 수명주기 계약을 추가하고 사용자 정정에 따라 Luna medium으로 복원했다. 같은 gold 필수회수 **0/3→2/3**, no_impact **true→false**, conflict-flag 후보5건(필수2·중립1·과잉2), 회수 필수 연산2/2 정확. 1개는 노출되지 않아 여전히 누락; reference gate 종료(실제 노출9497/12000, 차단결과 포함 counter20113). **모델·thinking confound 때문에 prompt-only 인과 금지**, 기존 실험 집계는 소급 교체하지 않는다. $0.00501840/63.078초, 실제 DB 미적용·자동 소화 미검증 유지. [후속 보고서/원자료](../../evidence/v2-update-flow-e06-gpt-restored-01.html).

## 6. 소화(digestion) 파이프라인 — 사용자 확정

workspace의 candidate 조각을 host 정본으로 올리는 절차다. **처음에는 반자동**으로 시작한다.

### 6.1 1단계: 반자동 제안 + 일괄 승인

값싼 모델이 workspace 조각마다 제안 하나와 **이유**를 붙인다.

| 제안 | 뜻 |
|---|---|
| `promote` | host 정본으로 올리자 |
| `discard-duplicate` | 이미 같은 사실이 정본에 있다(중복) |
| `conflict-flag` | 정본과 어긋난다 → 사람 판단 필요 |
| `keep` | 아직 workspace에 두자(미완결) |

사용자는 목록을 보고 **일괄 승인/수정**한다. 제안은 실행이 아니다.

### 6.2 2단계: 위험 등급별 점진 자동화

| 등급 | 예 | 자동화 |
|---|---|---|
| 낮음 | `discard-duplicate` | 가장 먼저 자동화 |
| 중간 | `fact`/`procedure` 승격 | 통계가 쌓인 뒤 후보 |
| 높음 | `conflict-flag`, `decision`·`constraint` kind | **사람 판단 유지** |

**규칙:** 에이전트는 최대 `candidate`까지 쓴다. `confirmed` 승격은 사용자 확인 또는 **그 판단 등급을 명시적으로 위임받은 경우**에만 자동 확정한다.

### 6.3 소화 트리거

- **명시적 종료**: 사용자가 workspace를 닫는다 → 즉시 소화 큐로.
- **유휴 N일**: 활동 없는 workspace에 큐 flag를 세운다(자동 승격은 아니다).
- **git 신호**(bound인 경우만): PR merge, worktree 제거 → 소화 시점 후보. **sleep-time 실행 메모**: 값싼 모델 제안 단계는 사용자가 쉬는 시간에 백그라운드로 돌릴 수 있다. 승인 단계는 사람이 깬 뒤에 한다.

## 7. git 편의 기능 (bound인 경우에만)

- `fragment.source`에 `commit`/`pr`을 함께 기록하고, **양방향 질의**를 지원한다: "이 PR에서 무슨 지식이 생겼나" ↔ "이 조각은 어느 PR에서 왔나".
- **참조 파일이 바뀌면** 그 파일을 출처로 가진 조각을 **staleness-review 후보**로 표시한다. 이것이 갱신 흐름의 입구다.
- git이 없으면 위 기능만 빠지고 나머지는 모두 동작한다.

## 8. 결정 분해 패턴 (worked example)

하나의 결정은 **여러 조각 + 같은 group_id**로 적는다. 이번 연구의 triple 기각 결정을 실제로 적은 예다.

| kind | text(요지) | 비고 |
|---|---|---|
| `decision` | "순수 triple KB를 정본 표현으로 채택하지 않는다. 2026-09-18 사용자 결정." | 묶음의 대표 |
| `rationale` | "13.37 출력토큰/바이트로 조각 대비 약 29배 표현 팽창, 전체 환산 약 $69·6시간." | 이유 1 |
| `rationale` | "entity 323개 중 35개가 2개 이상 span에 걸쳐 한 줄 수정에 여러 span 재추출(갱신 비국소성)." | 이유 2 |
| `rejected` | "전체 코퍼스 triple 구축안은 26/211 span에서 중단. 품질 문제가 아니라 비용." | 기각안 |
| `constraint` | "질의 성능 비교 없이 내린 결정이다. '정확도가 낮다'는 근거로 인용 금지." | 재사용 제약 |

효과: "왜 triple을 안 썼지?"는 `search(kind=['decision','rationale'])`로 닿고, `expand_group`으로 기각안·제약까지 한 번에 본다.

## 9. 빅뱅 마이그레이션 계획 스케치 (사용자 결정)

범위: **한 host의 V1 기록 전체**를 한 번에 조각으로 옮긴다(점진 혼용 없음).

1. 대상 기록 목록 동결(경로·hash) → 기록 단위 조각 추출(조건·예외·부정 보존, 문서 본문 불변).
2. **의미 보존 검수 큐**(이전 파일럿: 16건 후보 중 13건 실제 결함, 3건 오탐). 통과분만 `confirmed`, 나머지 `candidate`.
3. 임베딩 생성(파생물) → 흡수된 원본 문서는 **읽기 전용 참조**로 격하. 정본은 조각 하나다.

비용 근거 — **측정:** 9문서 195,144B → 1,021조각 **$0.1367042**(Luna 요율, 밀도 ≈0.46 출력토큰/바이트). **추정(외삽, 견적 아님):** 277 record host는 바이트 비례로 대략 **$2–4 + 검수 노동**.

위험: 검수 노동이 한 시점에 몰린다 · 추출 오류가 정본에 그대로 전파된다(검수 큐가 방어선) · 격하 전 기간에는 **문서 쪽 수정 금지** 규칙이 필요하다.

## 10. 프로덕션 공백 — 현재 상태 (2026-09-28 정리, G10)

| 공백 | 현재 상태 | 근거 |
|---|---|---|
| E5 상주 서비스 | **해결** — `lhv2-embed.service`(127.0.0.1:8765) 상주, 고정 모델·해시 검증 | INSTALL §2·§5 |
| 키워드 검색 | **해결(대체)** — tsvector 대신 pg_trgm 문자열 유사도 + 임베딩 하이브리드(search_hybrid, RRF), 한국어 형태소 분석은 쓰지 않음 | migration 0002·0003 |
| pgvector 인덱스 | **부분** — 벡터 인덱스 없이 35,081 조각에서 모으기 평균 20~30초(scale-02). HNSW/IVFFlat 도입은 필요해질 때 별도 결정 | schema-delta 'G9' |
| alias seq 발급 | **해결** — 도메인별 advisory xact lock(store_pg.next_seq) | schema-delta 'G8 완료' |
| 백업·복구 | **해결** — backup.py(일일 pg_dump, 14개 보관, restore 덮어쓰기 거부, verify 는 일회용 DB 복구 비교) + lhv2-backup.timer | schema-delta 'G3 완료' |
| history 보존 정책 | **결정** — 전부 보존, 백업이 이력/조각 비율 기록·10배 초과 경고 | schema-delta 'G9' |
| 규모/노이즈 | **측정** — 35,081 조각에서 knowledge_brief 담김 평균 약 82~85%(실행 편차 80~91%), 이전 v2(부모 직접) 70.6% | schema-delta 'knowledge_brief 편차 측정' |

**판정(갱신):** dogfood(자체 운영) 수준의 필수 3개(E5 상주·키워드 검색·백업/복구)는 갖춰짐. 남은 것은 실제 pi 세션 사용 확인(G7). 대규모 multi-tenant 운영은 범위 밖.

## 11. 열린 항목 (2026-09-28 정리)

- **실제 사용(G7)**: pi 세션에서 knowledge_brief 비동기 메시지 도착, 기록→소화→정리 전 과정 미확인.
- **knowledge_brief 알려진 한계**: 큰 모음에서 비슷한 기능의 유효한 규칙을 빠뜨리는 경우(R07) — 지시문 세 가지·영역 순서 변경으로 못 고침. 부모가 코드를 함께 읽고 knowledge_search/more 로 보완.
- **이관 시 어긋난 옛 조각(후보 G12)**: v1 기록끼리 대체된 옛/새 내용 공존 — 이관 직전에 쌍 찾기·폐기 제안.
- **규칙 모듈(G6)·작업 전 검색 강제(G11)**: 별도 계획(사용자 2026-09-28).
- **교차문서 관계**: 키워드 기반 edge 1.2% — 비키워드 방식 필요성 미확인.
- **채점 방식**: 실험 채점은 Jev(자동)·Sol(독립 모델) 이며 사람 blind 채점은 없음. 같은 설정도 실행 편차가 커서 판단은 여러 번 돌린 평균으로.
- ~~스키마 미구현~~ → migration 0001~0005 실제 DB 적용됨. ~~E5 상주~~·~~백업~~ → §10 참조.

## 12. §1.1 Stage-1 준비 증거 — 부분, 2026-09-19

- `experiments/v2-agentic-wiki-fragment-01/fragment-standard-stage1/`에서 동결 1,021조각 중 6개만 Luna medium으로 별도 표준화했다. 질문/gold 비노출, 동일 ID, 원본 전체 문서 문맥, 관계 확장 없음, 보충 문맥별 source mapping을 적용했다.
- 구조 검사는 6/6 parse·동일/고유 ID·7기준 audit 필드·source mapping 존재를 확인했다. 이는 §1.1의 검사 형식을 시험한 증거이며 모델의 자체 pass가 의미 보존 증명은 아니다. 독립 의미 검수와 전체 corpus 준수율은 미완료다.
- `D09-F007-A02`는 원래 ‘같은 익명 상태’ 대신 원문 근거가 있는 ‘병원/기기 등록 완료 및 사용자 세션 없음’을 명시했다. 검색 순위·회수 개선은 아직 측정하지 않았으므로 규격 효과로 주장하지 않는다.
- 실행·장부·route proof는 planning primary의 `Fragment 저장 규격 Stage-1 실행 checkpoint`가 소유한다. 이 부분 증거는 draft 스키마나 제품 API를 변경하지 않는다.
- 2026-09-20 same-document batching은 473/1,021까지만 assembled되었다. ID coverage/JSON 통과와 의미 준수는 분리해야 한다. 기존6 대조에서 byte-equal text는1/6이고 `D09-F007-A02`는 singleton이 보완한 병원/기기 등록·무로그인 문맥을 batch 출력이 다시 생략했다. fresh Luna semantic audit 전에는 동등성/개선으로 판정하지 않는다.
- provenance 검사는 quote가 선언 source line range에서 지지되어야 한다. 선언 line 오류는 quote가 동결 원문에 exact substring으로 존재할 때만 raw 보존+explicit derived mapping으로 복구하며, document-wide 존재만으로 조용히 통과시키지 않는다. bounded split 후에도 미달이면 original atom/source-unit mapping을 candidate/needs-review로 남긴다.

### 12.1 소표본 효과 증거 — inconclusive, 2026-09-20

- 24개 source unit/6유형×4/8문서, 답변6+영향6의 12 paired task를 성공 output 전에 동결했다. 알려진 E06 사례는1개이고 나머지23개는 해당 성공 output으로 선별하지 않았지만 모델에게 진정한 unseen임은 보장하지 않는다. 24 arm run은 12 task의 쌍이지 24 독립사례가 아니다.
- 표준 생성24/24는 supplied source-key와 exact frozen-line quote mapping을 기계적으로 통과했다. 별도 동일-Luna 의미감사는 표준23/24 complete로 판정했고 `D06-F005-A06`에서 ‘첫 remote await 전’이 ‘첫 remote revoke await 전’으로 좁아진 severe regression1건을 찾았다. 기계적 citation 통과와 의미 correctness를 합치지 않는다.
- 고정 E5 target recall@20 합은 원본17/표준18이지만 Q05 target은 rank2→25로 악화했고, 알려진 E06 target은381→250으로 이동했어도 top20 밖이었다. 12 paired outcome은 A1/B3/tie8이며 B의 두 승리는 exact operation 개선 없이 과잉제안1건 감소, 실질 개선은 E03 하나였다. E07 no-impact는 양쪽 false positive, E06 target은 양쪽 미회수다.
- 따라서 이 표본은 §1.1의 일반적 효과·동등성·생산 강제를 입증하지 않는다. 동일 Luna가 생성·참가·채점했고 목적표집이므로 모집단 confidence를 산출하지 않는다. enforcement/review system은 구현하지 않았으며 후속은 독립 의미검수/오류교정과 더 많은 고유 source unit을 별도 승인받아야 한다. 원자료와 한계는 `.lazy-harness/evidence/v2-fragment-standard-small-sample-01.html` 및 planning primary에 있다.

## 13. 채택된 운영 흐름 — 실측 기반 (사용자 승인 2026-09-26 'a로 가자')

근거: `spec/v2-knowledge-module-schema-delta.md` 의 write-01 · scale-01 · update-01(round B/C/D) · read_check 항목. 실험 코드는 `experiments/v2-knowledge-module-runner-01/`.

### 13.1 역할별 모델

| 역할 | 모델 | 하는 일 | 하지 않는 일 |
|---|---|---|---|
| 작업 AI(작성·답변·수정) | `openai-codex/gpt-6-luna` medium | fact 작성, 검색어 생성, 자료를 읽고 답변, 도구가 준 목록의 조각 수정 | 저장 여부·관련성 최종 판정 |
| 판정자 | Jev `~typesafe/jev-latest`(OpenRouter) | 예/아니오 확률 판정(noul): fact 흡수 질문, 검색 결과 관련성(완화 0.5), 수정 대상 '옛 내용인가'·고친 뒤 재확인 | 문장 생성 |
| 임베딩 | `intfloat/multilingual-e5-small` 상주 서비스(CPU) | 조각 ctx-v1 임베딩(종류·영역·형제 3개 앞 80자 문맥), 검색어 임베딩 | 판정 |
| 코드(모델 아님) | — | lint·자동 보정(normalize_fact), hybrid 검색·페이지네이션, group 확장, 이름 변경 기계 치환 | 의미 판단 |

### 13.2 기록 흐름 (write)
1. 작업 AI 가 작업 대화·코드 변경에서 fact(문장·kind·근거 인용)를 `knowledge_record` 로 제출.
2. 코드가 형식을 자동 보정(subject·keywords), 신뢰 검사는 거절: 인용에 없는 코드 식별자(E_CLAIM_QUOTE, §1.1.1 개정 2), 되묻는 발언(E_USER_REF), 이유 없는 결정(E_WHY). 근거 개수는 경고. 거절 시 고치는 법을 돌려주고 1회 재제출.
3. 상주 폴러가 Jev 로 흡수 판정(근거 충분·범위·중복) → 정책에 따라 조각 생성, 임베딩은 폴러가 뒤에서 채움(작성자는 기다리지 않음).
   - 소화 흐름(2026-09-27 확정): 작성자는 원장 기록만, 비교·중복·합치기·정본 반영은 소화자. 중복 버림은 Jev is_new < 0.1 일 때만(runner.DUP_SKIP_MAX) — 새 세부를 버리지 않기 위함(손실 22%→0.5%). 남는 비슷한 조각의 합치기는 나중 별도 정리 작업(미구현).
   - 도메인 태그(2026-09-27 구현): 조각당 도메인 하나, 목록은 knowledge.domain_type(동적 관리: 합치기·은퇴). 소화자가 작업자의 partition_key 를 기준으로 라우팅 — 이름 일치는 그대로, 아니면 Jev 선택형으로 기존 도메인에 붙이고 '해당 없음'(≥0.7)이면 작업자 이름으로 새로(domain_router.py). 작업 단위 라우팅(2026-09-27 채택): 작업 하나의 사실들을 묶어 한 번 판정, 기존 도메인 확률 ≥0.6 이면 거기, 아니면 작업자 이름으로 새로(route_unit). 실측(파일럿 60 기록): 오배정 3.5%·중복 도메인 0·Jev 52 호출. 비슷한 이름은 나중 merge. 도메인별로 묶어 보여 주면 섞임 9.7% → 0.4%·담김 90.5%(layer-01 round_domain). 레이어는 태그로 저장하지 않고 읽을 때 도메인 묶음에서 재구성. 노트 지시문은 '주제 도메인 조각은 모두 반영(2026-09-27 채택)' — 담김 95.1%·섞임 2.1%(layer-01 round_domain2, prompt-note-domain2.md). 레이어 노트의 쓰임(사용자 정정 2026-09-28): 주 용도는 **에이전트가 작업 중 필요할 때 스스로 검색해 쓰는 것**이고, 사용자가 요청하면 같은 방식으로 보여 준다. 노트는 대화 안에서만 만들고 **파일·DB 에 문서로 남기지 않는다**(정본은 조각). knowledge_brief(2026-09-28 채택, brief-01 담김 92.4%·부모 수신 평균 5,693자) [편차 반영(2026-09-28): 큰 규모 같은 설정 4회 평균 담김 약 84%(80~91%), 정리본 8,000자 상한·도메인 확장 150 을 기본값으로 채택]: 작업 전 지식은 넓게 모은 뒤 Luna 하위 에이전트가 네 칸(이전 결정·이유 / 현재 구현 / 유지할 것 / 충돌)으로 정리해 비동기로 부모에게 전달, 부모는 그동안 소스를 읽음. 이전 knowledge_search layer 모드(2026-09-28 채택, layer-02 담김 93.6%): 문서 맨 앞 '영역 목록', 작업 AI 가 주제 영역을 고름, 질문도 검색어, 검색어는 지식의 언어로, 작업 도메인 확장(max(3,25%) 이상이면 도메인 전체), 끝에 노트 작성 안내. 인용: '에이전트가 작업하면서 필요할때 검색해서 사용하는거잔아', '당연히 노트가 실제 문서로 남으면 안되지', '물론 사용자가 요청하면 보여주기도 해야하고'. 도메인은 조각당 하나로 확정(2026-09-28): 관련 도메인 리스트는 시험 후 제거(자동 배정 부적절 39%, 걸친 지식 0/42). 두 도메인이 지식을 공유하면 merge 하고, `domain show` 가 대표 + 합쳐진 도메인 조각을 모아 보여 줌.
- 실측: 담김 56.2%(v1 61.5%, 게이트 없이 쓴 것 전부 59.2%). 남은 차이는 작성 자체. 작성 안내 강화(v2b)는 불안정해 채택 안 함.
- 기록 흐름 개정(2026-09-27, 사용자 승인): 작업 종료 시점 작성 뒤 **Jev 가 작업 전체 문장·코드 줄을 '지식인데 아직 facts 에 없나' 로 병렬 검수** → 빠진 목록만 작업 AI 가 항목별 record/skip → 원장 lint. 실측 66.5%(v1 61.5%), 추가 비용 상황당 약 $0.001·Jev 1.5초 + Luna 1회. 턴마다 작성+검수(48.8%)는 채택 안 함(턴 단위 작성이 맥락을 못 봄). 도구화(2026-09-27): knowledge_audit (`experiments/v2-knowledge-module-runner-01/capture_audit.py`, knowledge_cli 명령 audit, pi 확장 도구 knowledge_audit). 세션 대화(사용자·조수 텍스트, 선택 code_summary)를 문장·코드 줄로 나눠 Jev 세 질문(Q0 현재 KQ·Q4 예시 포함·Q2 내용 종류 선택형) 중 하나라도 지식이면 후보 → 이 작업 단위의 원장 facts 와 대조(CQ)해 빠진 것만 돌려줌(내용 종류는 태그일 뿐 파티션 배정 아님). 작업자는 항목마다 knowledge_record 또는 skip. 질문 선택 근거: write-01 q_compare(합집합 놓침 15·F1 0.959). 검증: test_capture_audit 6개(가짜 Jev) + 전체 130 passed, knowledge.ts tsc 오류 0. 작업자 단계 원칙(사용자 확정 2026-09-27): 목표는 누락 없음 — 작업자는 '이미 기록됨' 을 이유로 건너뛰지 않고 지식이 아닐 때만 skip, 중복 제거는 소화 단계 Jev(is_new → duplicate_skip). 실측(실제 Jev 검수 + 보완 3회) 평균 66.5%·범위 65.0~67.7%(v1 61.5%). 미검증: 소화 단계가 늘어난 중복(보완 fact 의 약 30%)을 실제로 걸러내는지, pi 세션에서 실제 호출.

### 13.3 읽기 흐름 (B3)
1. 작업 AI(Luna)가 질문만 보고 검색어 3~6개 생성(저장소는 보지 않음).
2. 코드가 검색어별 병렬 hybrid 검색(ctx-v1) 30개씩 + 페이지네이션. 각 페이지를 Jev 가 관련성 판정(완화 0.5), 새 관련 조각이 없으면 그 검색어 중단(검색어당 최대 5페이지·전체 600).
3. 코드가 관련 조각의 group 전체를 확장하고 기록→묶음→순서로 정리한 문서 1개 생성.
4. 작업 AI 가 그 문서만 읽고 답변.
- 실측(655 기록·70문제): 86.8%·모순 3 vs v1 81.2%·모순 15. 문제당 수집 약 13s + 답변 69s. 답변 뒤 Jev '빠졌나' 점검·보완(read_check)은 모순만 늘어 채택 안 함.

### 13.4 수정 흐름 (round B + 이름 변경 기계 치환)
1. 작업 AI 가 확정된 변경으로 검색어 생성 → 13.3 의 2~3단계와 같은 수집.
2. Jev 가 수집된 조각 전부에 '이 변경으로 고치거나 폐기해야 하나' 판정(≥0.5) → **고칠 목록은 도구가 만든다**.
3. 이름 변경은 목록 중 옛 식별자가 든 조각을 코드가 식별자만 치환(AI 미사용). 범위가 좁은 이름 변경(같은 이름이 다른 뜻)은 AI 가 고른 조각에만 치환.
4. 나머지는 작업 AI 가 목록을 20개씩 받아 조각마다 update(바뀔 부분만 바꾼 전문)/deprecate/keep 을 **반드시 하나씩** 답함.
5. Jev 가 고친 문장을 '아직 옛 내용이 남았나' 재확인 → 남은 것만 1회 재수정.
- 실측(가상 변경 10개): 고친 비율 약 62%·범위 밖 약 29 vs v1 27.4%·17. 변경당 비용 약 $0.006·시간 약 2~3분(v1 $0.0068·116s 와 비슷). 목록 기준을 0.3 으로 낮추고 keep 을 막는 안(round C)은 73.1% 지만 범위 밖 113·없는 사실 덧붙임으로 **채택 안 함**. Jev 덧붙임 검사는 추론성 덧붙임을 거의 못 잡음.
- 구현됨(2026-09-26): 작업자 도구 knowledge_search · knowledge_fix_plan · knowledge_fix_submit (`experiments/v2-knowledge-module-runner-01/worker_tools.py`, `knowledge_cli.py` 명령 search/fix_plan/fix_submit, `pi-extension/knowledge.ts`). 검색어는 작업 AI 가 직접 넘김(도구 안 LLM 호출 없음). fix_plan 은 고칠 목록을 계획 파일(~/.cache/lh-knowledge/plans)로 저장하고 이름 변경은 식별자 치환안(proposed_text)을 줌. fix_submit 은 목록 전 항목 답 필수(E_MISSING), 문장 불변·1.6배 초과 · Jev '아직 옛 내용' 이면 retry 로 돌려보내고, 통과한 update 는 기존 record 경로(lint·Jev 흡수·폴러)로 원장에 제안 — 근거는 사용자 확정 발언 원문 + 고치기 전 조각 원문을 자동으로 붙임. ~~deprecate 보류~~ → 폐기(deprecate, 2026-09-28 구현): 판정 틀 intent-deprecate v0.1, 사용자 확정 원문 필수, 통과 시 active=false(이력 보존). 실제 Jev 8/8·잘못 지움 0. 검증: test_worker_tools 5개(가짜 Jev) + 전체 121 passed, knowledge.ts tsc 오류 0. 실제 규모 재현(round_tool, 2026-09-27): 도구 통과분 60.6%·범위 밖 21 로 재현됐으나, 실제 record lint 를 거치면 39개가 E_CLAIM_QUOTE(확정 발언에 없는 파생 식별자)로 거절돼 원장 반영분은 51.1% — fix_submit 이 lint 거절을 retry 로 돌려주지 않는 결함. → 선검사 추가(2026-09-27): fix_submit 이 원장과 같은 lint 를 먼저 돌려 거절분을 이유와 함께 retry 로 돌려줌 — 원장 반영 55.0%·선검사 후 lint 거절 0, 테스트 122 passed. 남은 한계: 확정 문장이 새 식별자를 풀어 쓰면 올바른 수정도 막힘. → forms_quote 추가(2026-09-27): fix_plan 이 새 표기 미확정을 needs_confirmation 으로 알리고, 사용자가 확정한 원문(forms_quote)을 근거로 붙이면 통과(질문형은 도구가 거절). 전체 56.6%·범위 밖 20, 테스트 123 passed. 미검증: pi 세션에서 실제 호출.

### 13.5 채택하지 않은 것
- jegrep(파일 단위 범위·`.gitignore` 따름·일부 변경 무결과) — 직접 만든다(사용자 확인). '요약 먼저 판정 → 통과 구간만 원문 판정' 아이디어만 후보.
- 작성 안내 강화(v2b), 읽기 점검(read_check), 수정 목록 확대+keep 금지(round C).

### 13.6 남은 한계
- 모든 비교는 같은 계열 모델로 자동 채점(blind 아님). 수정 시험은 가상 변경·자동 정답이고 v1 줄/v2 조각 단위가 다름. 도구·채점이 같은 Jev 라 과대평가 가능.
- 임베딩 대량 처리는 느림(34,784 조각 2,507s, CPU·스레드 2) — 최초 이관 때만 문제.

## Implementation map

- 역할 계약/fixture 생성: `experiments/v2-agentic-wiki-fragment-01/fragment-role-capability-02/prepare.py` → `protocol.json`, `guidelines.json`, `sources.json`, `fixtures.json`, `rubrics.json`, `mutation-manifest.json`, `freeze-hashes.json`.
- 보호 테스트: `test_preflight.py`(source/provenance·role isolation·taxonomy·ledger·history 불변)와 `test_mock_lifecycle.py`(disposable deactivate/restore).
- 실제 실행: `run.mjs` → `broker.mjs`의 ChatGPT backend-api/manual redirect deny 경로 → `runs/*.json`, `run-index.json`, `run-summary.json`; retrieval/embedding은 호출하지 않는다.
- 평가/감사: `assess.py`, `semantic_audit.py`, `sol-source-audit.json`, `final-audit.json`; frozen mechanical과 source-adjudicated secondary를 분리한다.
- 보고서: `.lazy-harness/evidence/v2-fragment-role-guidelines-retest-01.html`; primary 결과는 `.lazy-harness/planning/v2-vision-feasibility-research.md`, regression 경계는 `.lazy-harness/tests/v2-minimal-clarification-source-audit.md`가 소유한다.
- 현재 후보집합 종합 preflight(비생산 experimental pointer): `experiments/v2-agentic-wiki-fragment-01/three-role-candidate-synthesis-preflight-01/`은 최소 ID 선택 대신 공급된 여러 조각의 필요한 사실·조건·예외·제약을 지지된 작업 답으로 종합하는지를 평가한다. related supplied extra는 자체로 실패가 아니며 required/optional label은 core success가 아니다. Recorder는 source-document/event/candidate provenance와 unknown을 분리하고, Digester는 source-absent standalone과 source-backed fidelity/proposal을 분리한다. 단, preflight-01의 substring·keyword·allowed-operation 기반 pass는 의미 증거가 아니므로 결과 판정에 사용하지 않는다.
- 의미 채점 분리 repair(비생산 experimental pointer): `experiments/v2-agentic-wiki-fragment-01/three-role-candidate-synthesis-preflight-02-semantic-separation/`은 schema/type, supplied evidence ID, matching typed verbatim quote, scope, operation authorization, history/restore, approval/apply만 `mechanical_pass`로 검사한다. entailment·support·contradiction·clarity·proposal/rationale correctness·completion status는 explicit task+participant output+stage-visible evidence+rubric을 읽은 실제 adjudicator의 criterion별 judgement와 provenance가 있어야 하며, 없으면 `pending_unreviewed`다. fixture-origin judgement와 mechanical pass는 empirical quality aggregate에 들어가지 않는다. blind clarity packet은 candidate-only이고 source fidelity packet과 분리한다. 두 pointer 모두 retrieval/no-miss, 모델 성능, 운영 준비 또는 유료 실행 승인이 아니다.
- pilot03 contract repair(비생산 experimental pointer): `experiments/v2-agentic-wiki-fragment-01/three-role-candidate-synthesis-pilot-03-contract-repair-04/operation-lifecycle.json`을 operation lifecycle의 단일 선언원으로 사용해 instruction/schema/validator가 같은 history·restore·change rule을 공유한다. retain/needs_review는 비변경이며 unchanged retain을 허용하고, update/supersede는 구체적 before/after candidate text가 필요하다. operation authorization과 semantic correctness는 별도다. `repair.py`는 canonical target/declared alias, object-explicit review criteria, candidate 오류와 participant diagnosis 분리, host-attached exact request hash binding, swapped response 거부, candidate-only blind packet을 구현한다. 기존 pilot03 artifacts/hash/ledger는 수정하지 않으며 saved-output replay와 authored fixture는 실제 새 reviewer 결과가 아니다.

### Offline real-stage handoff adapter experimental pointer — 2026-09-22

`experiments/v2-agentic-wiki-fragment-01/tr-int-offline-08/adapter.py`는 비생산 fixture에서 Reader actual bytes/hash → task-local patch subprocess → independent root-owned validation receipt → actual observed recorder → recorder+canonical copy 기반 non-applied Digester proposal을 연결한다. supplied와 selected context, 각 stage output의 fixture/host provenance, upstream host-computed hashes를 분리하며 failed/timeout/tampered stage는 downstream recorder/digester success를 만들지 않는다. proposal에는 callable apply branch가 없고 approval의 `user_confirmed`는 controller-only다. review packet은 object별 semantic evidence/rationale를 요구하고 keyword/substring/ID-count 판정을 하지 않으며 retain null rewrite criterion은 `not_applicable`다. 이 pointer는 supplied-candidate requirement-following integration contract일 뿐 retrieval/search, model quality, production runtime 또는 live untrusted execution contract가 아니다.

Implementation: `fixture_actor.py`는 disposable copy에만 복사되는 trusted authored actor, `root_validate.py`는 actor 수정 밖의 fixed functional assertions, `render_live_requests.py`는 dispatch 없는 Parent review packet entrypoint다. `test_adapter.py`와 `offline-evidence-index.json`이 success3 및 failure/tamper/timeout/path boundary를 보호·보존한다.

### Actual model patch isolation experimental pointer — 2026-09-22

`experiments/v2-agentic-wiki-fragment-01/tr-int-live-09/`은 actual Luna Reader output을 actual Luna work request에 넘기고, work가 반환한 단일-file unified diff만 strict host parser로 disposable copy에 적용한 뒤 bubblewrap 안에서 실행하도록 제한한다. sandbox는 network namespace를 분리하고 synthetic root에서 host project root를 보이지 않게 하며 `/work`와 private scratch만 writable, root-owned assertion은 read-only external mount다. CPU/memory/per-user-process/time/file limits를 함께 둔다. patch admission 또는 behavior test가 실패하면 Recorder·Digester·reviewer를 호출하지 않고 success를 만들지 않는다. 실제 09 run은 model-added `*** End Patch`를 admission에서 거부해 downstream이 없고 semantic review는 pending이다.

`render_requests.mjs`는 private rubric/expected result 없이 original authored request와 supplied candidates를 명시하고 requirement-following—not retrieval effectiveness—로 표시한다. `run.mjs`는 guarded installed broker route, current ledger/catalog, ≤8 call/≤$1 continuation, no retry를 검사하며 actual stage bytes/hash/receipt를 보존한다. `sandbox_adapter.py`/`root_test_t1.py`가 isolation+trusted validation을, `test_live_integration.py`가 offline safety regression을 소유한다. 이 pointer는 generic Python sandbox, production execution, retrieval 품질, canonical apply 계약이 아니다.