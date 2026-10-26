#import "report-theme.typ": report-accent, report-theme
#import "@preview/glossarium:0.5.10": make-glossary, register-glossary, print-glossary, gls
#show: make-glossary
#let termos = (
  (key: "dca", short: "DCA", long: "Declaração das Contas Anuais", description: "Demonstrativo anual de contas remetido ao Tesouro Nacional."),
  (key: "finbra", short: "FINBRA", long: "Finanças do Brasil", description: "Conjunto de dados consolidados de finanças públicas subnacionais divulgado pelo Tesouro Nacional."),
  (key: "fundeb", short: "FUNDEB", long: "Fundo de Manutenção e Desenvolvimento da Educação Básica", description: "Mecanismo de financiamento e redistribuição da educação básica no Brasil."),
  (key: "ibge", short: "IBGE", long: "Instituto Brasileiro de Geografia e Estatística", description: "Instituto oficial de estatística e geociências do Brasil."),
  (key: "ipca", short: "IPCA", long: "Índice Nacional de Preços ao Consumidor Amplo", description: "Índice oficial brasileiro de inflação ao consumidor."),
  (key: "pib", short: "PIB", long: "Produto Interno Bruto", description: "Medida de valor adicionado de bens e serviços finais produzidos em uma unidade econômica."),
  (key: "siconfi", short: "Siconfi", long: "Sistema de Informações Contábeis e Fiscais do Setor Público Brasileiro", description: "Sistema de coleta e divulgação de informações contábeis e fiscais do setor público brasileiro."),
  (key: "stn", short: "STN", long: "Secretaria do Tesouro Nacional", description: "Órgão central de administração financeira e contabilidade federal do Brasil."),
  (key: "eurostat", short: "Eurostat", long: "Gabinete de Estatística da União Europeia", description: "Autoridade estatística da União Europeia."),
  (key: "esa", short: "ESA 2010", long: "Sistema Europeu de Contas Nacionais e Regionais 2010", description: "Quadro contábil e estatístico europeu para contas nacionais e setoriais."),
  (key: "s13", short: "S13", long: "Setor institucional governo geral", description: "Setor estatístico que reúne os subsetores de governo geral na classificação ESA 2010."),
  (key: "unb", short: "UnB", long: "Universidade de Brasília", description: "Instituição de ensino superior do Distrito Federal."),
)
#register-glossary(termos)

#show: report-theme.with(
  title: "Finanças públicas em dois níveis: Bélgica, Arcoverde e Araripina",
  author: "Miguel Fernandes dos Reis Silva",
  rhythm: "report",
  body-size: 10.5pt,
  running-header: true,
)
#set text(lang: "pt", region: "BR", font: "Libertinus Serif")

// ---------- Folha de rosto ----------
#page(margin: (top: 24%, x: 2.2cm), numbering: none, header: none)[
  #set par(first-line-indent: 0em, justify: false)
  #align(center)[
    #text(size: 24pt, weight: "bold", fill: report-accent)[Finanças públicas em dois níveis: Bélgica, Arcoverde e Araripina]
    #v(0.5em)
    #text(size: 13pt, fill: luma(90))[Comparação institucional e evidência fiscal descritiva]
    #text(size: 11pt, fill: luma(90))[Municípios: 2015–2024 · Bélgica: 2015–2025]
    #v(2em)
    #line(length: 42%, stroke: 0.6pt + luma(155))
    #v(2em)
    #text(size: 11pt)[Miguel Fernandes dos Reis Silva]
    #text(size: 10pt)[Matrícula 222036963]
    #v(1em)
    #text(size: 10pt)[Universidade de Brasília — UnB]
    #text(size: 10pt)[Finanças do Setor Público — CCA0169 · Turma 01 · 2026.2]
    #text(size: 10pt)[Docente: Lucas Oliveira Gomes Ferreira]
    #v(1.4em)
    #text(size: 9pt, fill: rgb("#9B4B3E"))[VERSÃO DE TRABALHO · validação bibliométrica editorial e auditoria final pendentes]
    #v(1.4em)
    #text(size: 10pt)[Brasília · outubro de 2026]
  ]
]

