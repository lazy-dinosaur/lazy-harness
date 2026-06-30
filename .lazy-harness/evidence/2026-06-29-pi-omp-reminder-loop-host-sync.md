# Evidence — Pi/OMP reminder-loop fix synced to local hosts

- Date: 2026-06-29
- Source root: `/home/lazydino/dev/lazy-harness`
- Source HEAD marker: `ac0570c45fc5389222711ff9bfd8ddcd582d2ad6`
- Source state: working tree contained the Pi/OMP reminder-loop patch in `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` plus SDD/TDD updates; host sync copied the working-tree managed files while markers record the source HEAD.
- Scope: all lazy-harness hosts discovered under `/home/lazydino/dev` except the source checkout itself:
  - `/home/lazydino/dev/medivance`
  - `/home/lazydino/dev/medivance-pwa`
  - `/home/lazydino/dev/medivance-homepage`
  - `/home/lazydino/dev/medivance-homepage.admin-members`
- Runtime package status:
  - OMP plugin path resolves to `/home/lazydino/dev/lazy-harness/packages/lazy-harness-pi` and `cmp` against the source extension returned `0`.
  - Pi user package list includes `/home/lazydino/dev/lazy-harness/packages/lazy-harness-pi`; Medivance local `.pi/settings.json` also points to `../../lazy-harness/packages/lazy-harness-pi`.

## Commands

```bash
SOURCE=/home/lazydino/dev/lazy-harness
for host in /home/lazydino/dev/medivance /home/lazydino/dev/medivance-pwa /home/lazydino/dev/medivance-homepage; do
  bun "$SOURCE/.lazy-harness/scripts/lazy-sync.ts" --from "$SOURCE" --target "$host" --force --quiet
  (cd "$host" && .lazy-harness/bin/lazy doctor --profile=smoke)
  (cd "$host" && .lazy-harness/bin/lazy test --scope=host)
done

host=/home/lazydino/dev/medivance-homepage.admin-members
bun "$SOURCE/.lazy-harness/scripts/lazy-sync.ts" --from "$SOURCE" --target "$host" --force --quiet
(cd "$host" && .lazy-harness/bin/lazy doctor --profile=smoke)
(cd "$host" && .lazy-harness/bin/lazy test --scope=host)

find /home/lazydino/dev -maxdepth 5 -path '*/.lazy-harness/bin/lazy' -print | sed 's#/.lazy-harness/bin/lazy##' | sort
grep -R "REMINDER (mid-turn re-grounding). Re-apply the lazy-harness grammar" -n \
  /home/lazydino/dev/medivance/.lazy-harness \
  /home/lazydino/dev/medivance-pwa/.lazy-harness \
  /home/lazydino/dev/medivance-homepage/.lazy-harness \
  /home/lazydino/dev/medivance-homepage.admin-members/.lazy-harness || true
```

## Results

| Host | Sync | Doctor smoke | Host test | Notes |
|---|---:|---:|---:|---|
| `/home/lazydino/dev/medivance` | pass | pass | pass (`ran=58`, `skipped=26`) | D07 package health ok |
| `/home/lazydino/dev/medivance-pwa` | pass | pass | pass (`ran=58`, `skipped=26`) | D07 package health warn |
| `/home/lazydino/dev/medivance-homepage` | pass | pass | pass (`ran=58`, `skipped=26`) | D07 package health ok |
| `/home/lazydino/dev/medivance-homepage.admin-members` | pass | pass | pass (`ran=58`, `skipped=26`) | worktree `.git` is a file; D07 package health warn |

Additional checks:

- Discovered lazy-harness hosts under `/home/lazydino/dev`: source checkout plus the four hosts above.
- The old generic fallback string `REMINDER (mid-turn re-grounding). Re-apply the lazy-harness grammar` was absent from all four host `.lazy-harness` copies.
- Each synced host's `.lazy-harness/spec/platform/pi-agent-package.md` contains the new contract: fail open silently when `on-context.sh` cannot provide the real relevant-record body; do not inject a generic fallback reminder.

## Interpretation

The managed lazy-harness framework files are updated across all discovered local downstream hosts. OMP/Pi runtime extension loading remains source-linked to `/home/lazydino/dev/lazy-harness/packages/lazy-harness-pi`, so fresh Pi/OMP sessions should load the patched extension. Existing already-running sessions may still hold the old handler until restart or reload.

## 2026-06-30 display-label cleanup

User chose Option A for the visible STOP/advisory duplication: keep the hook body (`STOP...`) and remove the Pi/OMP display transport label. Source change removes `customType: "lazy-harness-advisory"` from the non-steering `sendMessage({ display: true })` fallback while preserving the follow-up chain cap.

Validation:

- `python3 .lazy-harness/scripts/self-test.py --scope framework` — pass (`ran=84`, `skipped=0`).
- `.lazy-harness/bin/lazy doctor --profile=smoke` — pass.
- Fake Pi runtime agent_end test — pass: first advisory queued as follow-up, second/third rendered display-only, display messages contain no `customType`.
- Synced hosts: `/home/lazydino/dev/medivance`, `/home/lazydino/dev/medivance-pwa`, `/home/lazydino/dev/medivance-homepage`, `/home/lazydino/dev/medivance-homepage.admin-members`; all sync commands exit 0 and doctor smoke passes; synced SDD contains the no-custom-transport-label contract.
