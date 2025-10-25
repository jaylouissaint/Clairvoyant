df <- read.csv("final_data.csv")

library(dplyr)
company_counts <- df |>
  filter(industry %in% c("Semiconductors", "Technology")) |>
  group_by(industry, company) |>
  summarise(posting_count = n(), .groups = "drop") |>
  group_by(industry) |>
  filter(
    posting_count > mean(posting_count[company != "amazon.com, inc."], na.rm = TRUE)
  ) |>
  ungroup()


df_filtered <- df |>
  filter(
    industry %in% c("Semiconductors", "Technology"),
    company %in% company_counts$company
  )

df_filtered_tech <- df |>
  filter(
    industry %in% c("Technology"),
    company %in% company_counts$company) |>
  distinct(company, finance_mapping, company_health_score,company_vol_12m)

df_filtered_semi <- df |>
  filter(
    industry %in% c("Semiconductors"),
    company %in% company_counts$company
  ) |>
  distinct(company, finance_mapping, company_health_score, company_vol_12m)

library(ggplot2)
ggplot(df_filtered_, aes(x = finance_mapping, y = company_health_score)) +
  geom_col(
    color = "black",
    fill = "#6957CD",
    width = 1              
  ) +
  geom_text(
    aes(
      label = round(company_health_score, 2),
      vjust = ifelse(finance_mapping %in% c("CMicron Technology, Inc.", "QUALCOMM Incorporated"), 1.5, -0.3)  
    ),
    size = 4.3,
    fontface = "bold"
  ) +
  labs(
    title = "Healthscores of Companies with Job Postings Higher than Industry Average",
    x = "Company Name",
    y = "Company Health Score"
  ) +
  theme_minimal(base_size = 15, base_family = "Helvetica") +
  theme(
    plot.title = element_text(hjust = 0, face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 13, colour = "black"),
    axis.text.y = element_text(hjust = 1, size = 13,colour = "black"),
    panel.grid = element_blank(),
    panel.border = element_rect(colour = "black", fill = NA, linewidth = 0.8)
  ) +
  annotate(
    "segment",
    x = 1.64, y = 50,
    xend = 1.52, yend = 50,
    colour = "black",
    linewidth = 1,
    arrow = arrow(length = unit(0.2, "cm"))
  ) +
  annotate(
    "label",
    x = 1.95, y = 50,
    label = "Uses In-House Tech",
    fill = alpha("white", 0.7),
    color = "black",
    size = 3.5,
  ) 

library(ggplot2)
ggplot(df_filtered_semi, aes(x = finance_mapping, y = company_health_score)) +
  geom_col(
    color = "black",
    fill = "#6957CD",
    width = 1              
  ) +
  geom_text(
    aes(
      label = round(company_health_score, 2),
      vjust = ifelse(finance_mapping %in% c("CMicron Technology, Inc.", "QUALCOMM Incorporated"), 1.5, -0.3)  
    ),
    size = 4.3,
    fontface = "bold"
  ) +
  labs(
    title = "Healthscores of Companies with Job Postings Higher than Industry Average",
    x = "Company Name",
    y = "Company Health Score"
  ) +
  theme_minimal(base_size = 15, base_family = "Helvetica") +
  theme(
    plot.title = element_text(hjust = 0, face = "bold"),
    axis.text.x = element_text(angle = 45, hjust = 1, size = 13, colour = "black"),
    axis.text.y = element_text(hjust = 1, size = 13,colour = "black"),
    panel.grid = element_blank(),
    panel.border = element_rect(colour = "black", fill = NA, linewidth = 0.8)
  ) +
  annotate(
    "segment",
    x = 1.64, y = 50,
    xend = 1.52, yend = 50,
    colour = "black",
    linewidth = 1,
    arrow = arrow(length = unit(0.2, "cm"))
  ) +
  annotate(
    "label",
    x = 1.95, y = 50,
    label = "Uses In-House Tech",
    fill = alpha("white", 0.7),
    color = "black",
    size = 3.5,
  ) 

library(ggplot2)
ggplot(df_filtered_semi, aes(x = finance_mapping, y = company_health_score)) +
  geom_col(
    color = "black",
    fill = "#4b3e8f",
    width = 1              
  ) +
  geom_text(
    aes(
      label = round(company_health_score, 2),
      y = ifelse(company_health_score >= 0,
               company_health_score + 5,   # above positive bar
               company_health_score - 5)   # below negative bar
    ),
    size = 4.3,
    fontface = "bold"
  ) + annotate(
    "segment",
    x = 1.27, y = -30,       # start of arrow (left side, below bars)
    xend = 1.49, yend = -30,    # end of arrow (toward Qualcomm’s bar, adjust y)
    colour = "black",
    linewidth = 1,
    arrow = arrow(length = unit(0.15, "cm"))
  ) +
  annotate(
    "label",
    x = 1, y = -30,       # label on the left
    label = "Negative Health Score",
    fill = alpha("white", 0.7),
    color = "black",
    size = 3.5
  )+
  labs(
    title = "Health Score of Companies with Job Postings Higher than Industry Average",
    x = NULL,
    y = "Company Health Score"
  ) +
  theme_minimal(base_size = 15, base_family = "Helvetica")+
  theme(
    panel.grid = element_blank(),
    
    # Add border box around the panel
    panel.border = element_rect(color = "black", fill = NA, linewidth = 0.8),
    plot.title = element_text(hjust = 0.5, face = "bold", size = 13),
    plot.margin = margin(t = 25, r = 15, b = 15, l = 15),
    axis.text.x = element_text(color = "black")
  )

