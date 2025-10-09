# ===============================================
# Final_Financial_Dataframe builder (Colab-ready)
# ===============================================

import numpy as np
import pandas as pd
import yfinance as yf

# ---------- Helper functions ----------
def trailing_return(series, lookback_days):
    s = series.dropna()
    if len(s) < lookback_days + 1:
        return np.nan
    return s.iloc[-1] / s.iloc[-lookback_days - 1] - 1

def realized_vol(series, lookback_days=252):
    r = series.dropna().pct_change().dropna().tail(lookback_days)
    if r.empty:
        return np.nan
    return np.sqrt(252) * r.std()

def max_drawdown(series):
    s = series.dropna()
    if s.empty:
        return np.nan
    return (s / s.cummax() - 1.0).min()

def zscore(x):
    x = pd.Series(x, dtype=float)
    std = x.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(np.zeros(len(x)), index=x.index)
    return (x - x.mean()) / std

# ---------- Block 1: Industry-level (ETF proxies vs SPY) ----------
SECTOR_ETFS = {
    "Materials": "IYM",
    "Energy": "IYE",
    "Financials": "IYF",
    "Industrials": "IYJ",
    "Technology": "VGT",
    "Consumer Staples": "IYK",
    "Utilities": "IDU",
    "Health Care": "VHT",
    "Consumer Discretionary": "IYC",
    "Real Estate": "IYR",
    "Communication Services": "VOX"
}
EXTRA_INDUSTRY_ETFS = {
    "Semiconductors": "SOXX",
    "Software": "IGV",
    "Aerospace & Defense": "ITA"
}

ALL = {**SECTOR_ETFS, **EXTRA_INDUSTRY_ETFS}
BENCH = "SPY"

tickers = list(ALL.values())
prices_ind = yf.download(tickers + [BENCH], period="3y", interval="1d",
                         auto_adjust=True, progress=False)["Close"]

spy_ind = prices_ind[BENCH]
spy_ret3_ind  = trailing_return(spy_ind, 63)
spy_ret12_ind = trailing_return(spy_ind, 252)

rows_ind = []
for ind_name, ind_ticker in ALL.items():
    if ind_ticker not in prices_ind.columns:
        continue
    s = prices_ind[ind_ticker]
    r3  = trailing_return(s, 63)
    r12 = trailing_return(s, 252)
    vol = realized_vol(s, 252)
    mdd = max_drawdown(s)
    rows_ind.append({
        "Industry": ind_name,
        "Ticker": ind_ticker,
        "Return_3m": r3,
        "Return_12m": r12,
        "Excess_3m": r3 - spy_ret3_ind,
        "Excess_12m": r12 - spy_ret12_ind,
        "Vol_1y": vol,
        "MaxDD_3y": mdd
    })

df_ind = pd.DataFrame(rows_ind)

# HealthScore (industry) from EXCESS returns + lower risk
w_ex12, w_ex3, w_risk = 0.45, 0.35, 0.20
risk_component_ind = -0.5 * zscore(df_ind["Vol_1y"]) + -0.5 * zscore(df_ind["MaxDD_3y"].abs())
df_ind["Industry_Health_Score"] = 100 * (
    w_ex12 * zscore(df_ind["Excess_12m"].fillna(0)) +
    w_ex3  * zscore(df_ind["Excess_3m"].fillna(0))  +
    w_risk * risk_component_ind.fillna(0)
)

# Keep only the columns we need (raw decimals, not percents)
industry_metrics = df_ind.rename(columns={
    "Return_12m": "Industry_Return_12m",
    "Return_3m": "Industry_Return_3m",
    "Excess_12m": "Industry_Excess_Return_12m",
    "Excess_3m": "Industry_Excess_Return_3m",
    "Vol_1y": "Industry_Vol_12m"
})[[
    "Industry", "Industry_Health_Score",
    "Industry_Return_12m", "Industry_Return_3m",
    "Industry_Excess_Return_12m", "Industry_Excess_Return_3m",
    "Industry_Vol_12m"
]]

