# lazy-harness v2 knowledge module — install guide (for agents)

Audience: an AI agent installing this module on a user's machine. Follow the steps in order.
Each step has a **check**; do not continue until it passes. Never print secret values.
v2 is **fully isolated from v1** during dogfooding: use only the `lazy-harness-v2` / `lhv2-*` names below
and do not touch v1 paths (`~/.config/lazy-harness/`, `~/.local/share/lazy-harness/`, `~/.local/state/lazy-harness/`, `lh-r8-*` units).

## 0. What gets installed

| Item | Location |
|---|---|
| Config (secrets) | `~/.config/lazy-harness-v2/knowledge.json` (mode 600) |
| Poller state (retry hints only) | `~/.local/state/lazy-harness-v2/` |
| E5-small model + venv | `~/.local/share/lazy-harness-v2/e5-small/` |
| Embedding service | systemd user unit `lhv2-embed.service` (127.0.0.1:8765) |
| Digestion poller | `lhv2-digester.service` + `lhv2-digester.timer` (every 15 s, catches up after power-off/suspend) |
| Daily backup | `lhv2-backup.service` + `lhv2-backup.timer` (knowledge schema, newest 14 in `~/.local/share/lazy-harness-v2/backups`) |
| Brief writer | headless `pi -p` sub-agent (model `LH_BRIEF_MODEL`, default `openai-codex/gpt-6-luna:medium`) — needs the `pi` CLI with that provider logged in |

Code lives in this folder. Run every command below from it after setting `MODULE_DIR="$(pwd)"` (absolute path of this folder).

## 1. Prerequisites

- Linux with systemd user session; enable lingering so user units run without a login: `loginctl enable-linger "$USER"`.
- `/usr/bin/python3` (3.12+) with `psycopg2` or `psycopg` importable (Arch: `pacman -S python-psycopg2`; Debian: `apt install python3-psycopg2`).
- `uv` (for the model venv), `curl`, `sha256sum`.
- A PostgreSQL database with the pgvector extension (Supabase works). Ask the user for the connection URL.
- An OpenRouter API key with access to Jev. Ask the user for it.

**Check:** `/usr/bin/python3 -c "import psycopg2" || /usr/bin/python3 -c "import psycopg"`; `uv --version`; `loginctl show-user "$USER" -p Linger` shows `Linger=yes`.

## 2. Model and venv (download + hash verify)

