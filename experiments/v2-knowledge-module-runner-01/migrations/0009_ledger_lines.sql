-- 0009: ledger protocol in the schema (schema-delta '원장 규약·스키마 0009', 2026-09-29).
-- One ledger line = one change or observation of one target key ('대상/속성'). judgement_body stays for compatibility;
-- digestion and the ledger organizer compare lines by key, mechanically.
begin;

create table knowledge.fact_key (
  host_id text not null references knowledge.host(host_id),
  key text not null check (key ~ '^[^/[:space:]]+/[^/[:space:]]+$'),
  description text not null default '',
  status text not null default 'active' check (status in ('active', 'merged')),
  merged_into text,
  created_at timestamptz not null default now(),
  primary key (host_id, key),
  check ((status = 'merged') = (merged_into is not null))
);
alter table knowledge.fact_key enable row level security;
revoke all on knowledge.fact_key from anon, authenticated, public;

create table knowledge.ledger_line (
  line_id bigint generated always as identity primary key,
  entry_id uuid not null references knowledge.ledger_entry(entry_id),
  fact_index integer not null check (fact_index >= 0),
  line_no integer not null check (line_no >= 0),
  host_id text not null,
  key text not null,
  target_fragment_id uuid references knowledge.fragment(id),
  old_value text not null default '',
  new_value text not null check (btrim(new_value) <> ''),
  kind text not null check (kind in ('change', 'observation')),
  source text not null check (source in ('user', 'code', 'doc', 'worker')),
  temporary boolean not null default false,
  statement text not null check (btrim(statement) <> ''),
  created_at timestamptz not null default now(),
  unique (entry_id, fact_index, line_no),
  foreign key (host_id, key) references knowledge.fact_key(host_id, key)
);
create index ledger_line_key on knowledge.ledger_line(host_id, key, created_at);
create trigger ledger_line_append_only before update or delete on knowledge.ledger_line
for each row execute function knowledge.reject_history_mutation();
alter table knowledge.ledger_line enable row level security;
revoke all on knowledge.ledger_line from anon, authenticated, public;

commit;
