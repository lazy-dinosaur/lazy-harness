See INSTALL.md for the agent install guide (v2 namespace, isolated from v1).

## 작업 도구

Development only: `pi -e /home/lazydino/dev/lazy-harness.v2/experiments/v2-knowledge-module-runner-01/pi-extension/knowledge.ts`. Do not install globally or alter v1. The extension exposes `knowledge_record` (proposed ledger judgement), `knowledge_complete` (explicit user confirmation signal), and read-only `knowledge_status`. Review and absorption remain with the resident poller. Set `default_host` in knowledge.json (or `LH_KNOWLEDGE_DEFAULT_HOST`) unless passing host_id explicitly. The CLI accepts one stdin JSON object via `python3 knowledge_cli.py record|complete|status` and returns one JSON line; `db_url` is required. `record` requires partition_key and facts; `complete` requires work_unit_id and a verbatim non-question user_quote. No paid judge is called by these tools.

## Configuration (single file)

All programs (poller, worktime/digest drivers, runner collect/call) read **`~/.config/lazy-harness-v2/knowledge.json`** (override path with `LH_KNOWLEDGE_CONFIG`). Create it with mode 600 — programs refuse to read it if group/others can read it.

```json
{
  "db_url": "postgresql://USER:PASSWORD@HOST:5432/postgres",
  "jev": {
    "api_key": "sk-or-...",
    "base_url": "https://openrouter.ai/api",
    "model": "~typesafe/jev-latest"
  },
  "embed_url": "http://127.0.0.1:8765"
}
```

```sh
mkdir -p ~/.config/lazy-harness-v2 && touch ~/.config/lazy-harness-v2/knowledge.json && chmod 600 ~/.config/lazy-harness-v2/knowledge.json
nvim ~/.config/lazy-harness-v2/knowledge.json
```

