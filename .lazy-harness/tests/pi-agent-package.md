# Pi Agent Package Regression

Status: active
Layer: TDD

## Regression target

The in-repo Pi package must remain installable and must bridge Pi extension events to canonical lazy-harness lifecycle hooks without inventing a second policy engine.

## Protected fixtures

| Case | Trigger | Expected |
|---|---|---|
| `pi_package_manifest_resources` | Parse `packages/lazy-harness-pi/package.json` | Manifest name is `@lazy-dinosaur/lazy-harness-pi`; keyword includes `pi-package`; `pi.extensions`, `pi.skills`, and `pi.prompts` point to package-local resource directories |
| `pi_project_local_install_settings` | Parse `.pi/settings.json` | `packages` contains `../packages/lazy-harness-pi`, proving the source repo has the package installed project-locally |
| `pi_extension_before_agent_start_bridge` | Inspect extension source | Source contains `before_agent_start`, calls `on-message-received.sh`, and injects `REMINDER. Harness-first search/read debt before response.` fallback |
| `pi_extension_tool_call_bridge` | Inspect extension source | Source contains `tool_call`, calls `on-tool-execute-before.sh`, and returns `{ block: true, reason }` only when hook output supplies a reason |
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
pi -e /home/lazydino/dev/lazy-harness/packages/lazy-harness-pi --help
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
- `.pi/settings.json` — fixture for project-local package install path.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts` — fixture for hook bridge phrases/events.
- `packages/lazy-harness-pi/skills/*/SKILL.md` — fixture for skill availability.
- `.lazy-harness/scripts/self-test.py#check_pi_package_layout_and_contract` — regression implementation.
