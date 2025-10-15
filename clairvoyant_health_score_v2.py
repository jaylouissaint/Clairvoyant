from clairvoyant_helper_functions import trailing_return, realized_vol, max_drawdown, zscore, get_labels_safe, get_top_holdings
import yfinance as yf
import pandas as pd
import numpy as np

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
    "Industry", "Ticker", "Industry_Health_Score",
    "Industry_Return_12m", "Industry_Return_3m",
    "Industry_Excess_Return_12m", "Industry_Excess_Return_3m",
    "Industry_Vol_12m"
]]

# ---------- NEW: Pick Top 5 industries dynamically ----------
TOP_N = 5
top_rows = (df_ind
            .sort_values("Industry_Health_Score", ascending=False)
            .head(TOP_N)[["Industry","Ticker"]])
TOP5 = [{"Industry": r.Industry, "Ticker": r.Ticker} for r in top_rows.itertuples(index=False)]


# ---------- Build ETF -> tickers map from live holdings (with safe fallback) ----------
ETF_TO_TICKERS = {}
for item in TOP5:
    etf = item["Ticker"]
    holdings = get_top_holdings(etf, top_k=20)
    # If API gave nothing, you can optionally seed a minimal list (commented)
    # if not holdings and etf in {"ITA","VGT","VOX","SOXX","IGV","IYC"}:
    #     holdings = ["AAPL","MSFT","NVDA"]  # placeholder fallback
    ETF_TO_TICKERS[etf] = holdings

# ---------- Block 2: Company + Sub-Industry (TOP5 ETFs vs SPY) ----------
ALL_TICKERS_2 = sorted({t for it in TOP5 for t in ETF_TO_TICKERS.get(it["Ticker"], []) if isinstance(t, str)})
prices_comp = yf.download(ALL_TICKERS_2 + [BENCH], period="3y", interval="1d",
                          auto_adjust=True, progress=False)["Close"]

spy_comp = prices_comp[BENCH]
spy_ret3_comp  = trailing_return(spy_comp, 63)
spy_ret12_comp = trailing_return(spy_comp, 252)

all_comp_rows, all_sub_rows = [], []

for item in TOP5:
    parent_industry = item["Industry"]      # will become our "Industry" column
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
    industry_metrics.drop(columns=["Ticker"]),
    left_on="ETF_Name",
    right_on="Industry",
    how="left"
)

# ---------- Final selection & de-dup ----------
Final_Financial_Dataframe = companies_enriched.rename(columns={
    "ETF_Name": "Industry"
})[[
    "Company",
    "Industry",
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

Final_Financial_Dataframe_unique = (
    Final_Financial_Dataframe
    .sort_values(["Company_Health_Score", "Industry_Health_Score"], ascending=False)
    .drop_duplicates(subset="Company", keep="first")
    .reset_index(drop=True)
)

print("Top industries (dynamic):")
print(top_rows.to_string(index=False))
print("\nUnique companies:", Final_Financial_Dataframe_unique["Company"].nunique(),
      "| Rows:", len(Final_Financial_Dataframe_unique))
