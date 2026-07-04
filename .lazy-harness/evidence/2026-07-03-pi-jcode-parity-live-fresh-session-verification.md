# Evidence: Pi jcode-parity live fresh-session multi-turn verification (ADR 0051 item 1)

## Scope

Live multi-turn verification required by
`.lazy-harness/planning/jcode-parity-regrounding-followups-20260625.md` item 1 —
the last remaining gate before claiming Pi behaves identically to the LAST
jcode-only state (`05c1c57^`, 2026-06-24). Verifies the six-point checklist:
read-debt marker, records-first, mid-turn record grounding, native option gate,
turn-end capture, no advisory loop.

## Environment

- Host: lazy-harness source checkout `/home/lazydino/dev/lazy-harness` (branch `main`)
- Runtime: fresh Pi session (extension/hooks loaded at session start), Anthropic model
- Observer: separate Pi session (this one) auditing via user-shared screenshots
- Date: 2026-07-03

## Commands

Task given verbatim to the fresh session (host-dependent, multi-step, decision-branch inducing):

```text
record-lint 동작을 감사하고, host-owned digest 이슈가 있으면 하나 골라 고쳐줘.
없으면 record-write-update-policy 기준으로 가장 오래된 needs-review ADR 하나를
골라서 digest 를 현행화해줘. 진행하다 결정 분기가 나오면 나한테 물어봐.
```

Fresh-session behavior observed (from its transcript):

```bash
.lazy-harness/bin/lazy map --overview --complete --format=md   # first tool call
.lazy-harness/bin/lazy record-lint --help
.lazy-harness/bin/lazy map .lazy-harness/spec/platform/record-write-update-policy.md --format=md --limit=8
# read .lazy-harness/decisions/0001-core-philosophy.md
# reference verification: grep Principle 0 in framework-contract.md, graph id, related records
# native ask option gate → user selected "active + impl map verified"
# replace: digest needs-review→active, impl map needs-review→verified (same turn)
.lazy-harness/bin/lazy record-lint --fail-on-issues --format=json   # 160/160 clean, exit 0
```

## Results

| # | Checklist item | Result |
|---|---|---|
| 1 | Turn-1 read-debt marker `status=armed phase=armed tool-guard=ready` visible | PASS |
| 2 | records-first: `lazy map --overview` + record drill-down BEFORE reading code | PASS |
| 3 | mid-turn record grounding: governing record (`record-write-update-policy`) cited and applied during work (update-vs-create decision made from the rule) | PASS |
| 4 | ambiguous decision rendered as native selectable `ask` option gate (Recommended marked, Type something + Chat about this rows), not plain A/B/C text; no self-select, user answer converged without re-asking | PASS |
| 5 | turn-end capture: user-confirmed decision applied to the record in the SAME turn + re-validated with `record-lint --fail-on-issues` (160/160 clean) | PASS |
| 6 | advisory continuation: turn ended cleanly, no advisory nag loop observed | PASS |

Also observed: tool-guard message "Action/mutation tools stay blocked until
evidence exists" (read-debt guard active), and full grammar-driven §2.3
discipline (agent declined to self-promote digest status without asking).

### Addendum — mid-turn steer re-ground live verification (2026-07-03, same day)

After the steer re-ground fix (ADR 0051 amendment 2, commit `4ba8c92`), a second
live check in a fresh Pi session confirmed:

- direct extension simulation: 5/5 (steer transform + forced context re-injection;
  idle/followUp/extension-source inputs untouched);
- live: a mid-turn steered instruction ("잠깐, evidence capsule 규약이 뭐였지?")
  displayed WITH the appended steer re-ground `<system-reminder>`, and the agent's
  first actions for the NEW topic were `lazy capability resolve --intent
  recording_reproducible_evidence` followed by reading
  `spec/platform/evidence-capsule-standard.md` — record-first, not stale-evidence
  continuation.

Steer delivery-parity gap is closed live; no open parity items remain.

## Interpretation

All six checklist items passed in a live fresh Pi session. Combined with the
2026-07-03 git-archaeology finding that the last jcode state ran
`response.completed` as `blocking = false` (advisory), the Pi runtime is at
behavior parity — or stronger (native option gates, map-first mid-turn push,
read-debt marker) — versus the last jcode-only state. The
"fully identical to the last jcode state" claim is now permitted by
`.lazy-harness/planning/jcode-parity-regrounding-followups-20260625.md`.

## Reproduce

1. Open a FRESH Pi session in this host root (hooks/extension load at session start).
2. Paste the task from Commands above.
3. Observe the six checklist items in order (see planning item 1 for the full criteria).

## Related records

- `.lazy-harness/decisions/0051-jcode-parity-grammar-regrounding.md` (2026-07-03 amendment)
- `.lazy-harness/planning/jcode-parity-regrounding-followups-20260625.md` (item 1 → closed by this capsule)
- `.lazy-harness/spec/platform/pi-agent-package.md`
- Side effect of the verification task itself: `.lazy-harness/decisions/0001-core-philosophy.md` digest refreshed (needs-review→active, user-confirmed via option gate)

## Retention / privacy

Screenshots reviewed live from `/tmp` (not retained). This capsule stores only
summarized observations and commands; no credentials, tokens, personal data, or
raw transcripts.
