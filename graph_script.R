library(dplyr)
library(ggcorrplot)
library(ggplot2)
library(tidyr)
library(scales)



#df <- read.csv("/Users/aishanipradhan/Downloads/final_data_merged.csv")
df <- read.csv('/Users/louis/Desktop/CMU Grad/Fall/Professional Skills/Clairvoyant/final_data.csv')

# graph 1
# Summarize for Aerospace
comms <- df |>
  filter(Industry == "Communication Services") |>
  group_by(finance_name) |>
  summarise(
    Views = mean(views, na.rm = TRUE),
    `Follower Count` = mean(follower_count, na.rm = TRUE),
    `Company Health Score` = mean(Company_Health_Score, na.rm = TRUE),
    `Company Return (%)` = mean(Company_Return_12m, na.rm = TRUE),
    .groups = "drop"
  )

# Correlation matrix
comms_quant_cor <- cor(
  select(comms, Views, `Follower Count`, `Company Health Score`, `Company Return (%)`),
  use = "pairwise.complete.obs"
)

# Correlation plot with custom color scale
ggcorrplot(
  comms_quant_cor,
  lab = TRUE,
  lab_size = 3,
  method = "circle",
  type = "lower",
  title = "Communication Services",
  colors = c("#7AC5CD", "white", "#FF7F50")
) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  theme(
    plot.title = element_text(hjust = 0.5, face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 9),
    axis.text.y = element_text(size = 9)
  ) +
  labs(x = NULL, y = NULL)

# Summarize for Aerospace
comms <- df |>
  filter(Industry == "Aerospace & Defense") |>
  group_by(finance_name) |>
  summarise(
    Views = mean(views, na.rm = TRUE),
    `Follower Count` = mean(follower_count, na.rm = TRUE),
    `Company Health Score` = mean(Company_Health_Score, na.rm = TRUE),
    `Company Return (%)` = mean(Company_Return_12m, na.rm = TRUE),
    .groups = "drop"
  )

# Correlation matrix
comms_quant_cor <- cor(
  select(comms, Views, `Follower Count`, `Company Health Score`, `Company Return (%)`),
  use = "pairwise.complete.obs"
)

# Correlation plot with Dark2 palette
ggcorrplot(
  comms_quant_cor,
  lab = TRUE,
  lab_size = 3,
  method = "circle",
  type = "lower",
  title = "Aerospace & Defense",
  colors = c("#7AC5CD", "white", "#FF7F50")) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  theme(
    plot.title = element_text(hjust = 0.5, face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 9),
    axis.text.y = element_text(size = 9)
  ) +
  labs(x = NULL, y = NULL)

library(dplyr)
library(ggplot2)
library(scales)

# graph 3
df_filtered <- df |>
  filter(Industry %in% c("Aerospace & Defense", "Communication Services")) |>
  group_by(finance_name) |>
  filter(n() > 50) |>
  ungroup()

df_company <- df_filtered |>
  group_by(Industry, finance_name, company_name) |>
  summarise(
    avg_followers = mean(follower_count, na.rm = TRUE),
    avg_health = mean(Company_Health_Score, na.rm = TRUE),
    .groups = "drop"
  )

df_summary <- df_company |>
  group_by(Industry, finance_name) |>
  summarise(
    sum_avg_followers = sum(avg_followers, na.rm = TRUE),
    avg_health = mean(avg_health, na.rm = TRUE),
    .groups = "drop"
  )

max_followers <- max(df_summary$sum_avg_followers, na.rm = TRUE)
max_health <- max(df_summary$avg_health, na.rm = TRUE)
scale_factor <- max_followers / max_health

ggplot(df_summary, aes(x = reorder(finance_name, sum_avg_followers))) +
  geom_col(aes(y = sum_avg_followers, fill = "Follower Count")) +
  geom_line(aes(y = avg_health * scale_factor, group = 1, color = "Company Health Score"), linewidth = 1.2) +
  facet_wrap(~ Industry, scales = "free_x") +
  scale_y_continuous(
    name = "Follower Count",
    labels = comma,
    sec.axis = sec_axis(~ . / scale_factor, name = "Company Health Score")
  ) +
  scale_fill_manual(values = c("Follower Count" = "#1f77b4")) +
  scale_color_manual(values = c("Company Health Score" = "#ff7f0e")) +
  labs(
    title = "Follower Count and Health Score by Company",
    x = "Company Name",
    fill = "",
    color = "",
    caption = "Dataset filtered to companies with > 50 job postings"
  ) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  theme(
    legend.position = "top",
    plot.title = element_text(hjust = 0.5, face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 9),
    panel.spacing = unit(1, "lines"),
    plot.caption = element_text(hjust = 1, size = 10, face = "italic")  # bottom-right
  )


