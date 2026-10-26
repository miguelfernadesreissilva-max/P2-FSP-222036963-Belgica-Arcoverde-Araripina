# Evidências de coleta e cobertura oficial

**Data das consultas:** 25/10/2026, America/Recife. Os arquivos brutos estão em `data/brutos/`; os manifestos registram URL/consulta, exercício, município, quantidade de registros e SHA-256.

## Siconfi — DCA municipal

Foram obtidas as 20 combinações município-ano entre Arcoverde (código IBGE `2601201`) e Araripina (`2601102`), 2015–2024. Cada resposta do endpoint oficial DCA retornou `hasMore=false`; as 20 respostas incluem 20.618 linhas. Os arquivos `siconfi_dca_{arcoverde|araripina}_{ano}.json` são dados brutos integrais. A extração de linhas para os indicadores selecionados soma 556 registros em `data/tratados/linhas_contas_selecionadas.csv`.

Exemplos de consulta: [Arcoverde 2024](https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/dca?an_exercicio=2024&id_ente=2601201) e [Araripina 2024](https://apidatalake.tesouro.gov.br/ords/cdwhprd/siconfi/tt/dca?an_exercicio=2024&id_ente=2601102). O Anexo I-C contém receitas e deduções; o I-D contém execução por estágio; o I-E contém despesa por função. Os códigos, colunas e rótulos usados estão no CSV de linhagem.

Em 2024, Arcoverde reporta R$ 338.825.647,94 de receita bruta total, decomposta em R$ 327.484.071,00 exceto intra e R$ 11.341.576,94 intra. A despesa empenhada total é R$ 317.259.552,36; no Anexo I-E, a despesa empenhada exceto intra é R$ 306.654.812,31. Esses fluxos têm bases distintas se comparados sem ajuste. Para Araripina, em 2024, a receita bruta total é R$ 406.750.338,20, sendo R$ 377.202.550,76 exceto intra e R$ 29.547.787,44 intra; a despesa empenhada total é R$ 399.934.864,27, e a exceto intra é R$ 368.226.167,64.

FUNDEB e outras deduções são preservadas em campos separados. Em Arcoverde/2024 a DCA reporta R$ 21.887.725,46 de FUNDEB e R$ 27.457,17 de outras deduções. O campo líquido derivado desconta somente as linhas reportadas e não é tratado como líquido completo quando a cobertura não está completa. Por isso, o artigo não calcula superávit ou déficit municipal por simples subtração de receita bruta e despesa empenhada.

A abertura explícita de receita intra/extra está disponível em 2019–2024. Em 2015–2018, o quadro apresenta `TotalReceitas`, sem a decomposição intra/extra recuperada; não se assume que a ausência de abertura equivalha a saldo zero. A despesa empenhada por função de primeiro nível está disponível em 2017–2024; em cada município-ano, as funções selecionadas somam exatamente a despesa empenhada exceto intra do Anexo I-E. Não há linha funcional recuperada para 2015–2016.

O campo de população informado no DCA não foi usado como denominador per capita. Por exemplo, para Arcoverde em 2024, a DCA registra 77.660, enquanto a estimativa do IBGE registra 82.003; para Araripina, 85.135 versus 90.104. A população da análise vem do IBGE.

## População — IBGE/SIDRA

A tabela SIDRA 6579, variável 9324 (`População residente estimada`), foi consultada para 2015–2024. Há valores municipais para 2015–2021 e 2024, mas não para 2022–2023 na série extraída. Em 2022, foi usada a população residente do Censo Demográfico (SIDRA 4709, variável 93): Arcoverde, 77.742; Araripina, 85.088. A janela fica com 18 observações de população em 20 município-ano. 2023 permanece vazio e não há interpolação.

| Ano | Arcoverde/PE | Araripina/PE | Base |
|---:|---:|---:|---|
| 2015 | 72.625 | 82.800 | Estimativa IBGE |
| 2016 | 73.154 | 83.287 | Estimativa IBGE |
| 2017 | 73.667 | 83.757 | Estimativa IBGE |
| 2018 | 73.844 | 83.964 | Estimativa IBGE |
| 2019 | 74.338 | 84.418 | Estimativa IBGE |
| 2020 | 74.822 | 84.864 | Estimativa IBGE |
| 2021 | 75.295 | 85.301 | Estimativa IBGE |
| 2022 | 77.742 | 85.088 | Censo 2022 |
| 2023 | ausente | ausente | Sem estimativa extraída |
| 2024 | 82.003 | 90.104 | Estimativa IBGE |

## PIB municipal — IBGE/SIDRA

A tabela 5938, variável 37 (`Produto Interno Bruto a preços correntes`), fornece valores em mil R$ para 2015–2023. Foram obtidos 18 valores (dois municípios por nove anos). Os valores em R$ são calculados por `valor SIDRA × 1.000`. O PIB de 2024 não está disponível e não é estimado. A publicação do IBGE registra ressalvas para 2022–2023, inclusive quanto à abertura setorial; esses anos são tratados como totais anuais correntes, não como continuidade de um recorte setorial.

## IPCA — IBGE/SIDRA

A tabela 1737, variável 2266 (`IPCA - Número-índice`, base dezembro de 1993 = 100), fornece 120 valores mensais para 2015–2024, 12 em cada ano. O deflator é a razão entre a média dos 12 meses de 2024 e a média dos 12 meses do ano observado. O IPCA é nacional e representa preços de consumo; não é índice municipal nem deflator específico de custos públicos.

## Bélgica — Eurostat

A API `gov_10dd_edpt1` foi filtrada por Bélgica (`BE`), periodicidade anual (`A`), unidade `PC_GDP`, setor `S13` (governo geral) e itens `B9` (net lending/borrowing) e `GD` (dívida bruta consolidada), 2015–2025. A extração tem 11 observações para cada série. Para 2025, o saldo é −5,2% e a dívida é 108,1% do PIB. O trabalho anterior registra dívida de 107,9%; sem uma extração histórica arquivada não é possível identificar se isso decorre de revisão ou de outra data de consulta, portanto a diferença de 0,2 ponto percentual fica documentada sem especulação.

## Comparabilidade com o trabalho anterior

O PDF anterior informa para 2024 receita de R$ 327,48 milhões em Arcoverde e R$ 377,20 milhões em Araripina. Esses montantes correspondem às linhas de receita bruta **exceto** intraorçamentária da DCA. As despesas citadas, R$ 317,26 milhões e R$ 399,93 milhões, correspondem à despesa empenhada **total**, com intraorçamentárias. A subtração mistura bases distintas e não sustenta, por si, os saldos descritos naquele texto. Os valores não são copiados para a nova base; são apresentados apenas para explicar por que a comparação direta não é válida.
