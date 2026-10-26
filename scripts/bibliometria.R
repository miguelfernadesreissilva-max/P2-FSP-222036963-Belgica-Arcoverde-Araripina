#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
  script <- normalizePath(file_arg, mustWork = TRUE)
  root <- normalizePath(file.path(dirname(script), ".."), mustWork = TRUE)
  local_lib <- file.path(root, "data", "bibliometria", "Rlib")
  .libPaths(c(local_lib, .libPaths()))
  if (!requireNamespace("bibliometrix", quietly = TRUE)) {
    stop("bibliometrix ausente; execute Rscript scripts/install_R_packages.R")
  }
})

input <- file.path(root, "data", "bibliometria", "corpus_verificado.csv")
if (!file.exists(input)) stop("Corpus ainda não existe: ", input)
corpus <- read.csv(input, stringsAsFactors = FALSE, check.names = FALSE,
                   na.strings = c("", "NA"), fileEncoding = "UTF-8")
required <- c("doi", "doi_canonical", "citation_key", "title", "authors", "year",
              "journal", "keywords", "abstract", "peer_reviewed", "document_type",
              "metadata_source", "verified_source")
missing <- setdiff(required, names(corpus))
if (length(missing)) stop("Colunas ausentes no corpus: ", paste(missing, collapse = ", "))
if (nrow(corpus) < 80) stop("Corpus menor que 80 artigos distintos: ", nrow(corpus))
if (length(unique(tolower(corpus$doi_canonical))) < 80) stop("Menos de 80 DOIs canônicos distintos")

clean_authors <- function(x) {
  x <- ifelse(is.na(x), "", x)
  gsub("\\s*;\\s*", ";", x)
}
clean_keywords <- function(x) {
  x <- ifelse(is.na(x), "", x)
  gsub("\\s*;\\s*", ";", x)
}
M <- data.frame(
  AU = clean_authors(corpus$authors),
  TI = ifelse(is.na(corpus$title), "", corpus$title),
  SO = ifelse(is.na(corpus$journal), "", corpus$journal),
  PY = suppressWarnings(as.integer(corpus$year)),
  DI = ifelse(is.na(corpus$doi), "", corpus$doi),
  DE = clean_keywords(corpus$keywords),
  ID = clean_keywords(corpus$keywords),
  AB = ifelse(is.na(corpus$abstract), "", corpus$abstract),
  DB = "Curated peer-reviewed journal articles",
  stringsAsFactors = FALSE
)
rownames(M) <- corpus$citation_key

outdir <- file.path(root, "data", "bibliometria")
analysis_dir <- file.path(root, "analise")
figures_dir <- file.path(root, "figuras")
dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
dir.create(analysis_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)

# Core analysis uses the requested bibliometrix package, not a substitute.
bib <- bibliometrix::biblioAnalysis(M, sep = ";")
summary_obj <- summary(bib, k = 20, pause = FALSE)
summary_text <- capture.output(print(summary_obj))
writeLines(summary_text, file.path(analysis_dir, "bibliometrix_summary.txt"), useBytes = TRUE)
saveRDS(list(corpus = corpus, bibliometrix_input = M, analysis = bib, summary = summary_obj),
        file.path(outdir, "bibliometrix_results.rds"))

# Clear, reproducible annual and journal counts from the verified metadata.
year <- suppressWarnings(as.integer(corpus$year))
years <- sort(unique(year[!is.na(year)]))
annual <- data.frame(year = years, documents = vapply(years, function(y) sum(year == y), integer(1)))
write.csv(annual, file.path(analysis_dir, "bibliometria_producao_anual.csv"), row.names = FALSE, fileEncoding = "UTF-8")
source_counts <- sort(table(trimws(corpus$journal[!is.na(corpus$journal) & nzchar(trimws(corpus$journal))])), decreasing = TRUE)
sources <- data.frame(journal = names(source_counts), documents = as.integer(source_counts), row.names = NULL)
write.csv(sources, file.path(analysis_dir, "bibliometria_periodicos.csv"), row.names = FALSE, fileEncoding = "UTF-8")