library(tidyverse)

final_data <- read.csv("/Users/aishanipradhan/Downloads/final_data_merged.csv")

# Summarize
company_summary <- final_data |>
  group_by(finance_name, Industry) |>
  summarise(
    Open_Jobs = n(),
    Avg_Health_Score = mean(Company_Health_Score, na.rm = TRUE),
    .groups = "drop"
  )

# Custom colors for industries
industry_colors <- c(
  "Aerospace & Defense" = "#7AC5CD",      # teal-blue
  "Communication Services" = "#FF7F50",
  "Consumer Discretionary" = "#BCEE68",
  "Software" = "#FFE4E1",
  "Technology" = "#836FFF"
)

# Create scatterplot
ggplot(company_summary, aes(
  y = Open_Jobs,
  x = Avg_Health_Score,
  color = Industry
)) +
  geom_point(size = 3, alpha = 0.8) +
  scale_color_manual(values = industry_colors) +
  labs(
    title = "Number of Job Postings vs Company Health",
    y = "Number of Job Postings",
    x = "Company Health Score"
  ) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  theme(
    legend.position = "right",
    plot.title = element_text(hjust = 0.5, face = "bold"),
    axis.text = element_text(size = 9),
    plot.margin = margin(15, 20, 15, 20) # top, right, bottom, left (in pts)
  )


library(tidyverse)

final_data <- read.csv("/Users/aishanipradhan/Downloads/final_data_merged.csv")

# Summarize by company
company_summary <- final_data |>
  group_by(finance_name, Industry) |>
  summarise(
    Open_Jobs = n(),
    Avg_Health_Score = mean(Company_Health_Score, na.rm = TRUE),
    .groups = "drop"
  )

# Compute correlation between Open_Jobs and Avg_Health_Score by industry
industry_corr <- company_summary |>
  group_by(Industry) |>
  summarise(
    correlation = cor(Open_Jobs, Avg_Health_Score, use = "pairwise.complete.obs")
  )

# Custom colors for industries (optional if using a continuous fill scale)
industry_colors <- c(
  "Aerospace & Defense" = "#7AC5CD",
  "Communication Services" = "#FF7F50",
  "Consumer Discretionary" = "#BCEE68",
  "Software" = "#FFE4E1",
  "Technology" = "#836FFF"
)

# Create heatmap of correlations
ggplot(industry_corr, aes(x = Industry, y = 1, fill = correlation)) +
  geom_tile(color = "white", linewidth = 0.5) +
  geom_text(aes(label = round(correlation, 2)), color = "black", size = 4) +
  scale_fill_gradient2(
    low = "#7AC5CD",
    mid = "white",
    high = "#FF7F50",
    midpoint = 0,
    name = "Correlation"
  ) +
  labs(
    title = "Correlation Between Company Health and Number of Job Postings by Industry",
    x = NULL,
    y = NULL
  ) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  theme(
    legend.position = "right",
    plot.title = element_text(hjust = 0.5, face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 10),
    axis.text.y = element_blank(),
    panel.grid = element_blank(),
    plot.margin = margin(15, 20, 15, 20)
  )


# graph 3

df_filtered <- df |>
  filter(Industry %in% c("Aerospace & Defense", "Communication Services")) |>
  group_by(finance_name) |>
  filter(n() > 50) |>
  ungroup()

df_company <- df_filtered |>
  group_by(Industry, finance_name) |>
  summarise(
    job_postings = n(),
    avg_health = mean(Company_Health_Score, na.rm = TRUE),
    .groups = "drop"
  )

df_company |>
  select(finance_name, job_postings:avg_health) |>
  pivot_longer(
    job_postings:avg_health,
    names_to = "variable",
    values_to = "raw_value"
  ) |>
  group_by(variable) |>
  mutate(std_value = (raw_value - mean(raw_value)) / sd(raw_value)) |>
  ungroup() |>
  # Recode variable names for nicer axis labels
  mutate(variable = recode(variable,
                           "job_postings" = "Number of Job Postings",
                           "avg_health" = "Company Health Score"
  )) |>
  ggplot(aes(x = finance_name, y = variable, fill = std_value)) +
  geom_tile(color = "white", linewidth = 0.2) +
  scale_fill_gradient(
    low = "#FF69B4",  # light blue
    high = "#8B3A62", # deep navy blue
    name = NULL
  ) +
  labs(
    x = "Company Name",
    y = NULL
  ) + 
  labs(
    title = "Heatmap of Health Score and Number of Job Postings \nAcross Companies",
    caption = "Data filtered to Aerospace & Defense and Communication Services industries\nAnd companies with > 50 job postings",
    x = NULL,
    y = NULL
  )+
  theme_light(base_size = 12, base_family = "Helvetica") +
  theme(
    axis.text.x = element_text(size = 7, angle = 45, hjust = 1),
    axis.text.y = element_text(size = 10),
    legend.position = "bottom",
    panel.grid = element_blank(),
    plot.title = element_text(hjust = 0.5, face = "bold"),
    plot.caption = element_text(size = 9, hjust = 1, face = "italic")
  )


