# SDD — 모듈 저장소 분리와 lazy-harness 종합층 계약

Status: accepted (user-confirmed native options)
Layer: SDD

## Rule digest

- Status: active
- Layer: SDD
- Scope: host-project
- Aliases:
  - 모듈 분리
  - 모듈 종합층
  - module composition
  - module extraction
  - Fabric 어댑터 위치
- Applies when:
  - extracting a capability from lazy-harness into its own module repository
  - connecting a module repository to lazy-harness or deciding where pi-fabric/Jev code lives
  - adding a dependency to `.lazy-harness` core, `packages/lazy-harness-pi` or a module repository
- Must:
  - keep lazy-harness as the record/rule framework plus the module composition layer
  - keep `.lazy-harness` core (CLI, hooks, sync, records tooling) working without pi-fabric or any external SaaS (ADR 0013)
  - limit the pi-fabric dependency, exact version pin and bun/Node >= 24 compatibility check to the Pi integration package `packages/lazy-harness-pi`
  - give every module repository its own port contracts plus fake-backed conformance tests and no pi-fabric dependency in any package.json
  - attach external judgement such as Jev through a module judgement port; a module may ship an optional default transport (`hosts/<service>`) for standalone use, and the composition layer can replace it; behaviour without it or on failure must be defined
  - move only source, tests and the fixtures those tests need; keep design/decision/measurement records in lazy-harness `.lazy-harness/`
- Must not:
  - commit experiment result data (run outputs, raw model responses, DB dumps, `.local/**`) to any repository
  - shape a module port after the Fabric API or import Fabric internals in a module
  - copy module code back into lazy-harness or keep a second canonical implementation
- Record completion:
  - changes to the role, dependency placement, extraction procedure or repository relations update this SDD and the project-identity SSOT
- Related records:
  - `.lazy-harness/ssot/project-identity.md`
  - `.lazy-harness/decisions/0013-framework-external-dependency-invariant.md`
  - `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`
  - `.lazy-harness/decisions/0061-monitoring-core-fabric-optional.md`
  - `.lazy-harness/spec/platform/pi-agent-package.md`

## 확정된 역할

사용자가 native 선택으로 확정했다.

1. **lazy-harness = 기록·규칙 프레임워크 + 모듈 종합층.** `.lazy-harness`의 기록·규칙·CLI·hook·sync와 Pi 통합 패키지를 유지하고, 별도 저장소 모듈을 어댑터로 묶어 쓴다. 모든 모듈의 설계·결정·측정 기록도 lazy-harness에 둔다.
2. **pi-fabric 의존은 Pi 통합 패키지에서만.** `.lazy-harness` 코어는 Fabric 없이 동작한다. 모듈 저장소는 Fabric에 의존하지 않는다.
3. **외부 판단(Jev 등)은 모듈 판정 포트로.** 모듈은 단독 개발·시험용 선택적 기본 연결(`hosts/jev` 등)을 둘 수 있고, 조립할 때 lazy-harness 종합층이 자기 연결로 교체할 수 있다. 없거나 실패해도 명시 지정·메인 판단으로 동작할 수 있어야 한다. (후속 사용자 선택으로 처음 결정을 보완)

```text
lazy-harness (이 저장소)
├─ .lazy-harness/              기록·규칙·CLI·hook·sync — Fabric 미의존
│   └─ 모든 모듈의 설계·결정·측정 기록
└─ packages/lazy-harness-pi/   Pi 통합 + 모듈 포트의 Fabric/Jev 구현 (유일한 pi-fabric 의존처)

모듈 저장소 (pi-fabric 미의존, 자체 포트 + fake 적합성 시험)
├─ lazy-dinosaur/lazy-harness-monitoring
├─ 지식 모듈 (분리 방향 검토 중)
└─ 세션 매니저 모듈들 (계획 후보)
```

## 저장소 관계

| 모듈 | 위치 | 상태 | 소유 기록 |
| --- | --- | --- | --- |
| 모니터링 | GitHub `lazy-dinosaur/lazy-harness-monitoring`, 로컬 `/home/lazydino/dev/lazy-harness-monitoring` | core 이전·host 분리 진행, lazy-harness에는 thin consumer만 예정 | 모니터링 세션 소유 ADR 0061(로컬 main의 미push 커밋에 있음)·ADR 0062(work/monitoring-engine-v2 브랜치에만 있음)와 monitoring planning |
| 지식(V2) | 현재 worktree `/home/lazydino/dev/lazy-harness.v2-g16`의 `experiments/v2-knowledge-module-runner-01/` | 별도 저장소 분리 방향 검토 중, 시점 미정 | 승인 시 별도 planning record |
| 세션 매니저 | 없음 | 계획 후보 | 기록은 별도 작업에서 main에 올린다 |

