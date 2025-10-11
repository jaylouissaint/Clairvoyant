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

# ---------- Helper to pull top holdings for each ETF (robust) ----------


def get_top_holdings(etf_ticker: str, top_k: int = 15):
    """
    Try multiple yfinance pathways to fetch ETF holdings.
    Falls back to empty list if not available.
    """
    try:
        t = yf.Ticker(etf_ticker)

        # Newer yfinance: .fund_holdings or .get_fund_holdings()
        fh = getattr(t, "fund_holdings", None)
        if isinstance(fh, pd.DataFrame) and not fh.empty and "symbol" in fh.columns:
            syms = fh["symbol"].dropna().astype(str).tolist()
            return syms[:top_k]

        if hasattr(t, "get_fund_holdings"):
            df = t.get_fund_holdings()
            if isinstance(df, pd.DataFrame) and not df.empty and "symbol" in df.columns:
                syms = df["symbol"].dropna().astype(str).tolist()
                return syms[:top_k]

        # Some builds expose in .info
        info = {}
        if hasattr(t, "get_info"):
            info = t.get_info()
        elif hasattr(t, "info"):
            info = t.info

        if isinstance(info, dict):
            cand = info.get("holdings", None)
            if isinstance(cand, list) and cand:
                # sometimes it's a list of dicts with 'symbol'
                syms = [d.get("symbol") for d in cand if isinstance(d, dict) and d.get("symbol")]
                if syms:
                    return syms[:top_k]
    except Exception:
        pass

    # If nothing worked, return empty (you can manually fill later)
    return []