df_filtered |>
  filter(finance_name %in% c("Verizon Communications Inc.", "AT&T Inc.")) |>
  ggplot(aes(x = "", fill = finance_name)) +
  geom_bar(stat = "count", width = 0.5) +
  scale_fill_manual(
    values = c(
      "Verizon Communications Inc." = "#CD0000",  # soft red
      "AT&T Inc." = "#3A5FCD"                    # soft blue
    )
  ) +
  labs(
    title = "Number of Job Postings for Verizon and AT&T",
    x = NULL,
    y = "Number of Job Postings",
    fill = "Company"
  ) +
  theme_light(base_size = 12, base_family = "Helvetica") +
  theme(
    axis.text.x = element_blank(),
    axis.text.y = element_text(size = 10),
    panel.grid = element_blank(),
    plot.title = element_text(hjust = 0.5, face = "bold"),
    legend.position = "bottom"
  )

# Load libraries
library(tidyverse)
library(GGally)

library(tidyverse)

library(tidyverse)

library(tidyverse)
library(scales)  # for pretty axis labels

library(tidyverse)
library(scales)

# Select and reshape to long format
df_long <- df %>%
  select(
    views,
    follower_count,
    Industry_Health_Score,
    Industry_Return_12m,
    Industry_Vol_12m,
    Company_Health_Score,
    Company_Return_12m,
    Company_Excess_Return_12m,
    Company_Vol_12m
  ) %>%
  pivot_longer(everything(), names_to = "variable", values_to = "value") %>%
  # Clean variable names
  mutate(variable = str_replace_all(variable, "_", " "),
         variable = case_when(
           variable == "views" ~ "Views",
           variable == "follower count" ~ "Follower Count",
           TRUE ~ variable
         ))

# Plot black density curves with readable facet titles
ggplot(df_long, aes(x = value)) +
  geom_density(color = "black", fill = NA, linewidth = 0.7) +
  facet_wrap(~ variable, scales = "free", ncol = 3) +
  scale_x_continuous(labels = label_number(scale_cut = cut_short_scale())) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  labs(
    title = "Distributions of Company and Industry Metrics",
    x = NULL,
    y = "Density"
  ) +
  theme(
    strip.text = element_text(face = "bold"),
    plot.title = element_text(hjust = 0.5, face = "bold"),
    panel.grid = element_blank()
  )

library(dplyr)
library(ggplot2)
library(scales)

final_data_merged <- final_data_merged %>%
  group_by(Industry) %>%
  mutate(job_postings = n()) %>%
  ungroup()

# calculate averages
avg_vol <- mean(final_data_merged$Industry_Vol_12m, na.rm = TRUE)
avg_ret <- mean(final_data_merged$Industry_Return_12m, na.rm = TRUE)

ggplot(final_data_merged, aes(x = Industry_Vol_12m, 
                              y = Industry_Return_12m,
                              color = Industry,
                              size = job_postings)) +
  geom_point(alpha = 0.8) +
  geom_hline(yintercept = avg_ret, linetype = "dashed", color = "black", size = 0.8) +
  geom_vline(xintercept = avg_vol, linetype = "dashed", color = "black", size = 0.8) +
  scale_color_manual(values = c("#7AC5CD", "#FF7F50", "#BCEE68", "#EEA9b8", "#836FFF")) +
  labs(
    title = "Industry Return vs. Risk",
    x = "Volatility (%)",
    y = "Return (%)",
    size = "Number of Job Postings (Hundred of Thousands)",
    caption = "Dashed horizontal line: Average Return across industries\nDashed vertical line: Average Volatility across industries"
  ) +
  scale_size_continuous(labels = label_comma()) +
  theme_minimal(base_size = 12, base_family = "Helvetica") +
  theme(
    plot.title = element_text(hjust = 0.5, face = "bold"),
    axis.text.x = element_text(hjust = 1, size = 9),
    plot.caption = element_text(hjust = 1, vjust = 1, size = 10, face = "italic")
  )
