#!/usr/bin/env python3
"""Export the checked DOI set as an auditable CSV and Typst-compatible BibTeX."""
from __future__ import annotations
import csv, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/bibliometria"
CROSSREF = DATA / "crossref_verification.json"
CORPUS = DATA / "corpus_verificado.csv"
BIB = ROOT / "artigo/references.bib"

OFFICIAL = [
    ("SiconfiApi2026", "Tesouro Nacional", "API de Dados Abertos do Siconfi: documentação", 2026, "https://apidatalake.tesouro.gov.br/docs/siconfi/", "Documentação consultada em 25 out. 2026."),
    ("STNFinbra2026", "Secretaria do Tesouro Nacional", "FINBRA — Finanças Municipais", 2026, "https://www.gov.br/tesouronacional/pt-br/estados-e-municipios/dados-consolidados/finbra-financas-municipais", "Página metodológica consultada em 25 out. 2026."),
    ("IBGEPops2026", "Instituto Brasileiro de Geografia e Estatística", "Estimativas de população", 2026, "https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html", "Consultado em 25 out. 2026."),
    ("IBGECensus2022", "Instituto Brasileiro de Geografia e Estatística", "Censo Demográfico 2022: população residente", 2023, "https://www.ibge.gov.br/estatisticas/sociais/saude/22827-censo-demografico-2022.html", "Consulta SIDRA tabela 4709, variável 93."),
    ("IBGEPib2023", "Instituto Brasileiro de Geografia e Estatística", "Produto Interno Bruto dos Municípios", 2025, "https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html", "SIDRA tabela 5938; série municipal coletada até 2023."),
    ("IBGEIPCA2024", "Instituto Brasileiro de Geografia e Estatística", "Índice Nacional de Preços ao Consumidor Amplo — IPCA", 2026, "https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9256-indice-nacional-de-precos-ao-consumidor-amplo.html", "SIDRA tabela 1737; acesso em 25 out. 2026."),
    ("IBGEArcoverde2026", "Instituto Brasileiro de Geografia e Estatística", "Arcoverde (PE): Cidades e Estados", 2026, "https://www.ibge.gov.br/cidades-e-estados/pe/arcoverde.html", "Acesso em 25 out. 2026; área territorial 2025 e população censitária 2022."),
    ("IBGEAraripina2026", "Instituto Brasileiro de Geografia e Estatística", "Araripina (PE): Cidades e Estados", 2026, "https://www.ibge.gov.br/cidades-e-estados/pe/araripina.html", "Acesso em 25 out. 2026; área territorial 2025 e população censitária 2022."),
    ("IBGEMunicipalAreas2025", "Instituto Brasileiro de Geografia e Estatística", "Áreas territoriais: áreas dos municípios", 2025, "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15761-areas-dos-municipios.html", "Malha Municipal Digital 2025; valores publicados em 2026."),
    ("EurostatGFS2026", "Eurostat", "Government finance statistics", 2026, "https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Government_finance_statistics", "Conceitos de governo geral e ESA 2010; consultado em 25 out. 2026."),
    ("EurostatEDP2026", "Eurostat", "Government deficit and debt (gov_10dd_edpt1)", 2026, "https://ec.europa.eu/eurostat/databrowser/product/view/gov_10dd_edpt1", "API pública; recorte Bélgica, setor S13, unidade PC_GDP, 2015–2025; extração de 25 out. 2026."),
    ("BelgiumFederalState2026", "Belgium.be", "Belgium, a federal state", 2026, "https://www.belgium.be/en/about_belgium/government/federale_staat", "Fonte oficial sobre comunidades, regiões, províncias e conselhos municipais; consultado em 25 out. 2026."),
    ("BelgiumFederalAuthorities2026", "Belgium.be", "The Federal Authorities", 2026, "https://www.belgium.be/en/about_belgium/government/federal_authorities", "Fonte oficial sobre poderes federais; consultado em 25 out. 2026."),
    ("BelgiumMonarchy2026", "Belgium.be", "The role of the monarchy", 2026, "https://www.belgium.be/en/about_belgium/government/federal_authorities/king/role_monarchy", "Fonte oficial sobre monarquia constitucional e parlamentar; consultado em 25 out. 2026."),
    ("EUCountrypageBelgium2026", "European Union", "Belgium — EU country", 2026, "https://european-union.europa.eu/principles-countries-history/eu-countries/belgium_en", "Ficha institucional; área e população com referência Eurostat; atualizada em 16 out. 2026."),
]

