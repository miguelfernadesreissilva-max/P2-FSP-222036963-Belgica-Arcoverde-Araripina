#!/usr/bin/env python3
"""Gera estatísticas descritivas e figuras com base apenas nos dados tratados."""
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRT = ROOT / "data" / "tratados"
RAW = ROOT / "data" / "brutos"
AN = ROOT / "analise"
FIG = ROOT / "figuras"
CITIES = ["Arcoverde/PE", "Araripina/PE"]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def num(value):
    return float(value) if value not in (None, "") else math.nan


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def fmt(v):
    return "" if v is None or not np.isfinite(v) else f"{v:.10f}"


def pearson(x, y):
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    return float(np.corrcoef(x, y)[0, 1])


def ranks(values):
    """Average ranks for ties, with the smallest value ranked first."""
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    result = np.empty(len(values), dtype=float)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        result[order[i:j]] = (i + 1 + j) / 2
        i = j
    return result


def main():
    AN.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    municipal = read_csv(TRT / "municipais_2015_2024.csv")
    bel = read_csv(TRT / "belgica_2015_2025.csv")
    ipca = read_csv(TRT / "ipca_anual.csv")
    ipca_by_year = {int(r["ano"]): num(r["ipca_media_anual_numero_indice"]) for r in ipca}

    # Expand DCA functional totals from the official raw responses, selecting only
    # top-level function codes to avoid summing parent lines and descendants.
    function_rows = []
    for city_key, city_name in [("arcoverde", CITIES[0]), ("araripina", CITIES[1])]:
        for year in range(2015, 2025):
            source = RAW / f"siconfi_dca_{city_key}_{year}.json"
            payload = json.loads(source.read_text(encoding="utf-8"))
            items = payload["items"]
            candidates = [r for r in items if r.get("anexo") == "DCA-Anexo I-E"
                          and r.get("coluna") == "Despesas Empenhadas"
                          and r.get("rotulo") == "Total Geral da Despesa por Função"
                          and re.match(r"^\d{2} - ", str(r.get("conta", "")))]
            total_rows = [r for r in items if r.get("anexo") == "DCA-Anexo I-E"
                          and r.get("coluna") == "Despesas Empenhadas"
                          and r.get("rotulo") == "Total Geral da Despesa por Função"
                          and r.get("conta") == "Despesas Exceto Intraorçamentárias"]
            if not candidates or len(total_rows) != 1:
                continue
            total = num(total_rows[0].get("valor"))
            factor = ipca_by_year[2024] / ipca_by_year[year]
            sum_functions = sum(num(r.get("valor")) for r in candidates)
            if abs(sum_functions - total) > 0.02:
                raise AssertionError(f"Funções não reconciliam com total: {city_name} {year}")
            for r in candidates:
                nominal = num(r.get("valor"))
                code, label = str(r["conta"]).split(" - ", 1)
                function_rows.append({
                    "municipio": city_name, "ano": year, "codigo_funcao": code,
                    "funcao": label, "despesa_empenhada_nominal_rs": fmt(nominal),
                    "despesa_empenhada_reais_2024_rs": fmt(nominal * factor),
                    "participacao_despesa_funcional_pct": fmt(nominal / total * 100),
                    "total_funcional_exceto_intra_nominal_rs": fmt(total),
                    "fonte_arquivo": source.name,
                    "fonte_anexo": "DCA-Anexo I-E",
                    "cobertura": "2017-2024; 2015-2016 indisponíveis no anexo funcional recuperado",
                })
    write_csv(TRT / "despesas_por_funcao_2017_2024.csv", function_rows)

    # Descriptive statistics for nominal/real levels and growth from 2015 to 2024.
    desc = []
    correlation = []
    differences = []
    for city in CITIES:
        rows = sorted([r for r in municipal if r["municipio"] == city], key=lambda r: int(r["ano"]))
        years = np.array([int(r["ano"]) for r in rows])
        rev = np.array([num(r["receita_bruta_total_reportada_reais_2024"]) for r in rows])
        exp = np.array([num(r["despesa_empenhada_total_reais_2024"]) for r in rows])
        assert np.isfinite(rev).all() and np.isfinite(exp).all()
        cagr_rev = (rev[-1] / rev[0]) ** (1 / (years[-1] - years[0])) - 1
        cagr_exp = (exp[-1] / exp[0]) ** (1 / (years[-1] - years[0])) - 1
        for var, arr, cagr in [("receita_bruta_total", rev, cagr_rev), ("despesa_empenhada_total", exp, cagr_exp)]:
            desc.append({
                "municipio": city, "variavel": var, "ano_inicial": int(years[0]), "ano_final": int(years[-1]),
                "valor_2015_reais_2024": fmt(arr[0]), "valor_2024_reais_2024": fmt(arr[-1]),
                "variacao_acumulada_pct": fmt((arr[-1] / arr[0] - 1) * 100),
                "cagr_real_pct": fmt(cagr * 100), "observacoes": len(arr),
            })
        level_r = pearson(rev, exp)
        level_s = pearson(ranks(rev), ranks(exp))
        d_rev, d_exp = np.diff(rev), np.diff(exp)
        diff_r = pearson(d_rev, d_exp)
        correlation.extend([
            {"municipio": city, "base": "níveis reais R$ 2024", "metrica": "Pearson r", "coeficiente": fmt(level_r), "n": len(rev), "interpretacao": "descritivo; tendência temporal comum pode inflar associação; não causal"},
            {"municipio": city, "base": "níveis reais R$ 2024", "metrica": "Spearman rho", "coeficiente": fmt(level_s), "n": len(rev), "interpretacao": "descritivo; tendência temporal comum pode inflar associação; não causal"},
            {"municipio": city, "base": "variações anuais em reais de 2024", "metrica": "Pearson r", "coeficiente": fmt(diff_r), "n": len(d_rev), "interpretacao": "amostra curta e serial; não causal"},
        ])
        for i in range(1, len(rows)):
            differences.append({
                "municipio": city, "ano": int(years[i]), "variacao_receita_real_rs": fmt(rev[i] - rev[i-1]),
                "variacao_despesa_real_rs": fmt(exp[i] - exp[i-1]),
                "crescimento_receita_real_pct": fmt((rev[i] / rev[i-1] - 1) * 100),
                "crescimento_despesa_real_pct": fmt((exp[i] / exp[i-1] - 1) * 100),
            })
    write_csv(AN / "estatisticas_descritivas.csv", desc)
    write_csv(AN / "correlacoes.csv", correlation)
    write_csv(AN / "variacoes_anuais.csv", differences)

    # Revenue structure indicators are shares of reported gross revenue (not a balance).
    structure = []
    for r in municipal:
        structure.append({
            "municipio": r["municipio"], "ano": r["ano"],
            "tributaria_propria_pct_receita_bruta": fmt(num(r["receita_tributaria_share_receita_bruta_pct"])),
            "transferencias_correntes_pct_receita_bruta": fmt(num(r["transfer_correntes_share_receita_bruta_pct"])),
            "transferencias_intergov_correntes_proxy_pct_receita_bruta": fmt(num(r["transferencias_intergov_correntes_proxy_brutas_rs"]) / num(r["receita_bruta_total_reportada_rs"]) * 100),
        })
    write_csv(AN / "estrutura_receitas.csv", structure)

    # Style and color system: accessible, publication-ready, no 3-D effects.
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
                         "axes.labelsize": 10, "legend.fontsize": 9, "figure.dpi": 160,
                         "savefig.dpi": 220, "axes.spines.top": False, "axes.spines.right": False})
    colors = {CITIES[0]: "#145A75", CITIES[1]: "#B65C2E"}

    # 1. Real revenues and committed expenditure, panels by municipality.
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True, constrained_layout=True)
    for ax, city in zip(axes, CITIES):
        rs = sorted([r for r in municipal if r["municipio"] == city], key=lambda r: int(r["ano"]))
        x = [int(r["ano"]) for r in rs]
        rev = [num(r["receita_bruta_total_reportada_reais_2024"]) / 1e6 for r in rs]
        exp = [num(r["despesa_empenhada_total_reais_2024"]) / 1e6 for r in rs]
        ax.plot(x, rev, marker="o", linewidth=2.2, color="#145A75", label="Receita bruta reportada")
        ax.plot(x, exp, marker="s", linewidth=2.2, color="#B65C2E", label="Despesa empenhada total")
        ax.set_title(city)
        ax.set_xticks(x[::2])
        ax.grid(axis="y", alpha=.25)
        ax.set_xlabel("Ano")
    axes[0].set_ylabel("R$ milhões, preços médios de 2024")
    axes[1].legend(frameon=False, loc="upper left")
    fig.suptitle("Fluxos fiscais municipais em termos reais", fontsize=14, fontweight="bold")
    fig.savefig(FIG / "receitas_despesas_reais.png", bbox_inches="tight")
    plt.close(fig)

    # 2. Own-tax and current transfer shares in gross reported revenue.
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True, constrained_layout=True)
    for ax, city in zip(axes, CITIES):
        rs = sorted([r for r in municipal if r["municipio"] == city], key=lambda r: int(r["ano"]))
        x = [int(r["ano"]) for r in rs]
        tax = [num(r["receita_tributaria_share_receita_bruta_pct"]) for r in rs]
        tr = [num(r["transfer_correntes_share_receita_bruta_pct"]) for r in rs]
        ax.plot(x, tax, marker="o", linewidth=2.2, color="#26734D", label="Tributária própria")
        ax.plot(x, tr, marker="s", linewidth=2.2, color="#8C5AA7", label="Transferências correntes")
        ax.set_title(city)
        ax.set_xticks(x[::2])
        ax.grid(axis="y", alpha=.25)
        ax.set_xlabel("Ano")
    axes[0].set_ylabel("% da receita bruta reportada")
    axes[1].legend(frameon=False, loc="best")
    fig.suptitle("Composição da receita: tributação própria e transferências correntes", fontsize=13, fontweight="bold")
    fig.savefig(FIG / "estrutura_receitas.png", bbox_inches="tight")
    plt.close(fig)

    # 3. 2024 municipal expenditure composition by function; top-level functions only.
    rows24 = [r for r in function_rows if int(r["ano"]) == 2024]
    labels = sorted({r["funcao"] for r in rows24})
    fig, ax = plt.subplots(figsize=(10.8, 6.0), constrained_layout=True)
    y = np.arange(len(labels))
    h = .36
    for idx, city in enumerate(CITIES):
        vals = []
        subset = {r["funcao"]: num(r["despesa_empenhada_reais_2024_rs"]) / 1e6 for r in rows24 if r["municipio"] == city}
        vals = [subset.get(label, 0) for label in labels]
        ax.barh(y + (idx - .5) * h, vals, height=h, color=colors[city], label=city)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("R$ milhões, preços médios de 2024")
    ax.set_title("Despesa empenhada por função — 2024\n(valores reportados exceto intraorçamentárias)", fontweight="bold")
    ax.grid(axis="x", alpha=.22)
    ax.legend(frameon=False)
    fig.savefig(FIG / "despesas_funcao_2024.png", bbox_inches="tight")
    plt.close(fig)

    # 4. Belgian general-government balance and debt (% GDP), from Eurostat.
    years = [int(r["ano"]) for r in bel]
    deficit = [num(r["deficit_net_lending_pct_pib"]) for r in bel]
    debt = [num(r["divida_bruta_pct_pib"]) for r in bel]
    fig, ax = plt.subplots(figsize=(9.4, 4.8), constrained_layout=True)
    ax.plot(years, deficit, marker="o", linewidth=2.2, color="#146C94", label="Capacidade (+) / necessidade (−) de financiamento")
    ax.plot(years, debt, marker="s", linewidth=2.2, color="#C0443B", label="Dívida bruta Maastricht")
    ax.axhline(0, color="#666666", linewidth=.8)
    ax.set_xticks(years)
    ax.set_ylabel("% do PIB")
    ax.set_title("Governo geral da Bélgica — contas e dívida", fontweight="bold")
    ax.grid(axis="y", alpha=.22)
    ax.legend(frameon=False, loc="best")
    fig.savefig(FIG / "belgica_fiscal.png", bbox_inches="tight")
    plt.close(fig)

    # Machine-readable build summary.
    summary = {
        "municipal_rows": len(municipal), "function_rows": len(function_rows),
        "function_years": sorted({int(r["ano"]) for r in function_rows}),
        "belgium_rows": len(bel), "deflator": "IPCA, média anual; reais de 2024 = valor nominal × média do índice em 2024 / média do índice no ano",
        "correlation_caution": "n=10 níveis e n=9 primeiras diferenças por município; correlações descritivas, sem inferência causal; séries temporais curtas e autocorrelação possível.",
        "figures": ["receitas_despesas_reais.png", "estrutura_receitas.png", "despesas_funcao_2024.png", "belgica_fiscal.png"],
    }
    (AN / "resumo_execucao.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