// ---------- Navegação ----------
#page(numbering: none, header: none)[
  #outline(title: [Sumário], indent: 1.2em)
]
#counter(page).update(1)

= Resumo

Este artigo examina a evolução de receitas e despesas declaradas por Arcoverde e Araripina, em Pernambuco, entre 2015 e 2024, e a trajetória agregada de déficit e dívida do governo geral da Bélgica entre 2015 e 2025. A comparação é institucional e descritiva, não uma ordenação de desempenho entre unidades equivalentes: o recorte belga é nacional e multissetorial, enquanto os brasileiros são governos municipais. As contas municipais são obtidas na DCA do Siconfi; população, PIB e inflação vêm do IBGE/SIDRA; os indicadores belgas, do Eurostat. Em reais de 2024, a receita bruta total aumentou 61,3% em Arcoverde e 68,7% em Araripina; a despesa empenhada cresceu, respectivamente, 56,1% e 76,0%. Em 2024, tributos próprios representaram 10,3% da receita bruta de Arcoverde e 6,4% da de Araripina. A Bélgica registrou saldo de −5,2% do PIB e dívida bruta de 108,1% em 2025. Séries curtas, diferenças contábeis e lacunas de população e atividade econômica impedem inferência causal. O corpus preliminar tem 80 DOI distintos; a discussão integral dos textos e o processamento exigido em bibliometrix ainda requerem validação nesta versão.

*Palavras-chave:* finanças públicas; federalismo fiscal; transferências intergovernamentais; municípios; Bélgica; transparência fiscal.

= Introdução

Finanças públicas são simultaneamente um problema de alocação econômica, uma cadeia de decisões administrativas e um sistema de registro sujeito a controle. A contabilidade pública organiza autorizações, arrecadação, execução e saldos em classificações comparáveis; a auditoria e o controle interno/externo testam regularidade e confiabilidade; a administração pública conecta orçamento, capacidade estatal e entrega de políticas; a economia analisa incentivos, incidência distributiva e restrições fiscais. Uma série contábil descreve fluxos registrados — não mede, por si só, qualidade do serviço, necessidade social ou eficiência.

A Bélgica oferece um caso de federalismo multinível. A Constituição a define como Estado federal composto por comunidades e regiões; há três comunidades linguístico-culturais, três regiões, dez províncias e 565 conselhos municipais. A monarquia é constitucional e parlamentar: o Rei é chefe de Estado, mas atos executivos dependem de ministros responsáveis; o primeiro-ministro chefia o governo em sistema multipartidário parlamentar. A divisão de competências entre federação, comunidades e regiões estrutura financiamento e administração de políticas, mas a série Eurostat utilizada aqui é do governo geral consolidado, e não do governo federal isolado (@BelgiumFederalState2026; @BelgiumFederalAuthorities2026; @BelgiumMonarchy2026; @EUCountrypageBelgium2026).

Arcoverde e Araripina, por sua vez, são municípios brasileiros submetidos a regras nacionais de contabilidade e transferências intergovernamentais. No Censo de 2022, tinham 77.742 e 85.088 residentes; suas áreas territoriais de 2025 eram 343,923 km² e 2.037,394 km² (@IBGEArcoverde2026; @IBGEAraripina2026). A Bélgica tinha cerca de 11,96 milhões de habitantes e 30.667 km² em 2026 e usa o euro; os municípios usam o real (@EUCountrypageBelgium2026). Escala, moeda, estrutura tributária, subsetor institucional e regras de consolidação diferem. Portanto, não se calcula uma classificação direta nem se interpretam diferenças brutas como superioridade fiscal.

