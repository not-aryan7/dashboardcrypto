from __future__ import annotations
import pandas as pd
import requests
import time
import streamlit as st

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

@st.cache_data(ttl=3600, show_spinner=False)
def _load_binance(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    out = {}
    # Endpoints
    base_global = "https://api.binance.com/api/v3/klines"
    base_us = "https://api.binance.us/api/v3/klines"
    
    # Check which API works. This check is cached per session/function run effectively by logic flow,
    # but strictly speaking we re-check on failure. 
    # Let's try Global first, if 451/403/Timeout, switch to US for that ticker.
    
    # Ensure datetimes
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    
    start_ms = int(start.timestamp() * 1000)
    end_ms = int((end + pd.Timedelta(days=1)).timestamp() * 1000)

    session = requests.Session()

    for t in tickers:
        sym = BINANCE_MAP.get(t)
        if not sym:
            continue

        rows = []
        cur = start_ms
        
        # Decide base URL for this ticker (or session)
        # We start with global. If it fails, we mark a flag or just try US.
        current_base = base_global
        
        # Try a probe request or just start fetching.
        # If fetching fails midway, it's messy. Let's assume region block is immediate.
        
        while cur < end_ms:
            params = {"symbol": sym, "interval": "1d", "startTime": cur, "endTime": end_ms, "limit": 1000}
            try:
                r = session.get(current_base, params=params, timeout=5)
                
                # Debugging region blocks
                if r.status_code != 200:
                    print(f"BINANCE DEBUG: Status {r.status_code} from {current_base}")

                # Check for region block (451) or Forbidden (403)
                # Some environments might return other codes for blocked content, so we debug first.
                if r.status_code in [451, 403] and current_base == base_global:
                    print(f"Binance Global blocked ({r.status_code}). Switching to Binance US for {t}...")
                    current_base = base_us
                    r = session.get(current_base, params=params, timeout=5)
                
                r.raise_for_status()
                data = r.json()
                if not data:
                    break
                rows.extend(data)
                # Next start time
                cur = data[-1][6] + 1 
            except Exception as e:
                msg = f"Error fetching {t} from Binance ({current_base}): {e}"
                print(msg)
                # Don't clutter UI with every retry error, but store last one
                st.session_state["last_fetch_error"] = msg
                break
        
        if not rows:
            continue

        try:
            # Column 0 is Open Time, Column 4 is Close Price
            idx = pd.to_datetime([x[0] for x in rows], unit="ms")
            close = pd.to_numeric([x[4] for x in rows], errors="coerce")
            s = pd.Series(close, index=idx, name=t).sort_index()
            # Filter to requested range
            s = s.loc[(s.index >= start) & (s.index <= end + pd.Timedelta(days=1))] 
            out[t] = s
        except Exception as e:
            msg = f"Error parsing {t} from Binance: {e}"
            print(msg)
            continue

    return pd.DataFrame(out).sort_index().dropna(how="all")

@st.cache_data(ttl=3600, show_spinner=False)
def _load_coingecko(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    out = {}
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)
    days = max((end - start).days, 1)

    session = requests.Session()
    # Add User-Agent to avoid 403s
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    })

    for i, t in enumerate(tickers):
        coin_id = COINGECKO_MAP.get(t)
        if not coin_id:
            continue

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        # 'days' argument for CoinGecko:
        # 1/7/14/30/90/180/365/max
        # If we send a custom number, it tries its best, but sometimes defaults.
        # It's safer to request a bit more buffer.
        params = {"vs_currency": "usd", "days": str(max(days, 30)), "interval": "daily"}
        
        try:
            r = session.get(url, params=params, timeout=10)
            if r.status_code == 429:
                print(f"Rate limited on {t}, sleeping...")
                time.sleep(10) # Backoff
                r = session.get(url, params=params, timeout=10)
                
            r.raise_for_status()
            js = r.json()
            prices_list = js.get("prices", [])
            if not prices_list:
                print(f"No prices found for {t} from CoinGecko")
                continue

            idx = pd.to_datetime([p[0] for p in prices_list], unit="ms")
            vals = [p[1] for p in prices_list]
            s = pd.Series(vals, index=idx, name=t).sort_index()
            # Normalize index to 00:00:00 for easier joining if needed, or keep precise
            # CoinGecko usually returns ~00:00 UTC for 'daily' but sometimes varies.
            s.index = s.index.normalize()
            
            # Combine duplicates if any (take last)
            s = s[~s.index.duplicated(keep='last')]

            s = s.loc[(s.index >= start) & (s.index <= end)]
            out[t] = s
            
            # Polite delay between calls to avoid hitting rate limits immediately
            if i < len(tickers) - 1:
                time.sleep(1.2)
            
        except Exception as e:
            msg = f"Error fetching {t} from CoinGecko: {e}"
            print(msg)
            st.session_state["last_fetch_error"] = msg
            pass

    return pd.DataFrame(out).sort_index().dropna(how="all")

