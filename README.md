# clAIrvoyant — Evaluating Industry Alliances (Data + Market Signals)

## Overview
This project supports a mock “client” (clAIrvoyant) that wants to identify **which industry sectors are actively hiring**, assess whether those sectors appear **financially healthy**, and recommend **potential anchor clients** for a go-to-market strategy.

The assignment framing: analyze hiring + market data, identify a target sector, determine sector leaders, and communicate insights to a non-technical executive audience. (See the assignment prompt in `docs/`.) 

## What we built
I created a small analytics pipeline that:
1. **Cleans and merges job posting / hiring-related data**
2. **Maps company names** across datasets (job postings ↔ finance identifiers)
3. Computes **industry- and company-level financial indicators** (returns, volatility, drawdown, etc.)
4. Combines these features into a **Company Health Score** to compare companies/industries
5. Produces **visual analytics** (correlations, distributions, sector comparisons) and a **time-series benchmark** vs the S&P 500.

## Repo contents
- `src/`
  - `helper_functions.py`: reusable finance metrics (returns, vol, drawdown, z-scores, etc.)
  - `health_score.py`: logic to compute industry/company metrics and the composite health score
  - `build_dataset.py`: dataset merge + mapping utilities
- `reports/`
  - `Clairvoyant_Graphs.qmd`: main report with final visuals + narrative
  - `figures/`: exported charts used in the report/presentation
- `R/`
  - `time_series.R`: excess returns vs S&P 500 + rolling volatility (example companies)
  - `plot_functions.R`: reusable plotting helpers (if running the R workflow)
- `docs/`
  - `assignment_prompt.pdf`: original prompt / business context

## Key analyses
### Company / Industry “Health”
Health is calculated using market-derived indicators (returns, risk/volatility, drawdowns, relative performance vs benchmark), standardized and combined into a single score so industries/companies can be compared consistently.

### Visual insights
The report includes:
- correlation views of hiring signals (e.g., LinkedIn followers/views) vs health/returns
- comparisons of health score vs job posting intensity across industries/companies
- distribution plots to understand skew/outliers before ranking recommendations

### Time-series benchmark
A focused comparison of example companies vs the S&P 500:
- daily excess returns
- rolling 30-day annualized volatility
(see `R/time_series.R`)

## How to run
### Python
```bash
pip install -r requirements.txt
```

## Data
This project combines labor market data (LinkedIn job postings) with financial market data (ETF + company-level stock performance) to analyze the relationship between hiring activity and financial health.

### LinkedIn Job Postings Dataset
Source:
Kaggle — LinkedIn Job Postings (2023–2024)
https://www.kaggle.com/datasets/arshkon/linkedin-job-postings

#### Dataset Overview

This dataset contains a nearly comprehensive record of 124,000+ job postings from 2023–2024. Each posting includes detailed attributes about the job and associated company.

##### Key Fields Used in This Project
From the job postings file:
company_name, title, description, location, formatted_experience_level, work_type (remote, hybrid, onsite), salary-related fields, job-level metadata (application links, posting time, etc.)

From related company files:
company description, headquarters, industry, number of employees, LinkedIn follower count

From skills/industry mapping files:
job-to-skill relationships, job-to-industry classification

Why This Dataset Was Chosen

This dataset provides a large-scale snapshot of real hiring behavior, enabling: Measurement of hiring intensity (number of job postings), Industry-level hiring comparisons, Company-level hiring comparisons, Analysis of whether financial “health” aligns with hiring demand


### Financial Market Data

Financial data is retrieved programmatically using the Yahoo Finance API (via yfinance).

#### What Was Collected
Daily price data (3-year window), 3-month and 12-month trailing returns, Excess returns relative to the S&P 500 (SPY), 1-year realized volatility, 3-year maximum drawdown

These metrics are computed at:
Industry level (using ETF proxies), Sub-industry level, Company level

These are combined into a standardized Health Score.

#### finance_mapping.csv (Manual Mapping Layer)

This file was created manually to resolve inconsistencies between: Company names in the LinkedIn dataset, Company names used in financial datasets

This was necessary because company names may appear as: Subsidiaries (e.g., “Raytheon Missiles & Defense”), Business units (e.g., “Amazon Web Services”), Slight spelling variations, Legal entity differences

The finance_mapping file maps subsidiaries and alternative spellings to a single parent company.This manual mapping step reflects a common real-world data engineering task, entity resolution and cross-dataset harmonization.

### Data Integration Strategy

The final analytical dataset is built through cleaning and standardizing job postings, mapping company names to financial parent entities, joining financial metrics to company-level hiring data, merging follower counts and industry classifications, removing unused/highly sparse columns, and standardizing text formatting for consistent joins. The result is a merged dataset that connects hiring activity, financial health, and industry classification. 

## Notes on Reproducibility

Raw job posting data is not included in this repository due to size and licensing considerations.

Financial data is pulled dynamically via Yahoo Finance.

The manual finance_mapping.csv file is required to replicate entity matching.
