"""
src/health_score.py

Compute Industry / Sub-Industry / Company health metrics using ETF proxies and a benchmark.

This module refactors the notebook/script logic into small, testable functions.

Typical workflow
----------------
1) Compute industry metrics for a list of ETF proxies vs a benchmark (SPY).
2) Pick top-N industries by Industry Health Score.
3) For each top industry ETF, retrieve holdings (constituents).
4) Compute company metrics for constituents vs benchmark, and aggregate into sub-industries.
5) Join metrics together for an exportable table.

All returns are decimals, not percentages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import os

from helper_functions import (
    trailing_return,
    realized_vol,
    max_drawdown,
    get_labels_safe,
    get_top_holdings,
    safe_yf_download,
    compute_health_score,
    zscore,
)


# --- Defaults taken from your notebook/script ---

SECTOR_ETFS_DEFAULT: Dict[str, str] = {
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
    "Communication Services": "VOX",
}

EXTRA_INDUSTRY_ETFS_DEFAULT: Dict[str, str] = {
    "Semiconductors": "SOXX",
    "Software": "IGV",
    "Aerospace & Defense": "ITA",
}

BENCHMARK_DEFAULT = "SPY"


@dataclass(frozen=True)
class HealthScoreConfig:
    """
    Configuration for the Health Score formula.

    The default weights match your walkthrough reasoning:
    - 45%: Excess 12M return
    - 35%: Excess 3M return
    - 10%: Volatility penalty
    - 10%: Max drawdown penalty
    """
    w_ex12: float = 0.45
    w_ex3: float = 0.35
    w_vol: float = 0.10
    w_mdd: float = 0.10
    scale: float = 100.0


def compute_industry_metrics(
    industry_to_etf: Dict[str, str],
    benchmark: str = BENCHMARK_DEFAULT,
    period: str = "3y",
    interval: str = "1d",
    lookback_3m: int = 63,
    lookback_12m: int = 252,
    cfg: HealthScoreConfig = HealthScoreConfig(),
) -> pd.DataFrame:
    """
    Compute industry metrics using ETF proxies vs a benchmark (SPY).

    Returns a DataFrame with:
    - Industry, Ticker (ETF)
    - Industry_Return_3m/12m
    - Industry_Excess_Return_3m/12m
    - Industry_Vol_12m
    - MaxDD_3y (for penalty term)
    - Industry_Health_Score

    Notes
    -----
    - Max drawdown uses the full price window available in `period`.
    """
    tickers = list(industry_to_etf.values())
    prices = safe_yf_download(tickers + [benchmark], period=period, interval=interval, auto_adjust=True, progress=False)
    if prices.empty or benchmark not in prices.columns:
        return pd.DataFrame()

    bench_prices = prices[benchmark]
    bench_ret3 = trailing_return(bench_prices, lookback_3m)
    bench_ret12 = trailing_return(bench_prices, lookback_12m)

    rows: List[dict] = []
    for industry, etf in industry_to_etf.items():
        if etf not in prices.columns:
            continue

        s = prices[etf]
        r3 = trailing_return(s, lookback_3m)
        r12 = trailing_return(s, lookback_12m)
        vol = realized_vol(s, lookback_12m)
        mdd = max_drawdown(s)

        rows.append(
            {
                "Industry": industry,
                "Ticker": etf,
                "Industry_Return_3m": r3,
                "Industry_Return_12m": r12,
                "Industry_Excess_Return_3m": r3 - bench_ret3,
                "Industry_Excess_Return_12m": r12 - bench_ret12,
                "Industry_Vol_12m": vol,
                "MaxDD_3y": mdd,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["Industry_Health_Score"] = compute_health_score(
        excess_return_12m=df["Industry_Excess_Return_12m"],
        excess_return_3m=df["Industry_Excess_Return_3m"],
        vol_12m=df["Industry_Vol_12m"],
        max_dd=df["MaxDD_3y"],
        w_ex12=cfg.w_ex12,
        w_ex3=cfg.w_ex3,
        w_vol=cfg.w_vol,
        w_mdd=cfg.w_mdd,
        scale=cfg.scale,
    )
    return df


def pick_top_industries(industry_metrics: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Pick top-N industries by Industry_Health_Score.

    Returns a DataFrame with columns: Industry, Ticker.
    """
    if industry_metrics.empty:
        return pd.DataFrame(columns=["Industry", "Ticker"])
    cols = ["Industry", "Ticker", "Industry_Health_Score"]
    return (
        industry_metrics[cols]
        .sort_values("Industry_Health_Score", ascending=False)
        .head(top_n)[["Industry", "Ticker"]]
        .reset_index(drop=True)
    )


