# Current Fabric offline process test runtime

Run from the repository root:

```sh
bun install --frozen-lockfile
bun run test:fabric:setup
bun run test:run
# Just the actual current process matrix:
bun run test:fabric
```

The isolated dependency graph pins Pi1.5.2 and Fabric0.136.0 in its own lockfile. It does not upgrade the production SDK0.85.1 or install/register/rebind anything globally. Setup uses frozen installs and disables lifecycle scripts. Node24+ is required for the current Fabric process lane; use `LAZY_TEST_NODE` for an explicit executable if your default Node is older. Root Node-only SDK fixtures are separately run by supported Node flags rather than by Bun's node:test compatibility layer.

Aggregate target selection accepts concrete files/directories (including mixed Node/Bun lists). `-t PATTERN` / `--test-name-pattern=PATTERN` is translated for both engines; `bun run test:run <Node-file> <Bun-file> -t PATTERN` never sends the SDK file to Bun. Relative/absolute/backslash target forms normalize to the same root-relative lane. Bun-only `--timeout` is accepted only when no Node lane is selected. Other aggregate flags fail clearly; use direct engine commands for unsupported options rather than guessing equivalent semantics.

The process fixture attaches an owned-child observer immediately after spawn. Successful closed children receive no signal. A live Parent is terminated through its ChildProcess handle, with bounded close/TERM/KILL settlement; stale numeric process groups are never signalled. An unsettled pipe is an explicit failure and retains synthetic evidence. This is not a proof that arbitrary detached descendants are terminated; Fabric retains its own worker ownership/lifecycle.

The process lane creates private HOME/agent/auth/settings, registers a deterministic zero-cost provider, denies fetch/TCP in Parent and worker, and uses only real runtime proxy events/ledger files. No captured-handler or injected-result success is counted as process coverage. Private `defaultProjectTrust` is explicit: trusted cases load the actual project child guard; the untrusted negative verifies no successful join. No global trust setting changes. All successful synthetic sandboxes and their own Reader ledgers are removed; failing fixture logs are preserved.

Coverage is JSON/text × wait-first/source-first × capture/placement plus untrusted-child refusal. Wait-first is a scheduling contrast, not a new synchronous Reader default. Source-first verifies Parent source work precedes delayed Reader completion. The shared provider handles the pinned worker SDK1.5.0's legacy transcript context and Parent SDK1.5.2 system messages; provider errors terminate rather than hang.

`LAZY_TEST_PI_ROOT`/`LAZY_TEST_FABRIC_ROOT` may explicitly bind read-only roots of exactly the pinned versions for diagnostics. They are not old native A/B inputs. The untouched legacy matrix remains explicit via `bun run test:reader:legacy`, requiring separately approved historical native source inputs. It is not executed or claimed passed by current tests. Actual authenticated/model-selected retrieval, production rollout and installed-session reload remain separate.