A pergunta é: como evoluíram receitas, despesas, tributação própria e dependência de transferências em Arcoverde e Araripina, e o que a trajetória agregada de déficit e dívida belga acrescenta à compreensão de finanças públicas em arranjos institucionais diferentes? O objetivo é reconstruir séries oficiais, documentar lacunas e produzir comparação descritiva, sem identificar efeitos causais. A contribuição é uma base rastreável para discutir a relação entre capacidade arrecadatória, transferências, composição da despesa e governança multinível, distinguindo cuidadosamente conceitos que não são intercambiáveis.

= Referencial teórico

A literatura sobre federalismo fiscal e governos subnacionais investiga a atribuição de responsabilidades, autonomia tributária, equalização, desenho de transferências, disciplina orçamentária e prestação de serviços. Estudos sobre o Brasil, municípios europeus e governança fiscal da União Europeia diferem em unidade observacional, instituições e estratégia empírica; seus coeficientes não podem ser transplantados mecanicamente para dois municípios ou para uma comparação com o governo geral belga. A literatura informa quais mecanismos observar — base própria, incentivos de transferências, escala, composição funcional, regras e controles —, mas os dados deste trabalho permitem apenas descrição.

A questão de capacidade fiscal envolve tanto a dimensão da base tributária quanto o esforço de arrecadação, o desenho das bases e as restrições administrativas. Uma participação tributária maior não equivale automaticamente a maior bem-estar ou eficiência: pode refletir composição econômica, capacidade de cobrança, regras e competências. A literatura sobre transferências acrescenta a tensão entre equalização de capacidade e incentivos marginais; para testar causalmente efeitos de transferências seriam necessários desenho de identificação, contrafactual e dados de painel adequados, ausentes neste estudo. Estudos de despesa e serviços mostram que escala populacional, densidade, composição e arranjos de prestação condicionam comparações de custo; a despesa total não é um resultado de política.

Em auditoria, accountability e orçamento, a trilha de evidência liga o documento fonte, o código contábil, a transformação, o indicador e a interpretação. Essa cadeia é especialmente importante quando classificações mudam ou quando deduções, intraorçamentárias e estágios da despesa diferem. A análise financeira deste artigo segue essa lógica e não agrega simultaneamente contas-pai e descendentes. O mapa temático abaixo agrupa os 80 estudos por foco bibliográfico; títulos e DOI individuais constam no CSV do corpus. A organização é baseada em metadados e não deve ser lida como revisão sistemática dos resultados da totalidade dos textos completos.

#include "matriz_literatura.typ"

== Estudo bibliométrico

A seleção contém 80 registros com 80 DOI canônicos distintos e 58 títulos de periódicos, publicados entre 1981 e 2026. O procedimento priorizou artigos de periódico sobre finanças públicas, federalismo fiscal, receitas e despesas subnacionais, transferências, instituições, accountability e governança fiscal belga/europeia; excluiu livros, teses, relatórios, dados e preprints. As 80 correspondências de título, periódico, tipo “journal-article” e ano foram comparadas com metadados Crossref em `data/bibliometria/crossref_verification.csv`. Como referência de apresentação, Baker et al. (2022) identificam 744 estudos de finanças e contabilidade publicados entre 2000 e 2019 e 407 desenhos staggered DiD (55%); este corpus tem foco e universo diferentes, não sendo uma replicação daquela contagem (@BakerLarckerWang2022).

Os metadados consolidados de palavras-chave, afiliações, resumos e citações do corpus não estão completos; “não disponível” não significa zero. A instalação do pacote R bibliometrix foi tentada, mas downloads CRAN expiraram por timeout e a etapa computacional obrigatória não foi executada; as contagens acima são, portanto, descritivas do CSV, não resultados do bibliometrix. A verificação editorial em páginas de periódicos e políticas de revisão por pares está concluída para 19 dos 80 artigos; nos demais, a correspondência automática Crossref não substitui essa confirmação nem a leitura do texto completo. Estas limitações são registradas para não atribuir ao software ou aos artigos resultados que não foram verificados.

