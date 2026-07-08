# Evidence: lazy_move_project direct switch + downstream sync

## Scope

- Work unit: fix `lazy_move_project` so it actually switches Pi sessions instead of queuing `/lazy-move` as a follow-up chat message.
- Source commit validated/synced first: `b97e4d7b51f9fc974b40858d6f12ad64bffa19b3` (`Fix lazy_move_project direct session switch`).
- Downstream sync targets: initialized `/home/lazydino/dev/*` hosts with `.lazy-harness/state/synced-from-commit`; source checkout `lazy-harness` excluded.

## Environment

- Source root: `/home/lazydino/dev/lazy-harness`
- Runtime: local Pi/lazy-harness dogfood environment
- Date: 2026-07-08

## Commands

```bash
python3 -m py_compile .lazy-harness/scripts/self-test.py
bun packages/lazy-harness-pi/extensions/lazy-harness/index.ts
python3 .lazy-harness/scripts/self-test.py --scope framework

git add .lazy-harness/knowledge/candidates.jsonl \
  .lazy-harness/scripts/self-test.py \
  .lazy-harness/spec/platform/pi-agent-package.md \
  .lazy-harness/tests/pi-agent-package.md \
  packages/lazy-harness-pi/extensions/lazy-harness/index.ts
git commit -m "Fix lazy_move_project direct session switch"
git push

# Enumerate initialized downstream hosts and sync framework Category A.
python3 - <<'PY' > /tmp/lazy_move_sync_hosts.txt
from pathlib import Path
base=Path('/home/lazydino/dev')
for p in sorted(base.iterdir()):
    if not p.is_dir() or p.name == 'lazy-harness' or p.name.endswith('path-only-backup'):
        continue
    if (p/'.lazy-harness/bin/lazy').exists() and (p/'.lazy-harness/state/synced-from-commit').exists():
        print(p)
PY
python3 - <<'PY'
import subprocess, pathlib, sys
hosts=[pathlib.Path(x.strip()) for x in open('/tmp/lazy_move_sync_hosts.txt') if x.strip()]
for h in hosts:
    r=subprocess.run([str(h/'.lazy-harness/bin/lazy'),'sync','--force'],cwd=h,text=True,capture_output=True,timeout=180)
    if r.returncode:
        print(h, r.stdout, r.stderr, file=sys.stderr)
        sys.exit(1)
print('SYNC_OK', len(hosts))
PY

# Deployment-reach verification: marker + actual file contents on every host.
python3 - <<'PY'
from pathlib import Path
import json, sys
hosts=[Path(x.strip()) for x in open('/tmp/lazy_move_sync_hosts.txt') if x.strip()]
head='b97e4d7b51f9fc974b40858d6f12ad64bffa19b3'
checks=[
  ('.lazy-harness/spec/platform/pi-agent-package.md','must not claim success by queuing `/lazy-move` as a follow-up chat message'),
  ('.lazy-harness/tests/pi-agent-package.md','pi_extension_lazy_move_project_switches_directly'),
  ('.lazy-harness/scripts/self-test.py','lazy_move_project did not call switchSession'),
]
fail=[]
for h in hosts:
    marker=json.loads((h/'.lazy-harness/state/synced-from-commit').read_text())
    if marker.get('syncedFromCommit') != head:
        fail.append((h.name,'marker',marker.get('syncedFromCommit')))
    for rel,needle in checks:
        if needle not in (h/rel).read_text(errors='replace'):
            fail.append((h.name,rel,'missing '+needle))
if fail:
    print('VERIFY_FAIL', fail[:80])
    sys.exit(1)
print('VERIFY_OK',len(hosts),'hosts @',head[:7])
PY
```

## Results

- Source validation passed: `lazy-harness self-test ok (scope=framework, ran=84, skipped=0)`.
- Commit/push succeeded: `b97e4d7` pushed to `origin/main`.
- Downstream sync succeeded: `SYNC_OK 52`.
- Deployment-reach verification succeeded: `VERIFY_OK 52 hosts @ b97e4d7`.
- Sample target hosts verified: `beloaclinic`, `goedamjip-pipeline`, `medivance`, `medivance-homepage`, `medivance-homepage.admin-members`, `medivance.rebuild-dev-from-main-20260622`, `medivance.refactor-unify-chat-relay-toggle`, `medivance.release-main-dispatch-1.5.25`, `medivance.verify-pr-147`, `medivance.work-dev-20260613-1506`.

## Interpretation

- The source fix is protected by a new fake-runtime regression in `check_pi_package_layout_and_contract`.
- The original bug was confirmed: the tool path queued `/lazy-move` via `sendUserMessage(..., { deliverAs: 'followUp' })`, which is not command execution.
- The fixed tool path calls `switchToProjectSession(ctx, target, prompt)` directly when `ctx.switchSession` is available, and falls back to a truthful manual instruction when it is not.
- Deployment reach was verified by checking both the sync marker and actual synced file contents on every initialized downstream host.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, run `python3 .lazy-harness/scripts/self-test.py --scope framework`.
2. Re-run the host enumeration/sync script above.
3. Re-run the deployment-reach verification script above with the expected source commit.

## Related records

- `.lazy-harness/spec/platform/pi-agent-package.md`
- `.lazy-harness/tests/pi-agent-package.md`
- `.lazy-harness/spec/platform/evidence-capsule-standard.md`
- `.lazy-harness/knowledge/candidates.jsonl` (`candidate-lazy-move-project-tool-does-not-switch-20260705`)

## Retention / privacy

- No raw user transcript, credentials, tokens, or product data stored.
- Host names are local development checkout names used only to prove deployment reach.
