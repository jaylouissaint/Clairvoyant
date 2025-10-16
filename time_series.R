library(tidyverse)
library(tidyquant)
library(lubridate)
library(zoo)

tickers <- c("VZ", "T")     # Verizon & AT&T
benchmark <- "^GSPC"        # S&P 500
start_date <- "2023-01-01"
end_date <- "2025-12-31"

prices <- tq_get(c(tickers, benchmark), from = start_date, to = end_date)

returns <- prices %>%
  group_by(symbol) %>%
  mutate(daily_return = adjusted / lag(adjusted) - 1) %>%
  ungroup()

sp500_returns <- returns %>%
  filter(symbol == benchmark) %>%
  select(date, sp_return = daily_return)

excess_returns <- returns %>%
  filter(symbol %in% tickers) %>%
  left_join(sp500_returns, by = "date") %>%
  mutate(excess_return = daily_return - sp_return)

excess_returns <- excess_returns %>%
  mutate(symbol = recode(symbol,
                         "VZ" = "Verizon",
                         "T"  = "AT&T"))

p1 <- ggplot(excess_returns, aes(x = date, y = excess_return * 100, color = symbol)) +
  geom_line(linewidth = 0.7, alpha = 0.7) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray60") +
  scale_color_manual(
    values = c("Verizon" = "#CD0000", "AT&T" = "#3A5FCD"),
    name = "Company"
  ) +
  labs(
    title = "Excess Returns Over S&P 500 (2023–2025)",
    x = "Year",
    y = "Excess Return (%)"
  ) +
    theme_minimal(base_size = 12, base_family = "Helvetica") +
    theme(
      legend.position = "top",
      plot.title = element_text(hjust = 0.5, face = "bold"),
      axis.text = element_text(hjust = 1, size = 9))

volatility_data <- returns %>%
  filter(symbol %in% tickers) %>%
  group_by(symbol) %>%
  mutate(
    rolling_vol_30d = rollapply(
      daily_return, width = 30, FUN = sd,
      align = "right", fill = NA, na.rm = TRUE
    ) * sqrt(252) * 100  # Annualized %
  ) %>%
  ungroup() %>%
  mutate(symbol = recode(symbol,
                         "VZ" = "Verizon",
                         "T"  = "AT&T"))

p2 <- ggplot(volatility_data, aes(x = date, y = rolling_vol_30d, color = symbol)) +
  geom_line(linewidth = 1.1) +
  scale_color_manual(
    values = c("Verizon" = "#CD0000", "AT&T" = "#3A5FCD"),
    name = "Company"
  ) +
  labs(
    title = "Volatility for Verizon and AT&T (2023–2025)",
    x = "Year",
    y = "Volatility (%)"
  ) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  theme(
      legend.position = "top",
      plot.title = element_text(hjust = 0.5, face = "bold"),
      axis.text = element_text(hjust = 1, size = 9))

p1
p2

ggsave("Excess_Returns_Verizon_AT&T.png", plot = p1, width = 10, height = 6, dpi = 300)
ggsave("Volatility_Verizon_AT&T.png", plot = p2, width = 10, height = 6, dpi = 300)