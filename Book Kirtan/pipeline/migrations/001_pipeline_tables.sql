-- Stage 1 queue: artist names waiting to be researched
create table if not exists artist_pipeline (
  id          uuid primary key default gen_random_uuid(),
  name        text not null unique,
  source_url  text,
  status      text not null default 'pending'
                check (status in ('pending', 'researching', 'done', 'skipped')),
  notes       text,
  added_at    timestamptz default now(),
  updated_at  timestamptz default now()
);

-- Stage 2 output: raw research dump per artist
create table if not exists artist_research_dump (
  id            uuid primary key default gen_random_uuid(),
  pipeline_id   uuid references artist_pipeline(id) on delete cascade,
  artist_name   text not null,
  exa_results   jsonb,        -- raw Exa API response
  raw_text      text,         -- all Exa page content concatenated
  extracted     jsonb,        -- Claude-structured JSON matching artist schema
  model_used    text,
  researched_at timestamptz default now()
);

-- Auto-update updated_at on artist_pipeline
create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger artist_pipeline_updated_at
  before update on artist_pipeline
  for each row execute procedure set_updated_at();