= Metodologia

O desenho é observacional, quantitativo e descritivo. Para os municípios, o período fiscal é 2015–2024. Foram consultadas 20 respostas integrais da API de dados abertos do Siconfi — 10 exercícios por município —, totalizando 20.618 linhas de declarações preservadas. O mapeamento usa os códigos IBGE de Arcoverde (2601201) e Araripina (2601102), com receita bruta, deduções, transferências, estágio de execução e despesa funcional conforme os anexos DCA. A STN informa que declarações podem ser revisadas até a consolidação; por isso o número baixado é fotografia da extração, com hashes nos manifestos (@SiconfiApi2026; @STNFinbra2026).

População municipal foi extraída das estimativas anuais do IBGE/SIDRA tabela 6579, variável 9324; para 2022 usa-se o Censo (tabela 4709, variável 93). Não há valor de estimativa extraído para 2022–2023 na série selecionada; o Censo cobre 2022, mas 2023 permanece ausente, sem interpolação. O PIB municipal corrente vem da tabela SIDRA 5938 até 2023; 2024 não está publicado nessa série coletada. O IPCA mensal foi obtido na tabela 1737, variável 2266; usa-se a média dos índices mensais de cada ano como aproximação de deflator anual (@IBGEPops2026; @IBGECensus2022; @IBGEPib2023; @IBGEIPCA2024).

Valores monetários municipais foram convertidos a reais médios de 2024 pela fórmula

*Valor real em R\$ de 2024 = valor nominal do ano × (IPCA médio de 2024 ÷ IPCA médio do ano).* 

em que o IPCA médio do ano é a média anual do número-índice. Não se arredonda antes do cálculo; o valor integral permanece em CSV/XLSX. A taxa de crescimento acumulada é calculada como (valor real de 2024 ÷ valor real de 2015 − 1) × 100. A razão tributária própria é a receita tributária própria dividida pela receita bruta total; a razão de transferências usa contas de transferências identificadas no DCA e fica rotulada como proxy quando a abertura intergovernamental não é comparável ao longo de toda a série. Per capita só é calculado quando população anual está disponível; relação municipal/PIB não é exibida em 2024 por falta do denominador.

Para a Bélgica usa-se Eurostat `gov_10dd_edpt1`, frequência anual, território BE, setor S13, unidade PC_GDP, itens B9 (capacidade/necessidade líquida de financiamento) e GD (dívida bruta consolidada), 2015–2025. O setor S13 representa governo geral, não apenas o nível federal; as medidas são porcentagens do PIB, não fluxos locais em euros comparáveis aos valores municipais em reais (@EurostatGFS2026; @EurostatEDP2026). Não se convertem moedas nem se misturam os dois desenhos estatísticos.

A descrição inclui variação real 2015–2024, participação de receitas e funções da despesa, além da série Eurostat. Correlações Pearson/Spearman são apenas exploratórias, com n=10 em níveis e n=9 em primeiras diferenças por município; tendência comum e autocorrelação podem inflar associação. Não há regressão, experimento ou estratégia de identificação. Portanto, não se afirma causalidade, efeito flypaper, esforço fiscal ou efeito de gasto sobre resultados sociais.

= Resultados e discussão

== Municípios: receitas e despesas reais

Entre 2015 e 2024, a receita bruta total real de Arcoverde passou de R\$ 210,1 milhões para R\$ 338,8 milhões (alta acumulada de 61,3%; CAGR real de 5,45%). A despesa total empenhada aumentou de R\$ 203,2 milhões para R\$ 317,3 milhões (56,1%; 5,07% ao ano). Em Araripina, a receita real subiu de R\$ 241,1 milhões para R\$ 406,8 milhões (68,7%; 5,98% ao ano), enquanto a despesa empenhada cresceu de R\$ 227,2 milhões para R\$ 399,9 milhões (76,0%; 6,49% ao ano). Esses valores são comparáveis no tempo após deflação, mas receita realizada bruta e despesa empenhada são estágios e conceitos distintos; sua diferença não é apresentada como superávit orçamentário.

