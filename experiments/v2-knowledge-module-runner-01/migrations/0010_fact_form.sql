-- 0010: fact form stored (schema-delta '스키마 저장·활용 순서', 2026-09-30, step 2).
-- Local draft only; production application requires separate user approval.
-- A fact is Korean leaf sentences joined by English operators (fact_form.py). Record time parses the operator string
-- into form {kind, if?, even_if?, then[], except?, anchor?, because?}; digestion copies it to the fragment and writes
-- one row per leaf (role, text, subject, polarity) so contradiction, merge and dedup can compare leaves.
-- form is nullable: ledger entries and fragments made before this migration keep text only.
begin;

-- expression = {"leaf": text} | {"op": "AND"|"OR", "args": [expression, ...]}; checked recursively in SQL
create function knowledge.valid_form_expr(e jsonb, depth int default 0) returns boolean
language plpgsql immutable set search_path = '' as $$
declare a jsonb;
begin
  if depth > 8 or e is null or jsonb_typeof(e) is distinct from 'object' then return false; end if;
  if e ? 'leaf' then
    return coalesce(jsonb_typeof(e->'leaf') = 'string' and length(btrim(e->>'leaf')) > 0, false);
  end if;
  if coalesce(e->>'op', '') not in ('AND', 'OR') or jsonb_typeof(e->'args') is distinct from 'array'
     or jsonb_array_length(e->'args') < 2 then
    return false;
  end if;
  for a in select value from jsonb_array_elements(e->'args') loop
    if not knowledge.valid_form_expr(a, depth + 1) then return false; end if;
  end loop;
  return true;
end;
$$;

create function knowledge.valid_fact_form(f jsonb) returns boolean
language plpgsql immutable set search_path = '' as $$
declare t jsonb;
begin
  if f is null then return true; end if;
  -- review P1 (2026-10-01): a missing key is SQL NULL and must fail, not pass ('{}' was accepted)
  if jsonb_typeof(f) is distinct from 'object' or coalesce(f->>'kind', '') not in ('plain', 'if', 'before', 'after') then return false; end if;
  if jsonb_typeof(f->'then') is distinct from 'array' or jsonb_array_length(f->'then') < 1 then return false; end if;
  if (f->>'join') is not null and (f->>'join') not in ('AND', 'OR') then return false; end if;
  for t in select value from jsonb_array_elements(f->'then') loop
    if jsonb_typeof(t) is distinct from 'string' or length(btrim(t #>> '{}')) = 0 then return false; end if;
  end loop;
  if (f->>'kind') = 'if' and not knowledge.valid_form_expr(f->'if') then return false; end if;
  if (f->>'kind') <> 'if' and f ? 'if' then return false; end if;
  if f ? 'even_if' and ((f->>'kind') <> 'if' or not knowledge.valid_form_expr(f->'even_if')) then return false; end if;
  if f ? 'except' and not knowledge.valid_form_expr(f->'except') then return false; end if;
  if (f->>'kind') in ('before', 'after') and (jsonb_typeof(f->'anchor') is distinct from 'string' or coalesce(length(btrim(f->>'anchor')), 0) = 0) then
    return false;
  end if;
  if f ? 'because' and jsonb_typeof(f->'because') is distinct from 'string' then return false; end if;
  return true;
end;
$$;

create function knowledge.valid_judgement_forms(body jsonb) returns boolean
language sql immutable set search_path = '' as $$
  select not exists (
    select 1 from jsonb_array_elements(case when jsonb_typeof(body->'facts') = 'array' then body->'facts' else '[]'::jsonb end) as x(value)
    where x.value ? 'form' and not knowledge.valid_fact_form(x.value->'form'));
$$;

alter table knowledge.ledger_entry add constraint ledger_entry_fact_forms_valid
  check (knowledge.valid_judgement_forms(judgement_body));

alter table knowledge.fragment add column form jsonb check (knowledge.valid_fact_form(form));

create table knowledge.fragment_leaf (
  fragment_id uuid not null references knowledge.fragment(id),
  revision integer not null check (revision > 0),
  ord integer not null check (ord >= 0),
  role text not null check (role in ('if', 'even_if', 'then', 'except', 'anchor')),
  text text not null check (length(btrim(text)) > 0),
  subject_id uuid references knowledge.subject(subject_id),
  polarity text not null check (polarity in ('pos', 'neg')),
  primary key (fragment_id, revision, ord)
);
create index fragment_leaf_subject_idx on knowledge.fragment_leaf(subject_id, role);
alter table knowledge.fragment_leaf enable row level security;

commit;