library(ggplot2)
ggplot(df_filtered_semi, aes(x = finance_mapping, y = company_vol_12m)) +
  geom_col(
    color = "black",
    fill = "#4b3e8f",
    width = 1              
  ) +
  geom_text(
    aes(
      label = round(company_vol_12m, 2),
      y = company_vol_12m + 0.05
    ),
    size = 4.3,
    fontface = "bold"
  ) +
  geom_hline(yintercept = 0.39, color = "red", linewidth = 1, linetype = "dashed") +
  annotate(
    "segment",
    x = 2.3, y = 0.45,       # start of arrow (adjust as needed)
    xend = 2.3, yend = 0.39, # points exactly to the line
    colour = "black",
    linewidth = 1,
    arrow = arrow(length = unit(0.2, "cm"))
  ) +
  # label box for the annotation
  annotate(
    "label",
    x = 2.3, y = 0.48, 
    label = "Industry Average",
    fill = alpha("white", 0.7),
    color = "black",
    size = 3.5
  ) +
  labs(
    title = "Volatility of Companies with Job Postings Higher than Industry Average",
    x = NULL,
    y = "Company Volatility"
  ) +
  theme_minimal(base_size = 15, base_family = "Helvetica")+
  theme(
    panel.grid = element_blank(),
    
    # Add border box around the panel
    panel.border = element_rect(color = "black", fill = NA, linewidth = 0.8),
    plot.title = element_text(hjust = 0.5, face = "bold", size = 14),
    plot.margin = margin(t = 25, r = 15, b = 15, l = 15),
    axis.text.x = element_text(color = "black")
  )

ggplot(df_filtered_tech, aes(x = finance_mapping, y = company_health_score)) +
  geom_col(
    color = "black",
    fill = "#6957CD",
    width = 1              
  ) +
  geom_text(
    aes(
      label = round(company_health_score, 2),
      y = ifelse(company_health_score >= 0,
               company_health_score + 5,   # above positive bar
               company_health_score - 5)   # below negative bar
    ),
    size = 4.3,
    fontface = "bold"
  ) +
  labs(
    title = "Healthscores of Companies with Job Postings Higher than Industry Average",
    x = NULL,
    y = "Company Healthscore"
  ) +
  theme_minimal(base_size = 15, base_family = "Helvetica")+
  theme(
    panel.grid = element_blank(),
    
    # Add border box around the panel
    panel.border = element_rect(color = "black", fill = NA, linewidth = 0.8),
    plot.title = element_text(hjust = 0.5, face = "bold", size = 13),
    plot.margin = margin(t = 25, r = 15, b = 15, l = 15),
    axis.text.x = element_text(color = "black")
  )

ggplot(df_filtered_tech, aes(x = finance_mapping, y = company_vol_12m)) +
  geom_col(
    color = "black",
    fill = "#6957CD",
    width = 1              
  ) +
  geom_text(
    aes(
      label = round(company_vol_12m, 2),
      y = ifelse(company_vol_12m >= 0,
               company_vol_12m + 0.05,   # above positive bar
               company_vol_12m - 5)   # below negative bar
    ),
    size = 4.3,
    fontface = "bold"
  ) +
  labs(
    title = "Volatility of Companies with Job Postings Higher than Industry Average",
    x = NULL,
    y = "Company Volatility"
  ) +
  theme_minimal(base_size = 15, base_family = "Helvetica")+
  theme(
    panel.grid = element_blank(),
    
    # Add border box around the panel
    panel.border = element_rect(color = "black", fill = NA, linewidth = 0.8),
    plot.title = element_text(hjust = 0.5, face = "bold", size = 13),
    plot.margin = margin(t = 25, r = 15, b = 15, l = 15),
    axis.text.x = element_text(color = "black")
  )

clairvoyant_palette <- c(
  "#4b3e8f","#6957cd","#402b2a","#4281a3","#c6b9f6","#140f49","#b9cadd"
)

library(ggplot2)

clairvoyant_palette <- c(
  "#4b3e8f","#6957cd","#402b2a","#4281a3","#c6b9f6","#140f49","#b9cadd"
)

df <- data.frame(
  x = factor(seq_along(clairvoyant_palette)),
  col = clairvoyant_palette
)

ggplot(df, aes(x = x, y = 1, fill = col)) +
  geom_col() +
  scale_fill_identity() +
  scale_x_discrete(labels = clairvoyant_palette) +
  theme_void() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
