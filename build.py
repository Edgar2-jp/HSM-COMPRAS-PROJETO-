#!/usr/bin/env python3
"""Gera index.html protegido: cifra os dados embutidos (AES-256-GCM, PBKDF2-SHA256)
e injeta uma tela de senha. Uso: PAINEL_SENHA='...' python3 build.py origem.html [saida.html]
Sem PAINEL_SENHA, gera uma senha aleatória forte e a imprime uma única vez."""
import base64, json, os, re, secrets, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER = 600_000
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else "index.html"
html = open(src, encoding="utf-8").read()
pw = os.environ.get("PAINEL_SENHA")
generated = pw is None
if generated:
    pw = "-".join(secrets.token_urlsafe(4) for _ in range(5))

names = ["EMBEDDED_HIST", "EMBEDDED_CONSUMO", "EMBEDDED_ORDENS"]
data = {}
for n in names:
    m = re.search(r"^const %s = (.*);\s*$" % n, html, re.M)
    if not m: sys.exit("não achei " + n)
    data[n] = json.loads(m.group(1))
    html = html.replace(m.group(0), "")
html = html.replace("const HIST_EPOCH = new Date(EMBEDDED_HIST.epoch + 'T00:00:00');", "let HIST_EPOCH;")
html = html.replace("\ninit();\n</script>", "\n</script>")
assert "HIST_EPOCH;" in html and "\ninit();" not in html

salt, iv = os.urandom(16), os.urandom(12)
key = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(pw.encode())
ct = AESGCM(key).encrypt(iv, json.dumps(data, separators=(",", ":")).encode(), b"painel-v1")
blob = base64.b64encode(salt + iv + ct).decode()

gate_css = """<style>
#gate{position:fixed;inset:0;z-index:99999;background:#241615;display:flex;align-items:center;justify-content:center;font-family:Inter,system-ui,sans-serif}
#gate form{background:#fff;padding:32px;border-radius:6px;width:min(340px,90vw);text-align:center}
#gate h1{font-size:20px;margin:0 0 6px;color:#6E1B16}#gate p{font-size:13px;color:#6B4E4C;margin:0 0 16px}
#gate input,#gate button{width:100%;padding:11px;font-size:15px;border-radius:4px;box-sizing:border-box}
#gate input{border:1px solid #E9D9D7;margin-bottom:10px}#gate button{border:0;background:#A32B24;color:#fff;cursor:pointer}
#gate button:disabled{opacity:.6}#gate .err{color:#A32B24;font-size:13px;min-height:18px;margin-top:8px}
</style>"""
gate_html = """<div id="gate"><form id="gateForm" autocomplete="off"><h1>Painel de Compras</h1><p>Acesso restrito. Informe a senha.</p>
<input type="password" id="gatePw" placeholder="Senha" autofocus required><button id="gateBtn">Entrar</button><div class="err" id="gateErr"></div></form></div>"""
gate_js = """<script>
(function(){
const BLOB="%s",ITER=%d;
const b64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function unlock(pw){
  const raw=b64(BLOB),salt=raw.slice(0,16),iv=raw.slice(16,28),ct=raw.slice(28);
  const base=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
  const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:ITER,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['decrypt']);
  const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv,additionalData:new TextEncoder().encode('painel-v1')},key,ct);
  return JSON.parse(new TextDecoder().decode(pt));
}
document.getElementById('gateForm').addEventListener('submit',async e=>{
  e.preventDefault();
  const btn=document.getElementById('gateBtn'),err=document.getElementById('gateErr'),inp=document.getElementById('gatePw');
  if(!(window.crypto&&crypto.subtle)){err.textContent='Navegador sem suporte (use HTTPS).';return;}
  btn.disabled=true;err.textContent='Verificando...';
  try{
    const d=await unlock(inp.value);
    inp.value='';
    EMBEDDED_HIST=d.EMBEDDED_HIST;EMBEDDED_CONSUMO=d.EMBEDDED_CONSUMO;EMBEDDED_ORDENS=d.EMBEDDED_ORDENS;
    HIST_EPOCH=new Date(EMBEDDED_HIST.epoch+'T00:00:00');
    document.getElementById('gate').remove();
    init();
  }catch(_){err.textContent='Senha incorreta.';btn.disabled=false;inp.select();}
});
})();
</script>""" % (blob, ITER)

# variáveis globais (let) para serem preenchidas após o desbloqueio
html = html.replace("<script>\n", "<script>\nlet EMBEDDED_HIST, EMBEDDED_CONSUMO, EMBEDDED_ORDENS;\n", 1) if False else html
idx = html.index("let HIST_EPOCH;")
html = html[:idx] + "let EMBEDDED_HIST, EMBEDDED_CONSUMO, EMBEDDED_ORDENS;\n" + html[idx:]
meta = '<meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer">'
html = html.replace("<head>", "<head>\n" + meta + "\n" + gate_css, 1)
html = html.replace("<body>", "<body>\n" + gate_html, 1)
html = html.replace("</script>\n</body>", "</script>\n" + gate_js + "\n</body>", 1)
open(out, "w", encoding="utf-8").write(html)
print("gerado", out, len(html) // 1024, "KB")
if generated: print("SENHA GERADA (guarde; não será mostrada de novo):", pw)