# ---------- Block 2: Company + Sub-Industry (TOP5 ETFs vs SPY) ----------
TOP5 = [
    {"Industry": "Aerospace & Defense", "Ticker": "ITA"},
    {"Industry": "Technology", "Ticker": "VGT"},
    {"Industry": "Communication Services", "Ticker": "VOX"},
    {"Industry": "Technology", "Ticker": "SOXX"},  # thematic sub-sector ETF
    {"Industry": "Software", "Ticker": "IGV"},
    {"Industry": "Consumer Discretionary", "Ticker": "IYC"}

]

ETF_TO_TICKERS = {
    "ITA": ["RTX", "BA", "LHX", "NOC", "GD", "HII", "TDG", "TXT", "LMT"],
    "VOX": ["NFLX", "GOOGL", "T", "META", "DIS", "TMUS", "VZ", "CHTR", "CMCSA"],
    "VGT": ["AVGO", "NVDA", "CSCO", "AAPL", "CRM", "ACN"],
    "IGV": ["PLTR", "SNOW", "ORCL", "PANW", "MSFT", "INTU", "NOW", "TEAM", "ADBE"],
    "SOXX": ["NVDA", "AVGO"],
    "IYC": ["TSLA", "BKNG", "TJX", "AMZN", "HD", "MCD", "LOW", "SBUX", "NKE"],
}

# Build full company list and download prices + SPY
ALL_TICKERS_2 = sorted(set(t for item in TOP5 for t in ETF_TO_TICKERS.get(item["Ticker"], []) if isinstance(t, str)))
prices_comp = yf.download(ALL_TICKERS_2 + [BENCH], period="3y", interval="1d",
                          auto_adjust=True, progress=False)["Close"]

spy_comp = prices_comp[BENCH]
spy_ret3_comp  = trailing_return(spy_comp, 63)
spy_ret12_comp = trailing_return(spy_comp, 252)

def get_labels_safe(ticker):
    info = {}
    try:
        tk = yf.Ticker(ticker)
        info = tk.get_info() if hasattr(tk, "get_info") else tk.info
    except Exception:
        pass
    sector = info.get("sector") if isinstance(info, dict) else None
    industry = info.get("industry") if isinstance(info, dict) else None  # <-- Yahoo "industry" (we'll use as Sub_Industry)
    long_name = info.get("longName") if isinstance(info, dict) else None
    return sector, industry, long_name

# Collect company and sub-industry tables across all TOP5 ETFs
all_comp_rows = []
all_sub_rows  = []

for item in TOP5:
    parent_industry = item["Industry"]  # will become our "Industry" column
    etf_ticker = item["Ticker"]
    tickers = [t for t in ETF_TO_TICKERS.get(etf_ticker, []) if t in prices_comp.columns]

    # --- company rows for this ETF ---
    rows = []
    for t in tickers:
        s = prices_comp[t]
        ret_12 = trailing_return(s, 252)
        ret_3  = trailing_return(s, 63)
        vol_1y = realized_vol(s, 252)
        mdd_3y = max_drawdown(s)
        ex_12  = ret_12 - spy_ret12_comp
        ex_3   = ret_3  - spy_ret3_comp
        sector, sub_industry, long_name = get_labels_safe(t)
        rows.append({
            "ETF_Name": parent_industry,  # parent industry name (matches industry_metrics key)
            "Ticker": t,
            "Company": long_name or t,
            "Sector": sector,
            "Sub_Industry": sub_industry,  # Yahoo's "industry"
            "Company_Return_12m": ret_12,
            "Company_Return_3m": ret_3,
            "Company_Excess_Return_12m": ex_12,
            "Company_Excess_Return_3m": ex_3,
            "Company_Vol_12m": vol_1y,
            "MaxDD_3y": mdd_3y
        })
    comp_df = pd.DataFrame(rows)

    # company score within this ETF’s constituents
    if not comp_df.empty:
        risk_component = -0.5 * zscore(comp_df["Company_Vol_12m"]) + -0.5 * zscore(comp_df["MaxDD_3y"].abs())
        comp_df["Company_Health_Score"] = 100 * (
            0.45 * zscore(comp_df["Company_Excess_Return_12m"].fillna(0)) +
            0.35 * zscore(comp_df["Company_Excess_Return_3m"].fillna(0))  +
            0.20 * risk_component.fillna(0)
        )
    else:
        comp_df["Company_Health_Score"] = np.nan

    # append to global list
    all_comp_rows.append(comp_df)

    # --- sub-industry aggregation inside this ETF ---
    if not comp_df.empty:
        sub = (comp_df
               .groupby("Sub_Industry", dropna=False)
               .agg(Sub_Industry_Return_12m=("Company_Return_12m", "mean"),
                    Sub_Industry_Return_3m=("Company_Return_3m", "mean"),
                    Sub_Industry_Excess_Return_12m=("Company_Excess_Return_12m", "mean"),
                    Sub_Industry_Excess_Return_3m=("Company_Excess_Return_3m", "mean"),
                    Sub_Industry_Vol_12m=("Company_Vol_12m", "median"),
                    Num_Names=("Ticker", "count"))
               .reset_index())

        sub["Sub_Industry_Health_Score"] = 100 * (
            0.45 * zscore(sub["Sub_Industry_Excess_Return_12m"].fillna(0)) +
            0.35 * zscore(sub["Sub_Industry_Excess_Return_3m"].fillna(0))  -
            0.20 * zscore(sub["Sub_Industry_Vol_12m"].fillna(0))
        )
        sub["ETF_Name"] = parent_industry  # to merge back to company rows
        all_sub_rows.append(sub)