## 의존성 규칙

| 위치 | 허용 | 금지 |
| --- | --- | --- |
| `.lazy-harness` 코어 | git, 프로젝트 toolchain, python3, bash (ADR 0013) | pi-fabric, Jev, 외부 SaaS 필수 의존 |
| `packages/lazy-harness-pi` | Pi host peer, pi-fabric(정확한 버전 고정), 모듈 패키지, Jev 선택 연결 | 모듈 코드 복제, Pi host 패키지 bundle |
| 모듈 저장소 | 자체 의존성(예: typebox) | 모든 package.json의 pi-fabric, Fabric 내부 import |

포트 규칙:

- 포트 모양(작업자 실행 spawn/run/stop/wait·timeout·취소·동시성 제한, 판정, 모델 호출 등)은 모듈이 정한다. Fabric API를 복제하지 않아 Fabric이 바뀌어도 구현만 고친다.
- 모듈은 fake 구현으로 도는 적합성 시험을 갖는다. 실제 구현은 lazy-harness가 pi-fabric 공개 export(`pi-fabric/agents`, `pi-fabric/runners`, 선택적으로 Jev)로 작성하고 같은 적합성 시험을 통과시킨다.
- 판정 포트는 결과 없음·실패·모호함을 구분한다. 외부 판단이 없을 때의 대체 동작을 모듈 계약에 적는다. 실패를 ‘해당 없음’으로 취급하지 않는다.

## 모듈 분리 절차

1. **기록 먼저**: 분리 대상의 요구·계약·결정을 lazy-harness `.lazy-harness/`에 정리하고 planning record를 만든다. 분리 자체는 사용자 승인이 필요하다.
2. **포트 정의**: 모듈이 필요한 외부 능력(모델 호출·판정·실행·저장 등)을 포트로 정의하고 fake 적합성 시험을 만든다.
3. **저장소와 이슈**: 모듈 저장소를 만들고 단계로 나눈 큰 이슈 하나를 연다. 각 PR은 `Refs #N`과 Summary / Decisions / Verification을 담고, 큰 이슈를 일찍 닫지 않는다.
4. **단계적 이전**: 코드·시험·그 시험에 필요한 고정 자료만 옮기며, 단계마다 모듈 자체 시험이 통과하도록 한다. 이전 순서는 모듈 저장소의 `MIGRATION.md`에 기록한다.
5. **남기는 것**: 설계·결정·측정 기록과 evidence는 lazy-harness에 남기고 새 저장소를 가리킨다. 실험 결과 데이터는 어느 저장소에도 커밋하지 않는다. 실제 세션 내용·개인 trace는 모듈 저장소로 복사하지 않는다.
6. **어댑터**: `packages/lazy-harness-pi`에서 모듈 포트를 pi-fabric(및 선택적 Jev)으로 구현하고, 버전 고정과 bun/Node >= 24 호환을 확인한다.
7. **연결**: 모듈 시험이 통과한 뒤에만 lazy-harness에 thin consumer를 두고 기존 코드를 제거한다. 두 개의 canonical 구현을 남기지 않는다.
8. **기록 갱신**: 이 SDD의 저장소 관계 표와 project-identity SSOT를 갱신한다.

## 현재 모듈 저장소 점검 (사용자 요청, 읽기 전용)

사용자는 세션 매니저보다 먼저 lazy-harness가 모듈을 조립하는 구성과 pi-fabric 연결 계약을 확정하자고 정정했다. 이미 만든 모듈 저장소가 맞게 됐는지 확인해야 다른 저장소를 만들고 연결할 수 있다는 이유다. 아래는 GitHub 공개 API·raw 파일(모니터링 `main`, 지식 `master`)을 읽은 결과이며 코드 실행·시험은 하지 않았다.

확인한 저장소(사용자 계정의 lazy-harness 관련 공개 저장소는 이 세 개): `lazy-dinosaur/lazy-harness`, `lazy-dinosaur/lazy-harness-monitoring`, `lazy-dinosaur/lazy-harness-knowledge`.

