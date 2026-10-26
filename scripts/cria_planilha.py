#!/usr/bin/env python3
"""Cria a planilha auditável da P2, com fontes, fórmulas e rastreabilidade."""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.data_source import AxDataSource, NumDataSource, NumRef
from openpyxl.chart.series import SeriesLabel
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.dimensions import ColumnDimension

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "brutos"
TRT = ROOT / "data" / "tratados"
AN = ROOT / "analise"
OUT = ROOT / "base_atualizada_222036963.xlsx"
AS_OF = "2026-10-25"
CITIES = {"Arcoverde/PE": "2601201", "Araripina/PE": "2601102"}
BLUE = "0000FF"
BLACK = "000000"
GREEN = "008000"
DARK_GREEN = "135B44"
LIGHT_GREEN = "CFE9E0"
LIGHT_GRAY = "E7E5E4"
WHITE = "FFFFFF"
THIN_GRAY = Side(style="thin", color="A6A6A6")
TOP_BORDER = Border(top=Side(style="thin", color="444444"))
KEY_BORDER = Border(top=Side(style="medium", color="222222"))
DOUBLE_BOTTOM = Border(top=Side(style="thin", color="222222"), bottom=Side(style="double", color="222222"))


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def number(v):
    if v in (None, ""):
        return None
    try:
        return float(Decimal(str(v)))
    except Exception:
        return None


def cite_comment(text):
    return Comment(text, "Fonte dos dados")


def cell_source(cell, value, source):
    cell.value = value
    cell.font = Font(name="Aptos", size=10, color=BLUE)
    cell.comment = cite_comment(source)
    cell.alignment = Alignment(vertical="top")


def formula(cell, value, linked=False, number_format=None):
    cell.value = value
    cell.font = Font(name="Aptos", size=10, color=GREEN if linked else BLACK)
    cell.alignment = Alignment(horizontal="right" if number_format else "left", vertical="top")
    if number_format:
        cell.number_format = number_format


def add_sheet_shell(ws, title, subtitle, units, last_col, last_row):
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins.left = .25
    ws.page_margins.right = .25
    ws.page_margins.top = .5
    ws.page_margins.bottom = .5
    ws.oddFooter.center.text = "&A | Página &P"
    ws.print_area = f"B2:{get_column_letter(last_col)}{max(last_row, 8)}"
    ws.print_title_rows = "8:8"
    for col in (1, 2):
        ws.column_dimensions[get_column_letter(col)].width = 20
    for col in range(3, last_col + 1):
        c = ws.cell(3, col)
        c.fill = PatternFill("solid", fgColor=DARK_GREEN)
        c.font = Font(name="Aptos Display", size=16 if col == 3 else 10, bold=True, color=WHITE)
    ws.cell(3, 3, title)
    ws.cell(3, 3).font = Font(name="Aptos Display", size=16, bold=True, color=WHITE)
    ws.cell(5, 3, subtitle)
    ws.cell(5, 3).font = Font(name="Aptos", size=11, bold=True, color=BLACK)
    ws.cell(6, 3, units)
    ws.cell(6, 3).font = Font(name="Aptos", size=10, italic=True, color=BLACK)
    for cell in ws[8]:
        if cell.column >= 3 and cell.column <= last_col:
            cell.fill = PatternFill("solid", fgColor=LIGHT_GREEN)
            cell.font = Font(name="Aptos", size=10, bold=True, color=BLACK)
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            cell.border = Border(bottom=THIN_GRAY)
    ws.row_dimensions[8].height = 34


def finish_sheet(ws, last_col, last_row):
    # Excel's bestFit flag plus measured widths ensure readable output in common viewers.
    for col in range(3, last_col + 1):
        letter = get_column_letter(col)
        max_len = 10
        for row in range(3, last_row + 1):
            value = ws.cell(row, col).value
            if value is not None:
                text = str(value)
                max_len = max(max_len, min(52, max((len(x) for x in text.splitlines()), default=len(text))))
        ws.column_dimensions[letter].bestFit = True
        ws.column_dimensions[letter].width = max(12, min(48, max_len + 2))
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"B2:{get_column_letter(last_col)}{max(last_row, 8)}"
    ws.auto_filter.ref = f"C8:{get_column_letter(last_col)}{last_row}" if last_row >= 9 else None


def source_url_dca(code, year):
    return f"https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/dca?an_exercicio={year}&id_ente={code}"