def esc(s: str) -> str:
    return (s or "").replace("\\", "\\textbackslash{}").replace("{", "\\{").replace("}", "\\}")

def main() -> None:
    rows = json.loads(CROSSREF.read_text(encoding="utf-8"))
    candidate_rows = list(csv.DictReader((DATA / "candidatos.csv").open(encoding="utf-8-sig", newline="")))
    citation_keys = {str(r["id"]): r["citation_key"] for r in candidate_rows}
    if len(rows) != 80 or sum(bool(r.get("metadata_match_screen")) for r in rows) != 80:
        raise SystemExit("O Crossref não confirmou 80/80 correspondências de metadados; não exportar corpus como verificado.")
    csv_fields = ["id", "doi", "doi_canonical", "citation_key", "title", "authors", "journal", "year", "keywords", "abstract", "peer_reviewed", "document_type", "metadata_source", "verified_source", "publisher_url", "publisher_verified", "verification_level", "topic", "crossref_type", "title_similarity", "journal_similarity"]
    corpus = []
    entries = []
    for r in rows:
        key = citation_keys[str(r["id"])]
        authors = r.get("authors_crossref") or r.get("authors", "")
        title = r.get("title_crossref") or r.get("title", "")
        journal = r.get("journal_crossref") or r.get("journal", "")
        year = r.get("year_crossref") or r.get("year")
        doi = r["doi"]
        publisher_url = r.get("publisher_landing_url") or r.get("publisher_or_index_url") or f"https://doi.org/{doi}"
        corpus.append({
            "id": r["id"], "doi": doi, "doi_canonical": doi.strip().lower(), "citation_key": key,
            "title": title, "authors": authors, "journal": journal, "year": year,
            "keywords": "", "abstract": "", "peer_reviewed": "selected_as_peer_reviewed_candidate",
            "document_type": r.get("crossref_type", ""), "metadata_source": r.get("crossref_url", ""),
            "verified_source": r.get("crossref_url", ""), "publisher_url": publisher_url,
            "publisher_verified": "no", "verification_level": "Crossref metadata matched; publisher-policy check pending",
            "topic": r.get("topic", ""), "crossref_type": r.get("crossref_type", ""),
            "title_similarity": r.get("title_similarity", ""), "journal_similarity": r.get("journal_similarity", "")
        })
        bib_authors = " and ".join(esc(a.strip()) for a in authors.split(";") if a.strip())
        entries.append(f"""@article{{{key},
  author = {{{bib_authors}}},
  title = {{{esc(title)}}},
  journal = {{{esc(journal)}}},
  year = {{{year}}},
  doi = {{{esc(doi)}}},
  url = {{{esc(publisher_url)}}}
}}""")
    with CORPUS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields)
        w.writeheader(); w.writerows(corpus)
    for key, author, title, year, url, note in OFFICIAL:
        entries.append(f"""@misc{{{key},
  author = {{{esc(author)}}},
  title = {{{esc(title)}}},
  year = {{{year}}},
  howpublished = {{{esc(url)}}},
  url = {{{esc(url)}}},
  note = {{{esc(note)}}}
}}""")
    entries.append("""@article{BakerLarckerWang2022,
  author = {Baker, Andrew C. and Larcker, David F. and Wang, Charles C. Y.},
  title = {How much should we trust staggered difference-in-differences estimates?},
  journal = {Journal of Financial Economics},
  year = {2022},
  volume = {144},
  number = {2},
  pages = {370--395},
  doi = {10.1016/j.jfineco.2022.01.004},
  url = {https://doi.org/10.1016/j.jfineco.2022.01.004}
}""")
    BIB.parent.mkdir(parents=True, exist_ok=True)
    BIB.write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    print(f"Corpus exportado: {len(corpus)} artigos; {len({r['doi_canonical'] for r in corpus})} DOI distintos; {len(entries)-len(corpus)} fontes oficiais; {BIB}")

if __name__ == "__main__":
    main()
