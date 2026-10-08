# Painel de Compras

Painel em um único `index.html` (JS puro). Dados no **Supabase** (tabela `lotes`), publicado no **GitHub Pages**.
Acesso só com login (e-mails liberados). Só o admin envia/remove lotes. A segurança é a RLS do banco, não a tela.

## Subir um lote novo (admin)
1. Abra o link, entre com o e-mail de admin, vá na aba **Dados**.
2. Arraste o arquivo do mês (Compras/Emenda `.xls/.xlsx`, ou consumo `.txt`). O lote aparece em **Lotes carregados** e todos veem ao recarregar.
3. Para desfazer: **Remover** no lote (2 cliques).

## Liberar um e-mail
Supabase → *Authentication → Users → Add user* (e-mail + senha, marque "Auto Confirm"). O cadastro público fica desligado
(*Authentication → Sign In / Providers → Allow new users to sign up = off*).
Para tornar admin, no *SQL Editor*:
```sql
insert into public.admins (user_id) select id from auth.users where email = 'fulano@exemplo.com';
```
Para revogar: apague o usuário em *Users*.

## Carga inicial / reparo (no seu computador)
`DATABASE_URL=... python3 supabase/migrar.py painel_compras_26.html` (idempotente; use `--dry-run` para testar).
O HTML com dados e a senha do banco **nunca** vão ao Git (`.gitignore`).

## Segurança
- Só a chave pública (publishable/anon) está no front. **Nunca** commite `service_role` nem a senha do banco.
- Nenhum dado de compras no repositório.

## Plano grátis do Supabase
Projeto sem atividade por 7 dias é **pausado**. `.github/workflows/keepalive.yml` faz uma chamada a cada 2 dias.
Se pausar mesmo assim, o painel mostra um aviso; restaure em *Supabase → Restore project*.
