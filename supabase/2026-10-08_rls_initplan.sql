-- PENDENTE (não aplicada no banco): evita reavaliar auth.jwt() a cada linha nas políticas *_self.
-- Rode no SQL Editor do projeto hsm-compras-painel (ioephnjmzwlypnvbtlpl) — NUNCA no hsm-compras.
drop policy leitores_self on public.leitores;
drop policy admins_self   on public.admins;
create policy leitores_self on public.leitores for select to authenticated using (email = lower((select auth.jwt() ->> 'email')));
create policy admins_self   on public.admins   for select to authenticated using (email = lower((select auth.jwt() ->> 'email')));
