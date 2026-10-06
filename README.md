# HSM-COMPRAS-PROJETO-

Painel de análise de compras (arquivo único HTML), publicado via GitHub Pages.

## Segurança
- Os dados embutidos (fornecedores, ordens, consumo) ficam **cifrados** (AES-256-GCM, chave derivada da senha com PBKDF2-SHA256, 600 mil iterações) e só são decifrados no navegador após a senha correta.
- Este repositório é público: o arquivo cifrado pode ser baixado por qualquer pessoa, então a segurança depende de uma **senha longa e aleatória**. Nunca versione o HTML original sem criptografia (`.gitignore` já bloqueia).

## Estrutura
- `index.html`: painel protegido (gerado)
- `build.py`: gera o `index.html` cifrado a partir do HTML original
- `DEPLOY.md`: instruções de regeneração e deploy
- `vercel.json`: cabeçalhos de segurança (apenas se usar Vercel)

## Regenerar
```
PAINEL_SENHA='sua senha longa' python3 build.py painel_compras_10.html index.html
```