def build_etf_to_tickers_map(top_industries: pd.DataFrame, top_k_holdings: int = 20) -> Dict[str, List[str]]:
    """Map ETF ticker -> top holdings tickers. Uses a fallback list if yfinance holdings are unavailable."""
    FALLBACK = {
        "ITA": ["RTX", "BA", "LHX", "NOC", "GD", "HII", "TDG", "TXT", "LMT"],
        "SOXX": ["NVDA", "AVGO", "AMD", "QCOM", "TXN", "INTC", "LRCX", "AMAT", "MRVL", "MU"],
        "VGT": ["AAPL", "MSFT", "NVDA", "AVGO", "CRM", "ADBE", "CSCO", "ORCL", "ACN"],
        "VOX": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ", "T", "CHTR", "CMCSA"],
        "IGV": ["MSFT", "ORCL", "ADBE", "CRM", "NOW", "INTU", "PANW", "SNOW", "TEAM"],
        "IYE": ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "KMI"],
        "IYM": ["LIN", "SHW", "FCX", "NEM", "APD", "ECL", "DOW", "DD", "PPG"],
        "IDU": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "PEG"],
    }

    etf_to_tickers: Dict[str, List[str]] = {}
    for etf in top_industries["Ticker"].dropna().astype(str).tolist():
        holdings = get_top_holdings(etf, top_k=top_k_holdings)
        if not holdings:
            holdings = FALLBACK.get(etf, [])
        etf_to_tickers[etf] = holdings[:top_k_holdings]
    return etf_to_tickers