- Required: `db_url`, `jev.api_key`. Defaults: `jev.base_url` = OpenRouter, `jev.model` = `~typesafe/jev-latest` (OpenRouter latest alias; the `~` is required — `typesafe/jev-latest` returns 400), `embed_url` = local lhv2-embed, `embed.model_dir` = ~/.local/share/lazy-harness-v2/e5-small.
- Environment variables override the file for development: `LH_KNOWLEDGE_DB_URL`, `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `LH_JEV_MODEL`, `LH_EMBED_URL`.
- Missing values stop the program with the missing key names only; secrets are never printed.
- The actual Jev model and cost returned by OpenRouter are stored on each check receipt.
- systemd does not read shell (fish/bash) settings; the service relies on this file only. Install: copy `deploy/lhv2-{embed,digester}.service, deploy/lhv2-digester.timer` to `~/.config/systemd/user/`, `systemctl --user daemon-reload && systemctl --user enable --now lhv2-embed.service lhv2-digester.timer` (15 s interval, `Persistent=true` catches up after power-off/suspend).

DB poller (no LLM actor): `python3 poller.py --once --judge jev [--max-units 20 --window 50 --state PATH]`. Requires the Configuration file below (db_url, jev.api_key). The scheduler templates `deploy/lhv2-{embed,digester}.service, deploy/lhv2-digester.timer` are **not installed**; edit paths/config locally before use. The DB is the queue; the atomic JSON file only limits retries (five attempts by default), and deleting it resets backoff. `--window` bounds total ledger entries and embedding rows per tick; a unit larger than the remaining budget waits for a larger window. Missing embedding service skips optional backfill. No fixture judge is offered in the CLI; tests inject a fake callable. Offline test: `python3 -m pytest -q` (conftest disposable container only).

Worktime review: `worktime_driver.run_worktime(dsn, window, judge, utterance_judge=None)` builds packets for proposed entries, searches same-host excerpts (text fallback on local encoder outage), and passes injected answers to `store_pg.batch`. Failed judges leave entries proposed; worktime only reaches provisional, not absorption. CLI: `python3 worktime_driver.py --window N --judge fixture --fixture FILE --test-dsn`; explicit `--judge jev` uses the Configuration file (not used in offline tests). Question templates come from `templates.py` (single source: migration seeds).

Work-unit baseline (local 0004 draft): `store_pg.start_work_unit(dsn, unit_id, host, partition_key, code_ref=None)` captures the host history cursor before any ledger entry; `register` captures it for newly created units. `changed_since_baseline(dsn, unit_id)` lists current states changed after that cursor. Existing units keep their original/null baseline. Git code evidence uses `code_changed_since(repo_root, code_ref, path)` (None means unknown). Apply 0004 only to the conftest disposable container; production requires separate approval.

Completion-gated digestion: `store_pg.register_completion_sources(dsn, unit, ["merge", "confirm"])` then `signal_completion(dsn, unit, source, evidence=None)`; only the final AND signal completes the unit. `abandon(dsn, unit, reason)` expires pending ledger entries. `digest_driver.run_digestion(dsn, unit, judge, apply=True)` uses an injected `judge(packet) -> {"answers": {...}}` and rechecks current targets before acceptance. CLI: `python3 digest_driver.py --unit UUID --judge fixture --fixture FILE --test-dsn [--dry-run]` (fixture is a single `{ "answers": ... }` response). Explicit `--judge jev` uses the Configuration file and sends model-bearing requests; never used by offline tests. Tests: `python3 -m pytest -q` from this folder (conftest owns/removes the local container; no image pull).

Embedding service (offline, loopback only): model + venv live in knowledge.json embed.model_dir (default ~/.local/share/lazy-harness-v2/e5-small, pinned sha256 in embed.py). Run ~/.local/share/lazy-harness-v2/e5-small/venv/bin/python embed_server.py --host 127.0.0.1; LH_EMBED_PORT overrides 8765. Installed service: deploy/lhv2-embed.service (systemd user unit lhv2-embed, isolated from v1). Search supports --mode hybrid --min-similarity X.

Run offline tests: `python3 -m unittest discover -s experiments/v2-knowledge-module-runner-01 -p test_runner.py`.
Lint: `python3 experiments/v2-knowledge-module-runner-01/runner.py lint PACKET.json [--denylist FILE]`.
Decide: `python3 experiments/v2-knowledge-module-runner-01/runner.py decide PACKET.json RESPONSES.json [--operation add|update|deprecate]` (default add).
Dry-run: `python3 experiments/v2-knowledge-module-runner-01/runner.py call PACKET.json CASE-ID` (requires explicit packet questions and nonempty `model`; no implicit model).
`call --send` and `collect --judge jev` are network paths; do not use them for offline tests.

Fragment assembly: `fragment.render_prompt(record_id, source_path)` reads `fragmenter/prompt-v2.md`; `fragment.fragment_record(record_id, source_text, source_path, call_llm, max_retries=1)` accepts an injected callable returning raw text. Each attempt carries raw SHA-256, repair status and check reasons; failed final attempts remain `ok=False`. The original checker in `fragmenter/check_fragments.py` is imported as the single check/parse/repair authority. The actual LLM caller **must** use a fresh context, inherit no parent conversation, forbid writes, and run from a neutral cwd without harness rules. This isolation is the caller's responsibility, not enforced by the module; fork-inherited context collapsed fragmentation in Medivance pilot 02. Retain raw responses externally if needed: this module records their hashes, not raw text.

Collector: `python3 runner.py collect --backend pg --host HOST --queries-file QUERIES --judge oracle --oracle IDS.json` (oracle is the default). To use Jev explicitly: `python3 runner.py collect --backend pg --host HOST --queries-file QUERIES --judge jev [--topic-title TITLE] [--question relaxed|narrow] [--threshold 0.5]`; uses the Configuration file. Jev defaults to `~typesafe/jev-latest`, relaxed question "candidates 의 {i}번 조각은 topic 을 이해하거나 topic 의 기능을 작업할 때 알아야 할 내용인가?", criteria true "topic 을 다루는 데 필요한 내용이다" / false "topic 과 무관하다", threshold 0.5. `make_jev_judge` supports injected HTTP and optional redacted raw_dir, and exposes `judge.judgments` (score, relevant, candidate_id, query).