#!/usr/bin/env python3
"""Migração única e idempotente: extrai EMBEDDED_HIST / EMBEDDED_ORDENS / EMBEDDED_CONSUMO
do HTML antigo (que fica só no seu computador) e sobe como 3 lotes iniciais ('hist') no Supabase.

Usa o LOGIN DO ADMIN (e-mail + senha) com a chave pública — não precisa de service_role.
Só Python 3 padrão, sem instalar nada.

  python3 supabase/migrar.py painel_compras.html --dry-run      # só confere os totais, não envia
  SUPABASE_ADMIN_EMAIL=voce@x.com python3 supabase/migrar.py painel_compras.html   # pede a senha
  ... --recarregar    # apaga e reenvia os lotes 'hist' (por padrão, os que já existem são pulados)
"""
import getpass, json, os, re, sys, urllib.request, urllib.error
from datetime import date
from decimal import Decimal as D

URL = os.environ.get("SUPABASE_URL", "https://mjjpfomgxthzjtqzzfqs.supabase.co")
KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_UhlEoBQnKhZxNQWUnl8bFA_sGFnKzs4")  # chave PÚBLICA

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dry, reload_ = "--dry-run" in sys.argv, "--recarregar" in sys.argv
if not args: sys.exit(__doc__)
html = open(args[0], encoding="utf-8").read()

def grab(n):
    m = re.search(r"^const %s = (.*);\s*$" % n, html, re.M)
    if not m: sys.exit(f"não achei {n} — este HTML já está sem os dados embutidos?")
    return json.loads(m.group(1))

H, O, C = grab("EMBEDDED_HIST"), grab("EMBEDDED_ORDENS"), grab("EMBEDDED_CONSUMO")

# ---- mesmos registros que o painel antigo montava na memória ----
F, G, P, CA, U = H["F"], H["G"], H.get("P"), H["C"], H.get("U")
itens = [dict(i=i, n=n, day=day, forn=F[fi], gen=G[gi], prod=(P[pi] if P else G[gi]), cat=CA[ci], q=q, v=v,
              vi=vi, vn=vn, un=(U[ui] if (U and ui is not None) else "—"), sis="Emenda" if sf == 1 else "Compras")
         for i, n, day, fi, gi, pi, ci, q, v, vi, vn, sf, ui in H["R"]]
ordens = [dict(ord=o, day=d, forn=f, v=v, situacao=s) for o, d, f, v, s in O["R"]]
consumo = [dict(gen=g, marcas=m, tipo=t, qty=q, pmin=a, pmax=b, unidades=u) for g, m, t, q, a, b, u, *_ in C["R"]]

def pack(records):  # igual a packRecords() do index.html
    keys = []
    for r in records:
        for k in r:
            if k not in keys: keys.append(k)
    cols = {}
    for k in keys:
        if all(r.get(k) is None or isinstance(r.get(k), str) for r in records):
            idx, d, v = {}, [], []
            for r in records:
                x = r.get(k)
                if x is None: v.append(-1); continue
                if x not in idx: idx[x] = len(d); d.append(x)
                v.append(idx[x])
            cols[k] = {"d": d, "v": v}
        else:
            cols[k] = {"v": [r.get(k) for r in records]}
    return {"n": len(records), "c": cols}

days = lambda rs: (min(r["day"] for r in rs), max(r["day"] for r in rs))
lotes = [
    dict(dataset="itens", origin="hist", tipo="Compras", filename="Banco de Dados (histórico original)",
         rows=len(itens), min_day=days(itens)[0], max_day=days(itens)[1], payload=pack(itens)),
    dict(dataset="ordens", origin="hist", tipo="Emenda", filename="Emenda — ordens de pagamento (arquivo inicial)",
         rows=len(ordens), min_day=days(ordens)[0], max_day=days(ordens)[1], payload=pack(ordens)),
    dict(dataset="consumo", origin="hist", tipo="Consumo", filename="Paciente e Consumo — jul/ago/set 2026 (arquivo inicial)",
         rows=len(consumo), periodo="2026-07 a 2026-09", payload=pack(consumo)),
]

# ---- conferência (critérios de aceite, 01/2025 a 09/2026) ----
ep = date.fromisoformat(H["epoch"])
lo, hi = (date(2025, 1, 1) - ep).days, (date(2026, 9, 30) - ep).days
soma = lambda rs, f: sum((D(str(r["v"] or 0)) for r in rs if lo <= r["day"] <= hi and f(r)), D(0))
compras, emenda = soma(itens, lambda r: r["sis"] == "Compras"), soma(itens, lambda r: r["sis"] == "Emenda")
antes = soma(ordens, lambda r: True)
fmt = lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
print("Compras:", fmt(compras), "| Emenda após:", fmt(emenda), "| Total:", fmt(compras + emenda),
      "| Emenda antes:", fmt(antes), "| registros:", len(itens) + len(ordens))
for l in lotes: print(f"  lote {l['dataset']:8} {l['rows']:6} linhas  {len(json.dumps(l['payload'], separators=(',', ':')))/1e6:.2f} MB")
if dry: sys.exit(0)

# ---- envio ----
def call(method, path, body=None, token=None, extra=None):
    h = {"apikey": KEY, "Authorization": "Bearer " + (token or KEY), "Content-Type": "application/json"}
    h.update(extra or {})
    req = urllib.request.Request(URL + path, method=method, headers=h,
                                 data=json.dumps(body, separators=(",", ":")).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=300) as r: raw = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> {e.code}: {e.read().decode()[:400]}")
    return json.loads(raw) if raw else None

email = os.environ.get("SUPABASE_ADMIN_EMAIL") or input("E-mail do admin: ")
senha = os.environ.get("SUPABASE_ADMIN_PASSWORD") or getpass.getpass("Senha do admin: ")
tok = call("POST", "/auth/v1/token?grant_type=password", {"email": email, "password": senha})["access_token"]

exist = call("GET", "/rest/v1/lotes?select=id,dataset,filename&origin=eq.hist", token=tok)
for l in lotes:
    ja = [e for e in exist if e["dataset"] == l["dataset"] and e["filename"] == l["filename"]]
    if ja and not reload_:
        print("já existe, pulando:", l["dataset"]); continue
    for e in ja:
        call("DELETE", f"/rest/v1/lotes?id=eq.{e['id']}", token=tok)
    call("POST", "/rest/v1/lotes", l, token=tok, extra={"Prefer": "return=minimal"})
    print("enviado:", l["dataset"], l["rows"], "linhas")
print("pronto. Confira no painel (Visão Geral, 01/2025 a 09/2026).")
