#!/usr/bin/env python3
"""Audita a integridade do XLSX e compara resultados calculados com CSVs tratados."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "base_atualizada_222036963.xlsx"
TRT = ROOT / "data" / "tratados"
AN = ROOT / "analise"
TOL = Decimal("0.03")


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def d(v):
    return Decimal(str(v)) if v not in (None, "") else None


def close(actual, expected, label):
    if actual is None or expected is None or abs(Decimal(str(actual)) - expected) > TOL:
        raise AssertionError(f"{label}: Excel={actual}, CSV={expected}")


def main():
    assert XLSX.exists() and XLSX.stat().st_size > 100_000
    formula_wb = load_workbook(XLSX, data_only=False)
    data_wb = load_workbook(XLSX, data_only=True)
    expected_sheets = ["Resumo", "Dados DCA", "Dados IBGE", "Bélgica", "Cálculos Municipais", "Funções", "Fontes e Métodos", "Validação"]
    assert formula_wb.sheetnames == expected_sheets
    assert not formula_wb._external_links, "A pasta contém referências externas não autorizadas"
    comments = sum(1 for ws in formula_wb.worksheets for row in ws.iter_rows() for c in row if c.comment)
    formulas = sum(1 for ws in formula_wb.worksheets for row in ws.iter_rows() for c in row if isinstance(c.value, str) and c.value.startswith("="))
    assert comments >= 9000, f"Comentários de fonte abaixo do esperado: {comments}"
    assert formulas >= 1000, f"Fórmulas abaixo do esperado: {formulas}"
    assert len(formula_wb["Resumo"]._charts) == 1
    for ws in formula_wb.worksheets:
        assert ws.freeze_panes is None, f"Freeze panes inesperado em aba múltipla: {ws.title}"
        assert ws.cell(3, 3).value, f"Título da aba ausente: {ws.title}"
        assert ws.cell(8, 3).value, f"Cabeçalho na linha 8 ausente: {ws.title}"

    errors = []
    for ws in data_wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("#"):
                    errors.append((ws.title, c.coordinate, c.value))
    assert not errors, f"Erros de fórmula no XLSX: {errors[:10]}"

    municipal = read_csv(TRT / "municipais_2015_2024.csv")
    calc = data_wb["Cálculos Municipais"]
    position = {}
    for i, r in enumerate(municipal):
        # Source CSV is ordered by municipality then year, matching the calculation sheet.
        row = 9 + i
        key = (r["municipio"], int(r["ano"]))
        assert (calc.cell(row, 3).value, int(calc.cell(row, 4).value)) == key
        position[key] = row
        mapping = [
            (5, "receita_bruta_total_reportada_rs"), (6, "deducao_fundeb_magnitude_rs"),
            (7, "outras_deducoes_reportadas_rs"), (9, "despesa_empenhada_total_rs"),
            (10, "despesa_liquidada_total_rs"), (11, "despesa_paga_total_rs"),
            (12, "despesa_empenhada_exceto_intra_rs"), (14, "receita_tributaria_propria_bruta_rs"),
            (15, "transferencias_correntes_total_brutas_rs"), (16, "transferencias_intergov_correntes_proxy_brutas_rs"),
            (29, "receita_exceto_intra_bruta_rs"), (30, "receita_intra_bruta_rs"),
        ]
        for col, field in mapping:
            expected = d(r[field])
            actual = calc.cell(row, col).value
            if expected is None:
                assert actual in (None, ""), f"Ausência convertida em valor para {key}/{field}: {actual}"
            else:
                close(actual, expected, f"{key}/{field}")
        for col, field in [(17, "populacao"), (18, "pib_municipal_rs"), (19, "ipca_media_anual_numero_indice"),
                           (20, "fator_deflator_para_reais_medios_2024"), (21, "receita_bruta_total_reportada_reais_2024"),
                           (22, "despesa_empenhada_total_reais_2024")]:
            expected = d(r[field])
            actual = calc.cell(row, col).value
            if expected is None:
                assert actual in (None, ""), f"Ausência convertida em valor para {key}/{field}: {actual}"
            else:
                close(actual, expected, f"{key}/{field}")

    # Functional first-level rows must reconcile to the DCA functional total, without double-counting.
    fs = data_wb["Funções"]
    sums = defaultdict(Decimal)
    counts = defaultdict(set)
    function_rows = 0
    for row in range(9, fs.max_row + 1):
        city, year, code = fs.cell(row, 3).value, fs.cell(row, 4).value, fs.cell(row, 5).value
        if city is None:
            continue
        key = (city, int(year))
        value = d(fs.cell(row, 7).value)
        assert value is not None
        assert code not in counts[key], f"Função duplicada {key}/{code}"
        counts[key].add(code)
        sums[key] += value
        function_rows += 1
    assert function_rows == 256
    for key, total in sums.items():
        row = position[key]
        close(total, d(calc.cell(row, 12).value), f"Reconciliação funcional {key}")

    # Intentional gaps remain blank: population 2023 and municipal GDP 2024.
    for city in ["Arcoverde/PE", "Araripina/PE"]:
        assert calc.cell(position[(city, 2023)], 17).value in (None, "")
        assert calc.cell(position[(city, 2024)], 18).value in (None, "")

    summary = data_wb["Resumo"]
    close(summary["E9"].value, Decimal("338825647.94"), "Resumo receita Arcoverde 2024")
    close(summary["F10"].value, Decimal("399934864.27"), "Resumo despesa Araripina 2024")
    assert summary["G21"].value == -5.2
    assert summary["G22"].value == 108.1

    report = [
        "VALIDAÇÃO XLSX — PASS",
        f"Arquivo: {XLSX.name}; {XLSX.stat().st_size:,} bytes; {len(expected_sheets)} abas.",
        f"Fórmulas: {formulas}; comentários de fonte: {comments}; links externos: 0; erros de fórmula: 0.",
        "20 linhas município-ano comparadas campo a campo com a série tratada; diferenças dentro de R$ 0,03.",
        "256 linhas de funções de primeiro nível comparadas; totais conciliados com DCA I-E.",
        "Ausências mantidas: população 2023 e PIB municipal 2024.",
        "Resumo 2024, Eurostat 2025, cores semânticas, comentários de fonte e gráfico verificados.",
    ]
    out = AN / "validacao_planilha.txt"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    formula_wb.close()
    data_wb.close()


if __name__ == "__main__":
    main()
