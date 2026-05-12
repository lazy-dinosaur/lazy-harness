# ADR 0015 — Doctor C16 확장: Plan + Progress Freshness

- Status: Accepted
- Date: 2026-05-10
- Trigger: 사용자 catch — "지금 진행상황이나 이런거 전부 체크하면서 하고 있는거지??"
- Related: ADR 0010 (Principle #20 Plan Status Hygiene), ADR 0011 (Verification), ADR 0012 (Audit Cascade)

## Context

ADR 0011~0014 작성 + audit cascade fix + AGENTS.md 갱신 + framework 21.8 추가까지 모두 완료된 후, 사용자가 "전부 체크하면서 하고 있는거지??" 질문.

조사 결과 다음 누락 발견:

| 항목 | 상태 |
|---|---|
| ADR 작성 | ✅ |
| decisions.jsonl | ✅ |
| actions.jsonl | ✅ |
| Framework contract 갱신 | ✅ |
| AGENTS.md 갱신 | ✅ |
| Doctor 14 pass | ✅ |
| **phase plan `<addedDuringPhase>`** | ❌ ADR 0011~0014 미등록 |
| **handoff Husky/framework lines** | ❌ stale (ADR 0009 enforcement pending 표기, framework 956 lines 표기) |
| **progress/2026-05-10.md** | ❌ 16:00 이후 9 항목 작업 흔적 0 |

이는 **Principle #20 (Plan Status Hygiene) 의 본질이 다시 tested 된 것**. ADR 0010 으로 명문화했음에도 같은 패턴 재발.

원인: doctor C12 (Plan Hygiene) 가 closed phase status 만 검사. **closed phase 의 `<addedDuringPhase>` 갱신 여부, handoff 의 staleness, progress 의 누락은 검사 안 함**.

## Decision

Doctor C16 (Handoff Freshness) 의 검사 범위를 확장:

### 현재 C16 (충분치 않음)

```bash
ADR count match (handoff 의 ADR 수 vs 실제 ADR file 수)
Framework version match
actions count match
```

### 새 C16 (확장)

추가 검사:

```bash
# 1. handoff 안 stale ADR 표기 detect
# - "pending ADR ####" 같은 ADR enforcement 가 closed 됐는데 pending 표기 남은 케이스
# - "framework v1.X N lines" 의 N 이 실제와 다름

# 2. closed phase 의 addedDuringPhase 가 ADR cascade 반영하나
# - 마지막 closed phase 의 addedDuringPhase note 안 ADR ID 들 = decisions.jsonl 의 ADR ID 들 ⊃ 관계인지
# - phase close 시각 후 추가된 ADR 이 해당 phase addedDuringPhase 에 backfill 됐나

# 3. progress/<today>.md 가 actions.jsonl 의 오늘 entry 와 sync
# - 오늘 actions.jsonl 마지막 entry timestamp vs progress 파일 마지막 mtime 의 차이
# - >2 시간 gap + actions 가 더 신선하면 warn (사용자 작업했는데 progress 미갱신)
```

### 구현 위치

`.jcode/skills/harness-doctor/scripts/doctor.sh` 의 C16 함수 확장. 기존 ADR/version/actions count 검사는 유지, 위 3 항목 추가.

## Why now

이번 세션이 **사용자 catch 의 9/14 ADR 패턴** 의 새 instance:

| ADR | 사용자 trigger |
|---|---|
| 0010 | "phase close 했는데 status 안 바뀐듯" |
| 0011 | "검증하고... 사람에게 물어보는것도?" |
| 0012 | "전수조사 하고갈까??" |
| 0013 | "외부내용이 필요한게 있으면 안되" |
| 0014 | "버그 먼저 잡고가야하는거" |
| **0015** | **"진행상황 전부 체크하면서 하고 있는거지??"** |

framework 가 **AI self-report 한계** 를 인정하고, 사용자 catch 가능 항목을 점진적으로 doctor 자동 검사로 흡수해야 함. 이게 framework "self-correcting" 의 정의.

## Implementation (this session)

C16 확장은 5c 안에서 실행 (ts-morph 도입과 함께). 이번 세션은 다음만 즉시 처리:

1. ✅ phase plan `<addedDuringPhase>` 에 ADR 0010~0014 추가
2. ✅ handoff Husky/framework version 갱신
3. ✅ progress/2026-05-10.md 16:00 이후 작업 추가

C16 코드 변경은 5c 의 doctor 확장 작업으로 묶음.

## Verification

- L0: file written
- L2 marker: 다음 세션 ���입 시 doctor C16 새 검사 발동 → 이번 세션 같은 누락 자동 감지
- L4 사람 review: 5c 시작 전 사용자에게 doctor C16 확장 동의 ask

## Consequences

### Positive

- 사용자 catch 패턴 1 항목 자동화
- doctor 가 진짜 "session 끝나고 갱신 다 됐나" 게이트 역할

### Negative

- doctor 1 회 호출당 비용 약간 증가 (jsonl scan + xml parse)
- false positive 가능 — fix 시 false positive 줄이는 휴리스틱 정교화 필요

### Risk

- "C16 확장" 자체가 또 한 번의 self-report 가 될 가능성. 5c 에서 L3 negative test (의도적 stale handoff 만들고 fail 검증) 필수.