Pinned model: `intfloat/multilingual-e5-small` revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`.

```sh
D=~/.local/share/lazy-harness-v2/e5-small
BASE=https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx
mkdir -p "$D"
curl -fL -o "$D/model.onnx" "$BASE/model.onnx"          # ~470 MB
curl -fL -o "$D/tokenizer.json" "$BASE/tokenizer.json"
cd "$D" && sha256sum -c - <<'EOF'
ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665  model.onnx
0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39  tokenizer.json
EOF
uv venv --python 3.13 "$D/venv"
uv pip install --python "$D/venv/bin/python" onnxruntime==1.23.2 tokenizers==0.22.2 numpy==2.3.5
```

**Check:** `sha256sum -c` prints `OK` for both files (if not, delete them and stop — do not use unverified files). `"$D/venv/bin/python" -c "import onnxruntime, tokenizers, numpy"` succeeds. The pinned hashes are also enforced by `embed.py` at runtime.

## 3. Config file

Create the file with mode 600 **before** writing secrets into it:

```sh
mkdir -p ~/.config/lazy-harness-v2 && chmod 700 ~/.config/lazy-harness-v2
install -m 600 /dev/null ~/.config/lazy-harness-v2/knowledge.json
```

Content (the user or the agent fills `db_url` and `jev.api_key`; never echo them back):

```json
{
  "db_url": "postgresql://USER:PASSWORD@HOST:5432/postgres",
  "jev": {
    "api_key": "sk-or-...",
    "base_url": "https://openrouter.ai/api",
    "model": "~typesafe/jev-latest"
  },
  "embed_url": "http://127.0.0.1:8765",
  "embed": { "model_dir": "/home/USER/.local/share/lazy-harness-v2/e5-small" }
}
```

Notes: `~typesafe/jev-latest` needs the leading `~` (without it OpenRouter returns 400). Environment variables
(`LH_KNOWLEDGE_DB_URL`, `TYPESAFE_API_KEY`, `TYPESAFE_BASE_URL`, `LH_JEV_MODEL`, `LH_EMBED_URL`, `LH_EMBED_MODEL_DIR`) override the file for development only; systemd units use the file.

**Check (prints no secrets):**
```sh
cd "$MODULE_DIR" && env -u TYPESAFE_API_KEY -u LH_KNOWLEDGE_DB_URL /usr/bin/python3 -c "import config; c=config.require('db_url','jev_api_key','jev_base_url','jev_model'); print('config ok', c['jev_model'])"
```

## 4. Database schema

Apply the migrations in order to the database from step 3 (skip any already applied; the fingerprints below identify the applied forms):

| Order | File | sha256 of applied form |
|---|---|---|
| 1 | `migrations/0001_knowledge_init.sql` | `0bd2a8a92e1c0989beca4cc3f0c598f55cc151ed100d108bf095ceac1bbc82bc` |
| 2 | `migrations/0002_search_and_cost.sql` | `01ffbcaa02332d0ace42f8b5770831c1e7d54048ae4f8ebaa5e4e3ea4c6dd153` |
| 3 | `migrations/0003_apply_form.sql` (0003 without the transaction wrapper) | `ae7b95c299b0d73ea94200b091ae345d9c52f58535ef01eb9f049aff59a4fc16` |
| 4 | `migrations/0004_apply_form.sql` (work-unit baseline) | `7fc9e71a4a5733b663186bd0cea67a385ae7ce747184d1c6e19427614d0b4baf` |
| 5 | `migrations/0005_apply_form.sql` (domain list `knowledge.domain_type`, RLS on, backfilled from existing fragments) | `59ec969903646d8b1e272477d83be221f880fc4544e37d6009d45750cb727773` |
| 6 | `migrations/0006_rules.sql` (rule module schema `rules`: rule, rule_history, judgement_receipt, injection; RLS on; apply with `psql -1`) | `86dff2547e1138731ec5c9829bffb812ceeae964d77c60db4c156abf0ca4ab10` |

Apply with `psql "$DB_URL" -v ON_ERROR_STOP=1 -f FILE` or the Supabase MCP `apply_migration` tool. Register the host once:
`insert into knowledge.host(host_id,name,repo_locator,cross_search_allowed) values ('<host-id>','<name>','<repo path>',false) on conflict do nothing;`

**Check:** `select to_regclass('knowledge.fragment'), to_regclass('knowledge.fragment_embedding');` returns both names; RLS is on for every `knowledge.*` table (Supabase advisor shows only INFO `rls_enabled_no_policy`).

## 5. Services

The templates contain the author's absolute path; rewrite it to `$MODULE_DIR`, then install:

```sh
mkdir -p ~/.config/systemd/user
for f in lhv2-embed.service lhv2-digester.service lhv2-digester.timer lhv2-backup.service lhv2-backup.timer; do
  sed "s#/home/lazydino/dev/lazy-harness.v2/experiments/v2-knowledge-module-runner-01#$MODULE_DIR#g" "$MODULE_DIR/deploy/$f" > ~/.config/systemd/user/$f