@st.cache_data(ttl=3600, show_spinner=False)
def _load_yfinance(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    import yfinance as yf
    out = {}
    
    # yfinance expects date strings or datetime objects
    # It handles batch downloading well
    try:
        data = yf.download(tickers, start=start, end=end, group_by='ticker', auto_adjust=True, threads=True)
        
        if data.empty:
            return pd.DataFrame()

        # If only one ticker is requested, yfinance returns a flat DataFrame (not MultiIndex columns for tickers)
        # unless we force it, but group_by='ticker' usually handles structure well.
        # However, if len(tickers) == 1, the columns are just 'Open', 'High'... 
        # If len(tickers) > 1, columns are ('BTC-USD', 'Open'), ...
        
        for t in tickers:
            try:
                if len(tickers) == 1:
                    # Single ticker case
                    s = data["Close"]
                else:
                    # Multi ticker case
                    if t not in data.columns:
                        continue
                    s = data[t]["Close"]
                
                s = s.dropna()
                # Ensure time zone naive or consistent? 
                # yfinance returns tz-aware. We often want naive or UTC.
                # The rest of the app seems to expect somewhat loose checks.
                # Let's strip tz just in case to match other sources
                if s.index.tz is not None:
                    s.index = s.index.tz_convert(None)

                # Filter range (yf usually precise but good to double check)
                s = s.loc[(s.index >= start) & (s.index <= end)]
                out[t] = s.sort_index()
            except Exception as e:
                print(f"Error extracting {t} from yfinance data: {e}")
                continue
                
    except Exception as e:
        msg = f"Error fetching from Yahoo Finance: {e}"
        print(msg)
        st.session_state["last_fetch_error"] = msg
        return pd.DataFrame()

    return pd.DataFrame(out).sort_index().dropna(how="all")

def get_prices(tickers: list[str], start: pd.Timestamp, end: pd.Timestamp, source: str = "auto") -> pd.DataFrame:
    tickers = [t.strip().upper() for t in tickers if t.strip()]
    if not tickers:
        return pd.DataFrame()

    source = (source or "auto").lower()
    
    # Define strategy
    # If auto, try Binance first (fastest/best data), then Yahoo (Reliable), then CoinGecko (Backup)
    if source == "auto":
        print("Attempting Binance...")
        df = _load_binance(tickers, start, end)
        if is_valid_result(df, tickers):
            return df
        
        print("Binance partial/failed. Attempting Yahoo Finance...")
        df_yf = _load_yfinance(tickers, start, end)
        if is_valid_result(df_yf, tickers):
            return df_yf

        print("Yahoo partial/failed. Attempting CoinGecko...")
        df_cg = _load_coingecko(tickers, start, end)
        if not df_cg.empty:
            return df_cg
            
        # Return best effort (yahoo or binance)
        if not df_yf.empty: 
            return df_yf
        return df

    elif source == "binance":
        return _load_binance(tickers, start, end)
    elif source == "yahoo":  # Allow manual selection if added to UI later
        return _load_yfinance(tickers, start, end)
    elif source == "coingecko":
        return _load_coingecko(tickers, start, end)

    return pd.DataFrame()

def is_valid_result(df: pd.DataFrame, requested_tickers: list[str]) -> bool:
    """Check if the result is 'good enough' to avoid falling back."""
    if df.empty:
        return False
    # If we got at least 50% of requested tickers, consider it a success?
    # Or strict: if any column exists.
    # For now: if not empty, it's something.
    return True

