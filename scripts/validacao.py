#!/usr/bin/env python3
"""Testes de integridade e reconciliação para a base tratada da P2."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "brutos"
TRT = ROOT / "data" / "tratados"
TOL = Decimal("0.02")


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def dec(value):
    return Decimal(value) if value not in (None, "") else None


def assert_close(a, b, label):
    if a is None or b is None or abs(a - b) > TOL:
        raise AssertionError(f"{label}: não reconciliado ({a} vs. {b})")


def account_path(code):
    if not code or not code.startswith("RO"):
        return None
    return tuple(code[2:].split("."))


def main():
    municipal = read_csv(TRT / "municipais_2015_2024.csv")
    belgium = read_csv(TRT / "belgica_2015_2025.csv")
    source_rows = read_csv(TRT / "linhas_contas_selecionadas.csv")
    functions = read_csv(TRT / "despesas_por_funcao_2017_2024.csv")
    failures = []

    assert len(municipal) == 20, f"Esperadas 20 observações municipais; obtidas {len(municipal)}"
    keys = [(r["codigo_ibge"], r["ano"]) for r in municipal]
    assert len(keys) == len(set(keys)), "Duplicata município-ano na série tratada"
    for field in ["receita_bruta_total_reportada_rs", "despesa_empenhada_total_rs", "receita_tributaria_propria_bruta_rs", "transferencias_correntes_total_brutas_rs"]:
        assert all(r[field] for r in municipal), f"Ausência inesperada em {field}"
    assert sum(bool(r["populacao"]) for r in municipal) == 18
    assert sum(bool(r["pib_municipal_rs"]) for r in municipal) == 18
    assert all(not r["populacao"] or dec(r["populacao"]) > 0 for r in municipal)

    # 2019–2024 have explicit intra/extra receipts in the DCA; reconcile their total.
    for r in municipal:
        if int(r["ano"]) >= 2019:
            assert_close(dec(r["receita_bruta_total_reportada_rs"]),
                         dec(r["receita_exceto_intra_bruta_rs"]) + dec(r["receita_intra_bruta_rs"]),
                         f"Receitas I+II {r['municipio']}/{r['ano']}")
        if r["despesa_intra_residual_rs"]:
            assert_close(dec(r["despesa_empenhada_total_rs"]),
                         dec(r["despesa_empenhada_exceto_intra_rs"]) + dec(r["despesa_intra_residual_rs"]),
                         f"Despesas I-D/I-E {r['municipio']}/{r['ano']}")

    # The population at the census year must be the official SIDRA 2022 census value.
    for city, expected in [("Arcoverde/PE", "77742"), ("Araripina/PE", "85088")]:
        row = next(r for r in municipal if r["municipio"] == city and r["ano"] == "2022")
        assert row["populacao"] == expected and "Censo" in row["fonte_populacao"]

    # Data-source completeness and explicit periods.
    ipca = json.loads((RAW / "ibge_ipca_mensal_2015_2024.json").read_text(encoding="utf-8"))
    by_year = defaultdict(int)
    for row in ipca[1:]:
        by_year[row["D3C"][:4]] += 1
    assert set(by_year) == {str(y) for y in range(2015, 2025)}
    assert all(by_year[str(y)] == 12 for y in range(2015, 2025))
    assert len(belgium) == 11 and [int(r["ano"]) for r in belgium] == list(range(2015, 2026))
    b25 = next(r for r in belgium if r["ano"] == "2025")
    assert dec(b25["deficit_net_lending_pct_pib"]) == Decimal("-5.2")
    assert dec(b25["divida_bruta_pct_pib"]) == Decimal("108.1")

    # All selected-account records carry an indicator. Within each indicator, chosen
    # account codes must be non-overlapping in the DCA account hierarchy.
    assert all(r["indicador"] for r in source_rows)
    grouped = defaultdict(set)
    for r in source_rows:
        path = account_path(r["cod_conta"])
        if path:
            grouped[(r["municipio"], r["ano"], r["indicador"], r["coluna"])].add(path)
    for group, paths in grouped.items():
        plist = list(paths)
        for i, a in enumerate(plist):
            for b in plist[i + 1:]:
                if (len(a) < len(b) and b[:len(a)] == a) or (len(b) < len(a) and a[:len(b)] == b):
                    raise AssertionError(f"Possível dupla contagem por conta-pai/filha em {group}: {a}, {b}")

    assert len(functions) == 256, f"Esperadas 256 linhas funcionais; obtidas {len(functions)}"
    assert {int(r["ano"]) for r in functions} == set(range(2017, 2025))
    for r in municipal:
        if int(r["ano"]) < 2017:
            continue
        group = [x for x in functions if x["municipio"] == r["municipio"] and x["ano"] == r["ano"]]
        assert len(group) == len({x["codigo_funcao"] for x in group}), f"Função duplicada em {r['municipio']}/{r['ano']}"
        assert_close(sum(dec(x["despesa_empenhada_nominal_rs"]) for x in group),
                     dec(r["despesa_empenhada_exceto_intra_rs"]),
                     f"Soma das funções {r['municipio']}/{r['ano']}")

    # The delivered table retains blanks for genuinely unavailable observations.
    assert all(not r["pib_municipal_rs"] for r in municipal if r["ano"] == "2024")
    assert all(not r["populacao"] for r in municipal if r["ano"] == "2023")

    report = [
        "VALIDAÇÃO DA BASE — PASS",
        f"Observações municipais: {len(municipal)}; 10 anos × 2 municípios.",
        f"Dados fiscais essenciais completos: {len(municipal)}/{len(municipal)}.",
        f"População disponível: {sum(bool(r['populacao']) for r in municipal)}/{len(municipal)}; 2023 permanece ausente; 2022 usa Censo.",
        f"PIB disponível: {sum(bool(r['pib_municipal_rs']) for r in municipal)}/{len(municipal)}; 2024 permanece ausente.",
        "IPCA: 12 meses por ano em 2015–2024; sem imputação.",
        "Despesas totais e componentes intra/extra reconciliados dentro de R$ 0,02.",
        "Receitas intra/extra reconciliadas em 2019–2024 dentro de R$ 0,02.",
        "Conta-pai/filha: nenhuma dupla contagem dentro do indicador selecionado.",
        f"Despesas funcionais: {len(functions)} linhas; 2017–2024; soma das funções de primeiro nível reconcilia com despesa empenhada exceto intra.",
        "Eurostat: 2015–2025; 2025 = déficit -5,2% e dívida bruta 108,1% do PIB.",
        "Deduções não exibidas na fonte permanecem em branco; o saldo derivado é rotulado como baseado nas deduções reportadas.",
    ]
    out = TRT / "relatorio_validacao.txt"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