| 항목 | monitoring | knowledge | 이 SDD 규칙과의 관계 |
| --- | --- | --- | --- |
| 언어·런타임 | TypeScript, bun workspace | Python core/eval + Pi용 작은 Node transport | 언어가 다르다. lazy-harness Pi 패키지(TS)가 Python 모듈을 부르는 방식은 정의돼 있지 않다 |
| 구성 | `packages/core`, `hosts/pi`, `packages/eval`, `modules/*` | `packages/core`, `hosts/pi`, `hosts/jev`, `hosts/embed`, `packages/eval`, migrations | core/hosts/eval 기본 모양은 같다 |
| pi-fabric 의존 | 없음(core는 typebox만, `hosts/pi`는 core + Pi SDK peer) | 없음(README에 명시) | 규칙에 맞다 |
| 포트 | `WorkerExecutionPort` 등 비동기 객체 + `runWorkerPortConformance`, Host Adapter 계약(`HostCapabilities`, frame) | 동기 callable `model/encode/choose/ask/writer/worker` + `conforms()`, transport 설치 훅 | 둘 다 모듈 소유 포트와 fake 시험이 있다. 모듈 간 공통 규격·버전·등록 방식은 없다 |
| 호스트 코드 | `hosts/pi`: Pi 이벤트 frame 관찰·report 전달(모듈 저장소 안) | `hosts/pi`: Pi ModelRuntime transport, `hosts/jev`: Jev HTTP 직접 호출(모듈 저장소 안) | ADR 0062는 agent별 host adapter를 모듈 저장소 `hosts/<agent>`에 둔다. 점검 당시 이 SDD의 ‘외부 판단은 종합층에서 연결’과 `hosts/jev`가 충돌했으나, 사용자가 모듈 안 기본 연결 허용 + 종합층 교체로 정리했다(아래 연결 계약) |
| 기록 위치 | MIGRATION이 가리키는 ADR 0061/0062·계획은 lazy-harness `work/monitoring-engine-v2` 브랜치에 있고 origin/main에는 없다 | MIGRATION이 가리키는 기록은 `lazy-harness.v2-g16` worktree 쪽이며 main에는 없다 | ‘기록은 lazy-harness에 둔다’는 지켰지만 통합 기준 브랜치에는 아직 없다 |
| 배포·수용 | 모든 package `private`, 미배포 | 미배포 | 사용자가 git submodule + 커밋 고정으로 확정했다(아래 연결 계약) |
| 기본 브랜치 | `main` | `master` | 규칙 없음(사소한 불일치) |

lazy-harness 쪽 현황: main의 `packages/lazy-harness-pi/monitoring/`에 이전 전 모니터링 SDK 파일이 남아 있고, Pi 패키지에는 아직 pi-fabric 의존·모듈 어댑터가 없다.

정리: 두 저장소는 ‘Fabric 미의존, 자체 포트 + fake 시험, 기록은 lazy-harness’ 원칙에는 맞다. 연결에 필요한 종합 계약(모듈 선언·포트 규격·언어 경계·수용 방식·호스트 코드 위치·기록의 main 반영)은 아직 없다. 이 적합 판단은 문서 대조이며 각 저장소의 시험 통과를 재확인한 것은 아니다.

## 연결 계약 (사용자 확정)

점검에서 드러난 미결점을 사용자가 native 선택으로 정했다.

### 1. 세 층 구조

```text
lazy-harness (완제품 조립)
├─ .lazy-harness/              기록·규칙·CLI·hook·sync, 모든 모듈의 설계·결정·측정 기록
├─ packages/lazy-harness-pi/   Fabric 기반 실행·통신 어댑터 + 모듈 조립 (유일한 pi-fabric 의존처)
└─ <submodule>/<모듈>          커밋 고정된 모듈 저장소

모듈 저장소 (pi-fabric 없음)
├─ packages/core       순수 엔진 + 모듈 소유 포트 + fake 적합성 시험
├─ hosts/<agent>       agent별 연결(예: Pi 이벤트 관찰, Pi 모델 호출) — Fabric 아님
├─ hosts/<service>     선택적 기본 외부 연결(예: Jev) — 단독 개발·시험용, 조립 시 교체 가능
└─ packages/eval       평가 도구
```

