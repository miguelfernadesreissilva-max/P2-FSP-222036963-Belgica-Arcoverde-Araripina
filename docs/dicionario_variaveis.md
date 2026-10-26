# Dicionário de variáveis — base efetivamente analisada

**Período principal:** exercícios 2015–2024 para Arcoverde/PE e Araripina/PE. **Data de extração:** 25/10/2026. Todos os valores originais e os códigos de seleção estão em `data/brutos/` e `data/tratados/linhas_contas_selecionadas.csv`.

| Campo | Definição operacional | Unidade | Fonte e cobertura | Regra de cálculo / limitação |
|---|---|---|---|---|
| `receita_bruta_total_reportada_rs` | Total de receitas brutas realizadas no DCA, código `TotalReceitas` | R$ correntes | Siconfi DCA, 20/20 município-ano | Preserva o total oficialmente reportado. A partir de 2019 o total inclui receitas intraorçamentárias explicitadas; análises de receita intra/extra usam as linhas separadas. Não é receita líquida. |
| `receita_exceto_intra_bruta_rs` | Receita bruta realizada exceto intraorçamentária, conta `ReceitasExcetoIntraOrcamentarias` | R$ correntes | Siconfi DCA, disponível em 2019–2024 | Para 2015–2018 a DCA consultada não abre contas intra/extra; não se presume que ausência de abertura seja zero. |
| `receita_intra_bruta_rs` | Receita bruta intraorçamentária, conta `ReceitasIntraOrcamentarias` | R$ correntes | Siconfi DCA, disponível em 2019–2024 | Não somar novamente ao total; é uma decomposição do total reportado. |
| `deducao_fundeb_magnitude_rs` | Dedução FUNDEB apresentada como magnitude positiva | R$ correntes | Siconfi DCA, quando reportada | `abs(valor original)`; sinais originais preservados em `Dados DCA`. |
| `outras_deducoes_reportadas_rs` | Outras deduções explicitamente reportadas | R$ correntes | Siconfi DCA, cobertura variável | Vazio significa que a linha não foi reportada na consulta, não que o valor seja zero. |
| `receita_liquida_apos_deducoes_reportadas_rs` | Receita bruta menos FUNDEB e outras deduções que aparecem na DCA | R$ correntes | Cálculo local | `receita_bruta_total_reportada − FUNDEB − outras deduções reportadas`; denominação deliberadamente qualificada: a fonte pode não exibir todas as deduções em todos os anos. Não é usado para declarar resultado orçamentário. |
| `receita_tributaria_propria_bruta_rs` | Impostos, taxas e contribuições de melhoria (conta de primeiro nível selecionada) | R$ correntes | Siconfi DCA, 20/20 | Participação = receita tributária / receita bruta total reportada. Manter fora de qualquer soma que inclua o agregado total. |
| `transferencias_correntes_total_brutas_rs` | Transferências correntes totais (categoria econômica de primeiro nível) | R$ correntes | Siconfi DCA, 20/20 | Indicador amplo; inclui transferências que não são necessariamente intergovernamentais. Participação = total / receita bruta reportada. |
| `transferencias_capital_total_brutas_rs` | Transferências de capital totais | R$ correntes | Siconfi DCA, conforme classificação | Indicador distinto das transferências correntes. |
| `transferencias_intergov_correntes_proxy_brutas_rs` | Proxy de transferências intergovernamentais correntes | R$ correntes | Siconfi DCA, 20/20 | Quebra de classificação documentada: 2015–2017 usa agregado rotulado “Transferências Intergovernamentais”; 2018–2024 soma contas de primeiro nível de União e Estados. Não constitui série perfeitamente homogênea. |
| `despesa_empenhada_total_rs` | Total geral da despesa no estágio empenhado | R$ correntes | Siconfi DCA, 20/20 | Estágio empenhado; não misturar com liquidação ou pagamento. O total pode incluir intraorçamentárias. |
| `despesa_liquidada_total_rs` | Total geral da despesa no estágio liquidado | R$ correntes | Siconfi DCA, 20/20 | Mantida separada da empenhada e da paga. |
| `despesa_paga_total_rs` | Total geral da despesa no estágio pago | R$ correntes | Siconfi DCA, 20/20 | Mantida separada dos demais estágios. |
| `despesa_empenhada_exceto_intra_rs` | Total de despesa empenhada exceto intraorçamentária no Anexo I-E | R$ correntes | Siconfi DCA, 2017–2024 | Usada como denominador das participações funcionais; a soma das funções de primeiro nível foi testada contra este total. |
| `despesa_intra_residual_rs` | Diferença entre despesa empenhada total e empenhada exceto intra | R$ correntes | Cálculo local, 2017–2024 | `total empenhado − empenhado exceto intra`; residual de apresentação, não uma conta-filha a somar com o total. |
| `despesa_por_funcao` | Despesa empenhada de cada função de primeiro nível (`NN - rótulo`) | R$ correntes e R$ médios de 2024 | Siconfi DCA, 2017–2024 | Selecionar somente funções de primeiro nível do Anexo I-E; a soma reconcilia com o total funcional exceto intra. 2015–2016 não têm linhas funcionais na extração. |
| `populacao` | Estimativa anual do IBGE; em 2022, população residente do Censo | pessoas | IBGE/SIDRA, 18/20 observações | Estimativas 2015–2021 e 2024; Censo em 2022; 2023 ausente. Não interpolar nem substituir ausência por zero. |
| `pib_municipal_rs` | PIB municipal a preços correntes, variável 37 | R$ correntes | IBGE/SIDRA, 2015–2023, 18/20 | A fonte retorna mil R$; converter por `valor × 1.000`. Não inferir 2024. |
| `ipca_media_anual_numero_indice` | Média aritmética de 12 índices mensais nacionais | número-índice | IBGE/SIDRA, 2015–2024, 120 meses | Deflator nacional de consumo, não índice municipal nem índice específico de preços de insumos públicos. |
| `fator_deflator_para_reais_medios_2024` | Fator para trazer fluxos anuais a preços médios de 2024 | fator | Cálculo local | `média(IPCA mensal jan–dez/2024) ÷ média(IPCA mensal jan–dez/t)`; sem arredondar entre etapas. |
| `valor_real_2024` | Fluxo fiscal em reais médios de 2024 | R$ médios de 2024 | Cálculo local | `valor corrente × fator deflator`. Unidade compatível com o fluxo anual, não com estoque. |
| `valor_real_per_capita` | Fluxo real anual dividido pela população do respectivo ano | R$ médios de 2024 por habitante | Siconfi + IBGE, quando população disponível | `valor_real ÷ população`; fica vazio em 2023. |
| `receita_bruta_pct_pib` / `despesa_empenhada_pct_pib` | Fluxo anual fiscal dividido pelo PIB municipal a preços correntes | % do PIB municipal | Siconfi + IBGE, 2015–2023 | Numerador e denominador em preços correntes e ano coincidente. Ausente em 2024 por falta do PIB municipal. Indicadores de escala; não são saldo fiscal nem elasticidade. |
| `deficit_belgica_pct_pib` | Net lending (+) / net borrowing (−) do governo geral | % do PIB | Eurostat, 2015–2025 | Unidade `PC_GDP`, setor S13, ESA 2010. Valor negativo indica necessidade líquida de financiamento. |
| `divida_belgica_pct_pib` | Dívida bruta consolidada do governo geral | % do PIB | Eurostat, 2015–2025 | Estoque ao fim do período; não equivale ao fluxo anual municipal. |

## Regras para leitura

As séries de receita total e despesa total são examinadas separadamente. O artigo não calcula superávit ou déficit municipal subtraindo receita bruta de despesa empenhada, pois a cobertura das deduções e o tratamento intraorçamentário não estão harmonizados em todos os exercícios. Receita, despesa empenhada, despesa liquidada e despesa paga são conceitos diferentes.

A Bélgica é observada no nível do governo geral nacional; Arcoverde e Araripina são governos municipais brasileiros. Diferenças de competências, consolidação, classificações, moeda e escala impedem comparação direta de níveis. A análise usa séries temporais descritivas, não causalidade.

Nenhuma conta-pai é somada junto com descendentes. Os valores vazios representam ausência de observação ou abertura classificatória; não representam zero.