# Offline Fabric compaction summary coverage evidence

2026-11-14 approved regression; metadata only. Raw synthetic prompts/frames remain private,
not distributed framework knowledge. Governing SDD: `.lazy-harness/spec/platform/monitoring-thin-consumer.md#fabric-compaction-coexistence`;
protection TDD: `.lazy-harness/tests/monitoring-attach-phase1.md`.

## Scope and isolation

Reused the original private faux Pi 1.5.0 + pi-fabric 0.135.2 probe, pointing only its three
monitoring imports at the isolated host sumfix worktree. Reused identical fixed-ID seed,
scripted streamFunction, local typed classifier, ModelRuntime allowModelNetwork:false,
fail-closed runtime inference/fetch/net/tls sentinels and unshare -Urn network isolation.
Pi compaction keepRecentTokens is **20000** in all three comparison processes. No user
settings/credentials/live activation; ZERO real model calls and ZERO network attempts.
Git fetch/worktree creation invoked from /tmp; every repository command ran inside new
sumfix worktrees, never either shared checkout. Root/submodule frozen installs; no new deps.

## Verified results (monitoring pin 8ff4cdf)

| Receipt | Fabric only | Monitoring before Fabric | Monitoring after Fabric |
| --- | --- | --- | --- |
| Real model calls / network attempts | 0 / 0 | 0 / 0 | 0 / 0 |
| Scripted chat completions | 6 | 6 | 6 |
| Fake classifier calls | 0 | 3 | 3 |
| Fabric/native compaction result | baseline | exactly equal | exactly equal |
| firstKeptEntryId | seed0051 | seed0051 | seed0051 |
| Observer snapshot bytes (ceiling 65536) | n/a | 58094 | 58094 |
| Separate derived summary bytes (cap 8192) | n/a | 7883 | 7883 |
| Snapshot summary omitted bytes | n/a | 0 | 0 |
| truncatedHead / newest messages | n/a | 23 / 32 | 23 / 32 |
| Next judgement includes `[summary]` | n/a | yes | yes |
| material_limit | n/a | none | none |
| Window bytes (ceiling 16384) | n/a | 9900 | 9900 |
| Material summary bytes / omitted original bytes | n/a | 4106 / 3816 | 4106 / 3816 |
| Fabric section headers preserved in material | n/a | all 5 | all 5 |

Exact equality covers native summary/firstKeptEntryId/tokensBefore, manual compact result and
Fabric hook result including token projection. Summary SHA-256 in all three runs:
`996619712b2aa297ef010729e4f91c20397880aec4a386880be006f8c3a65279`.
This new run is compared against its equal-cwd-length baseline, not historical probe hashes.

Before boundary: attached=true, paused=true, rebuilding=true, ready=false. Terminal compact:
attached=true, paused=false, rebuilding=true, ready=false. Subsequent input after drain:
attached=true, paused=false, rebuilding=false, ready=true, running window, generation 2.
All pre-compact monitoring callbacks return undefined. The held old completion is aborted and
logged once as skipped/stale_scope, never accepted; third fake call succeeds. Lifetime budgets
and event-budget renewal distinction remain intact.

This fixture's 7883-byte summary fits the snapshot share without truncation; material still
shrinks it and marks omitted bytes. Oversize/multibyte section and catalog-heavy cases are
separately protected by the vendor summary-coverage and summary-material tests. An initial
checker incorrectly required nonzero snapshot omissions; corrected to permit zero for a fitting
summary. The checker also now selects conversation-history before JSON-decoding material (catalog references are plain Markdown). Both were checker assumptions, not product defects or inference calls.

## Reproduction and private receipts

Private tree: `/tmp/fabric-compaction-probe/out/`. Original `REPORT.md`, `verification.json`,
`probe.ts` and `*-verified/result.json` retain the old limitation evidence. New
`sumfix-probe.ts` and `sumfix-verify.ts` use `default-tail-{baseline,before,after padded to 8}-sumfix/result.json`
and emit `sumfix-verification.json`. Each run from `/tmp/fabric-compaction-probe`:
`timeout 120 unshare -Urn bun out/sumfix-probe.ts default-tail <baseline|before|after>`;
then `bun out/sumfix-verify.ts`. All three result files are read by the strict checker.
Directories/files are private 0700/0600. No raw result is committed. Scripts depend on the
installed versions above; these ephemeral local receipts are not a portable published harness.

Module validation: 1021 tests pass, 0 fail; full typecheck; frozen install and unchanged lockfile.
Host validation is recorded in the PR body after monitoring/capture/Reader/typecheck/full-suite,
record-lint, changed-file and privacy checks finish. These synthetic receipts do not claim live
provider quality, hard cancellation/termination, restart durability, paging GC or RSS reduction.
