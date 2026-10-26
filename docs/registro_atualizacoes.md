# Registro de atualizações e inspeção do material de comparação

**Data:** 25/10/2026 (hora local).  
**Origem consultada:** <https://github.com/victorhugo2109/Trabalho-de-Finan-as-do-Setor-P-blico> (clone depth-1, somente leitura).  
**Destino de trabalho:** projeto da matrícula 222036963; proprietário GitHub definido pelo usuário como a conta autenticada `miguelfernadesreissilva-max`.

## Inventário real do repositório-fonte

O clone de leitura contém somente:

| Arquivo | Tipo/conteúdo observado | Observações |
|---|---|---|
| `README.md` | Markdown, 81 bytes | Uma frase genérica; não documenta bases, versão ou procedimento. |
| `Excel dos dados.xlsx` | Planilha Excel | 10 abas (“Questão 1” a “Questão 10”); abas 1 e 8 vazias. Células sem fórmulas e sem tabelas Excel. Há séries em blocos separados, lacunas de anos e cabeçalhos repetidos. |
| `Finanças do Setor Público - Prova 1.pdf` | PDF, 8 páginas físicas / 37 páginas lógicas extraídas | Identifica nominalmente outro estudante e contém texto, gráficos e resultados de P1. Consultado integralmente por páginas; não será copiado nem usado como base numérica. |
| `REFERÊNCIAS.pdf` | PDF, 2 páginas | Lista principalmente portais oficiais, bases e uma referência ao próprio trabalho; não contém o mínimo de 80 artigos científicos. |

## Variáveis vistas na planilha/PDF anterior

Entre as variáveis e temas identificados estão: dívida pública/PIB da Bélgica; receita e despesa municipais; receitas tributárias e totais; PIB municipal; população/per capita; gastos em educação e saúde; IDEB; cobertura de atenção básica; proxy receita tributária/receita total; transferências; e resultados fiscais. O PDF declara períodos de dez anos em várias questões, mas diversas séries da planilha têm somente 2015–2021 ou cobertura desigual. A base editável não contém scripts de coleta, fórmulas ou notas de origem por série.

## Inconsistências e limitações verificadas

1. As abas da planilha não contêm fórmulas; valores de correlação e relações do texto não podem ser reproduzidos a partir do arquivo sem reconstrução.
2. As séries municipais aparecem em tabelas isoladas, às vezes com linhas vazias e cabeçalhos duplicados; faltam valores em anos recentes em alguns blocos.
3. Não há metadados por célula que identifiquem tabela, conta, atualização, classificação, unidade ou data de extração.
4. O PDF mistura valores aproximados, séries históricas e afirmações inferenciais sem trilha numérica completa. Esses resultados não serão copiados.
5. A aba “Questão 8” está vazia e o PDF correspondente não apresenta mapa verificável.
6. A referência bibliográfica anterior não satisfaz o mínimo de 80 artigos revisados por pares exigido no prompt-mestre.
7. Códigos tentados inicialmente não produziram dados; o cadastro oficial Siconfi retornou Arcoverde `2601201` e Araripina `2601102`. A extração DCA 2024 ainda não foi obtida de modo verificável: consultas testadas responderam sem itens ou tiveram timeout. Nenhum valor decorrente dessas chamadas será usado.
8. O IBGE informa que a base municipal do PIB consultada cobre 2002–2023 e que os dados recentes têm ressalvas metodológicas; não será criada observação 2024 por extrapolação.
9. A comparação Bélgica–municípios exige distinção de nível de governo, moeda, unidade, consolidação e estoque versus fluxo; não se copiará uma comparação direta do texto anterior.

## Decisões de atualização

- Preservar apenas a proveniência e o inventário em `data/original/README.md`; não redistribuir o material individual de outro estudante.
- Usar a planilha antiga como inventário das perguntas/variáveis e atualizar os valores por reextração independente de fontes oficiais.
- Manter ausências como ausências, registrar cobertura desigual e evitar imputação silenciosa.
- Não transcrever texto, números, gráficos ou conclusões do trabalho anterior.
- Não publicar enquanto coleta, tratamentos, planilha, artigo, testes e revisão final não estiverem concluídos.
- A bibliometria permanece pendente porque cumprir o mínimo de 80 artigos exige pesquisa científica extensa e isso conflita com a orientação simultânea para não fazer nova validação bibliográfica extensa.
