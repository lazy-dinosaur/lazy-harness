# V2 sandbox bootstrap

## Rule digest
- Status: active
- Layer: TDD
- Scope: host-project
- Aliases:
  - V2 sandbox
  - offline experiment runner
  - 샌드박스
  - 합성 비교 실험
- Applies when: running or extending the V2 offline experiment scaffold.
- Must: isolate each run; preserve input/results on reset; distinguish synthetic explicit-operation tests from actual model digestion and production benchmarks; no external/model calls in this first slice.

## Approval and boundary
User approved creating the minimal sandbox in the existing V2 worktree, then explicitly approved parent-session implementation after subagent skill/guide ENOENT. No child was launched. V2 knowledge compatibility is not required. No production DB, schema adoption, daemon deployment, vector retrieval, model integration or file migration is authorized by this slice.

This is a trusted local experiment runner, not an OS security sandbox. It has no network/model code path. Cooperative deadlines do not interrupt blocking IO. No semantic search algorithm is implemented: explicit keys/operations exercise experimental storage plumbing.

## Protected behavior
- All three storage modes answer synthetic proposal/change/rollback and cross-area checkpoints.
- Duplicate IDs do not apply twice; conflicting duplicate IDs in fixture are rejected.
- Oracle answer mutation changes only scoring, not query output.
- Deadline/budget bounds fail visibly.
- Runs start from empty state, have unique output directories, and retain input hashes and runner hashes.
- Reset adds a new empty state artifact without deleting prior input, state or results.
- Invalid run IDs, symlink output root, and unknown reset targets are refused.

## Approved scoring repair (version 2)
User requested repair of the readiness review findings. Scope: type-aware JSON scoring, explicit missing/null gold, optional CI score gate; not shared-state concurrency, models, OS portability or a scheduler.
- 사용자 목적 재확인: 이 샌드박스는 향후 병렬 읽기·병렬 작성 등 병렬 작업을 작은 단위로 분리하여 시험할 기반이다. 현재 독립 run 병렬 실행은 준비 단계일 뿐, 공유 지식에 대한 읽기/쓰기 동시성 검증을 대신하지 않는다. 이 확인은 목적 정렬이며 새 동시성 구현 범위·정책 채택이나 실행 승인은 아니다.
- 사용자 명명·역할 확인: ‘하네스 연구소’. 하네스 자체를 설계·구축·개발하며, 구성 요소와 조합을 작은 실험으로 비교·측정하고 결과를 근거로 채택/수정하는 개발·연구 환경이다. 샌드박스는 그 실험 기반이며, 고정된 제품 설계를 미리 정답으로 삼는 곳이 아니다. 이 역할 확인만으로 새 구현이나 실험 실행을 승인한 것은 아니다.
- 사용자 확인: 개별 모듈의 단독 시험뿐 아니라 모듈들을 연결했을 때 정상 동작하는지 검증할 수 있어야 한다. 연구소의 검증 범위는 단위 검증에서 모듈 간 통합·전체 흐름 검증으로 이어진다. 구체 연결 계약·실험 구현은 아직 미확정이다.
- `json_equal` recursively distinguishes booleans/numbers, respects array order and ignores object key order; JSON numbers 1/1.0 compare equal. Nonfinite values are rejected before run creation.
- `expected_found` defaults true; present expectations require `expected` (including null). Missing expectations set false and omit `expected`; ambiguous gold is rejected. Query returns `found` independently of value.
- `--min-accuracy` is optional, finite, within [0,1]; every condition/repetition must pass independently. With a parsed invocation, threshold failure returns 2 after persisting results/gate; runtime failure returns 1; unrequested/passed returns 0. Argument syntax errors also use argparse exit 2 and are not score evidence.
- Existing receipts remain immutable. New manifests record scorer_version=2 and min_accuracy. This does not measure semantic LLM truth.

## Layer completeness / Discovery capture
- SDD: updated here — local run/reset CLI and artifact contract; not a product API. Contract is documented in this primary record; no separate layer record updated.
- BDD: updated here — repeatable local experiments and evidence-preserving reset. Behavior is documented in this primary record; no separate layer record updated.
- SSOT: updated here — output confined to sandbox runs; no external DB/model; experimental JSON is not V2 storage adoption. Experiment boundary is documented here; no production storage policy changed.
- DDD: no independent delta — explicit fixture operations only, no ontology adoption.

Planning: updated by reference to this approved execution slice; TDD: updated; ADR: none. Rule placement: this test/experiment contract is the primary canonical record for the bootstrap, not a new project operating policy.

## Implementation map
- `experiments/v2-sandbox/sandbox.py`: `validate_fixture`, `Replay.apply/query/snapshot`, `evaluate`, `run_directory`, `save`, `run`, `reset`, `main`. CLI → validate/copy fixture → fresh replay per condition → oracle scoring → immutable result artifacts.
- `experiments/v2-sandbox/fixtures/smoke.json`: six input events, five checkpoint questions, explicit expected values.
- `experiments/v2-sandbox/test_sandbox.py`: nine unittest cases for replay, budgets, scoring separation and filesystem boundaries.
- `experiments/v2-sandbox/test_scoring.py`: nine regression methods for `json_equal`, `score_answer`, missing/null, duplicate-ID type conflicts, finite inputs, per-condition gates and CLI exit/evidence behavior.
- `experiments/v2-sandbox/README.md`: commands and honest limitations.
- `experiments/v2-sandbox/.gitignore`: run artifacts and Python cache excluded from Git, not deleted.
- Related intent: [V2 research](../planning/v2-vision-feasibility-research.md), especially sections 14–15. Older unapproved product proposals there remain proposals; this record only approves the sandbox slice.

## Validation procedure
Focused: `cd experiments/v2-sandbox && python3 -m unittest discover -v` plus smoke runner in the same checkpoint. Final: `.lazy-harness/bin/lazy validate --plan standard`. Prior standard gate failure in this worktree includes existing Archify binary fixtures; do not delete them to manufacture green. Actual run receipts are kept in the local run directory and validation capture, not claimed before execution.

Focused evidence: 9/9 unittest cases passed (0.004s). Three conditions × three repetitions smoke artifact: `experiments/v2-sandbox/runs/327252e47b9941de8e400e18b2e91007/`. Python primary LSP diagnostics: two files clean. This evidence only checks local experiment plumbing; it is not LLM accuracy or scaling evidence.
