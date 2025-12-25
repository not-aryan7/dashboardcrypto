from __future__ import annotations
import pandas as pd
import requests

DEFAULT_UNIVERSE = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOGE-USD","AVAX-USD"]

COINGECKO_MAP = {
    "BTC-USD": "bitcoin",
    "ETH-USD": "ethereum",
    "SOL-USD": "solana",
    "BNB-USD": "binancecoin",
    "XRP-USD": "ripple",
    "ADA-USD": "cardano",
    "DOGE-USD": "dogecoin",
    "AVAX-USD": "avalanche-2",
}

BINANCE_MAP = {
    "BTC-USD": "BTCUSDT",
    "ETH-USD": "ETHUSDT",
    "SOL-USD": "SOLUSDT",
    "BNB-USD": "BNBUSDT",
    "XRP-USD": "XRPUSDT",
    "ADA-USD": "ADAUSDT",
    "DOGE-USD": "DOGEUSDT",
    "AVAX-USD": "AVAXUSDT",
}

def last_price_and_change(series: pd.Series) -> tuple[float, float]:
    s = series.dropna()
    if len(s) < 2:
        return float("nan"), float("nan")
    px = float(s.iloc[-1])
    prev = float(s.iloc[-2])
    return px, (px/prev - 1) * 100.0

def _load_binance(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    out = {}
    base = "https://api.binance.com/api/v3/klines"
    start_ms = int(start.timestamp() * 1000)
    end_ms = int((end + pd.Timedelta(days=1)).timestamp() * 1000)

    for t in tickers:
        sym = BINANCE_MAP.get(t)
        if not sym:
            continue

        rows = []
        cur = start_ms
        while cur < end_ms:
            params = {"symbol": sym, "interval": "1d", "startTime": cur, "endTime": end_ms, "limit": 1000}
            r = requests.get(base, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            rows.extend(data)
            cur = data[-1][0] + 24*60*60*1000

        if not rows:
            continue

        idx = pd.to_datetime([x[0] for x in rows], unit="ms")
        close = pd.to_numeric([x[4] for x in rows], errors="coerce")
        s = pd.Series(close, index=idx, name=t).sort_index()
        s = s.loc[(s.index >= start) & (s.index <= end)]
        out[t] = s

    return pd.DataFrame(out).sort_index().dropna(how="all")

def _load_coingecko(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    out = {}
    days = max((end - start).days, 1)

    for t in tickers:
        coin_id = COINGECKO_MAP.get(t)
        if not coin_id:
            continue

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": min(days + 5, 3650), "interval": "daily"}
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        js = r.json()
        prices_list = js.get("prices", [])
        if not prices_list:
            continue

        idx = pd.to_datetime([p[0] for p in prices_list], unit="ms")
        vals = [p[1] for p in prices_list]
        s = pd.Series(vals, index=idx, name=t).sort_index()
        s = s.loc[(s.index >= start) & (s.index <= end)]
        out[t] = s

    return pd.DataFrame(out).sort_index().dropna(how="all")

def get_prices(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp, source: str = "auto") -> pd.DataFrame:
    tickers = [t.strip().upper() for t in tickers if t.strip()]
    if not tickers:
        return pd.DataFrame()

    source = (source or "auto").lower()
    tries = ["binance", "coingecko"] if source == "auto" else [source]

    for s in tries:
        try:
            if s == "binance":
                df = _load_binance(tickers, start, end)
            elif s == "coingecko":
                df = _load_coingecko(tickers, start, end)
            else:
                df = pd.DataFrame()

            if not df.empty:
                return df
        except Exception:
            continue

    return pd.DataFrame()
