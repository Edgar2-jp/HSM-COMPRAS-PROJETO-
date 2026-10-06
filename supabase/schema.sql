-- Esquema do Painel de Compras (já aplicado no projeto hsm-compras).
create table if not exists public.fornecedores (id int primary key, nome text not null);
create table if not exists public.itens (id int primary key, nome text not null);
create table if not exists public.produtos (id int primary key, nome text not null);
create table if not exists public.categorias (id int primary key, nome text not null);
create table if not exists public.unidades (id int primary key, nome text not null);
create table if not exists public.compras (
  id bigserial primary key,
  cod_item bigint, nota bigint, data date not null,
  fornecedor_id int references public.fornecedores(id),
  item_id int references public.itens(id),
  produto_id int references public.produtos(id),
  categoria_id int references public.categorias(id),
  unidade_id int references public.unidades(id),
  quantidade int, valor numeric(14,2), valor_item numeric(14,4), valor_negociado numeric(14,2),
  sistema text check (sistema in ('Compras','Emenda'))
);
create index if not exists compras_data_idx on public.compras (data);
create index if not exists compras_fornecedor_idx on public.compras (fornecedor_id);
create index if not exists compras_item_idx on public.compras (item_id);
create table if not exists public.ordens (
  id bigserial primary key, ordem bigint, data date not null, fornecedor text, valor numeric(14,2), situacao text
);
create table if not exists public.consumo (
  id bigserial primary key, item text, marcas jsonb, tipo text, quantidade numeric,
  periodo_min text, periodo_max text, extra jsonb, mensal jsonb
);
alter table public.fornecedores enable row level security;
alter table public.itens enable row level security;
alter table public.produtos enable row level security;
alter table public.categorias enable row level security;
alter table public.unidades enable row level security;
alter table public.compras enable row level security;
alter table public.ordens enable row level security;
alter table public.consumo enable row level security;
