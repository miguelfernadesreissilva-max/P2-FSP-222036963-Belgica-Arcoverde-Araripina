#!/usr/bin/env python3
"""Generate a concise thematic citation map from the DOI-verified corpus."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/"data/bibliometria/corpus_verificado.csv"
OUT=ROOT/"artigo/matriz_literatura.typ"

def cluster(topic: str) -> str:
    x=topic.lower()
    if "belg" in x or "europe" in x or "eu " in x: return "Bélgica e governança europeia"
    if "transfer" in x or "grant" in x: return "Transferências intergovernamentais"
    if "revenue" in x or "tax" in x or "fiscal capacity" in x: return "Receita própria e capacidade fiscal"
    if "budget" in x or "accountability" in x or "participation" in x or "audit" in x: return "Orçamento, auditoria e accountability"
    if "expenditure" in x or "service" in x or "spending" in x: return "Despesa e provisão de serviços"
    if "rule" in x or "institution" in x: return "Regras e instituições fiscais"
    return "Federalismo e finanças subnacionais"

def main() -> None:
    with IN.open(encoding="utf-8-sig", newline="") as f: rows=list(csv.DictReader(f))
    if len(rows)!=80: raise SystemExit(f"Esperados 80 artigos; encontrados {len(rows)}")
    groups={}
    for r in rows: groups.setdefault(cluster(r.get("topic","")), []).append(r)
    lines=[
        "== Mapa temático da literatura", "",
        "Os 80 registros foram agrupados por foco temático declarado nos metadados de triagem. Os DOI, títulos e periódicos individuais estão na planilha `data/bibliometria/corpus_verificado.csv`. Esta organização situa as perguntas e unidades de análise da literatura, mas não substitui a leitura crítica de cada texto completo; nenhuma conclusão específica foi atribuída sem evidência individual disponível.", "",
    ]
    order=["Federalismo e finanças subnacionais", "Receita própria e capacidade fiscal", "Transferências intergovernamentais", "Despesa e provisão de serviços", "Orçamento, auditoria e accountability", "Regras e instituições fiscais", "Bélgica e governança europeia"]
    for name in order:
        group=groups.get(name, [])
        if not group: continue
        group=sorted(group, key=lambda r:(int(r["year"]), r["citation_key"]))
        cite_text="; ".join("@"+r["citation_key"] for r in group)
        lines.append(f"*{name}* ({len(group)} estudos): {cite_text}.")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Mapa temático gerado: {len(rows)} citações; {len(groups)} núcleos; {OUT}")
if __name__=="__main__": main()
