# R/time_series.R
# Time-series benchmark: Excess returns vs S&P 500 and rolling volatility.
#
# Refactored from your original script into small functions.

suppressPackageStartupMessages({
  library(tidyverse)
  library(tidyquant)
  library(lubridate)
  library(zoo)
})

compute_daily_returns <- function(prices_df) {
  prices_df %>%
    group_by(symbol) %>%
    mutate(daily_return = adjusted / lag(adjusted) - 1) %>%
    ungroup()
}

compute_excess_returns <- function(returns_df, tickers, benchmark) {
  sp500_returns <- returns_df %>%
    filter(symbol == benchmark) %>%
    select(date, sp_return = daily_return)

  returns_df %>%
    filter(symbol %in% tickers) %>%
    left_join(sp500_returns, by = "date") %>%
    mutate(excess_return = daily_return - sp_return)
}

compute_rolling_vol <- function(returns_df, tickers, window = 30) {
  returns_df %>%
    filter(symbol %in% tickers) %>%
    group_by(symbol) %>%
    mutate(
      rolling_vol = rollapply(
        daily_return, width = window, FUN = sd,
        align = "right", fill = NA, na.rm = TRUE
      ) * sqrt(252) * 100
    ) %>%
    ungroup()
}

plot_excess_returns <- function(excess_returns_df, label_map = NULL) {
  df <- excess_returns_df
  if (!is.null(label_map)) {
    df <- df %>% mutate(symbol = recode(symbol, !!!label_map))
  }

  ggplot(df, aes(x = date, y = excess_return * 100, color = symbol)) +
    geom_line(linewidth = 0.7, alpha = 0.7) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "gray60") +
    labs(
      title = "Excess Returns Over S&P 500",
      x = "Date",
      y = "Excess Return (%)",
      color = "Company"
    ) +
    theme_minimal(base_size = 12, base_family = "Helvetica") +
    theme(
      legend.position = "top",
      plot.title = element_text(hjust = 0.5, face = "bold"),
      axis.text = element_text(hjust = 1, size = 9)
    )
}

plot_rolling_vol <- function(vol_df, label_map = NULL) {
  df <- vol_df
  if (!is.null(label_map)) {
    df <- df %>% mutate(symbol = recode(symbol, !!!label_map))
  }

  ggplot(df, aes(x = date, y = rolling_vol, color = symbol)) +
    geom_line(linewidth = 1.1) +
    labs(
      title = "Rolling 30-Day Annualized Volatility",
      x = "Date",
      y = "Volatility (%)",
      color = "Company"
    ) +
    theme_minimal(base_size = 12, base_family = "Helvetica") +
    theme(
      legend.position = "top",
      plot.title = element_text(hjust = 0.5, face = "bold"),
      axis.text = element_text(hjust = 1, size = 9)
    )
}

# ---- Script entrypoint (safe to source) ----
run_time_series_analysis <- function(tickers = c("VZ", "T"),
                                     benchmark = "^GSPC",
                                     start_date = "2023-01-01",
                                     end_date = "2025-12-31",
                                     out_dir = "output") {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  prices <- tq_get(c(tickers, benchmark), from = start_date, to = end_date)
  returns <- compute_daily_returns(prices)

  excess <- compute_excess_returns(returns, tickers, benchmark)
  vol_df <- compute_rolling_vol(returns, tickers, window = 30)

  label_map <- c("VZ" = "Verizon", "T" = "AT&T")

  p1 <- plot_excess_returns(excess, label_map)
  p2 <- plot_rolling_vol(vol_df, label_map)

  ggsave(file.path(out_dir, "Excess_Returns_Verizon_AT&T.png"), plot = p1, width = 10, height = 6, dpi = 300)
  ggsave(file.path(out_dir, "Volatility_Verizon_AT&T.png"), plot = p2, width = 10, height = 6, dpi = 300)

  invisible(list(excess_plot = p1, vol_plot = p2, excess_df = excess, vol_df = vol_df))
}

if (sys.nframe() == 0) {
  run_time_series_analysis()
}