### 2. 호스트 코드 위치

- agent별 연결 코드(Fabric이 아닌 것)는 모듈 저장소 `hosts/<agent>`에 둔다(ADR 0062와 같은 방향, 두 저장소의 현재 구조 인정).
- lazy-harness는 Fabric으로 실행·통신을 묶는 어댑터와 조립만 맡는다. 모듈의 포트(예: 모니터링 `WorkerExecutionPort`, 지식 `worker`/`choose`/`ask`)를 Fabric으로 구현하고 모듈이 제공하는 적합성 시험을 통과시킨다.

### 3. 외부 판단 연결

- 모듈은 판정 포트를 갖고, 단독 개발·시험용 선택적 기본 연결(`hosts/jev` 등)을 둘 수 있다.
- 조립할 때 lazy-harness가 자기 연결로 교체할 수 있어야 한다(지식 모듈의 `install_judgement_http` 같은 설치 훅). 교체 우선순위는 종합층 연결 > 모듈 기본 연결 > 사용 불가 오류 순이다.
- 없거나 실패해도 대체 동작을 계약에 적고, 실패를 ‘해당 없음’으로 취급하지 않는다.

### 4. 언어 경계

- TypeScript 모듈(예: monitoring)은 lazy-harness Pi 패키지가 같은 프로세스에서 import한다.
- 다른 언어 모듈(예: Python knowledge)은 별도 프로세스로 실행하고 JSON 메시지 규약으로 포트 호출을 주고받는다. 모듈이 포트를 호출하면(예: worker 실행, 판정) 종합층이 그 요청을 받아 Fabric으로 처리하고 결과를 돌려준다.
- 규약의 전송 방식(예: stdin/stdout JSON lines), 메시지 모양, 오류·취소·timeout·불확실 결과 표현, 버전 표기는 아직 정하지 않았다.

### 5. 수용 방식

- lazy-harness는 모듈 저장소를 git submodule로 포함하고 특정 커밋에 고정한다. 패키지 배포는 필요하지 않다.
- submodule 경로, 커밋을 올리는 절차·호환성 확인은 아직 정하지 않았다.

### 6. 모듈 선언·메시지 규약·결과 형식·버전 (사용자 확정)

사용자가 native 선택으로 네 가지를 정했다. 선언 파일의 필수·선택 필드(§6.1)와 보류 표현(§6.3)은 2026-11-10에 사용자가 확정했다. method 이름(`module.<operation>`, `port.<name>.<op>`)은 v1 초안이며 schema 파일을 만들 때 확정한다.

#### 6.1 모듈 선언 — 저장소 루트 파일 하나

- 각 모듈 저장소 루트에 `lazy-harness.module.json`을 둔다. 언어와 무관한 같은 형식이며 lazy-harness는 submodule에서 이 파일을 읽는다.
- v1 필드 (사용자 확정 2026-11-10: 필수 8개 + 선택 2개):

| 필드 | 필수 | 뜻 |
| --- | --- | --- |
| `schema` | 필수 | `lazy-harness-module/v1` |
| `id` | 필수 | 모듈 저장소 식별자(예: `monitoring`, `knowledge`) |
| `version` | 필수 | 모듈 배포 표시(semver 문자열). 호환성은 이 값이 아니라 `schema`와 포트의 정수 major로 판단한다(§6.4) |
| `runtime` | 필수 | `inprocess-ts` \| `process` |
| `entry` | 필수 | `inprocess-ts`: 저장소 기준 TS export 경로 / `process`: 실행 argv 배열 |
| `requires` | 필수 | 필요한 포트 목록 `[{"port", "v"(정수 major), "default"?(선택적 기본 연결)}]`. 필요한 포트가 없으면 빈 배열 |
| `test` | 필수 | 모듈 자체 시험 명령 |
| `conformance` | 필수 | lazy-harness의 포트 구현이 통과해야 하는, 모듈이 제공하는 적합성 시험 경로 |
| `provides` | 선택 | 제공 기능 이름 목록 |
| `records` | 선택 | lazy-harness 쪽 기록 경로 |

