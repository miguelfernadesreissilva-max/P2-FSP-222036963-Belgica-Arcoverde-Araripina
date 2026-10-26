# P2 — Finanças do Setor Público

**Autor:** Miguel Fernandes dos Reis Silva · **Matrícula:** 222036963  
**Disciplina:** CCA0169 — Finanças do Setor Público, Turma 01, 2026.2  
**Instituição:** Universidade de Brasília (UnB) · **Docente:** Lucas Oliveira Gomes Ferreira  
**Conjunto:** Bélgica; Arcoverde/PE; Araripina/PE  
**Entrega:** 25/10/2026

Este repositório contém a versão encaminhada para avaliação. As limitações que afetam a avaliação estão registradas no artigo e em [validação e limitações](docs/auditoria_versao_trabalho.md); a publicação não afirma que uma etapa não executada tenha sido concluída.

## Arquivos principais

- [Artigo em PDF](artigo/main.pdf)
- [Fonte Typst do artigo](artigo/main.typ)
- [Planilha Excel auditável](base_atualizada_222036963.xlsx)
- [Corpus de 80 DOI e metadados](data/bibliometria/corpus_verificado.csv)
- [Verificação Crossref](data/bibliometria/crossref_verification.csv)
- [Resumos OpenAlex disponíveis](data/bibliometria/resumos_openalex.csv)
- [Registro de validação e limitações](docs/auditoria_versao_trabalho.md)

## Escopo e dados

A P2 reconstrói as séries em fontes oficiais, sem copiar resultados ou números do trabalho de outra matrícula. A Bélgica é tratada como governo geral nacional; Arcoverde e Araripina são governos municipais. O artigo não interpreta esses níveis como equivalentes nem afirma causalidade.

O material anterior foi inspecionado em clone somente leitura. Contém essencialmente um PDF não editável e referências esparsas; os números de 2024 misturam receita bruta exceto intra e despesa empenhada total, portanto não sustentam o saldo apresentado. A cópia não é redistribuída. Ver `data/original/README.md` e `docs/registro_atualizacoes.md`.

- **Siconfi DCA:** 20 respostas municipais anuais (2015–2024), 20.618 linhas brutas; contas e códigos selecionados rastreados em 556 linhas.
- **População IBGE:** 18 de 20 município-ano; estimativas 2015–2021 e 2024, Censo em 2022; 2023 permanece vazio.
- **PIB municipal IBGE:** 18 de 20 município-ano, 2015–2023; 2024 indisponível.
- **IPCA:** 120 observações mensais (2015–2024); valores fiscais reais em reais médios de 2024.
- **Eurostat/Bélgica:** saldo de financiamento e dívida bruta do governo geral, 2015–2025.
- **Despesa por função:** 256 linhas de funções de primeiro nível, 2017–2024; total reconciliado; 2015–2016 sem série funcional extraída.

Os vazios são ausências, não zeros. A série principal mantém etapas contábeis separadas. Não se calcula saldo orçamentário municipal subtraindo receita bruta e despesa empenhada quando deduções e intraorçamentárias não são compatíveis em toda a janela.

## Estrutura e reprodução

- `artigo/`: fonte Typst, PDF, bibliografia e figuras.
- `data/original/`: nota de proveniência do material anterior, que não foi copiado.
- `data/brutos/`: JSON/CSV diretamente obtidos, manifestos e hashes.
- `data/tratados/`: séries harmonizadas e linhas-fonte selecionadas.
- `data/bibliometria/`: corpus, verificações, resumos e resultados bibliométricos disponíveis.
- `docs/`: fontes, dicionário, evidências, validação e registro de alterações.
- `scripts/`: coleta, tratamento, análise, validação e geração XLSX.
- `analise/`, `figuras/`: resultados e gráficos reproduzíveis.

A partir da raiz do projeto:

```bash
python3 scripts/coleta_dados.py
python3 scripts/trata_base.py
python3 scripts/analise.py
python3 scripts/validacao.py
Rscript scripts/bibliometria.R
Rscript scripts/validacao_bibliometrica.R
python3 scripts/cria_planilha.py
python3 scripts/valida_planilha.py
cd artigo && typst compile --root .. main.typ main.pdf
```

O coletor reutiliza respostas já preservadas, salvo quando chamado com `--refresh`. No ambiente de produção desta entrega, os downloads CRAN expiraram; por isso o processamento obrigatório pelo pacote bibliometrix não foi executado. A cobertura editorial e a leitura integral da literatura também são parciais, como discriminado no artigo e na auditoria.

## Fontes principais

- Siconfi/STN: <https://apidatalake.tesouro.gov.br/docs/siconfi/>
- IBGE/SIDRA: tabelas 6579 (população), 4709 (Censo 2022), 5938 (PIB municipal) e 1737 (IPCA).
- Eurostat: <https://ec.europa.eu/eurostat/databrowser/product/view/gov_10dd_edpt1>
- Bélgica: <https://www.belgium.be/en/about_belgium/government/federale_staat>
- Baker, Larcker e Wang (2022): <https://doi.org/10.1016/j.jfineco.2022.01.004>

Parâmetros, unidades, cobertura e limitações estão em `docs/fontes_consultadas.md` e `docs/dicionario_variaveis.md`.
