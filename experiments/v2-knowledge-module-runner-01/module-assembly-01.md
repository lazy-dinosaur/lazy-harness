# Module assembly 01

Implemented fragment generation with injected LLM transport, prompt rendering, SHA-256 attempt audit and validator reuse; added injectable Jev page judge with model-bearing packets, two-attempt response validation, redacted optional raw capture and exposed judgments. Added CLI `collect --judge oracle|jev`, `decide --operation`, and required model for `call`. Protected group ID construction and pre-expansion `collect.relevant` with tests.

Changed files: `fragment.py`, `judge_jev.py`, `runner.py`, `fixtures/call-packet.json`, `test_assembly.py`, `test_runner.py`, `test_collect.py`, `README.md`, `NOTES.md`, this report. Existing `fragmenter/` and `medivance-pilot-*` sources/results were read-only.

New functions: `render_prompt`, `fragment_record`, `make_jev_judge`, `safe_error` (in `judge_jev.py`). Existing checker remains the single implementation, imported by `fragment.py`.

Validation: `cd experiments/v2-knowledge-module-runner-01 && python3 -m pytest -q` — 79 passed, 31 subtests passed (91.71 s). An initial root-invoked run had 78 passed, one failure: existing embedding subprocess test assumes the experiment directory as cwd (`import embed`); running from the experiment directory passed. No network/Jev/LLM paid requests or remote DB writes were made. Test container is absent after the suite. No staged files.

Limitations: fragment caller must itself enforce fresh LLM context, no inherited conversation, read-only invocation and harness-free neutral cwd; hashes are retained in attempts, full raw responses need caller-managed retention. Jev network path was exercised only by fake HTTP; live connectivity not verified. The full `lazy validate --plan standard` was not run because it can mutate files outside the task's write boundary. Existing host record migration remains pending (record-lint issues 30, graph legacy rows 37); guided migration is separate user-approved work.

Review: no blockers found within the implemented and locally tested scope.