# Concatenate all companies and sub-industries
companies_all = pd.concat(all_comp_rows, ignore_index=True) if all_comp_rows else pd.DataFrame()
subinds_all   = pd.concat(all_sub_rows,  ignore_index=True) if all_sub_rows  else pd.DataFrame()

# ---------- Join: company + sub-industry + industry ----------
# 1) Merge companies with their sub-industry metrics (on ETF_Name + Sub_Industry)
if not subinds_all.empty:
    companies_enriched = companies_all.merge(
        subinds_all[[
            "ETF_Name","Sub_Industry","Sub_Industry_Health_Score",
            "Sub_Industry_Return_12m","Sub_Industry_Return_3m",
            "Sub_Industry_Excess_Return_12m","Sub_Industry_Excess_Return_3m",
            "Sub_Industry_Vol_12m"
        ]],
        on=["ETF_Name","Sub_Industry"],
        how="left"
    )
else:
    companies_enriched = companies_all.copy()
    companies_enriched["Sub_Industry_Health_Score"] = np.nan
    companies_enriched["Sub_Industry_Return_12m"] = np.nan
    companies_enriched["Sub_Industry_Return_3m"] = np.nan
    companies_enriched["Sub_Industry_Excess_Return_12m"] = np.nan
    companies_enriched["Sub_Industry_Excess_Return_3m"] = np.nan
    companies_enriched["Sub_Industry_Vol_12m"] = np.nan

# 2) Merge in industry-level metrics (on Industry name == ETF_Name)
companies_enriched = companies_enriched.merge(
    industry_metrics,
    left_on="ETF_Name",
    right_on="Industry",
    how="left",
    suffixes=("","")
)

# ---------- Final selection & renaming ----------
Final_Financial_Dataframe = companies_enriched.rename(columns={
    "ETF_Name": "Industry"
})[[
    "Company",
    "Industry",               # parent industry from TOP5/ETF
    "Sub_Industry",

    "Company_Health_Score",
    "Sub_Industry_Health_Score",
    "Industry_Health_Score",

    "Industry_Return_12m",
    "Industry_Return_3m",
    "Industry_Excess_Return_12m",
    "Industry_Excess_Return_3m",
    "Industry_Vol_12m",

    "Sub_Industry_Return_12m",
    "Sub_Industry_Return_3m",
    "Sub_Industry_Excess_Return_12m",
    "Sub_Industry_Excess_Return_3m",
    "Sub_Industry_Vol_12m",

    "Company_Return_12m",
    "Company_Return_3m",
    "Company_Excess_Return_12m",
    "Company_Excess_Return_3m",
    "Company_Vol_12m",
]]

# ---------- Export to CSV (Colab) ----------
Final_Financial_Dataframe.to_csv("Final_Financial_Dataframe.csv", index=False)
print("Saved: Final_Financial_Dataframe.csv  |  Rows:", len(Final_Financial_Dataframe))
