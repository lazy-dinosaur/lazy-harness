# Pi Agent Package Regression

Status: active
Layer: TDD

## Regression target

The in-repo Pi package must remain installable and must bridge Pi extension events to canonical lazy-harness lifecycle hooks without inventing a second policy engine.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `pi_package_manifest_resources` | Parse `packages/lazy-harness-pi/package.json` | Manifest name is `@lazy-dinosaur/lazy-harness-pi`; keyword includes `pi-package`; `pi.extensions`, `pi.skills`, and `pi.prompts` point to package-local resource directories |
| `pi_clean_default_no_project_settings` | Inspect source checkout | `.pi/settings.json` is absent by default after factory reset; project-local Pi attachment is generated only by an intentional install command |
| `pi_install_guidance` | Inspect package README and SDD | Global and project-local install commands are documented, including that the package is not installed by default after a clean reset |
| `lazy_pi_wrapper_guidance` | Inspect package README, SDD, `.lazy-harness/bin/lazy`, and `.lazy-harness/scripts/pi-package.ts` | `lazy pi install/list/remove/smoke/doctor` is documented and dispatched; install/remove require explicit scope and support dry-run |
| `lazy_pi_wrapper_dry_run` | Run `pi-package.ts` dry-run fixtures | Local/global install, local remove, and one-run smoke dry-run produce the exact Pi command arrays without mutating settings |
| `lazy_pi_wrapper_doctor_no_smoke` | Run `pi-package.ts doctor --no-smoke --format=json` | Doctor is safe in environments without persistent Pi package settings and reports that smoke is skipped/non-mutating |
| `pi_extension_before_agent_start_bridge` | Inspect extension source | Source contains `before_agent_start`, calls `on-message-received.sh`, and injects `REMINDER. Harness-first search/read debt before response.` fallback |
| `pi_extension_tool_call_bridge` | Inspect extension source | Source contains `tool_call`, calls `on-tool-execute-before.sh`, and returns `{ block: true, reason }` only when hook output supplies a reason |
| `pi_extension_shell_alias_guard` | Fake Pi runtime calls `tool_call` with `cmd`, `terminal`, `bash`, and `batch` shell actions after `before_agent_start` | All action shell variants block until root-bound read/search evidence exists |
| `pi_extension_tool_result_evidence` | Inspect extension source | Source contains `tool_result` and records recent tool calls for evidence guard payloads |
| `pi_package_skills` | Inspect package skills | `lazy-init`, `lazy-doctor`, `lazy-sync`, `lazy-update`, and `lazy-test` expose `SKILL.md` wrappers |

## Automated coverage

Implemented by:

```text
.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract
```

This check is `FRAMEWORK_ONLY` because `packages/lazy-harness-pi` is source-repo package code, not currently a Category A downstream mirror artifact.

## Manual/current-host smoke

After implementation, run:

```bash
bun packages/lazy-harness-pi/extensions/lazy-harness/index.ts
.lazy-harness/bin/lazy pi install --local --dry-run
.lazy-harness/bin/lazy pi install --global --dry-run
.lazy-harness/bin/lazy pi remove --local --dry-run
.lazy-harness/bin/lazy pi smoke --dry-run
.lazy-harness/bin/lazy pi doctor --no-smoke
.lazy-harness/bin/lazy pi smoke
pi -e /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --help
pi install /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --no-approve
pi install -l /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --approve
pi list --approve
```

## Layer completeness

- SDD: `.lazy-harness/spec/platform/pi-agent-package.md`
- BDD: Pi behavior mirrors `.lazy-harness/behavior/llm-owned-record-retrieval.md` for reminder and mutation guard behavior.
- SSOT: `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md` is the placement decision for now.
- ADR: `.lazy-harness/decisions/0043-pi-native-package-in-source-repo.md`
- DDD: no domain/business term impact.

## Implementation map

- `packages/lazy-harness-pi/package.json` — fixture for package manifest resource paths.
- `.lazy-harness/scripts/pi-package.ts` — fixture for `lazy pi` wrapper command construction and safe dry-run behavior.
- `.lazy-harness/bin/lazy` — fixture for wrapper dispatch.
- `.pi/settings.json` — optional generated project-local package install path; absent in clean default.
- `~/.pi/agent/settings.json` — optional generated global package install path; not committed to the repository and absent after factory reset.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — fixture for hook bridge phrases/events.
- `packages/lazy-harness-pi/skills/*/SKILL.md` — fixture for skill availability.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — regression implementation.