def compute_company_metrics_for_top_industries(
    top_industries: pd.DataFrame,
    etf_to_tickers: Dict[str, List[str]],
    benchmark: str = BENCHMARK_DEFAULT,
    period: str = "3y",
    interval: str = "1d",
    lookback_3m: int = 63,
    lookback_12m: int = 252,
    cfg: HealthScoreConfig = HealthScoreConfig(),
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute company-level metrics for constituent tickers in top industries.

    Returns
    -------
    (companies_all, subindustry_all)

    companies_all columns include:
      - ETF_Name (parent industry label), Ticker, Company, Sector, Sub_Industry
      - Company_Return_3m/12m, Company_Excess_Return_3m/12m, Company_Vol_12m, MaxDD_3y
      - Company_Health_Score

    subindustry_all columns include:
      - ETF_Name, Sub_Industry
      - Sub_Industry_* metrics and Sub_Industry_Health_Score
    """
    # Union of all constituent tickers across top industries
    all_constituents = sorted(
        {
            t
            for etf in top_industries["Ticker"].dropna().astype(str).tolist()
            for t in etf_to_tickers.get(etf, [])
            if isinstance(t, str) and t.strip()
        }
    )

    prices = safe_yf_download(all_constituents + [benchmark], period=period, interval=interval, auto_adjust=True, progress=False)
    if prices.empty or benchmark not in prices.columns:
        return (pd.DataFrame(), pd.DataFrame())

    bench_prices = prices[benchmark]
    bench_ret3 = trailing_return(bench_prices, lookback_3m)
    bench_ret12 = trailing_return(bench_prices, lookback_12m)

    company_frames: List[pd.DataFrame] = []
    sub_frames: List[pd.DataFrame] = []

    for row in top_industries.itertuples(index=False):
        parent_industry = str(row.Industry)
        etf_ticker = str(row.Ticker)

        tickers = [t for t in etf_to_tickers.get(etf_ticker, []) if t in prices.columns]
        rows: List[dict] = []
        for t in tickers:
            s = prices[t]
            ret12 = trailing_return(s, lookback_12m)
            ret3 = trailing_return(s, lookback_3m)
            vol = realized_vol(s, lookback_12m)
            mdd = max_drawdown(s)
            ex12 = ret12 - bench_ret12
            ex3 = ret3 - bench_ret3
            sector, sub_industry, long_name = get_labels_safe(t)

            rows.append(
                {
                    "ETF_Name": parent_industry,
                    "Ticker": t,
                    "Company": long_name or t,
                    "Sector": sector,
                    "Sub_Industry": sub_industry,
                    "Company_Return_12m": ret12,
                    "Company_Return_3m": ret3,
                    "Company_Excess_Return_12m": ex12,
                    "Company_Excess_Return_3m": ex3,
                    "Company_Vol_12m": vol,
                    "MaxDD_3y": mdd,
                }
            )

        comp_df = pd.DataFrame(rows)
        if comp_df.empty:
            company_frames.append(comp_df)
            continue

        comp_df["Company_Health_Score"] = compute_health_score(
            excess_return_12m=comp_df["Company_Excess_Return_12m"],
            excess_return_3m=comp_df["Company_Excess_Return_3m"],
            vol_12m=comp_df["Company_Vol_12m"],
            max_dd=comp_df["MaxDD_3y"],
            w_ex12=cfg.w_ex12,
            w_ex3=cfg.w_ex3,
            w_vol=cfg.w_vol,
            w_mdd=cfg.w_mdd,
            scale=cfg.scale,
        )
        company_frames.append(comp_df)

        # Sub-industry aggregation
        sub = (
            comp_df.groupby("Sub_Industry", dropna=False)
            .agg(
                Sub_Industry_Return_12m=("Company_Return_12m", "mean"),
                Sub_Industry_Return_3m=("Company_Return_3m", "mean"),
                Sub_Industry_Excess_Return_12m=("Company_Excess_Return_12m", "mean"),
                Sub_Industry_Excess_Return_3m=("Company_Excess_Return_3m", "mean"),
                Sub_Industry_Vol_12m=("Company_Vol_12m", "median"),
                Sub_Industry_MaxDD_3y=("MaxDD_3y", "median"),
                Num_Names=("Ticker", "count"),
            )
            .reset_index()
        )
        sub["ETF_Name"] = parent_industry
        sub["Sub_Industry_Health_Score"] = compute_health_score(
            excess_return_12m=sub["Sub_Industry_Excess_Return_12m"],
            excess_return_3m=sub["Sub_Industry_Excess_Return_3m"],
            vol_12m=sub["Sub_Industry_Vol_12m"],
            max_dd=sub["Sub_Industry_MaxDD_3y"],
            w_ex12=cfg.w_ex12,
            w_ex3=cfg.w_ex3,
            w_vol=cfg.w_vol,
            w_mdd=cfg.w_mdd,
            scale=cfg.scale,
        )
        sub_frames.append(sub)

    companies_all = pd.concat(company_frames, ignore_index=True) if company_frames else pd.DataFrame()
    subinds_all = pd.concat(sub_frames, ignore_index=True) if sub_frames else pd.DataFrame()
    return (companies_all, subinds_all)


def build_final_financial_dataframe(
    industry_metrics: pd.DataFrame,
    companies_all: pd.DataFrame,
    subinds_all: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join company-level + sub-industry + industry metrics into a single table.

    Output columns match your notebook export (with consistent snake_case):
    - Company, Industry, Sub_Industry
    - Company_Health_Score, Sub_Industry_Health_Score, Industry_Health_Score
    - Industry_* metrics, Sub_Industry_* metrics, Company_* metrics
    """
    if companies_all.empty:
        return pd.DataFrame()

    # 1) Merge sub-industry metrics onto companies
    if not subinds_all.empty:
        companies_enriched = companies_all.merge(
            subinds_all[
                [
                    "ETF_Name",
                    "Sub_Industry",
                    "Sub_Industry_Health_Score",
                    "Sub_Industry_Return_12m",
                    "Sub_Industry_Return_3m",
                    "Sub_Industry_Excess_Return_12m",
                    "Sub_Industry_Excess_Return_3m",
                    "Sub_Industry_Vol_12m",
                ]
            ],
            on=["ETF_Name", "Sub_Industry"],
            how="left",
        )
    else:
        companies_enriched = companies_all.copy()
        for c in [
            "Sub_Industry_Health_Score",
            "Sub_Industry_Return_12m",
            "Sub_Industry_Return_3m",
            "Sub_Industry_Excess_Return_12m",
            "Sub_Industry_Excess_Return_3m",
            "Sub_Industry_Vol_12m",
        ]:
            companies_enriched[c] = np.nan

    # 2) Merge industry metrics (on ETF_Name == Industry)
    ind_cols = [
        "Industry",
        "Industry_Health_Score",
        "Industry_Return_12m",
        "Industry_Return_3m",
        "Industry_Excess_Return_12m",
        "Industry_Excess_Return_3m",
        "Industry_Vol_12m",
    ]
    companies_enriched = companies_enriched.merge(
        industry_metrics[ind_cols],
        left_on="ETF_Name",
        right_on="Industry",
        how="left",
        suffixes=("", "_industrydup"),
    )

    # Final selection & rename
    out = companies_enriched.rename(columns={"ETF_Name": "Industry"}).loc[
        :,
        [
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
        ],
    ].copy()

    return out


def dedupe_best_company_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep the best row per company (highest Company_Health_Score, then Industry_Health_Score).

    This matches your notebook logic for the "unique" export.
    """
    if df.empty or "Company" not in df.columns:
        return df
    return (
        df.sort_values(["Company_Health_Score", "Industry_Health_Score"], ascending=False)
        .drop_duplicates(subset="Company", keep="first")
        .reset_index(drop=True)
    )


def run_health_score_pipeline(
    top_n_industries: int = 5,
    benchmark: str = BENCHMARK_DEFAULT,
    sector_etfs: Dict[str, str] = SECTOR_ETFS_DEFAULT,
    extra_etfs: Dict[str, str] = EXTRA_INDUSTRY_ETFS_DEFAULT,
    period: str = "3y",
    interval: str = "1d",
    top_k_holdings: int = 20,
    cfg: HealthScoreConfig = HealthScoreConfig(),
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    End-to-end convenience wrapper.

    Returns
    -------
    (industry_metrics, final_financial_dataframe, final_unique_companies)
    """
    all_industry_etfs = {**sector_etfs, **extra_etfs}
    ind = compute_industry_metrics(all_industry_etfs, benchmark=benchmark, period=period, interval=interval, cfg=cfg)
    top = pick_top_industries(ind, top_n=top_n_industries)
    etf_map = build_etf_to_tickers_map(top, top_k_holdings=top_k_holdings)
    companies, subs = compute_company_metrics_for_top_industries(top, etf_map, benchmark=benchmark, period=period, interval=interval, cfg=cfg)
    final = build_final_financial_dataframe(ind, companies, subs)
    final_unique = dedupe_best_company_rows(final)
    return (ind, final, final_unique)


if __name__ == "__main__":
    # Compute and print top industries
    ind, final, final_unique = run_health_score_pipeline()
    top = pick_top_industries(ind, top_n=5)
    print("Top industries (dynamic):")
    print(top.to_string(index=False))
    print(f"\nCompanies (rows): {len(final)} | Unique companies: {final_unique['Company'].nunique() if not final_unique.empty else 0}")

    # Create output folder if it doesn't exist
    os.makedirs("output", exist_ok=True)

    final_unique.to_csv(
        "output/final_financial_data.csv",
        index=False)