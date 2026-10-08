-- Esquema do Painel de Compras: um registro por lote, RLS em tudo.
-- Leitura: só usuários logados (authenticated). Escrita: só quem está em public.admins.
-- Não mexe nas tabelas consumo_* (outro uso do projeto).

drop table if exists public.compras, public.ordens, public.consumo,
  public.fornecedores, public.itens, public.produtos, public.categorias, public.unidades cascade;

create table if not exists public.admins (
  user_id uuid primary key references auth.users(id) on delete cascade
);
alter table public.admins enable row level security;

create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (select 1 from public.admins where user_id = (select auth.uid()));
$$;
revoke all on function public.is_admin() from public, anon;
grant execute on function public.is_admin() to authenticated;

create table if not exists public.lotes (
  id       bigint generated always as identity primary key,
  dataset  text not null check (dataset in ('itens','ordens','consumo')),
  origin   text not null check (origin in ('hist','mensal','consolidado')),
  tipo     text not null,
  filename text not null,
  added_at timestamptz not null default now(),
  rows     integer not null default 0,
  periodo  text,
  min_day  integer,
  max_day  integer,
  payload  jsonb not null
);
-- torna a migração idempotente (upsert por nome) sem proibir reenvios mensais com o mesmo nome
create unique index if not exists lotes_hist_uq on public.lotes (dataset, filename) where origin = 'hist';
alter table public.lotes enable row level security;

revoke all on public.lotes, public.admins from anon, public;
grant select on public.lotes to authenticated;
grant insert, update, delete on public.lotes to authenticated;
grant select on public.admins to authenticated;

create policy lotes_select on public.lotes for select to authenticated using (true);
create policy lotes_insert on public.lotes for insert to authenticated with check ((select public.is_admin()));
create policy lotes_update on public.lotes for update to authenticated
  using ((select public.is_admin())) with check ((select public.is_admin()));
create policy lotes_delete on public.lotes for delete to authenticated using ((select public.is_admin()));
create policy admins_self on public.admins for select to authenticated using (user_id = (select auth.uid()));
