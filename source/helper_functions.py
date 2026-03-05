"""
helper_functions.py

Small, reusable utilities used across the Clairvoyant project.

Keep this file "pure helpers":
- no top-level execution
- no project-specific file paths
- functions are safe to import from anywhere
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Union

import numpy as np
import pandas as pd
import yfinance as yf
import random
import time


TickerLike = Union[str, Sequence[str], Iterable[str]]


try:
    import requests_cache
    requests_cache.install_cache("output/yf_cache", expire_after=60 * 60 * 12)  # 12h cache
except Exception:
    # caching is optional
    pass


def safe_yf_download(
    tickers,
    *,
    period="3y",
    interval="1d",
    auto_adjust=True,
    progress=False,
    max_retries=6,
    base_sleep=2.0,
):
    """
    Safer yfinance downloader:
    - Uses request caching (if available)
    - Retries with exponential backoff + jitter on rate limits / transient errors
    - Downloads all tickers in ONE request (reduces request count)
    """
    if isinstance(tickers, str):
        tickers_list = [tickers]
    else:
        tickers_list = [str(t).strip() for t in list(tickers) if str(t).strip()]

    if not tickers_list:
        return pd.DataFrame()

    last_err = None
    for attempt in range(max_retries):
        try:
            data = yf.download(
                tickers=tickers_list,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                progress=progress,
                threads=False,          # important: fewer parallel requests
                group_by="column",
            )

            if data is None or len(data) == 0:
                return pd.DataFrame()

            if isinstance(data.columns, pd.MultiIndex):
                level0 = data.columns.get_level_values(0)
                field = "Close" if "Close" in level0 else ("Adj Close" if "Adj Close" in level0 else None)
                if field is None:
                    return pd.DataFrame()
                close = data[field].copy()
                close.columns = [str(c) for c in close.columns]
                return close

            if "Close" in data.columns:
                close = data[["Close"]].copy()
                close.columns = [tickers_list[0]]
                return close

            return pd.DataFrame()

        except Exception as e:
            last_err = e
            # exponential backoff + jitter
            sleep_s = base_sleep * (2 ** attempt) + random.uniform(0.0, 1.0)
            time.sleep(sleep_s)

    # exhausted retries
    return pd.DataFrame()


def trailing_return(series: pd.Series, lookback_days: int) -> float:
    """Trailing return over lookback_days: last / lagged - 1."""
    s = series.dropna()
    if len(s) < lookback_days + 1:
        return np.nan
    return float(s.iloc[-1] / s.iloc[-lookback_days - 1] - 1.0)


def realized_vol(series: pd.Series, lookback_days: int = 252) -> float:
    """Annualized realized volatility using last lookback_days of daily returns."""
    r = series.dropna().pct_change().dropna().tail(lookback_days)
    if r.empty:
        return np.nan
    return float(np.sqrt(252) * r.std())


def max_drawdown(series: pd.Series) -> float:
    """Maximum drawdown over the available series window."""
    s = series.dropna()
    if s.empty:
        return np.nan
    return float((s / s.cummax() - 1.0).min())


def zscore(x: Union[pd.Series, Sequence[float]]) -> pd.Series:
    """Z-score standardization with safe zero fallback when std is 0/NaN."""
    x = pd.Series(x, dtype=float)
    std = x.std(ddof=0)
    if std == 0 or pd.isna(std):
        return pd.Series(np.zeros(len(x)), index=x.index)
    return (x - x.mean()) / std


def compute_health_score(
    *,
    excess_return_12m: Union[pd.Series, Sequence[float]],
    excess_return_3m: Union[pd.Series, Sequence[float]],
    vol_12m: Union[pd.Series, Sequence[float]],
    max_dd: Union[pd.Series, Sequence[float]],
    w_ex12: float = 0.45,
    w_ex3: float = 0.35,
    w_vol: float = 0.10,
    w_mdd: float = 0.10,
    scale: float = 100.0,
) -> pd.Series:
    """
    Composite Health Score (higher is better):

      scale * (
        w_ex12 * z(Excess 12M Return) +
        w_ex3  * z(Excess  3M Return) -
        w_vol  * z(Volatility) -
        w_mdd  * z(|Max Drawdown|)
      )
    """
    ex12 = pd.Series(excess_return_12m, dtype=float)
    ex3 = pd.Series(excess_return_3m, dtype=float)
    vol = pd.Series(vol_12m, dtype=float)
    mdd = pd.Series(max_dd, dtype=float).abs()

    score = (
        w_ex12 * zscore(ex12.fillna(0.0))
        + w_ex3 * zscore(ex3.fillna(0.0))
        - w_vol * zscore(vol.fillna(0.0))
        - w_mdd * zscore(mdd.fillna(0.0))
    )
    return scale * score


def get_labels_safe(ticker: str):
    """Fetch (sector, industry, longName) safely from yfinance; return Nones if unavailable."""
    info = {}
    try:
        tk = yf.Ticker(ticker)
        info = tk.get_info() if hasattr(tk, "get_info") else tk.info
    except Exception:
        info = {}

    sector = info.get("sector") if isinstance(info, dict) else None
    industry = info.get("industry") if isinstance(info, dict) else None
    long_name = info.get("longName") if isinstance(info, dict) else None
    return sector, industry, long_name


def get_top_holdings(etf_ticker: str, top_k: int = 15) -> List[str]:
    """Try multiple yfinance pathways to fetch ETF holdings; return list of tickers (may be empty)."""
    try:
        t = yf.Ticker(etf_ticker)

        fh = getattr(t, "fund_holdings", None)
        if isinstance(fh, pd.DataFrame) and not fh.empty and "symbol" in fh.columns:
            syms = fh["symbol"].dropna().astype(str).tolist()
            return syms[:top_k]

        if hasattr(t, "get_fund_holdings"):
            df = t.get_fund_holdings()
            if isinstance(df, pd.DataFrame) and not df.empty and "symbol" in df.columns:
                syms = df["symbol"].dropna().astype(str).tolist()
                return syms[:top_k]

        info = {}
        if hasattr(t, "get_info"):
            info = t.get_info()
        elif hasattr(t, "info"):
            info = t.info

        if isinstance(info, dict):
            cand = info.get("holdings", None)
            if isinstance(cand, list) and cand:
                syms = [d.get("symbol") for d in cand if isinstance(d, dict) and d.get("symbol")]
                if syms:
                    return syms[:top_k]
    except Exception:
        pass

    return []
