# TDD — Experimental OMP thin adapter and shared-core isolation

## Rule digest

- Status: active
- Layer: TDD
- Scope: framework-global
- Aliases:
  - OMP native Reader
  - runtime instance isolation
- Surface terms:
  - OmpReaderTransport
  - explicitOmpOutputMode
  - onOmpNativeSteer
- Applies when:
  - loading or changing the OMP entrypoint, Reader, output or consumed-steer bridge
- Must:
  - keep Pi Fabric Reader/policy behavior and one shared guard/ledger/join authority
  - bind native lifecycle identity plus actual visible successful untruncated packet and terminal child ledger
  - conservatively charge finite native read ranges and suppress unverifiable/excess coverage
  - preserve Experimental status and distinguish synthetic/source checks from native runtime certification
- Must not:
  - assert async/artifact/full-runtime parity or use real credentials/providers in default fixtures

## Approved implementation and correction reasons

The user approved staged OMP compatibility, project-local create-only Reader activation and same-root session isolation, not runtime upgrades or global configuration. Native read ignored legacy limit fields; the user selected actual-range enforcement, not disabling the Reader. Shared mutable state must belong to each factory instance: same-root Parent and child cannot advance each other's epoch or share Reader role/capture evidence.

OMP manifest selects `omp/index.ts`, Pi keeps `./extensions` and its Fabric transport. Known native mode wins; otherwise explicit CLI print/JSON/RPC capability is parsed without reading prompt intent. Unknown/embedded modes stay unknown. Headless advisories use stderr/structural entries, never replace primary stdout or trigger another model call.

One native blocking task uses an exact managed project definition/model and low thinking. Legacy assignment and newer task/batch/yield forms are decoded strictly; conflicting selectors/overrides fail. Lifecycle binds launch to run/session but is not content. Only visible successful untruncated yielded packet enters shared parsing; transcript prose/details.output cannot substitute. OMP title metadata cannot substitute for session identity. Finite raw selectors conservatively include possible one-leading/three-trailing native context lines, and returned line coverage must fit. No alternate join authority.

Consumed `message_start` steering metadata invalidates old evidence once, with one-use session-bound prepared-turn handling for native runtimes that already advanced before delivery. Enqueue acknowledgement is not cancellation of a running tool. Session switches clear session state and advance epochs; same-session ordinary follow-up can reuse unchanged fingerprints. No user-text classifier decides scope.

## Implementation map and protection

- `packages/lazy-harness-pi/omp/index.ts#lazyHarnessOmp`: thin runtime composition; `output-mode.ts#explicitOmpOutputMode`, `steering.ts#onOmpNativeSteer`, `session-header.ts#ompSessionHeader` own native mechanics.
- `packages/lazy-harness-pi/omp/reader-definition.ts#ompReaderDefinition/activateOmpReader` and `scripts/activate-omp-reader.ts`: exact shared-body projection, explicit preview/apply, idempotence, differing-content/symlink refusal.
- `packages/lazy-harness-pi/omp/reader-transport.ts#OmpReaderTransport`: prepare/admit/lifecycle/visible receive/range/model validation and disposal.
- `packages/lazy-harness-pi/extensions/lazy-harness/index.ts#lazyHarnessPi`: per-instance state, native callbacks, shared ledger/join and prompt-less Reader fail-closed guard. Pi SessionManager is dynamically imported only by the Pi switch path so OMP startup does not require Pi SDK runtime resolution.
- Unit/default suites: `omp-reader.test.ts`, `omp-steering.test.ts`, `omp-output-mode.test.ts`, `runtime-instance-isolation.test.ts`, `omp-loader.test.ts`, `omp-native-stream.test.ts`, `omp-gpt6-sol-registration.test.ts`. Loader copies only source plus schema dependency to a credential-free fake runtime with no Pi SDK. Metadata registration preserves fake OAuth functions without invoking them; no model request.
- Opt-in native suites: `omp-native-lifecycle.test.ts`, `omp-native-reader.test.ts`, `omp-native-steer.test.ts`; scripted `tests/fixtures/omp-native-*.ts` use disposable hosts and synthetic providers. `LAZY_OMP_NATIVE_TEST=1` requires an explicitly selected installed OMP; default skipped cases are not passes. TUI setup is a manual isolated helper, not automatic certification.
- `.lazy-harness/scripts/pi-package.ts#ensurePackageLayout`, `self-test.py#check_pi_package_layout_and_contract`, package manifest/tsconfig: entrypoint and registration checks.
- `.lazy-harness/spec/platform/pi-agent-package.md`: interface/remaining-gap contract. Fresh results: `.lazy-harness/planning/repository-publication-review.md`.

## Remaining compatibility boundaries

Pi development dependencies remain pinned to 0.85.1. Managed Pi 1.3 is not a source compatibility pass: its before-agent-start user/custom union and integration-fixture ABI differ. The bounded prompt-less guard does not implement SDK/fixture migration. Native OMP fork/resume/root transitions, broader ask/RPC differences and async/artifact parity need independent scenarios. Do not promote Experimental or claim latest-SDK/full-native compatibility from build/default fixtures.

## Layer completeness

- SDD: independent OMP entrypoint, output/native task/activation/consumed-steer interfaces in `.lazy-harness/spec/platform/pi-agent-package.md`.
- BDD: no independent product flow; existing root-bound grounding/join behavior is preserved through a native transport.
- SSOT: package manifest selects the OMP adapter; no global configuration/installation, Reader model default or ownership promotion.
- DDD: no independent delta; no domain/business rule change.
