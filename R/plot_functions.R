# R/plot_functions.R
# Reusable plotting helpers for the Clairvoyant analysis.
#
# Goal: keep the Quarto report clean by moving repeated plotting code here.

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(scales)
  library(ggcorrplot)
})

clairvoyant_palette <- c(
  "#4b3e8f","#6957cd","#402b2a","#4281a3","#c6b9f6","#140f49","#b9cadd"
)

theme_clairvoyant <- function(base_size = 12, base_family = "Helvetica") {
  theme_minimal(base_size = base_size, base_family = base_family) +
    theme(
      plot.title = element_text(hjust = 0.5, face = "bold"),
      panel.grid = element_blank()
    )
}


save_plot <- function(plot_obj,
                      filename,
                      out_dir = "output",
                      width = 10,
                      height = 6,
                      dpi = 300) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  ggsave(filename = file.path(out_dir, filename),
         plot = plot_obj,
         width = width,
         height = height,
         dpi = dpi)
  invisible(plot_obj)
}


plot_top_industries_bar <- function(df,
                                   industry_col = "industry",
                                   score_col = "industry_health_score",
                                   fill = "#b9cadd") {
  ggplot(df, aes(x = .data[[industry_col]], y = .data[[score_col]])) +
    stat_summary(fun = "mean", geom = "bar", fill = fill, color = "black", width = 1) +
    labs(
      title = "Industries by Health Score",
      x = "Industry",
      y = "Health Score"
    ) +
    theme_clairvoyant() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 9),
          legend.position = "none")
}

summarize_industry_risk_return <- function(df,
                                          industry_col = "industry",
                                          vol_col = "industry_vol_12m",
                                          ret_col = "industry_return_12m",
                                          job_postings_col = "job_postings") {
  df %>%
    group_by(.data[[industry_col]]) %>%
    summarize(
      industry_vol_12m = mean(.data[[vol_col]], na.rm = TRUE),
      industry_return_12m = mean(.data[[ret_col]], na.rm = TRUE),
      job_postings = mean(.data[[job_postings_col]], na.rm = TRUE),
      .groups = "drop"
    ) %>%
    rename(industry = .data[[industry_col]])
}

plot_industry_risk_return <- function(df_labels,
                                      palette = clairvoyant_palette) {
  avg_vol <- mean(df_labels$industry_vol_12m, na.rm = TRUE)
  avg_ret <- mean(df_labels$industry_return_12m, na.rm = TRUE)

  ggplot(df_labels, aes(x = industry_vol_12m,
                        y = industry_return_12m,
                        color = industry,
                        size = job_postings)) +
    geom_point(alpha = 0.8) +
    geom_text(aes(label = industry),
              vjust = -1,
              size = 3.5,
              fontface = "bold",
              show.legend = FALSE) +
    geom_hline(yintercept = avg_ret, linetype = "dashed", color = "black", linewidth = 0.5, alpha = .2) +
    geom_vline(xintercept = avg_vol, linetype = "dashed", color = "black", linewidth = 0.5, alpha = .2) +
    scale_color_manual(values = palette) +
    scale_size_continuous(labels = scales::label_comma()) +
    labs(
      title = "Industry Risk vs Return (Top-left is most attractive)",
      x = "Volatility (12m)",
      y = "Excess return over benchmark (12m)",
      size = "Job postings"
    ) +
    theme_clairvoyant() +
    theme(legend.position = "none")
}

plot_correlation_matrix <- function(df,
                                    title = "Correlation matrix",
                                    cols,
                                    low = "#7AC5CD",
                                    mid = "white",
                                    high = "#FF7F50") {
  d <- df %>% select(all_of(cols))
  cmat <- cor(d, use = "pairwise.complete.obs")
  ggcorrplot(
    cmat,
    lab = TRUE,
    lab_size = 3,
    method = "circle",
    type = "lower",
    title = title,
    colors = c(low, mid, high)
  ) +
    theme_clairvoyant() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1, size = 9),
          axis.text.y = element_text(size = 9)) +
    labs(x = NULL, y = NULL)
}

plot_distributions <- function(df, cols) {
  df_long <- df %>%
    select(all_of(cols)) %>%
    pivot_longer(everything(), names_to = "variable", values_to = "value") %>%
    mutate(variable = gsub("_", " ", variable))

  ggplot(df_long, aes(x = value)) +
    geom_density(color = "black", fill = NA, linewidth = 0.7) +
    facet_wrap(~ variable, scales = "free", ncol = 3) +
    scale_x_continuous(labels = label_number(scale_cut = cut_short_scale())) +
    theme_clairvoyant() +
    labs(
      title = "Distributions of key metrics",
      x = NULL,
      y = "Density"
    ) +
    theme(strip.text = element_text(face = "bold"))
}
