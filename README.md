# Painel de Compras — Hospital São Marcos

Arquivo único (`index.html`, JS puro, sem build) publicado no GitHub Pages. Os dados ficam no **Supabase**
(tabela `lotes`); todos que entram veem o mesmo histórico. Login obrigatório; só admins enviam/removem lotes.
A segurança é feita pela **RLS do banco** — a tela só esconde botões por conveniência.

## Subir um lote novo (admin)
Entre no painel → aba **Dados** → arraste o arquivo do mês (bruto Compras/Emenda, base consolidada ou consumo `.txt`).
Para remover: **Remover** → **Confirmar remoção?** (2 cliques). Outros usuários veem a mudança ao reabrir/voltar à aba.

## Liberar / bloquear um e-mail
1. Supabase → Authentication → Users → **Add user / Invite** (marque *Auto Confirm*). A pessoa usa
   "Primeiro acesso / esqueci a senha" na tela de login para definir a senha.
2. No SQL Editor: `insert into public.leitores values ('pessoa@exemplo.com');`
   (admin: também `insert into public.admins values ('pessoa@exemplo.com');`).
3. Bloquear: `delete from public.leitores where email = '...';` (e de `admins`, se for o caso).
E-mails sempre em minúsculas. Recomendado: Authentication → Sign In → **desligar "Allow new users to sign up"**.

## Migração inicial dos dados (uma vez, no seu computador)
O HTML antigo com os dados **nunca** vai para o Git (está no `.gitignore`).
```
python3 supabase/migrar.py painel_compras.html --dry-run       # confere totais
SUPABASE_ADMIN_EMAIL=voce@exemplo.com python3 supabase/migrar.py painel_compras.html
```
Usa o login do admin com a chave pública — não precisa de `service_role` (que **nunca** deve entrar no repo).

## Publicação
Settings → Pages → *Deploy from a branch* → `main` / `(root)`. O workflow `keepalive` faz um ping a cada 3 dias
para o Supabase grátis não pausar por inatividade. Se pausar: painel do Supabase → **Restore project**.
