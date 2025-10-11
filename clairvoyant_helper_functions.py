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