- 필수 기준: lazy-harness가 모듈을 시작(`runtime`, `entry`)하고, 버전을 검사(`schema`, `requires[].v`)하고, 조립을 검증(`test`, `conformance`)하는 데 꼭 필요한 것만 필수로 둔다.
- 필수 필드가 없거나 지원하지 않는 major이면 lazy-harness는 조립할 때 명확한 오류로 거부한다(§6.4, §6.6).
- 저장소 안의 여러 package(core, hosts/*, modules/*)는 이 파일 하나에서 함께 선언한다.

```json
{
  "schema": "lazy-harness-module/v1",
  "id": "knowledge",
  "version": "0.3.0",
  "runtime": "process",
  "entry": ["python3", "-m", "lh_knowledge.serve"],
  "provides": ["knowledge.place", "knowledge.search"],
  "requires": [
    {"port": "judgement", "v": 1, "default": "hosts/jev"},
    {"port": "worker", "v": 1}
  ],
  "test": "./run-tests.sh",
  "conformance": "packages/core/tests/test_port_conformance_kit.py",
  "records": ".lazy-harness/planning/v2-knowledge-module-extraction.md"
}
```

(예시의 entry·provides·records 값은 설명용이며 지식 저장소에 아직 있는 것이 아니다.)

#### 6.2 메시지 규약 — JSON-RPC 2.0, 표준입출력, 양방향

- 이 규약은 모듈이 구현해 제공한다. 다른 언어 모듈은 자기 RPC 서버와 함께 lazy-harness가 import할 TS client를 제공한다(§6.6).
- `runtime: process` 모듈에 적용한다. stdin/stdout에 한 줄에 JSON 객체 하나(LF로만 구분, U+2028/U+2029를 줄바꿈으로 취급하지 않음)를 쓴다. stderr는 진단 로그로만 쓴다.
- 한 연결에서 두 방향을 모두 쓴다: lazy-harness→모듈은 기능 호출(초안 `module.<operation>`), 모듈→lazy-harness는 포트 호출(초안 `port.<name>.<op>`, 예: worker 실행·판정). lazy-harness는 포트 호출을 Fabric·Jev 등으로 처리해 돌려준다.
- 시작 시 `initialize`에서 규약 버전·모듈 id·필요한 포트와 lazy-harness가 제공하는 포트를 맞춘다. 취소는 요청 id를 담은 취소 알림, 종료는 `shutdown` 요청 뒤 stdin 닫기로 한다. 동시 요청은 id로 상관시킨다.
- JSON-RPC error는 규약 오류(parse, 없는 method, 잘못된 인수, 버전 불일치)에만 쓴다. 기능·포트의 실패는 아래 공통 결과 형식으로 result에 담는다.
- 참고 계열: Pi RPC(JSONL), Codex app-server, ACP. 상태가 필요한 오래 가는 연결이다.

#### 6.3 공통 결과 형식

- 모든 포트·기능 결과는 모니터링 `WorkerCompletion`과 같은 형식을 쓴다: `status`(`completed` | `failed` | `timed-out` | `cancelled` | `refused`), `certainty`(`terminal` | `uncertain`), 성공 시 `value`, 실패 시 `reason`.
- `uncertain`은 효과가 있었는지 모르는 상태이며 자동 재시도하지 않는다. 한 번 나온 최종 결과는 늦게 온 값으로 바꾸지 않는다.
- 보류(HOLD, 사용자 확정 2026-11-10): 실패가 아니라 모듈이 일부러 처리를 미룬 결과(예: 지식 배치가 자리를 찾지 못한 `PlacementHeld`)는 공통 status를 늘리지 않는다. `status: completed`, `certainty: terminal`로 돌려주고 `value`에 `{"held": true, "reason": "..."}` 표시를 넣는다. 다시 시도할지는 호출자나 사용자가 정하며 자동 재시도하지 않는다. held 값의 나머지 필드(trace 등)는 모듈 계약이 정한다.
- 모듈 내부 경로도 `uncertain` 재시도 금지를 지켜야 한다. 지식 모듈의 Jev 판정 경로(`capture_audit.request_answers`, `worker_tools.make_ask`)가 불확실한 요청을 자동으로 다시 보낼 수 있다는 검수 지적이 있다(지식 세션이 수정 예정). 모듈 적합성 시험은 이 규칙을 확인해야 한다.
- TS in-process 모듈도 같은 형식을 쓴다. 현재 지식 모듈 포트는 dict/확률을 반환하고 `Stop`을 던지므로 경계에서 이 형식으로 바꾸는 정렬이 필요하다.

#### 6.4 버전 표기

- 선언 형식(`lazy-harness-module/v1`), 메시지 규약, 포트마다 정수 major 버전을 표기한다.
- lazy-harness가 지원하지 않는 major이면 시작 단계에서 명확한 오류로 거부한다. 같은 major 안에서는 하위 호환되는 추가만 허용한다.

#### 6.5 안정성 검토와 필요한 보호 장치 — 제안, 미채택

사용자가 이 방식이 안정적인지 물었다. 설계만 정했고 구현·시험은 없으므로 안정성은 아직 검증되지 않았다. 검증된 기반(JSON-RPC stdio는 LSP·MCP·Pi RPC·Codex app-server가 쓰는 방식)을 고른 것이지, 연결이 저절로 안정적이라는 뜻은 아니다. 알려진 위험과 보호 장치 후보:

| 위험 | 보호 장치 후보 |
| --- | --- |
| 모듈이 stdout에 일반 출력(print 등)을 써서 규약이 깨짐 | stdout은 규약 전용, 로그는 stderr. 모듈 진입점이 stdout을 규약 writer로만 열고, 잘못된 줄은 규약 오류로 끊는다 |
| 양방향 호출 교착(서로 응답을 기다림) | 양쪽 모두 수신 루프를 멈추지 않고 요청을 동시에 처리한다. 포트 호출 중에도 다른 메시지를 읽는다 |
| stdout을 읽지 않아 프로세스가 멈춤(backpressure) | lazy-harness는 stdout을 계속 읽고 메시지 크기 상한을 둔다. 큰 자료는 파일 참조로 넘긴다 |
| 모듈 크래시·멈춤·좌비 프로세스 | 시작 시간 제한, 요청 timeout, 종료 감지 후 진행 중 요청을 `uncertain`으로 끝내기, 종료 신호·정리. 자동 재시작은 효과 중복을 막는 규칙과 함께만 |
| 취소·timeout 뒤 늦게 오는 결과 | 최종 결과는 한 번만 확정하고 늦은 값은 버린다(모니터링 worker port와 같은 규칙) |
| 줄바꿈·문자 처리 오류 | LF로만 구분하고 일반 line reader(U+2028/U+2029 분리)를 쓰지 않는다(Pi RPC 문서의 경고와 동일) |
| submodule 커밋과 선언·포트 버전 불일치 | 시작 시 선언 파일·major 버전 검사(이미 확정), submodule 갱신 시 적합성 시험 통과를 조건으로 한다 |
| submodule 운영 실수(초기화 누락, 오래된 커밋) | 설치·검사가 submodule 상태를 확인하고 누락 시 명확히 실패한다 |
| 자격 증명·환경 변수 노출 | 모듈 프로세스에는 필요한 환경 변수만 전달하고, 외부 호출은 가능하면 lazy-harness 포트를 통하게 한다 |

안정성 확인 방법 후보: 규약 적합성 시험 세트(정상 호출, 취소, timeout, 동시 요청, 양방향 중첩 호출, 모듈 강제 종료, 깨진 줄, stdout 오염, 버전 불일치)를 만들고 모든 process 모듈과 lazy-harness 어댑터가 통과하도록 한다. 이 보호 장치와 시험은 아직 채택되지 않았다.

#### 6.6 계약의 정본 위치 — 모듈이 정의, lazy-harness는 설치·import (사용자 결정)

사용자는 별도 계약 저장소가 정말 좋은지 물으며 “계약 형태를 모듈에서 정의하고 lazy-harness에서는 설치하고 임포트해서 사용하면 되는 것 아닌가”라고 제안했고, native 선택에서 그 방식을 골랐다. 같은 날 정한 ‘별도 계약 저장소(가칭 `lazy-harness-contract`)’ 결정은 대체되었고 그 저장소는 만들지 않는다.

```text
monitoring  ─ 계약(포트 타입)·fake·적합성 시험 export
knowledge   ─ 계약 + RPC 서버 + lazy-harness가 import할 TS client
                    │
                    ▼
lazy-harness: submodule로 설치 → import → 포트를 Fabric으로 구현 → 모듈의 적합성 시험 통과
```

| 계약 | 정본 |
| --- | --- |
| 각 모듈의 연결 계약(포트 타입, fake, 적합성 시험, 다른 언어 모듈의 RPC 서버·TS client) | 그 모듈 저장소 |
| 모든 모듈 계약이 지켜야 할 공통 규칙 | 이 SDD(짧게 유지): Fabric 의존 금지, 루트 선언 파일(§6.1), 다른 언어 모듈의 JSON-RPC 2.0 stdio(§6.2), 공통 결과 의미(§6.3), 정수 major 버전(§6.4) |
| Fabric 기반 포트 구현·조립 | lazy-harness `packages/lazy-harness-pi` |

- 이유: 포트 모양은 이미 모듈이 소유한다는 원칙과 같고, 지금 모듈 2~3개에서는 세 번째 저장소가 버전·운영 부담만 늘린다. 모듈 사이에서 실제로 같은 코드가 반복될 때 공통 package를 다시 검토한다.
- 모듈 저장소의 연결 문서(예: 모니터링 `docs/design/attachment-contract.md`)는 그 모듈 계약의 정본이다. 이 SDD의 공통 규칙을 따르고 링크한다.
- 공통 규칙을 어기는 모듈 계약은 lazy-harness가 조립 시 거부한다(선언 파일·버전 검사).
- 용어: ‘모듈 저장소’(monitoring·knowledge 같은 저장소 단위)와 모니터링 저장소 안 `modules/*`의 ‘모니터링 목적 모듈’을 구분한다.
- LH-1의 `module-contract.md`·`attachment-contract.md`는 아직 GitHub에 없어 내용 비교를 하지 못했다.

#### 6.7 Fabric 연결 방식 — lazy-harness 쪽 계약 (문서화, 구현 전)

- 모듈 공통 규칙이 아니라 lazy-harness Pi 패키지가 지키는 계약이다. 모듈은 이 내용에 의존하지 않는다.
- lazy-harness Pi 패키지는 pi-fabric 내부를 import하지 않고, 설치된 Fabric의 공개 host 이벤트 `pi-fabric:program:run:v1`(`pi.events.emit`)로 프로그램을 실행한다. 요청은 저장된 프로그램 `ref` 또는 TypeScript `code`(최대 65,536자) 중 하나, JSON `input`(최대 64 KiB), 취소 `signal`, 한 번만 불리는 `reply`를 담는다. 응답은 `{ok:true, program, value, logs}` 또는 `{ok:false, error, program?}`이다.
- 응답을 공통 결과 형식(§6.3)으로 바꾸는 규칙:

| Fabric 응답·상황 | 공통 결과 | 이유 |
| --- | --- | --- |
| `ok:true` | `completed` / `terminal`, `value` | 성공 |
| `ok:false`이고 error가 `Invalid program run request:`, `No active Pi session to run the program in`, `Fabric program host unavailable:`로 시작 | `refused` / `terminal` | 프로그램 코드가 실행되기 전에 거부됨 |
| 그 밖의 `ok:false` | `failed` / `uncertain` | 프로그램이 일부 행동을 한 뒤 실패했을 수 있음 |
| 시간 안에 응답 없음(Fabric 미설치 포함) | `timed-out` / `uncertain` | 실행 여부를 알 수 없음 |
| 호출자 취소 | `cancelled` / `uncertain` | 이미 일부 실행됐을 수 있음 |

- 결과는 한 번만 확정하고 늦게 온 응답은 버린다. 자동 재시도하지 않는다.
- Fabric이 실행을 거부하는 조건: 활성 세션 없음, Python kernel 세션, `programs` provider가 없는 managed embedded host, `programs.run`을 막는 승인 정책. 프로그램 안의 각 행동은 따로 승인을 받는다.
- 이 방식은 라이브러리 의존 없이 설치된 Fabric을 쓴다. 설치된 Fabric의 버전 확인·고정 방법은 붙이기 PR에서 정한다.
- 근거: 설치본 `pi-fabric/docs/programs.md`(Running caller-supplied code), `pi-fabric/dist/protocol.d.ts`, `pi-fabric/dist/programs/host.js`(`handleFabricProgramRunEvent`, `runHostProgram`).
- 상태: 위 대응표는 근거에 기반한 문서화이며, 실제 구현과 확정은 모니터링을 붙이는 PR(시점은 사용자가 정함)에서 한다.

### 7. 아직 필요한 연결 규격

- 공통 포트 목록: 여러 모듈이 같이 쓸 포트(worker 실행, 판정, 모델 호출, embedding 등)의 v1 이름과 입력/출력 모양.
- 메시지 규약의 세부 schema 파일 위치와 형식(JSON Schema 등), 프로세스 환경 변수·자격 증명 전달 규칙.
- 기존 두 모듈의 정렬 작업(선언 파일 추가, 지식 모듈 결과의 공통 형식 변환, 지식 모듈 프로세스 진입점)은 각 모듈 세션이 자기 저장소에서 한다. 사용자 지시(2026-11-10): 모듈 세션들은 규약이 정해지기 전에 만들기 시작했으므로 자기 작업을 이 규약에 스스로 맞추고, 이 규약 작업에 맡기지 않는다.
- 기록 반영: 모니터링 기록(ADR 0061·0062 등)은 PR #16·#17로 main에 들어갔다(`2bb103f`, `e0048e4`). 지식 모듈 기록은 지식 세션이 정한다.
- 정리: main `packages/lazy-harness-pi/monitoring/`의 이전 전 복사본 정리는 모니터링 세션이 붙이기 PR(PR #15 + Fabric 어댑터)에서 한다. 붙이는 시점은 사용자가 정한다.

## 아직 정하지 않은 것

- 모듈 버전 갱신 정책(submodule 커밋을 언제 올리는지)과 호환성 확인 절차.
- `packages/lazy-harness-pi`와 pi-fabric의 관계: §6.7의 공개 이벤트 방식은 라이브러리 의존 없이 설치된 Fabric을 쓴다. 설치된 Fabric 버전의 확인·고정 방법은 붙이기 PR에서 정한다.
- 모듈별 공통 포트 규격을 둘지. 지식 모듈은 모니터링 포트 모양이 정해지면 맞추기로 한 상태다.

## 관련 결정과의 관계

- main의 project-identity SSOT `2026-11-07 correction`과 work/monitoring-engine-v2 브랜치의 ADR 0061 보강분 `Connector boundary (corrected 2026-11-09)`(아직 main 미반영)은 ‘모듈은 포트만, pi-fabric 의존은 lazy-harness 종합층만’을 이미 담고 있다. 이 SDD는 그것을 대체하지 않고, 그 종합층 안에서도 pi-fabric 위치를 Pi 통합 패키지로 한정하고 lazy-harness 역할·분리 절차를 확정한다.
- 결정과 이유는 ADR 0063(`.lazy-harness/decisions/0063-module-composition-contract.md`)에 남겼다. 모니터링 ADR 0061·0062가 PR #16으로 main에 들어간 뒤 번호를 정했다.

## Implementation map

- Status: `planned`
- Primary files:
  - `.lazy-harness/spec/platform/module-composition.md` — 이 계약.
  - `.lazy-harness/ssot/project-identity.md` — 소유권·저장소 관계의 정본 포인터.
- Key symbols: none; 어댑터·포트 코드는 아직 없다.
- Tests / protection: 없음. 모듈 fake 적합성 시험과 어댑터 적합성 시험은 각 분리 작업에서 만든다.
- Ownership boundaries: lazy-harness는 기록·종합 계약·어댑터를, 모듈 저장소는 모듈 내부와 그 시험을 소유한다. `packages/lazy-harness-pi/package.json`이 향후 pi-fabric 의존의 유일한 위치다.

## Rule placement

- Rule: lazy-harness는 기록·규칙 프레임워크이자 모듈 종합층이다. pi-fabric은 Pi 통합 패키지에서만 쓰고, 외부 판단은 모듈 판정 포트로 둔다(모듈 기본 연결 허용, 종합층이 교체 가능). 연결 계약: agent 연결 코드는 모듈 `hosts/<agent>`, Fabric 어댑터와 조립은 lazy-harness, TS 모듈은 in-process·다른 언어는 프로세스+JSON 메시지, 모듈은 git submodule 커밋 고정으로 받는다. 모듈 분리는 위 절차를 따른다.
- Scope: host-project
- Primary record: `.lazy-harness/spec/platform/module-composition.md` (절차·계약), 소유권 포인터는 `.lazy-harness/ssot/project-identity.md`
- Why not AGENTS.md: 모든 host에 적용할 agent 문법이 아니라 이 저장소와 모듈 저장소의 구조 계약이다.
- Why not local notes: 여러 세션과 저장소가 따라야 하는 공유 소유권이다.
- Confirmation: user-confirmed
