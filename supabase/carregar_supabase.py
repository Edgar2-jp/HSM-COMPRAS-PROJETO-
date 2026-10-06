#!/usr/bin/env python3
"""Carrega a base embutida no painel_compras_*.html para o Supabase (Postgres).

Uso:
  pip install psycopg2-binary
  DATABASE_URL='postgresql://postgres:SENHA@db.<ref>.supabase.co:5432/postgres' \
      python3 supabase/carregar_supabase.py painel_compras_10.html [--dry-run]

Roda no seu computador: os dados não passam por terceiros nem vão para o Git.
Remove as políticas temporárias 'carga_tmp' (acesso anon) e recarrega do zero.
"""
import json, os, re, sys
from datetime import date, timedelta

args = [a for a in sys.argv[1:] if not a.startswith("--")]
dry = "--dry-run" in sys.argv
if not args: sys.exit(__doc__)
html = open(args[0], encoding="utf-8").read()

def grab(n):
    m = re.search(r"^const %s = (.*);\s*$" % n, html, re.M)
    if not m: sys.exit("não achei " + n)
    return json.loads(m.group(1))

H, C, O = grab("EMBEDDED_HIST"), grab("EMBEDDED_CONSUMO"), grab("EMBEDDED_ORDENS")
ep = date.fromisoformat(H["epoch"])
d = lambda n: (ep + timedelta(days=n)).isoformat()
oep = date.fromisoformat(O.get("epoch", H["epoch"]))

dim = {t: [(i, v) for i, v in enumerate(H[k])] for t, k in
       [("fornecedores","F"),("itens","G"),("produtos","P"),("categorias","C"),("unidades","U")]}
compras = [(r[0], r[1], d(r[2]), r[3], r[4], r[5], r[6], r[12], r[7], r[8], r[9], r[10],
            "Emenda" if r[11] == 1 else "Compras") for r in H["R"]]
ordens = [(r[0], (oep + timedelta(days=r[1])).isoformat(), r[2], r[3], r[4] or None) for r in O["R"]]
consumo = [(r[0], json.dumps(r[1], ensure_ascii=False), r[2], r[3], r[4], r[5],
            json.dumps(r[6]), json.dumps(r[7])) for r in C["R"]]

print({**{k: len(v) for k, v in dim.items()}, "compras": len(compras),
       "ordens": len(ordens), "consumo": len(consumo)})
if dry: sys.exit(0)

import psycopg2
from psycopg2.extras import execute_values
con = psycopg2.connect(os.environ["DATABASE_URL"])
cur = con.cursor()
tabs = ["fornecedores","itens","produtos","categorias","unidades","compras","ordens","consumo"]
for t in tabs:
    cur.execute(f"drop policy if exists carga_tmp on public.{t}")
cur.execute("truncate " + ",".join("public." + t for t in tabs) + " restart identity cascade")
for t, rows in dim.items():
    execute_values(cur, f"insert into public.{t} (id, nome) values %s", rows, page_size=5000)
execute_values(cur, "insert into public.compras (cod_item,nota,data,fornecedor_id,item_id,produto_id,categoria_id,"
    "unidade_id,quantidade,valor,valor_item,valor_negociado,sistema) values %s", compras, page_size=5000)
execute_values(cur, "insert into public.ordens (ordem,data,fornecedor,valor,situacao) values %s", ordens)
execute_values(cur, "insert into public.consumo (item,marcas,tipo,quantidade,periodo_min,periodo_max,extra,mensal) "
    "values %s", consumo, page_size=2000)
con.commit()
for t in tabs:
    cur.execute(f"select count(*) from public.{t}"); print(t, cur.fetchone()[0])