done
systemctl --user daemon-reload
systemctl --user enable --now lhv2-embed.service
systemctl --user enable --now lhv2-digester.timer
systemctl --user enable --now lhv2-backup.timer
```

Backup (G3): `lhv2-backup.timer` runs `backup.py backup` daily (knowledge schema, `pg_dump -Fc`, newest 14 kept in `~/.local/share/lazy-harness-v2/backups`, mode 600, sidecar JSON with row counts and sha256). Check a backup with `python3 backup.py verify` (restores into a disposable local Supabase PG container, compares row counts and one search, removes the container). Restore after loss: `python3 backup.py restore FILE NEW_DB_URL` — it refuses a target that already has a `knowledge` schema.

**Check:**
- `curl -s http://127.0.0.1:8765/health` returns `"dim": 384` and the pinned model id.
- `systemctl --user list-timers lhv2-digester.timer` shows a next run within 15 s.
- `journalctl --user -u lhv2-digester.service -n 5 -o cat` shows JSON lines with `"failed": 0` and `Result=success` in `systemctl --user show lhv2-digester.service -p Result`.

## 6. Final verification

```sh
cd "$MODULE_DIR" && env -u TYPESAFE_API_KEY -u LH_KNOWLEDGE_DB_URL /usr/bin/python3 poller.py --once --judge jev
```
Expect one JSON line; with an empty ledger all counts are 0 and no Jev call is made. Optional offline test suite (needs local Docker and the image `public.ecr.aws/supabase/postgres:17.6.1.134` already present; never pulls): `python3 -m pytest -q`.

## 작업 도구 (개발 실행, 설치 아님)

`pi -e /home/lazydino/dev/lazy-harness.v2/experiments/v2-knowledge-module-runner-01/pi-extension/knowledge.ts`

전역 설치나 v1 설정 변경 없이 실행한다. knowledge.json 에 `default_host` 를 등록하거나 호출 시 `host_id` 를 전달한다. 도구(모두 이 확장이 등록):

| 도구 | 용도 |
|---|---|
| `knowledge_brief` | 작업 전·변경 전. 즉시 brief_id 를 돌려주고, 넓게 모은 지식을 Luna 하위 에이전트(`pi -p`, read 도구만)가 네 칸(이전 결정·이유 / 현재 구현 / 유지할 것 / 충돌)으로 정리해 끝나면 'knowledge-brief' 메시지로 전달. 그동안 작업 AI 는 코드를 읽는다. 기본 8,000자 상한(`LH_BRIEF_LIMIT=0` 으로 끔) |
| `knowledge_search` / `knowledge_more` | 작업 중 작은 질문. 판정된 조각만 네 칸으로, `change` 를 주면 충돌 후보 표시, '더 있음' 색인의 영역·묶음을 more 로 받음 |
| `knowledge_record` / `knowledge_complete` / `knowledge_status` | 원장 등록(add/update/deprecate — deprecate 는 사용자 확정 원문 필수), 사용자 확정 발언으로 완료 신호, 세션 상태. 흡수는 상주 poller 만 |
| `knowledge_audit` | 완료 전 대화에서 기록 안 된 지식 후보 검수(Jev) |
| `knowledge_fix_plan` / `knowledge_fix_submit` | 확정된 변경으로 옛 내용이 된 조각 목록 → 항목별 update/deprecate/keep |

관리 명령(사람이 실행): `knowledge_cli.py domain` (list/show/merge/retire), `cleanup.py` (비슷한 조각 합치기 — 포함·같음만, 기본 미리보기, `--apply`, `--revert RUN_ID`), `backup.py` (backup/restore/verify).

## Behaviour the agent must know

- The poller is the only resident component. Reading (search) is not a service: it runs per request.
- The ledger is the queue. Nothing is absorbed into canonical knowledge until the work unit's completion signal(s) arrive; a power-off or suspend loses nothing and the next tick resumes the oldest pending work first.
- Repeated failures back off and stop as `stuck` after 5 attempts (no runaway Jev spend). Deleting the state file only resets that backoff.

## Uninstall (v2 only)

```sh
systemctl --user disable --now lhv2-digester.timer lhv2-embed.service
rm ~/.config/systemd/user/lhv2-{embed,digester}.service ~/.config/systemd/user/lhv2-digester.timer
systemctl --user daemon-reload
rm -r ~/.local/share/lazy-harness-v2 ~/.local/state/lazy-harness-v2   # keep ~/.config/lazy-harness-v2 unless the user asks
```
