#!/usr/bin/env python3
"""Harmoniza dados oficiais locais; preserva ausências e registra as linhas fonte."""
from __future__ import annotations

import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "brutos"
OUT = ROOT / "data" / "tratados"
CITIES = {"arcoverde": (2601201, "Arcoverde/PE"), "araripina": (2601102, "Araripina/PE")}
D = Decimal


def number(x):
    if x is None or x == "" or str(x).strip() in {"...", "-", "x", "X"}:
        return None
    try:
        return D(str(x))
    except (InvalidOperation, ValueError):
        return None


def decimal_sum(values):
    values = list(values)
    return sum(values, D("0")) if values else None


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: ("" if row.get(k) is None else str(row.get(k))) for k in fieldnames})


def exact_code(pattern, code):
    return re.fullmatch(pattern, str(code or "")) is not None


def select_one(rows, *, code=None, code_re=None, column=None, account=None):
    found = []
    for r in rows:
        if code is not None and r.get("cod_conta") != code:
            continue
        if code_re is not None and not exact_code(code_re, r.get("cod_conta")):
            continue
        if column is not None and r.get("coluna") != column:
            continue
        if account is not None and r.get("conta") != account:
            continue
        found.append(r)
    if len(found) > 1:
        raise ValueError(f"Conta ambígua: {[{k:x.get(k) for k in ('cod_conta','conta','coluna','valor')} for x in found]}")
    return found[0] if found else None


def parse_eurostat(path):
    data = read_json(path)
    ids, sizes = data["id"], data["size"]
    dims = data["dimension"]
    index = {dim: dims[dim]["category"]["index"] for dim in ids}
    values = data["value"]

    def get(indicator, year):
        keys = {"freq": "A", "unit": "PC_GDP", "sector": "S13", "na_item": indicator, "geo": "BE", "time": str(year)}
        flat = 0
        for dim in ids:
            flat = flat * sizes[ids.index(dim)] + index[dim][keys[dim]]
        return number(values.get(str(flat)))

    rows = []
    for year in range(2015, 2026):
        rows.append({
            "ano": year, "deficit_net_lending_pct_pib": get("B9", year),
            "divida_bruta_pct_pib": get("GD", year),
            "fonte": "Eurostat gov_10dd_edpt1; A; PC_GDP; S13; BE",
        })
    return rows


def population_map():
    pop = {}
    for r in read_json(RAW / "ibge_pop_estimativas_2015_2024.json")[1:]:
        value = number(r.get("V"))
        if value is not None:
            pop[(int(r["D1C"]), int(r["D3C"]))] = (int(value), "Estimativa IBGE, SIDRA 6579, v. 9324")
    for r in read_json(RAW / "ibge_censo2022_populacao.json")[1:]:
        value = number(r.get("V"))
        if value is not None:
            pop[(int(r["D1C"]), int(r["D3C"]))] = (int(value), "Censo Demográfico 2022, SIDRA 4709, v. 93")
    return pop


def gdp_map():
    out = {}
    for r in read_json(RAW / "ibge_pib_municipal_2015_2023.json")[1:]:
        if r.get("D2C") != "37":
            continue
        value = number(r.get("V"))
        if value is not None:
            out[(int(r["D1C"]), int(r["D3C"]))] = value  # R$ mil
    return out


def ipca_map():
    by_year = {}
    for r in read_json(RAW / "ibge_ipca_mensal_2015_2024.json")[1:]:
        value = number(r.get("V"))
        if value is not None:
            year = int(r["D3C"][:4])
            by_year.setdefault(year, []).append(value)
    if set(by_year) != set(range(2015, 2025)):
        raise ValueError(f"Cobertura anual IPCA inesperada: {sorted(by_year)}")
    annual = {}
    for y, values in by_year.items():
        if len(values) != 12:
            raise ValueError(f"IPCA {y}: esperados 12 meses, obtidos {len(values)}")
        annual[y] = sum(values, D("0")) / D(12)
    base = annual[2024]
    return annual, {y: base / v for y, v in annual.items()}


def normalize_deduction(r):
    """DCA mudou o sinal de apresentação; valor de dedução tratado como magnitude."""
    v = number(r.get("valor")) if r else None
    return abs(v) if v is not None else None


