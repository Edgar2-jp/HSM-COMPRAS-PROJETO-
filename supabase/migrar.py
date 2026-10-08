#!/usr/bin/env python3
"""Migração idempotente: extrai EMBEDDED_* de um painel_compras_*.html LOCAL e grava como lotes.

Roda no SEU computador. Os dados não vão para o Git nem para terceiros.
  pip install psycopg2-binary
  DATABASE_URL='postgresql://postgres:SENHA@db.<ref>.supabase.co:5432/postgres' \
      python3 supabase/migrar.py painel_compras_26.html [--dry-run]

Um lote por mês e tipo (Compras/Emenda) para os itens, mais um lote de ordens e um de consumo.
Reexecutar é seguro: cada lote é regravado (upsert) pelo nome. A senha do banco/DATABASE_URL
vem só do ambiente; nunca a coloque em arquivo versionado.
"""
import json, os, re, sys
from collections import defaultdict
from datetime import date, timedelta

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dry = "--dry-run" in sys.argv
if not args: sys.exit(__doc__)
html = open(args[0], encoding="utf-8").read()

def grab(n):
    m = re.search(r"^const %s = (.*);\s*$" % n, html, re.M)
    if not m: sys.exit("não achei " + n)
    return json.loads(m.group(1))

H, O, C = grab("EMBEDDED_HIST"), grab("EMBEDDED_ORDENS"), grab("EMBEDDED_CONSUMO")
ep = date.fromisoformat(H["epoch"])
MES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
day_date = lambda n: ep + timedelta(days=n)

lotes = []
# --- itens: agrupa por (ano-mês, sistema) reaproveitando os dicionários do histórico
grupos = defaultdict(list)
for r in H["R"]:
    d = day_date(r[2])
    grupos[(d.year, d.month, "Emenda" if r[11] == 1 else "Compras")].append(r)
for (y, m, tipo), rows in sorted(grupos.items()):
    # reindexa os dicionários só com o que o lote usa (payload compacto)
    dims = {k: {} for k in "FGPC U".replace(" ", "")}
    def ix(k, v):
        t = dims[k]
        if v not in t: t[v] = len(t)
        return t[v]
    R = []
    for r in rows:
        i, n, day, fi, gi, pi, ci, q, v, vi, vn, sf, ui = r
        R.append([i, n, day, ix("F", H["F"][fi]), ix("G", H["G"][gi]), ix("P", H["P"][pi]),
                  ix("C", H["C"][ci]), q, v, vi, vn, sf, ix("U", H["U"][ui] if ui is not None else "—")])
    payload = {k: list(dims[k]) for k in dims}; payload["R"] = R
    days = [r[2] for r in rows]
    lotes.append(dict(dataset="itens", origin="hist", tipo=tipo,
        filename=f"{tipo} — {MES[m-1]}/{y} (histórico)", rows=len(rows), periodo=None,
        min_day=min(days), max_day=max(days), payload=payload))
# --- ordens (Emenda)
if O["R"]:
    days = [r[1] for r in O["R"]]
    lotes.append(dict(dataset="ordens", origin="hist", tipo="Emenda",
        filename="Emenda — ordens de pagamento (arquivo inicial)", rows=len(O["R"]), periodo=None,
        min_day=min(days), max_day=max(days), payload={"R": O["R"]}))
# --- consumo
if C["R"]:
    lotes.append(dict(dataset="consumo", origin="hist", tipo="Consumo",
        filename="Paciente e Consumo — jul/ago/set 2026 (arquivo inicial)", rows=len(C["R"]),
        periodo="2026-07 a 2026-09", min_day=None, max_day=None, payload={"R": C["R"]}))

tot = sum(l["rows"] for l in lotes if l["dataset"] != "consumo")
print(f"{len(lotes)} lotes; {tot} registros (itens+ordens); maior payload: "
      f"{max(len(json.dumps(l['payload'], separators=(',', ':'))) for l in lotes)/1e3:.0f} KB")
if dry: sys.exit(0)

import psycopg2
from psycopg2.extras import Json
url = os.environ.get("DATABASE_URL") or sys.exit("defina DATABASE_URL (veja o topo do arquivo)")
con = psycopg2.connect(url); cur = con.cursor()
for l in lotes:
    cur.execute("""insert into public.lotes (dataset,origin,tipo,filename,rows,periodo,min_day,max_day,payload)
        values (%(dataset)s,%(origin)s,%(tipo)s,%(filename)s,%(rows)s,%(periodo)s,%(min_day)s,%(max_day)s,%(payload)s)
        on conflict (dataset, filename) where origin = 'hist'
        do update set tipo=excluded.tipo, rows=excluded.rows, periodo=excluded.periodo,
                      min_day=excluded.min_day, max_day=excluded.max_day, payload=excluded.payload""",
        {**l, "payload": Json(l["payload"])})
con.commit()
cur.execute("select dataset, count(*), sum(rows) from public.lotes group by 1 order by 1")
for row in cur.fetchall(): print(row)