#table(
  columns: (1.3fr, 1.1fr, 1.1fr, 0.9fr, 0.9fr),
  align: (left, right, right, right, right),
  inset: 5pt,
  stroke: (x, y) => 0.35pt + luma(210),
  table.header([Município], [Receita 2015 (R\$ mi)], [Receita 2024 (R\$ mi)], [Var. real %], [Despesa: var. real %]),
  [Arcoverde], [210,1], [338,8], [61,3], [56,1],
  [Araripina], [241,1], [406,8], [68,7], [76,0],
)

A trajetória não é monotônica. Em 2020, a despesa empenhada real cresceu 17,1% em Arcoverde, enquanto a receita real subiu 7,1%; em Araripina, os aumentos foram 7,2% e 11,5%. Em 2024, a receita real avançou 15,7% e a despesa 12,8% em Arcoverde; em Araripina, 10,8% e 26,2%. A coincidência temporal com choques macroeconômicos não identifica seus mecanismos nem demonstra que decisões de gasto causaram resultados econômicos ou sociais.

#figure(image("figuras/receitas_despesas_reais.png", width: 100%), caption: [Receitas brutas realizadas e despesas empenhadas, em reais de 2024. Fonte: elaboração própria com dados DCA/Siconfi e IPCA/IBGE. A diferença visual não representa saldo contábil.])

== Composição de receitas e transferências

Em 2024, a receita tributária própria correspondeu a 10,29% da receita bruta de Arcoverde e 6,42% em Araripina. A parcela ampla de transferências correntes foi 75,00% e 73,46%, respectivamente; a proxy mais restrita de transferências intergovernamentais correntes, 60,80% e 54,84%. Em 2015, as proxies eram 70,47% e 79,74%. A queda aparente entre 2017 e 2018 coincide com alteração da estrutura/classificação das contas nos arquivos DCA; por isso não se descreve a mudança como redução econômica sem validação das rubricas. A participação tributária sugere uma diferença descritiva na composição da receita, não uma medida isolada de autonomia ou esforço fiscal.

#figure(image("figuras/estrutura_receitas.png", width: 100%), caption: [Composição selecionada das receitas municipais. A proxy intergovernamental é sensível a quebras de classificação.])

A taxa tributária própria mais baixa de Araripina e a alta participação de transferências são compatíveis com debates sobre desigualdade de bases locais e equalização intergovernamental, mas duas séries municipais não identificam incentivos marginais, esforço tributário ou efeitos distributivos. Uma conclusão causal exigiria painel mais amplo, controle de composição e mudanças normativas e uma fonte de variação exógena.

== Bélgica: governo geral consolidado

Na série do Eurostat, o saldo líquido do governo geral belga variou de −2,5% do PIB em 2015 para −5,2% em 2025; o déficit atingiu −9,0% em 2020. A dívida bruta consolidada passou de 105,7% do PIB em 2015 a 108,1% em 2025, com pico de 111,4% em 2020 e queda até 102,3% em 2023, seguida de aumento. Trata-se de agregados do setor institucional S13, com perímetro e padrão ESA 2010 próprios; não são receitas ou despesas de uma prefeitura nem valores em moeda que devam ser comparados diretamente com os municípios.

#figure(image("figuras/belgica_fiscal.png", width: 100%), caption: [Saldo e dívida bruta do governo geral belga como porcentagem do PIB, Eurostat.])