def main():
    wb = Workbook()
    summary = wb.active
    summary.title = "Resumo"
    dca = wb.create_sheet("Dados DCA")
    ibge = wb.create_sheet("Dados IBGE")
    be = wb.create_sheet("Bélgica")
    calc = wb.create_sheet("Cálculos Municipais")
    func = wb.create_sheet("Funções")
    sources = wb.create_sheet("Fontes e Métodos")
    tests = wb.create_sheet("Validação")
    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True
    wb.calculation.calcMode = "auto"

    # Raw DCA lines selected by indicator; each hardcoded cell gets an audit comment.
    dca_rows = csv_rows(TRT / "linhas_contas_selecionadas.csv")
    dca_headers = ["Município", "Código IBGE", "Ano", "Indicador", "Arquivo de origem", "Anexo",
                   "Código da conta", "Conta", "Coluna contábil", "Valor (R$ correntes)", "Rótulo do quadro"]
    for j, h in enumerate(dca_headers, 3):
        dca.cell(8, j, h)
    for i, r in enumerate(dca_rows, 9):
        code = r["codigo_ibge"]
        year = r["ano"]
        url = source_url_dca(code, year)
        note = (f"Fonte: Siconfi/STN, API DCA; consulta anual. Exercício {year}; município {r['municipio']} "
                f"(código IBGE {code}); anexo {r['anexo']}; conta {r['cod_conta']} / {r['conta']}; "
                f"coluna {r['coluna']}; indicador de seleção {r['indicador']}. URL: {url}. "
                f"Arquivo preservado: data/brutos/{r['arquivo_fonte']}. Consulta da base: {AS_OF}.")
        values = [r["municipio"], int(code), int(year), r["indicador"], r["arquivo_fonte"], r["anexo"],
                  r["cod_conta"], r["conta"], r["coluna"], number(r["valor"]), r["rotulo"]]
        for j, value in enumerate(values, 3):
            cell_source(dca.cell(i, j), value, note)
        dca.cell(i, 4).number_format = "0"
        dca.cell(i, 5).number_format = "0"
        dca.cell(i, 12).number_format = '#,##0.00;(#,##0.00);-'
    add_sheet_shell(dca, "Dados-fonte — Siconfi DCA", "Linhas selecionadas para construir os indicadores municipais; não some indicadores distintos.",
                    "R$ correntes; manter separadas receitas brutas, deduções e estágios da despesa.", 13, 8 + len(dca_rows))
    finish_sheet(dca, 13, 8 + len(dca_rows))

    # Raw IBGE series in long format; Censo 2022 is kept separately from annual estimates.
    ibge_rows = []
    pop = read_json(RAW / "ibge_pop_estimativas_2015_2024.json")
    for r in pop[1:]:
        if r.get("D1C") not in CITIES.values() or r.get("D2C") != "9324":
            continue
        city = next(k for k, v in CITIES.items() if v == r["D1C"])
        ibge_rows.append({"municipio": city, "codigo": r["D1C"], "ano": int(r["D3C"]), "mes": None,
                          "serie": "pop_estimada", "variavel": r["D2N"], "unidade": r["MN"], "valor": number(r["V"]),
                          "arquivo": "ibge_pop_estimativas_2015_2024.json", "url": "https://apisidra.ibge.gov.br/values/t/6579/n6/2601201,2601102/v/9324/p/2015-2024"})
    census = read_json(RAW / "ibge_censo2022_populacao.json")
    for r in census[1:]:
        if r.get("D1C") not in CITIES.values() or r.get("D2C") != "93":
            continue
        city = next(k for k, v in CITIES.items() if v == r["D1C"])
        ibge_rows.append({"municipio": city, "codigo": r["D1C"], "ano": 2022, "mes": None,
                          "serie": "pop_censo", "variavel": r["D2N"], "unidade": r["MN"], "valor": number(r["V"]),
                          "arquivo": "ibge_censo2022_populacao.json", "url": "https://apisidra.ibge.gov.br/values/t/4709/n6/2601201,2601102/v/93/p/2022"})
    gdp = read_json(RAW / "ibge_pib_municipal_2015_2023.json")
    for r in gdp[1:]:
        if r.get("D1C") not in CITIES.values() or r.get("D2C") != "37":
            continue
        city = next(k for k, v in CITIES.items() if v == r["D1C"])
        ibge_rows.append({"municipio": city, "codigo": r["D1C"], "ano": int(r["D3C"]), "mes": None,
                          "serie": "pib", "variavel": r["D2N"], "unidade": r["MN"], "valor": number(r["V"]),
                          "arquivo": "ibge_pib_municipal_2015_2023.json", "url": "https://apisidra.ibge.gov.br/values/t/5938/n6/2601201,2601102/v/37/p/2015-2023"})
    ipca = read_json(RAW / "ibge_ipca_mensal_2015_2024.json")
    for r in ipca[1:]:
        ibge_rows.append({"municipio": "Brasil", "codigo": "1", "ano": int(r["D3C"][:4]), "mes": int(r["D3C"][4:]),
                          "serie": "ipca", "variavel": r["D2N"], "unidade": r["MN"], "valor": number(r["V"]),
                          "arquivo": "ibge_ipca_mensal_2015_2024.json", "url": "https://apisidra.ibge.gov.br/values/t/1737/n1/1/v/2266/p/201501-202412"})
    ibge_headers = ["Município", "Código IBGE", "Ano", "Mês", "Série", "Variável", "Unidade", "Valor", "Arquivo de origem", "URL consultada"]
    for j, h in enumerate(ibge_headers, 3):
        ibge.cell(8, j, h)
    for i, r in enumerate(ibge_rows, 9):
        period = f"{r['ano']}-{r['mes']:02d}" if r["mes"] is not None else str(r["ano"])
        note = (f"Fonte: IBGE/SIDRA; tabela/variável selecionada conforme Série e Variável desta linha. "
                f"Período {period}; valor/unidade conforme resposta oficial. "
                f"Arquivo preservado: data/brutos/{r['arquivo']}. URL: {r['url']}. Consulta da base: {AS_OF}.")
        vals = [r["municipio"], r["codigo"], r["ano"], r["mes"], r["serie"], r["variavel"], r["unidade"], r["valor"], r["arquivo"], r["url"]]
        for j, value in enumerate(vals, 3):
            cell_source(ibge.cell(i, j), value, note)
        ibge.cell(i, 5).number_format = "0"
        ibge.cell(i, 6).number_format = "0"
        ibge.cell(i, 10).number_format = '#,##0.00;(#,##0.00);-'
    add_sheet_shell(ibge, "Dados-fonte — IBGE/SIDRA", "População, PIB municipal e IPCA mensal em formato longo.",
                    "População: pessoas; PIB: mil R$ correntes; IPCA: número-índice nacional.", 12, 8 + len(ibge_rows))
    finish_sheet(ibge, 12, 8 + len(ibge_rows))

    # Eurostat: Belgium, general government, annual ESA 2010 indicators as % GDP.
    eu = read_json(RAW / "eurostat_gov_10dd_edpt1_be.json")
    ids, sizes = eu["id"], eu["size"]
    idx = {dim: eu["dimension"][dim]["category"]["index"] for dim in ids}
    def euro_value(na_item, year):
        keys = {"freq": "A", "unit": "PC_GDP", "sector": "S13", "na_item": na_item, "geo": "BE", "time": str(year)}
        flat = 0
        for dim in ids:
            flat = flat * sizes[ids.index(dim)] + idx[dim][keys[dim]]
        return number(eu["value"].get(str(flat)))
    be.cell(8, 3, "Ano")
    be.cell(8, 4, "Saldo de financiamento líquido / PIB")
    be.cell(8, 5, "Dívida bruta consolidada / PIB")
    be.cell(8, 6, "Setor institucional")
    for year in range(2015, 2026):
        i = year - 2015 + 9
        for col, value, metric in [(3, year, "ano"), (4, euro_value("B9", year), "B9"), (5, euro_value("GD", year), "GD"), (6, "S13 — Governo geral", "S13")]:
            note = (f"Fonte: Eurostat dataset gov_10dd_edpt1, Belgium (BE), annual, sector S13 general government, "
                    f"unit PC_GDP, item {metric}, year {year}; ESA 2010/EDP metadata. "
                    f"Arquivo preservado: data/brutos/eurostat_gov_10dd_edpt1_be.json. "
                    "URL: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/gov_10dd_edpt1?geo=BE. "
                    f"Consulta da base: {AS_OF}.")
            cell_source(be.cell(i, col), value, note)
        be.cell(i, 4).number_format = '0.0;(0.0);-'
        be.cell(i, 5).number_format = '0.0;(0.0);-'
    add_sheet_shell(be, "Bélgica — governo geral", "Eurostat gov_10dd_edpt1; não equiparar a contas municipais brasileiras.",
                    "% do PIB; saldo negativo = necessidade líquida de financiamento; dívida é estoque consolidado.", 6, 19)
    finish_sheet(be, 6, 19)

    # Formula-driven annual municipal series (cross-sheet links green, same-sheet calculations black).
    calc_headers = ["Município", "Ano", "Receita bruta reportada", "Dedução FUNDEB", "Outras deduções reportadas",
                    "Receita líquida após deduções reportadas", "Despesa empenhada total", "Despesa liquidada total",
                    "Despesa paga total", "Despesa empenhada exceto intra", "Despesa intra residual",
                    "Receita tributária própria", "Transferências correntes totais", "Proxy transferências intergovernamentais correntes",
                    "População", "PIB municipal", "IPCA média anual", "Fator deflator 2024", "Receita bruta real",
                    "Despesa empenhada real", "Receita real per capita", "Despesa real per capita",
                    "Receita tributária / receita bruta", "Transferências correntes / receita bruta",
                    "Receita bruta / PIB", "Despesa empenhada / PIB", "Receita exceto intra", "Receita intra"]
    for j, h in enumerate(calc_headers, 3):
        calc.cell(8, j, h)
    dca_start, dca_end = 9, 8 + len(dca_rows)
    ibge_start, ibge_end = 9, 8 + len(ibge_rows)
    dca_val = f"'Dados DCA'!$L${dca_start}:$L${dca_end}"
    dca_city = f"'Dados DCA'!$C${dca_start}:$C${dca_end}"
    dca_year = f"'Dados DCA'!$E${dca_start}:$E${dca_end}"
    dca_ind = f"'Dados DCA'!$F${dca_start}:$F${dca_end}"
    ibge_val = f"'Dados IBGE'!$J${ibge_start}:$J${ibge_end}"
    ibge_city = f"'Dados IBGE'!$C${ibge_start}:$C${ibge_end}"
    ibge_year = f"'Dados IBGE'!$E${ibge_start}:$E${ibge_end}"
    ibge_series = f"'Dados IBGE'!$G${ibge_start}:$G${ibge_end}"
    ibge_month = f"'Dados IBGE'!$F${ibge_start}:$F${ibge_end}"
    def dca_formula(row, indicator):
        return f'=IF(COUNTIFS({dca_city},$C{row},{dca_year},$D{row},{dca_ind},"{indicator}")=0,"",SUMIFS({dca_val},{dca_city},$C{row},{dca_year},$D{row},{dca_ind},"{indicator}"))'
    for n, (city, code) in enumerate(CITIES.items()):
        for year in range(2015, 2025):
            row = 9 + n * 10 + year - 2015
            cell_source(calc.cell(row, 3), city, "Fonte: cadastro oficial Siconfi/IBGE; identificação do município atribuída na P2.")
            cell_source(calc.cell(row, 4), year, f"Fonte: exercício fiscal informado na API Siconfi DCA; município {city}; {source_url_dca(code, year)}")
            # E-I: source-linked fiscal values, each formula ties to the selected raw DCA line.
            for col, ind in [(5,"receita_total_bruta"),(6,"deducao_fundeb"),(7,"outras_deducoes"),
                             (9,"despesa_empenhada_total"),(10,"despesa_liquidada_total"),(11,"despesa_paga_total"),
                             (12,"despesa_empenhada_exceto_intra"),(14,"receita_tributaria_propria_bruta"),
                             (15,"transferencias_correntes_total_brutas"),(16,"transferencias_intergov_correntes_proxy"),
                             (29,"receita_exceto_intra_bruta"),(30,"receita_intra_bruta")]:
                expr = dca_formula(row, ind)
                if ind in ("deducao_fundeb", "outras_deducoes"):
                    expr = expr.replace("SUMIFS(", "ABS(SUMIFS(").replace("))", ")))" , 1)
                formula(calc.cell(row, col), expr, linked=True, number_format='#,##0.00;(#,##0.00);-')
            formula(calc.cell(row, 8), f'=IF(OR(E{row}="",F{row}=""),"",E{row}-F{row}-IF(G{row}="",0,G{row}))', number_format='#,##0.00;(#,##0.00);-')
            formula(calc.cell(row, 13), f'=IF(OR(I{row}="",L{row}=""),"",I{row}-L{row})', number_format='#,##0.00;(#,##0.00);-')
            # Population chooses Censo 2022; otherwise the annual July estimate.
            pop_formula = (f'=IF(COUNTIFS({ibge_city},$C{row},{ibge_year},$D{row},{ibge_series},"pop_censo")>0,'
                           f'SUMIFS({ibge_val},{ibge_city},$C{row},{ibge_year},$D{row},{ibge_series},"pop_censo"),'
                           f'IF(COUNTIFS({ibge_city},$C{row},{ibge_year},$D{row},{ibge_series},"pop_estimada")=0,"",'
                           f'SUMIFS({ibge_val},{ibge_city},$C{row},{ibge_year},$D{row},{ibge_series},"pop_estimada")))')
            formula(calc.cell(row, 17), pop_formula, linked=True, number_format='#,##0;(#,##0);-')
            gdp_formula = (f'=IF(COUNTIFS({ibge_city},$C{row},{ibge_year},$D{row},{ibge_series},"pib")=0,"",'
                           f'SUMIFS({ibge_val},{ibge_city},$C{row},{ibge_year},$D{row},{ibge_series},"pib")*1000)')
            formula(calc.cell(row, 18), gdp_formula, linked=True, number_format='#,##0.00;(#,##0.00);-')
            ipca_formula = (f'=IF(COUNTIFS({ibge_year},$D{row},{ibge_series},"ipca")<>12,"",'
                             f'SUMIFS({ibge_val},{ibge_year},$D{row},{ibge_series},"ipca")/12)')
            formula(calc.cell(row, 19), ipca_formula, linked=True, number_format='0.0000')
            # Deflator uses annual average IPCA and real values are annual flow approximations.
            formula(calc.cell(row, 20), f'=IF(OR(S{row}="",S{row}=0),"",AVERAGEIFS({ibge_val},{ibge_year},2024,{ibge_series},"ipca")/S{row})', linked=True, number_format='0.0000')
            formula(calc.cell(row, 21), f'=IF(OR(E{row}="",T{row}=""),"",E{row}*T{row})', number_format='#,##0.00;(#,##0.00);-')
            formula(calc.cell(row, 22), f'=IF(OR(I{row}="",T{row}=""),"",I{row}*T{row})', number_format='#,##0.00;(#,##0.00);-')
            formula(calc.cell(row, 23), f'=IF(OR(Q{row}="",Q{row}=0,U{row}=""),"",U{row}/Q{row})', number_format='#,##0.00;(#,##0.00);-')
            formula(calc.cell(row, 24), f'=IF(OR(Q{row}="",Q{row}=0,V{row}=""),"",V{row}/Q{row})', number_format='#,##0.00;(#,##0.00);-')
            formula(calc.cell(row, 25), f'=IF(OR(E{row}="",E{row}=0,N{row}=""),"",N{row}/E{row})', number_format='0.0%')
            formula(calc.cell(row, 26), f'=IF(OR(E{row}="",E{row}=0,O{row}=""),"",O{row}/E{row})', number_format='0.0%')
            formula(calc.cell(row, 27), f'=IF(OR(R{row}="",R{row}=0,E{row}=""),"",E{row}/R{row})', number_format='0.0%')
            formula(calc.cell(row, 28), f'=IF(OR(R{row}="",R{row}=0,I{row}=""),"",I{row}/R{row})', number_format='0.0%')
            for col in [4]:
                calc.cell(row, col).number_format = "0"
    add_sheet_shell(calc, "Série municipal — fórmulas", "Linhas anuais; fórmulas ligam cada indicador às fontes brutas e explicitam a cobertura.",
                    "R$ correntes ou R$ médios de 2024 conforme coluna; população em pessoas; razões em %.", 30, 28)
    finish_sheet(calc, 30, 28)
    calc.auto_filter.ref = f"C8:AD28"

    # Functional expenditure sheet links each top-level DCA function to its selected source line.
    frows = csv_rows(TRT / "despesas_por_funcao_2017_2024.csv")
    func_headers = ["Município", "Ano", "Código da função", "Função", "Despesa empenhada exceto intra nominal",
                    "Despesa em reais médios de 2024", "Participação na despesa funcional", "Arquivo DCA"]
    for j, h in enumerate(func_headers, 3):
        func.cell(8, j, h)
    for i, r in enumerate(frows, 9):
        c = r["municipio"]
        y = int(r["ano"])
        code = r["codigo_funcao"]
        cell_source(func.cell(i, 3), c, "Fonte: identificação do município na P2; códigos IBGE oficiais documentados em Fontes e Métodos.")
        cell_source(func.cell(i, 4), y, f"Fonte: exercício DCA {y}; {source_url_dca(CITIES[c], y)}")
        cell_source(func.cell(i, 5), code, f"Fonte: DCA-Anexo I-E, conta {code} - {r['funcao']}, função de despesa de primeiro nível.")
        cell_source(func.cell(i, 6), r["funcao"], f"Fonte: DCA-Anexo I-E, rótulo da função {code}; arquivo data/brutos/{r['fonte_arquivo']}.")
        # Exact source indicator for the function code, no parent + child roll-up.
        calc_formula = (f'=IF(COUNTIFS({dca_city},$C{i},{dca_year},$D{i},{dca_ind},"despesa_funcao_"&$E{i})=0,"",'
                        f'SUMIFS({dca_val},{dca_city},$C{i},{dca_year},$D{i},{dca_ind},"despesa_funcao_"&$E{i}))')
        formula(func.cell(i, 7), calc_formula, linked=True, number_format='#,##0.00;(#,##0.00);-')
        calc_row_start = 9
        calc_row_end = 28
        deflator = f"SUMIFS('Cálculos Municipais'!$T${calc_row_start}:$T${calc_row_end},'Cálculos Municipais'!$C${calc_row_start}:$C${calc_row_end},$C{i},'Cálculos Municipais'!$D${calc_row_start}:$D${calc_row_end},$D{i})"
        formula(func.cell(i, 8), f'=IF(OR(G{i}="",{deflator}=0),"",G{i}*{deflator})', linked=True, number_format='#,##0.00;(#,##0.00);-')
        total_nonintra = f'SUMIFS({dca_val},{dca_city},$C{i},{dca_year},$D{i},{dca_ind},"despesa_empenhada_exceto_intra")'
        formula(func.cell(i, 9), f'=IF(OR(G{i}="",{total_nonintra}=0),"",G{i}/{total_nonintra})', linked=True, number_format='0.0%')
        cell_source(func.cell(i, 10), r["fonte_arquivo"], f"Fonte: Siconfi DCA municipal do exercício {y}; {source_url_dca(CITIES[c], y)}")
    add_sheet_shell(func, "Despesa empenhada por função", "Funções de primeiro nível; seleção sem soma simultânea de conta-pai e filhas.",
                    "R$ correntes e R$ médios de 2024; participação sobre o total empenhado exceto intra.", 10, 8 + len(frows))
    finish_sheet(func, 10, 8 + len(frows))

    # Summary formulas refer to the calculation and Eurostat sheets.
    for j, h in enumerate(["Indicador", "Unidade", "Arcoverde/PE", "Araripina/PE", "Bélgica"], 3):
        summary.cell(8, j, h)
    summary_rows = [
        ("Receita bruta reportada — 2024", "R$ correntes", "E", 2024),
        ("Despesa empenhada total — 2024", "R$ correntes", "I", 2024),
        ("Receita bruta real — 2024", "R$ médios de 2024", "U", 2024),
        ("Despesa empenhada real — 2024", "R$ médios de 2024", "V", 2024),
        ("Crescimento real da receita, 2015–2024", "% acumulado", "U", "growth_rev"),
        ("Crescimento real da despesa empenhada, 2015–2024", "% acumulado", "V", "growth_exp"),
        ("Receita tributária / receita bruta — 2024", "%", "Y", 2024),
        ("Transferências correntes / receita bruta — 2024", "%", "Z", 2024),
        ("Receita bruta real per capita — 2024", "R$ 2024/habitante", "W", 2024),
        ("Despesa empenhada real per capita — 2024", "R$ 2024/habitante", "X", 2024),
        ("População — 2024", "pessoas", "Q", 2024),
        ("PIB municipal — 2023", "R$ correntes", "R", 2023),
        ("Saldo de financiamento líquido — 2025", "% do PIB", "B9", "belgium_def"),
        ("Dívida bruta consolidada — 2025", "% do PIB", "GD", "belgium_debt"),
    ]
    for i, (label, unit, col, year) in enumerate(summary_rows, 9):
        summary.cell(i, 3, label)
        summary.cell(i, 4, unit)
        if year in ("growth_rev", "growth_exp"):
            calc_col = col
            real_col = "U" if year == "growth_rev" else "V"
            for city_col, city in [(5, "Arcoverde/PE"), (6, "Araripina/PE")]:
                start = f'SUMIFS(\'Cálculos Municipais\'!${real_col}$9:${real_col}$28,\'Cálculos Municipais\'!$C$9:$C$28,"{city}",\'Cálculos Municipais\'!$D$9:$D$28,2015)'
                end = f'SUMIFS(\'Cálculos Municipais\'!${real_col}$9:${real_col}$28,\'Cálculos Municipais\'!$C$9:$C$28,"{city}",\'Cálculos Municipais\'!$D$9:$D$28,2024)'
                formula(summary.cell(i, city_col), f'=IFERROR({end}/{start}-1,"")', linked=True, number_format='0.0%')
            summary.cell(i, 7, "não aplicável")
        elif year == "belgium_def":
            formula(summary.cell(i, 7), "='Bélgica'!D19", linked=True, number_format='0.0;(0.0);-')
        elif year == "belgium_debt":
            formula(summary.cell(i, 7), "='Bélgica'!E19", linked=True, number_format='0.0;(0.0);-')
        else:
            for city_col, city in [(5, "Arcoverde/PE"), (6, "Araripina/PE")]:
                formula(summary.cell(i, city_col), f'=SUMIFS(\'Cálculos Municipais\'!${col}$9:${col}$28,\'Cálculos Municipais\'!$C$9:$C$28,"{city}",\'Cálculos Municipais\'!$D$9:$D$28,{year})', linked=True,
                        number_format='0' if col == 'Q' else ('0.0%' if col in ('Y','Z') else '#,##0.00;(#,##0.00);-'))
            summary.cell(i, 7, "—")
    add_sheet_shell(summary, "Resumo analítico", "Valores derivados por fórmulas; indicadores de Brasil municipal e Bélgica permanecem em níveis institucionais distintos.",
                    "Consulte unidade por linha. R$ correntes e R$ médios de 2024 não são intercambiáveis.", 7, 22)
    finish_sheet(summary, 7, 23)
    summary.cell(24, 3, "Nota: não se calcula superávit/déficit municipal a partir de receita bruta e despesa empenhada sem harmonização completa das deduções; PIB municipal termina em 2023 e população anual falta em 2023.")
    summary.merge_cells("C24:G25")
    summary.cell(24, 3).alignment = Alignment(wrap_text=True, vertical="top")
    summary.cell(24, 3).font = Font(name="Aptos", size=10, italic=True, color=BLACK)
    summary.row_dimensions[24].height = 30

    # Add a paired line chart to the summary, using the formula-driven series.
    chart = LineChart()
    chart.title = "Fluxos fiscais reais (R$ médios de 2024)"
    chart.y_axis.title = "R$"
    chart.x_axis.title = "Ano"
    chart.style = 13
    chart.height = 7.5
    chart.width = 14
    for city, start_row, color in [("Arcoverde/PE", 9, "145A75"), ("Araripina/PE", 19, "B65C2E")]:
        for col, title in [(21, f"Receita real — {city}"), (22, f"Despesa real — {city}")]:
            data = Reference(calc, min_col=col, min_row=start_row, max_row=start_row + 9)
            chart.add_data(data, titles_from_data=False, from_rows=False)
            s = chart.series[-1]
            # Each pair of municipal blocks shares the same 2015–2024 categories.
            s.val = NumDataSource(numRef=NumRef(f=f"'Cálculos Municipais'!${get_column_letter(col)}${start_row}:${get_column_letter(col)}${start_row+9}"))
            s.cat = AxDataSource(numRef=NumRef(f="'Cálculos Municipais'!$D$9:$D$18"))
            s.tx = SeriesLabel(v=title)
            s.graphicalProperties.line.solidFill = color if col == 21 else ("26734D" if city == "Arcoverde/PE" else "8C5AA7")
            s.graphicalProperties.line.width = 22000
    summary.add_chart(chart, "C27")

    # Compact source/method documentation inside the workbook.
    method_rows = [
        ("Fonte", "Uso e URL"),
        ("Siconfi/STN DCA", "Contas anuais municipais — consulta DCA por exercício e código IBGE; 20 respostas JSON em data/brutos. https://apidatalake.tesouro.gov.br/docs/siconfi/"),
        ("Receita", "Total bruto reportado; FUNDEB/outros descontos registrados em campos separados. Líquido após deduções reportadas não é necessariamente líquido completo quando outra dedução não aparece."),
        ("Despesa", "Empenhada, liquidada e paga são estágios distintos; as séries não são misturadas. Valor total e valor exceto intra aparecem separadamente."),
        ("Transferências", "Transferências correntes totais são uma rubrica ampla. Proxy intergovernamental mantém quebra de classificação: agregado antigo 2015–2017; contas de União + Estados de primeiro nível a partir de 2018."),
        ("Tributação própria", "Receitas tributárias municipais brutas conforme código selecionado no DCA; proporção dividida por receita bruta total reportada."),
        ("IBGE/SIDRA população", "Tabela 6579, variável 9324, estimativa de referência 1º de julho; 2022 substituída pelo Censo 2022, tabela 4709, variável 93. Faltam estimativas na série extraída em 2023."),
        ("IBGE/SIDRA PIB", "Tabela 5938, variável 37, PIB municipal a preços correntes, unidade mil R$; multiplicar por 1.000 para R$. Cobertura 2015–2023; sem valor de 2024."),
        ("IBGE/SIDRA IPCA", "Tabela 1737, variável 2266, número-índice mensal Brasil; fator t = média mensal de 2024 / média mensal do ano t; real de 2024 = nominal × fator."),
        ("Eurostat", "gov_10dd_edpt1; Belgium (BE), annual, sector S13 General government, unit PC_GDP; B9 net lending/borrowing e GD consolidated gross debt. https://ec.europa.eu/eurostat/databrowser/product/view/gov_10dd_edpt1"),
        ("Ausências", "Valor ausente permanece vazio; não se converte ausência em zero. Série funcional está disponível de 2017 a 2024; 2015–2016 não aparecem nos quadros funcionais recuperados."),
        ("Unidades institucionais", "Bélgica: governo geral nacional, ESA 2010; Brasil: municípios. PIB/percentuais são indicadores de escala, não equivalência de competências ou regime fiscal."),
        ("Data da coleta", AS_OF),
    ]
    for j, h in enumerate(["Tópico", "Definição, critério ou fonte"], 3):
        sources.cell(8, j, h)
    for i, (a, b) in enumerate(method_rows[1:], 9):
        sources.cell(i, 3, a)
        sources.cell(i, 4, b)
        sources.cell(i, 3).font = Font(name="Aptos", size=10, bold=True, color=BLACK)
        sources.cell(i, 4).alignment = Alignment(wrap_text=True, vertical="top")
        sources.row_dimensions[i].height = 36 if len(b) > 120 else 26
    add_sheet_shell(sources, "Fontes e métodos", "Definições de medição, cobertura, transformação e limitações incorporadas à planilha.",
                    "Consulte os arquivos JSON/CSV originais em data/brutos e os scripts em scripts/.", 4, 8 + len(method_rows) - 1)
    finish_sheet(sources, 4, 8 + len(method_rows) - 1)

    # Validation evidence in workbook.
    validation = (TRT / "relatorio_validacao.txt").read_text(encoding="utf-8").splitlines()
    for j, h in enumerate(["Verificação", "Resultado"], 3):
        tests.cell(8, j, h)
    for i, line in enumerate(validation, 9):
        tests.cell(i, 3, f"Controle {i-8}")
        tests.cell(i, 4, line)
        tests.cell(i, 4).alignment = Alignment(wrap_text=True, vertical="top")
        tests.row_dimensions[i].height = 24
    add_sheet_shell(tests, "Validação automática", "Testes executados contra dados tratados e observações de cobertura.",
                    "Ver scripts/validacao.py e data/tratados/relatorio_validacao.txt.", 4, 8 + len(validation))
    finish_sheet(tests, 4, 8 + len(validation))

    # Consistent font, number alignment, formula colors, no freeze panes on multi-sheet output.
    for ws in wb.worksheets:
        ws.freeze_panes = None
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    if cell.font.name is None:
                        cell.font = Font(name="Aptos", size=10, color=BLACK)
                    if isinstance(cell.value, (int, float)) or (isinstance(cell.value, str) and cell.value.startswith("=")):
                        if cell.row >= 9:
                            cell.alignment = Alignment(horizontal="right", vertical="top", wrap_text=cell.alignment.wrap_text)
        ws.sheet_view.zoomScale = 85
    # Ensure chart and summary note are within the print layout.
    summary.print_area = "B2:G25"
    wb.active = 0
    wb.save(OUT)
    libreoffice = shutil.which("libreoffice")
    if libreoffice:
        with tempfile.TemporaryDirectory(prefix="p2-xlsx-recalc-") as tmp:
            proc = subprocess.run([libreoffice, "--headless", "--convert-to", "xlsx", "--outdir", tmp, str(OUT)],
                                  capture_output=True, text=True, timeout=120)
            recalculated = Path(tmp) / OUT.name
            if proc.returncode == 0 and recalculated.exists():
                shutil.copy2(recalculated, OUT)
                print("Fórmulas recalculadas com LibreOffice.")
            else:
                print(f"AVISO: recálculo LibreOffice não concluído; retorno={proc.returncode}; {proc.stderr[-600:]}")
    # Re-open once to ensure the produced artifact is parseable before recalculation.
    check = load_workbook(OUT, data_only=False, read_only=False)
    assert check.sheetnames == ["Resumo", "Dados DCA", "Dados IBGE", "Bélgica", "Cálculos Municipais", "Funções", "Fontes e Métodos", "Validação"]
    check.close()
    print(f"Criada {OUT} ({OUT.stat().st_size:,} bytes); abas={len(wb.sheetnames)}; linhas DCA={len(dca_rows)}; IBGE={len(ibge_rows)}; funções={len(frows)}")


if __name__ == "__main__":
    main()
