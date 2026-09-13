# Evidence — Dedicated Reader live canary R3

Status: **TERMINAL-INCOMPLETE — no retry**

## Identity and approval

- User selected `사전점검 통과 후 1회 실행 (Recommended)` after exact prompt/checklist preparation. One allowance consumed; no further run is authorized.
- Fresh root: `/tmp/lh-reader-canary-r3-preparation-c2vytczu`; isolated source checkout at `source/`, revision `58fbcbf5e9d632bf9b0e7a87857ad8ed05f01f7b` plus 618-file `source-manifest.json` (dirty source bytes are bound independently of revision).
- Prompt SHA-256: `c370086ac3f0139142f487c235af2d431fdad8dc0871ce91fe44f78e689ca561`.
- Checklist SHA-256: `a9b008a32f91d907e0be8770e5d0e48d39547e767c2559f0675cb2ef96b1198b`.
- Parent session `01a07b21-95d9-767d-bd24-6b2480ba302f`: actual `openai-codex/gpt-5.6-sol`, medium.
- Reader async run `342a08d1-fff2-4be8-b084-de2354908670`: actual `openai-codex/gpt-5.6-luna`, low; one child session only.
- Process dispatch `ember-dune` exited 0 after 86.228s. Process exit is not functional PASS.

## Observed outcome

Package discovery, exact models, first complete overview, Reader-selected drill, and actual content-before-incomplete-join were observed. Requested body budget stayed within six calls / 1,200 lines / 200 per call. Parent performed no canonical body reads. All manifest-bound source bytes were preserved.

The intended parallel evidence workflow did not succeed:

1. Parent added `toolBudget: {hard: 6, block: "*"}` to the Reader launch. This is a total-tool cap, not a body-read cap. Overview, three identity probes, and drill consumed five calls. Of six requested body reads, only the first succeeded; five were blocked by the subagent tool budget. This live result does not justify changing the derived per-read cap.
2. Parent's source `rg` command included `2>/dev/null`. The pending guard rejected this forbidden redirection. This is not evidence of a false block for permitted simple `rg`; no source evidence was delivered.
3. Parent first emitted a terminal stop, then consumed the child notification, called `lazy_reader_join` with incomplete status, and emitted another stop. It did not retry or use fallback, but did not obey the prompt's literal no-tools-after-failure stop rule.
4. Final stdout was a terminal incomplete message with a migration advisory; stderr was empty. No substantive policy answer was delivered, so substantive-answer preservation cannot be credited as tested successfully.

The Reader's `recordsRead` reported lines 1–200 for the only successful record, which has 182 lines in the snapshot. Requested range is not proof that all 200 lines were delivered. No complete-ledger or quality PASS is inferred.

## Diagnostic measurements

| Measure | Parent | Reader | Combined |
|---|---:|---:|---:|
| Assistant turns | 6 | 5 | 11 |
| Tool calls | 4 | 11 | 15 |
| Failed tool calls | 1 | 5 | 6 |
| Provider total tokens | 92,616 | 60,672 | 153,288 |
| Reported cost | $0.16562700 | $0.00924952 | $0.17487652 |

No semantic quality score, efficiency promotion, general model-default claim, or production-readiness claim is admitted. The eight-criterion substantive checklist was not satisfied because no substantive answer was produced.

## Implementation map / evidence paths

- Fresh-root `execution-approval.json`, `preflight.json`, `prompt.md`, `checklist.json`, `source-manifest.json`: admission inputs and byte identities.
- Fresh-root `run/started.json`, `run/status.json`, `run/output.md`, `run/stderr.txt`: one-shot process evidence.
- Fresh-root `sessions/**/*.jsonl`: actual model identity, launch arguments, tool calls/results, child notification, and output chronology.
- Fresh-root `analysis.json`, `terminal-outcome.json`: transcript-derived counts and terminal disposition.
- `packages/lazy-harness-pi/agents/record-reader.md`: existing body-budget and no-retry contract; not changed by R3.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts`: existing pending shell guard and incomplete join; no runtime fix applied here.
- `.lazy-harness/tests/pi-agent-package.md` and `.lazy-harness/tests/pre-action-search-evidence-guard.md`: existing static protection; static review success did not predict this live launch behavior.
- `.lazy-harness/planning/agent-neutral-orchestration-pilot.md`: approved plan and outcome pointer.

## Discovery capture

| Layer | Judgment | Disposition |
|---|---|---|
| DDD | none | No new domain rule. |
| SDD | none | No contract change; observed launch did not meet existing operational restrictions. |
| BDD | none | Intended parallel flow unchanged and not successfully demonstrated. |
| TDD | updated | This capsule captures the immutable failing live witness; existing static tests remain distinct. |
| ADR | none | Reader ownership and fallback architecture unchanged. |
| SSOT | none | No settings or ownership change; copied temporary credentials were removed. |
| Planning | updated | R3 allowance consumed; further remediation/execution requires a new decision. |

Potential follow-up is a candidate only: separate total-tool and body-read budget guidance, use allowed native/simple source reads, and reconcile terminal-stop versus late-child notification handling. No fix, new canary, main integration, commit, push, release, or legacy graph migration is authorized or performed. R2 and earlier frozen artifacts remain unchanged.
