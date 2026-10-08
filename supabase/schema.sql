-- Esquema do Painel de Compras (já aplicado no projeto hsm-compras). Referência / recriação.
create table public.leitores (email text primary key check (email = lower(email)));
create table public.admins   (email text primary key check (email = lower(email)));
alter table public.leitores enable row level security;
alter table public.admins   enable row level security;

create table public.lotes (
  id        bigint generated always as identity primary key,
  dataset   text not null check (dataset in ('itens','ordens','consumo')),
  origin    text not null check (origin in ('hist','mensal','consolidado')),
  tipo      text,
  filename  text not null,
  added_at  timestamptz not null default now(),
  rows      int  not null,
  min_day   int,
  max_day   int,
  periodo   text,
  payload   jsonb not null            -- formato colunar compacto (ver packRecords no index.html)
);
alter table public.lotes enable row level security;
create unique index lotes_hist_uniq on public.lotes (dataset, filename) where origin = 'hist';

create policy leitores_self on public.leitores for select to authenticated using (email = lower(auth.jwt() ->> 'email'));
create policy admins_self   on public.admins   for select to authenticated using (email = lower(auth.jwt() ->> 'email'));
create policy lotes_select on public.lotes for select to authenticated
  using (exists (select 1 from public.leitores l where l.email = lower((select auth.jwt() ->> 'email'))));
create policy lotes_insert on public.lotes for insert to authenticated
  with check (exists (select 1 from public.admins a where a.email = lower((select auth.jwt() ->> 'email'))));
create policy lotes_update on public.lotes for update to authenticated
  using (exists (select 1 from public.admins a where a.email = lower((select auth.jwt() ->> 'email'))))
  with check (exists (select 1 from public.admins a where a.email = lower((select auth.jwt() ->> 'email'))));
create policy lotes_delete on public.lotes for delete to authenticated
  using (exists (select 1 from public.admins a where a.email = lower((select auth.jwt() ->> 'email'))));
revoke all on public.lotes, public.leitores, public.admins from anon;

create function public.ping() returns int language sql stable security invoker set search_path = '' as $$ select 1 $$;
grant execute on function public.ping() to anon, authenticated;

-- primeiro admin (troque pelo seu e-mail):
-- insert into public.leitores values ('voce@exemplo.com'); insert into public.admins values ('voce@exemplo.com');
