# Validação e limitações da entrega P2

**Data:** 25/10/2026. **Status:** versão disponibilizada para avaliação no repositório público, a pedido do autor. Este registro distingue verificações concluídas de requisitos que não foi possível concluir antes do prazo.

## Verificações concluídas

- 20 respostas oficiais DCA para Arcoverde e Araripina (2015–2024), com dados brutos, contagens e hashes preservados.
- Séries IBGE/SIDRA e Eurostat coletadas, transformadas e documentadas; ausências de população e PIB permanecem vazias.
- Scripts de tratamento, análise e geração do XLSX executados; planilha Excel recalculada e validada em LibreOffice.
- 80 DOI distintos confrontados com Crossref; título, periódico, ano e tipo de documento coincidem nas 80 respostas automatizadas.
- 68 resumos foram recuperados via OpenAlex e sintetizados em português por campos estruturados. São sínteses de abstracts, não leitura dos textos completos. Para 12 registros, não há abstract recuperado nessa fonte.
- 19 dos 80 artigos tiveram checagem adicional em páginas editoriais/políticas; nos demais, a correspondência Crossref não prova peer review nem substitui conferência editorial.
- Artigo Typst compilado em PDF estrito, com referência Baker et al. (2022) localizada na página editorial pública da Elsevier.

## Limitações de conformidade

1. O uso computacional do pacote R `bibliometrix`, obrigatório no enunciado, não foi executado. Downloads CRAN expiraram; uma tentativa de instalar imports pelo espelho GitHub também falhou por dependências ainda indisponíveis. As contagens do artigo são descritivas do corpus, não resultados atribuíveis ao bibliometrix.
2. A revisão editorial individual e a leitura integral de 80 artigos não foram concluídas. A matriz temática usa metadados; 68 sínteses são baseadas em abstracts e 12 abstracts não foram recuperados. Isso limita o atendimento à exigência de discutir 80 estudos em profundidade.
3. O PDF registra explicitamente essas limitações; não se afirma execução de etapas não realizadas nem causalidade nas comparações fiscais.
4. A checagem automática do PDF pode sinalizar falsamente a palavra “Metodologia” por conter a sequência de caracteres `todo`; o cabeçalho foi mantido por ser seção obrigatória. A compilação Typst em modo estrito passou após a atualização bibliográfica.

A entrega prioriza o envio dentro do prazo e a transparência sobre a extensão efetivamente concluída. A nota ou aceitação do professor não pode ser prevista.
