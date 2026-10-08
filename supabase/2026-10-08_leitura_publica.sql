-- Remove a exigência de login para VER os dados (decisão do dono do painel).
-- Escrita/remoção de lotes continua só para admins (políticas lotes_insert/update/delete inalteradas).
-- Rodar no SQL Editor do projeto hsm-compras-painel (ioephnjmzwlypnvbtlpl) — NUNCA no hsm-compras.
drop policy lotes_select on public.lotes;
create policy lotes_select on public.lotes for select to anon, authenticated using (true);
grant select on public.lotes to anon;
-- Para voltar a exigir login:
--   drop policy lotes_select on public.lotes;
--   create policy lotes_select on public.lotes for select to authenticated using (exists (select 1 from public.leitores l where l.email = lower((select auth.jwt() ->> 'email'))));
--   revoke select on public.lotes from anon;
