#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
script <- normalizePath(file_arg, mustWork = TRUE)
root <- normalizePath(file.path(dirname(script), ".."), mustWork = TRUE)
corpus_file <- file.path(root, "data", "bibliometria", "corpus_verificado.csv")
main_file <- file.path(root, "artigo", "main.typ")
bib_file <- file.path(root, "artigo", "references.bib")
stopifnot(file.exists(corpus_file), file.exists(main_file), file.exists(bib_file))
corpus <- read.csv(corpus_file, stringsAsFactors = FALSE, check.names = FALSE,
                   na.strings = c("", "NA"), fileEncoding = "UTF-8")
required <- c("doi", "doi_canonical", "citation_key", "title", "authors", "year", "journal",
              "peer_reviewed", "document_type", "metadata_source", "verified_source")
missing <- setdiff(required, names(corpus))
if (length(missing)) stop("Colunas ausentes: ", paste(missing, collapse = ", "))
if (nrow(corpus) < 80) stop("CRÍTICO: menos de 80 artigos no corpus.")
if (length(unique(tolower(trimws(corpus$doi_canonical)))) < 80) stop("CRÍTICO: menos de 80 DOIs canônicos distintos.")
if (anyDuplicated(tolower(trimws(corpus$doi_canonical)))) stop("DOI duplicado no corpus.")
if (any(!grepl("^10\\.[0-9]{4,9}/", trimws(corpus$doi)))) stop("Há DOI ausente ou malformado.")
if (any(is.na(corpus$title) | !nzchar(trimws(corpus$title)))) stop("Título ausente.")
if (any(is.na(corpus$authors) | !nzchar(trimws(corpus$authors)))) stop("Autor ausente.")
if (any(is.na(corpus$journal) | !nzchar(trimws(corpus$journal)))) stop("Periódico ausente.")
if (any(is.na(corpus$year) | !grepl("^[0-9]{4}$", as.character(corpus$year)))) stop("Ano ausente ou inválido.")
if (any(tolower(as.character(corpus$peer_reviewed)) %in% c("false", "no", "n", "0"))) stop("Documento não revisado por pares incluído.")
if (any(!grepl("article|journal", tolower(corpus$document_type)))) stop("Documento que não é artigo de periódico incluído.")
if (any(is.na(corpus$metadata_source) | !nzchar(corpus$metadata_source))) stop("Fonte de metadados ausente.")
if (any(is.na(corpus$verified_source) | !nzchar(corpus$verified_source))) stop("Fonte verificadora ausente.")

manuscript <- paste(readLines(main_file, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
bibtext <- paste(readLines(bib_file, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
manuscript <- gsub("(?m)^#import.*$", "", manuscript, perl = TRUE)
article_keys <- unique(trimws(corpus$citation_key))
bib_keys <- unique(regmatches(bibtext, gregexpr("(?<=\\{)[^,[:space:]]+(?=,)", bibtext, perl = TRUE))[[1]])
if (length(bib_keys) == 0 || any(!article_keys %in% bib_keys)) stop("Há artigos do corpus sem entrada @article correspondente em references.bib.")
if (anyDuplicated(bib_keys)) stop("Há chaves BibTeX duplicadas.")
# Match in-text Typst citation keys against all bibliography entries. Exclude the known glossary keys and Universe import.
cited <- unique(regmatches(manuscript, gregexpr("(?<![[:alnum:]_])@[[:alnum:]][[:alnum:]_:.+-]*", manuscript, perl = TRUE))[[1]])
cited <- sub("^@", "", cited)
known_glossary <- c("dca", "finbra", "fundeb", "ibge", "ipca", "pib", "siconfi", "stn", "eurostat", "esa", "unb")
cited <- cited[!grepl("^(preview/|local/)", cited)]
unknown <- setdiff(cited, c(bib_keys, known_glossary))
if (length(unknown)) stop("Citação sem referência/glossário correspondente: ", paste(unknown, collapse = ", "))
uncited <- setdiff(bib_keys, cited)
if (length(uncited)) stop("Referência no .bib sem citação no manuscrito: ", paste(uncited, collapse = ", "))
uncited_articles <- setdiff(article_keys, cited)
if (length(uncited_articles)) stop("Artigos do corpus sem citação textual: ", paste(uncited_articles, collapse = ", "))

out <- file.path(root, "analise", "validacao_bibliometrica.txt")
dir.create(dirname(out), recursive = TRUE, showWarnings = FALSE)
lines <- c("VALIDAÇÃO BIBLIOMÉTRICA — PASS",
           paste("Artigos de periódico com DOI canônico distinto:", length(unique(tolower(corpus$doi_canonical)))),
           paste("Artigos com entrada BibTeX e citação em texto:", length(article_keys)),
           paste("Entradas BibTeX distintas e citadas:", length(bib_keys)),
           "DOIs duplicados: 0; títulos/autores/periódicos/anos/fonte de verificação presentes.",
           paste("Chaves não bibliográficas do glossário permitidas:", paste(known_glossary, collapse = ", ")))
writeLines(lines, out, useBytes = TRUE)
cat(paste(lines, collapse = "\n"), "\n")