O arranjo federal belga atribui competências a comunidades e regiões, enquanto o indicador aqui disponível consolida o governo geral. Assim, a informação contextualiza a gestão fiscal nacional, mas não permite atribuir déficit/dívida ao governo federal, à Região da Valônia, à Flandres, a Bruxelas ou às comunas. Essa limitação de nível é substantiva, não meramente técnica. A Bélgica e os municípios brasileiros diferem também em população, moeda, cobertura institucional e arquitetura de transferências.

== Despesa funcional, lacunas e sensibilidade

A despesa funcional comparável foi obtida para 2017–2024 (256 linhas, dois municípios e funções declaradas); não há valores harmonizados para 2015–2016. A figura de 2024 descreve composição declarada, não custo-efetividade nem resultado do serviço. As alterações de classificação, despesas intraorçamentárias e diferentes estágios de execução são preservados nos arquivos-fonte e no dicionário.

#figure(image("figuras/despesas_funcao_2024.png", width: 100%), caption: [Despesa empenhada por função em 2024, segundo a DCA. Valores não são medidas de produto ou qualidade do serviço.])

O PIB municipal termina em 2023; população anual tem lacuna em 2023 e a série de estimativas não substitui a contagem censitária de 2022. Por padrão, valores ausentes permanecem ausentes. Qualquer per capita depende do denominador disponível e não preenche o buraco de 2023. A deflação usa IPCA médio anual e pode divergir de deflator específico do gasto público; é uma aproximação uniforme, explicitada para permitir reprodução. A série Eurostat foi extraída em outubro de 2026; revisões estatísticas podem alterar observações futuras.

As correlações entre nível de receita e despesa são elevadas (Pearson r=0,987 em Arcoverde e r=0,977 em Araripina, n=10), mas as séries crescem no tempo e são curtas. Em primeiras diferenças, r=0,750 e r=0,779 (n=9). Nenhum coeficiente é teste causal ou estatística inferencial; não controla tendências, autocorrelação, população, transferências ou choques comuns.

= Conclusão

Entre 2015 e 2024, ambas as cidades ampliaram receita e despesa em termos reais. O avanço da despesa empenhada superou o da receita em Araripina, enquanto em Arcoverde as taxas acumuladas foram próximas. A participação tributária própria foi maior em Arcoverde em 2024, mas transferências correntes permaneceram uma parcela predominante da receita nos dois municípios. As quebras de classificação impedem leitura linear da proxy de transferências. Na Bélgica, déficit e dívida do governo geral foram elevados em 2025 relativamente a 2015, com choque de 2020 visível nas séries; a estatística consolidada não permite repartir esse resultado por níveis federados.

A comparação responde à pergunta de forma institucional, não hierárquica: as séries revelam padrões fiscais distintos, mas pertencem a unidades, moedas, classificações e níveis de governo diferentes. O trabalho demonstra a importância de vincular demonstrações contábeis à auditoria de conceitos, à administração das competências e à interpretação econômica, evitando somas hierárquicas e falsas equivalências. Não há evidência para afirmar que transferências causam determinado gasto, que maior receita própria implica maior esforço ou que dívida/deficit belgas equivalem a desequilíbrio municipal.

As limitações centrais são: cobertura menor de despesa funcional, ausência municipal de PIB em 2024 e de população anual em 2023, mudança de rubricas DCA, deflator aproximado, painel de apenas dois municípios e ausência de desenho causal. Para completar a versão final ainda são necessários: (i) processamento efetivo do corpus pelo pacote bibliometrix; (ii) leitura e discussão individual dos achados dos 80 artigos e validação editorial/política de peer review restante; (iii) integração do material Baker do curso, que não foi disponibilizado; (iv) auditoria cruzada final do PDF, XLSX e CSVs. Pesquisas futuras podem ampliar municípios, harmonizar subfunções e subsectores belgas e usar estratégia de identificação causal e indicadores de serviços.

= Glossário

#print-glossary(termos, show-all: true)

#bibliography("references.bib", title: [Referências], style: "apa")
