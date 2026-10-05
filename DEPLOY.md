# Publicação segura do Painel de Compras

`index.html` é gerado por `build.py`: os dados (fornecedores, ordens, consumo) ficam
**cifrados com AES-256-GCM** (chave derivada da senha via PBKDF2, 600 mil iterações).
Sem a senha, o código-fonte não revela nenhum dado.

## Regerar após alterar o painel
    PAINEL_SENHA='sua senha longa' python3 build.py painel_compras_10.html index.html
(sem PAINEL_SENHA, uma senha aleatória é gerada e impressa). Nunca versione o HTML original.

## Deploy (Vercel)
    npm i -g vercel
    vercel login
    vercel --prod        # na pasta do projeto; aceite os padrões (sem build, diretório ".")
O link final aparece no terminal. Envie o link e a senha por canais separados.
