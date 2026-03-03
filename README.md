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


## Data is available for dowload at the link below
https://www.kaggle.com/datasets/arshkon/linkedin-job-postings