def process_municipality(city, code, populations, gdp, ipca_avg, deflators):
    rows_out, source_rows = [], []
    for year in range(2015, 2025):
        raw_path = RAW / f"siconfi_dca_{city}_{year}.json"
        dca = read_json(raw_path)
        if dca.get("hasMore"):
            raise ValueError(f"Resposta DCA incompleta: {raw_path.name}")
        items = dca["items"]
        ic = [r for r in items if r.get("anexo") == "DCA-Anexo I-C"]
        id_ = [r for r in items if r.get("anexo") == "DCA-Anexo I-D"]
        ie = [r for r in items if r.get("anexo") == "DCA-Anexo I-E"]

        # TotalReceitas é o total oficial nos exercícios; a DCA passa a abrir receitas
        # intra/extra a partir de 2019. A série mantém o total reportado e arquiva a abertura.
        gross_r = select_one(ic, code="TotalReceitas", column="Receitas Brutas Realizadas")
        fundeb_r = select_one(ic, code="TotalReceitas", column="Deduções - FUNDEB")
        other_r = select_one(ic, code="TotalReceitas", column="Outras Deduções da Receita")
        if not gross_r:
            raise ValueError(f"Total de receita ausente em {city}/{year}")
        gross = number(gross_r.get("valor"))
        fundeb = normalize_deduction(fundeb_r)
        other = normalize_deduction(other_r)
        known_ded = decimal_sum(v for v in (fundeb, other) if v is not None)
        net_after_reported = gross - known_ded if known_ded is not None else None

        total_exp = select_one(id_, code="TotalDespesas", column="Despesas Empenhadas", account="Total Geral da Despesa")
        liquid_exp = select_one(id_, code="TotalDespesas", column="Despesas Liquidadas", account="Total Geral da Despesa")
        paid_exp = select_one(id_, code="TotalDespesas", column="Despesas Pagas", account="Total Geral da Despesa")
        function_exp = select_one(ie, code="TotalDespesas", column="Despesas Empenhadas", account="Despesas Exceto Intraorçamentárias")
        function_liq = select_one(ie, code="TotalDespesas", column="Despesas Liquidadas", account="Despesas Exceto Intraorçamentárias")
        function_paid = select_one(ie, code="TotalDespesas", column="Despesas Pagas", account="Despesas Exceto Intraorçamentárias")
        intra_rev_r = select_one(ic, code="ReceitasIntraOrcamentarias", column="Receitas Brutas Realizadas")
        extra_rev_r = select_one(ic, code="ReceitasExcetoIntraOrcamentarias", column="Receitas Brutas Realizadas")

        tax_r = select_one(ic, code_re=r"RO1\.1\.0\.0\.00(?:\.0+){2}", column="Receitas Brutas Realizadas")
        transfer_current_r = select_one(ic, code_re=r"RO1\.7\.0\.0\.00(?:\.0+){2}", column="Receitas Brutas Realizadas")
        transfer_capital_r = select_one(ic, code_re=r"RO2\.4\.0\.0\.00(?:\.0+){2}", column="Receitas Brutas Realizadas")
        tax = number(tax_r.get("valor")) if tax_r else None
        transfer_current = number(transfer_current_r.get("valor")) if transfer_current_r else None
        transfer_capital = number(transfer_capital_r.get("valor")) if transfer_capital_r else None

        # Melhor indicador intergovernamental possível nos quadros publicados; há quebra
        # de classificação. Anos antigos usam o agregado explicitamente rotulado; a partir
        # de 2018 são somadas as contas federais e estaduais de primeiro nível.
        if year <= 2017:
            current_codes = ["RO1.7.2.0.00.00.00"]
            capital_codes = ["RO2.4.2.0.00.00.00"]
            transfer_rule = "2015-2017: agregado DCA 'Transferências Intergovernamentais'"
        else:
            current_codes = ["RO1.7.1.0.00.0.0", "RO1.7.2.0.00.0.0"]
            capital_codes = ["RO2.4.1.0.00.0.0", "RO2.4.2.0.00.0.0"]
            transfer_rule = "2018-2024: contas de primeiro nível União + Estados; convênios conforme classificação vigente"
        curr_sel = [select_one(ic, code=c, column="Receitas Brutas Realizadas") for c in current_codes]
        cap_sel = [select_one(ic, code=c, column="Receitas Brutas Realizadas") for c in capital_codes]
        intergov_current = sum((number(r["valor"]) for r in curr_sel), D("0")) if all(curr_sel) else None
        intergov_capital = sum((number(r["valor"]) for r in cap_sel), D("0")) if all(cap_sel) else None

        p = populations.get((code, year))
        pib = gdp.get((code, year))
        pop = p[0] if p else None
        ipca_factor = deflators.get(year)
        exp_nom = number(total_exp.get("valor")) if total_exp else None
        exp_liq = number(liquid_exp.get("valor")) if liquid_exp else None
        exp_pago = number(paid_exp.get("valor")) if paid_exp else None
        exp_nonintra = number(function_exp.get("valor")) if function_exp else None
        exp_nonintra_liq = number(function_liq.get("valor")) if function_liq else None
        exp_nonintra_paid = number(function_paid.get("valor")) if function_paid else None
        exp_intra_residual = exp_nom - exp_nonintra if exp_nom is not None and exp_nonintra is not None else None
        intra_rev = number(intra_rev_r.get("valor")) if intra_rev_r else None
        extra_rev = number(extra_rev_r.get("valor")) if extra_rev_r else None
        pib_rs = pib * D(1000) if pib is not None else None
        real_rev = gross * ipca_factor if ipca_factor is not None else None
        real_exp = exp_nom * ipca_factor if exp_nom is not None and ipca_factor is not None else None
        saldo_deductions_known = net_after_reported - exp_nom if net_after_reported is not None and exp_nom is not None else None

        row = {
            "municipio": CITIES[city][1], "codigo_ibge": code, "ano": year,
            "receita_bruta_total_reportada_rs": gross,
            "deducao_fundeb_magnitude_rs": fundeb,
            "outras_deducoes_reportadas_rs": other,
            "receita_liquida_apos_deducoes_reportadas_rs": net_after_reported,
            "deducoes_completude": "FUNDEB + outras deduções reportadas" if other_r else "FUNDEB reportado; outras deduções sem linha explícita",
            "receita_exceto_intra_bruta_rs": number(extra_rev_r.get("valor")) if extra_rev_r else None,
            "receita_intra_bruta_rs": intra_rev,
            "receita_tributaria_propria_bruta_rs": tax,
            "transferencias_correntes_total_brutas_rs": transfer_current,
            "transferencias_capital_total_brutas_rs": transfer_capital,
            "transferencias_intergov_correntes_proxy_brutas_rs": intergov_current,
            "transferencias_intergov_capital_proxy_brutas_rs": intergov_capital,
            "regra_conta_transferencia": transfer_rule,
            "despesa_empenhada_total_rs": exp_nom,
            "despesa_liquidada_total_rs": exp_liq,
            "despesa_paga_total_rs": exp_pago,
            "despesa_empenhada_exceto_intra_rs": exp_nonintra,
            "despesa_liquidada_exceto_intra_rs": exp_nonintra_liq,
            "despesa_paga_exceto_intra_rs": exp_nonintra_paid,
            "despesa_intra_residual_rs": exp_intra_residual,
            "saldo_receita_liquida_reportada_menos_empenho_rs": saldo_deductions_known,
            "populacao": pop,
            "fonte_populacao": p[1] if p else None,
            "pib_municipal_mil_rs": pib,
            "pib_municipal_rs": pib_rs,
            "ipca_media_anual_numero_indice": ipca_avg.get(year),
            "fator_deflator_para_reais_medios_2024": ipca_factor,
            "receita_bruta_total_reportada_reais_2024": real_rev,
            "despesa_empenhada_total_reais_2024": real_exp,
            "receita_bruta_total_reais_2024_per_capita": real_rev / D(pop) if real_rev is not None and pop else None,
            "despesa_empenhada_reais_2024_per_capita": real_exp / D(pop) if real_exp is not None and pop else None,
            "receita_tributaria_share_receita_bruta_pct": tax / gross * D(100) if tax is not None and gross else None,
            "transfer_correntes_share_receita_bruta_pct": transfer_current / gross * D(100) if transfer_current is not None and gross else None,
            "transfer_corr_capital_share_receita_bruta_pct": (transfer_current + transfer_capital) / gross * D(100) if transfer_current is not None and transfer_capital is not None and gross else None,
            "receita_bruta_pct_pib": gross / pib_rs * D(100) if gross is not None and pib_rs else None,
            "despesa_empenhada_pct_pib": exp_nom / pib_rs * D(100) if exp_nom is not None and pib_rs else None,
            "fonte_dca": raw_path.name,
        }
        rows_out.append(row)

        chosen = [
            ("receita_total_bruta", gross_r), ("deducao_fundeb", fundeb_r), ("outras_deducoes", other_r),
            ("despesa_empenhada_total", total_exp), ("despesa_liquidada_total", liquid_exp),
            ("despesa_paga_total", paid_exp), ("despesa_empenhada_exceto_intra", function_exp),
            ("despesa_liquidada_exceto_intra", function_liq), ("despesa_paga_exceto_intra", function_paid),
            ("receita_intra_bruta", intra_rev_r), ("receita_exceto_intra_bruta", extra_rev_r),
            ("receita_tributaria_propria_bruta", tax_r),
            ("transferencias_correntes_total_brutas", transfer_current_r),
            ("transferencias_capital_total_brutas", transfer_capital_r),
        ]
        chosen.extend(("transferencias_intergov_correntes_proxy", r) for r in curr_sel if r)
        chosen.extend(("transferencias_intergov_capital_proxy", r) for r in cap_sel if r)
        function_source_rows = [
            r for r in ie
            if r.get("coluna") == "Despesas Empenhadas"
            and r.get("rotulo") == "Total Geral da Despesa por Função"
            and re.match(r"^\d{2} - ", str(r.get("conta", "")))
        ]
        chosen.extend(("despesa_funcao_" + re.match(r"^(\d{2}) - ", str(r.get("conta", ""))).group(1), r)
                      for r in function_source_rows)
        for indicator, source in chosen:
            if not source:
                continue
            source_rows.append({
                "municipio": CITIES[city][1], "codigo_ibge": code, "ano": year,
                "indicador": indicator, "arquivo_fonte": raw_path.name, "anexo": source.get("anexo"),
                "cod_conta": source.get("cod_conta"), "conta": source.get("conta"),
                "coluna": source.get("coluna"), "valor": source.get("valor"),
                "rotulo": source.get("rotulo"),
            })
        # Se o quadro separa intra, soma do total funcional e do residual deve fechar com I-D.
        if exp_nom is not None and exp_nonintra is not None and exp_intra_residual is not None:
            if abs((exp_nonintra + exp_intra_residual) - exp_nom) > D("0.02"):
                raise AssertionError(f"Reconciliação I-D/I-E falhou em {city}/{year}")
    return rows_out, source_rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    populations, gdp = population_map(), gdp_map()
    ipca_avg, deflators = ipca_map()
    municipal, source_rows = [], []
    for city, (code, _) in CITIES.items():
        rows, sources = process_municipality(city, code, populations, gdp, ipca_avg, deflators)
        municipal.extend(rows)
        source_rows.extend(sources)
    write_csv(OUT / "municipais_2015_2024.csv", municipal)
    write_csv(OUT / "linhas_contas_selecionadas.csv", source_rows)
    write_csv(OUT / "ipca_anual.csv", [
        {"ano": y, "ipca_media_anual_numero_indice": ipca_avg[y],
         "fator_deflator_para_reais_medios_2024": deflators[y],
         "meses_observados": 12, "base": "IBGE/SIDRA tabela 1737, variável 2266"}
        for y in sorted(ipca_avg)
    ])
    belgium = parse_eurostat(RAW / "eurostat_gov_10dd_edpt1_be.json")
    write_csv(OUT / "belgica_2015_2025.csv", belgium)
    print(f"Municípios: {len(municipal)} observações; linhas-fonte selecionadas: {len(source_rows)}")
    print(f"População disponível: {sum(r['populacao'] is not None for r in municipal)}/{len(municipal)}")
    print(f"PIB disponível: {sum(r['pib_municipal_rs'] is not None for r in municipal)}/{len(municipal)}")
    print(f"Bélgica: {len(belgium)} anos")


if __name__ == "__main__":
    main()