kw <- unlist(strsplit(ifelse(is.na(corpus$keywords), "", corpus$keywords), ";", fixed = TRUE), use.names = FALSE)
kw <- tolower(trimws(kw))
kw <- kw[nzchar(kw)]
if (length(kw)) {
  keyword_counts <- sort(table(kw), decreasing = TRUE)
  keyword_df <- data.frame(keyword = names(keyword_counts), documents = as.integer(keyword_counts), row.names = NULL)
  write.csv(keyword_df, file.path(analysis_dir, "bibliometria_palavras_chave.csv"), row.names = FALSE, fileEncoding = "UTF-8")
} else {
  write.csv(data.frame(status = "não disponível", reason = "Nenhum registro contém palavras-chave de autor verificadas."),
            file.path(analysis_dir, "bibliometria_palavras_chave.csv"), row.names = FALSE, fileEncoding = "UTF-8")
}

fields <- c(abstract = "abstract", keywords = "keywords", journal = "journal", affiliations = "affiliations", cited_by = "citation_count")
coverage <- data.frame(field = names(fields), available = NA_integer_, unavailable = NA_integer_, interpretation = NA_character_)
for (i in seq_along(fields)) {
  f <- fields[[i]]
  values <- if (f %in% names(corpus)) corpus[[f]] else rep(NA_character_, nrow(corpus))
  present <- !is.na(values) & nzchar(trimws(as.character(values)))
  coverage$available[i] <- sum(present)
  coverage$unavailable[i] <- sum(!present)
  coverage$interpretation[i] <- if (any(present)) "contagem de registros com metadado" else "não disponível; ausência não equivale a zero substantivo"
}
write.csv(coverage, file.path(analysis_dir, "bibliometria_cobertura_metadados.csv"), row.names = FALSE, fileEncoding = "UTF-8")

# Simple plots are included only when there is real metadata to display.
png(file.path(figures_dir, "bibliometria_producao_anual.png"), width = 1600, height = 900, res = 160)
if (nrow(annual)) {
  graphics::barplot(annual$documents, names.arg = annual$year, col = "#28745A",
                    border = NA, xlab = "Ano de publicação", ylab = "Artigos no corpus",
                    main = "Produção anual no corpus bibliométrico", las = 2)
} else {
  graphics::plot.new(); graphics::title("Produção anual: não disponível")
}
dev.off()

if (length(kw)) {
  top_kw <- head(data.frame(keyword = names(sort(table(kw), decreasing = TRUE)),
                            documents = as.integer(sort(table(kw), decreasing = TRUE))), 15)
  png(file.path(figures_dir, "bibliometria_palavras_chave.png"), width = 1600, height = 1000, res = 160)
  graphics::par(mar = c(5, 14, 4, 2))
  graphics::barplot(rev(top_kw$documents), names.arg = rev(top_kw$keyword), horiz = TRUE,
                    las = 1, col = "#59759A", border = NA, xlab = "Ocorrências",
                    main = "Palavras-chave de autor mais frequentes")
  dev.off()
}

report <- c(
  "ESTUDO BIBLIOMÉTRICO — PROCESSADO COM BIBLIOMETRIX",
  paste("Pacote:", as.character(utils::packageVersion("bibliometrix"))),
  paste("Documentos no corpus:", nrow(corpus)),
  paste("DOIs canônicos distintos:", length(unique(tolower(corpus$doi_canonical)))),
  paste("Periódicos distintos:", length(unique(corpus$journal[!is.na(corpus$journal) & nzchar(corpus$journal)]))),
  paste("Anos cobertos:", if (length(years)) paste(min(years), max(years), sep = "–") else "não disponível"),
  paste("Registros com palavras-chave de autor:", sum(!is.na(corpus$keywords) & nzchar(corpus$keywords))),
  "Afiliações e citações não encontradas no corpus não são interpretadas como zero substantivo."
)
writeLines(report, file.path(analysis_dir, "bibliometria_status.txt"), useBytes = TRUE)
cat(paste(report, collapse = "\n"), "\n")
